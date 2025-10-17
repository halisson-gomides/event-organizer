from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from advanced_alchemy.extensions.litestar import repository, service
from models import EventModel, EventOccurrenceModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from config import settings


class EventService(service.SQLAlchemyAsyncRepositoryService[EventModel]):
    """Event service."""
    class Repo(repository.SQLAlchemyAsyncRepository[EventModel]):
        """Event repository."""
        model_type = EventModel
    repository_type = Repo

    async def generate_occurrences(self, event: EventModel, session: AsyncSession) -> list[EventOccurrenceModel]:
        """
        Generate EventOccurrence records from an EventModel.
        
        For single events: creates 1 occurrence
        For recurring events: creates multiple occurrences based on recurrence_rule
        
        Args:
            event: The EventModel to generate occurrences for
            session: SQLAlchemy async session for database operations
            
        Returns:
            List of created EventOccurrenceModel instances
        """
        occurrences = []
        
        # Delete existing occurrences for this event
        stmt = delete(EventOccurrenceModel).where(EventOccurrenceModel.event_id == event.id)
        await session.execute(stmt)
        
        if event.is_recurring:
            # Generate occurrences for recurring events
            occurrences = await self._generate_recurring_occurrences(event, session)
        else:
            # Generate single occurrence for one-off events
            if event.single_start and event.single_end:
                occurrence = EventOccurrenceModel(
                    event_id=event.id,
                    start_at=event.single_start,
                    end_at=event.single_end
                )
                session.add(occurrence)
                occurrences.append(occurrence)
        
        await session.flush()
        return occurrences
    

    async def _generate_recurring_occurrences(self, event: EventModel, session: AsyncSession) -> list[EventOccurrenceModel]:
        """
        Generate occurrences for a recurring event based on recurrence_rule.
        
        Recurrence rule format:
        {
            "weekdays": ["0", "1", "2"],  # 0=Monday, 1=Tuesday, ..., 6=Sunday
            "time_windows": ["10:00-12:00", "14:00-16:00"]
        }
        """
        occurrences = []
        
        if not event.recurrence_rule or not event.recurrence_start_date or not event.recurrence_end_date:
            return occurrences
        
        rule = event.recurrence_rule
        weekdays = rule.get("weekdays", [])
        time_windows = rule.get("time_windows", [])
        
        if not weekdays or not time_windows:
            return occurrences
        
        # Convert weekday strings to integers
        try:
            weekdays = [int(day) for day in weekdays]
        except (ValueError, TypeError):
            return occurrences
        
        # Generate occurrences for each date in the recurrence period
        current_date = event.recurrence_start_date
        end_date = event.recurrence_end_date
        
        while current_date <= end_date:
            # Check if current day of week is in the recurrence rule
            if current_date.weekday() in weekdays:
                # Create an occurrence for each time window
                for time_window in time_windows:
                    try:
                        start_time_str, end_time_str = time_window.split("-")
                        start_hour, start_min = map(int, start_time_str.strip().split(":"))
                        end_hour, end_min = map(int, end_time_str.strip().split(":"))
                        
                        # Create datetime objects in local timezone and convert to UTC
                        local_start_dt = datetime.combine(current_date, datetime.min.time()).replace(
                            hour=start_hour, minute=start_min, tzinfo=ZoneInfo(settings.timezone)
                        )
                        local_end_dt = datetime.combine(current_date, datetime.min.time()).replace(
                            hour=end_hour, minute=end_min, tzinfo=ZoneInfo(settings.timezone)
                        )

                        # Convert to UTC for storage
                        start_dt = local_start_dt.astimezone(ZoneInfo("UTC"))
                        end_dt = local_end_dt.astimezone(ZoneInfo("UTC"))
                        
                        occurrence = EventOccurrenceModel(
                            event_id=event.id,
                            start_at=start_dt,
                            end_at=end_dt
                        )
                        session.add(occurrence)
                        occurrences.append(occurrence)
                    except (ValueError, IndexError):
                        # Skip malformed time windows
                        continue
            
            # Move to next day
            current_date += timedelta(days=1)
        
        return occurrences
