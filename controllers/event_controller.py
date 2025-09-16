from typing import Annotated

from litestar import Controller, get, post, patch, delete
from litestar.params import Dependency, Parameter
from advanced_alchemy.extensions.litestar import filters, providers, service
from services.event_service import EventService
from schemas import EventRead, EventCreate, EventUpdate
from models import EventModel


class EventController(Controller):
    """Event CRUD endpoints"""

    dependencies = providers.create_service_dependencies(
        EventService,
        "events_service",
        load=[EventModel.occurrences],
        filters={"pagination_type": "limit_offset", "id_filter": int, "search": "email", "search_ignore_case": True},
    )


    @get(path="/events", response_model=service.OffsetPagination[EventRead])
    async def list_events(
        self,
        events_service: EventService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[EventRead]:
        """List all events with pagination."""
        results, total = await events_service.list_and_count(*filters)
        return events_service.to_schema(results, total, filters=filters, schema_type=EventRead)
    

    @post(path="/events")
    async def create_event(
        self,
        events_service: EventService,
        data: EventCreate,
    ) -> EventRead:
        """Create a new event."""
        obj = await events_service.create(data)
        return events_service.to_schema(obj, schema_type=EventRead)
    

    @get(path="/events/{event_id:int}")
    async def get_event(
        self,
        events_service: EventService,
        event_id: int = Parameter(
            title="Event ID",
            description="The event to retrieve.",
        ),
    ) -> EventRead:
        """Get an existing event."""
        obj = await events_service.get(event_id)
        return events_service.to_schema(obj, schema_type=EventRead)
    

    @patch(path="/events/{event_id:int}")
    async def update_event(
        self,
        events_service: EventService,
        data: EventUpdate,
        event_id: int = Parameter(
            title="Event ID",
            description="The event to update.",
        ),
    ) -> EventRead:
        """Update an event."""
        obj = await events_service.update(data, item_id=event_id, auto_commit=True)
        return events_service.to_schema(obj, schema_type=EventRead)
    

    @delete(path="/events/{event_id:int}")
    async def delete_event(
        self,
        events_service: EventService,
        event_id: int = Parameter(
            title="Event ID",
            description="The event to delete.",
        ),
    ) -> None:
        """Delete an event from the system."""
        _ = await events_service.delete(event_id)