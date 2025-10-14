from typing import Annotated
from datetime import datetime, date

from litestar import Controller, get, post, patch, delete, Request
from litestar.params import Dependency, Parameter, Body
from litestar.response import Template
from litestar.status_codes import HTTP_200_OK
from litestar.plugins.htmx import HTMXTemplate, HTMXRequest
from litestar.plugins.flash import flash
from advanced_alchemy.extensions.litestar import filters, providers, service
from services.event_service import EventService
from schemas import EventRead, EventCreate, EventUpdate
from models import EventModel
from middleware import require_profiles


class EventController(Controller):
    """Event CRUD endpoints"""

    dependencies = providers.create_service_dependencies(
        EventService,
        "events_service",
        load=[EventModel.occurrences],
        filters={"pagination_type": "limit_offset", "id_filter": int, "search": "name", "search_ignore_case": True},
    )


    @get(path="/events")
    async def list_events(
        self,
        request: HTMXRequest,
        events_service: EventService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> Template:
        """List all events with pagination."""
        results, total = await events_service.list_and_count(*filters)
        events_data = events_service.to_schema(results, total, filters=filters, schema_type=EventRead)
        
        context = {
            "events": events_data.items,
            "total": events_data.total,
            "has_events": len(events_data.items) > 0
        }
        
        if request.htmx:
            return HTMXTemplate(template_name="event_list_content.html", context=context)
        return HTMXTemplate(template_name="event_list.html", context=context)
    

    @get(path="/events/new")
    async def new_event_form(self, request: Request) -> Template:
        """Render the event creation form."""
        require_profiles(request, ["admin", "organizer"])
        return HTMXTemplate(template_name="event_form.html")
    

    @post(path="/events")
    async def create_event(
        self,
        request: HTMXRequest,
        events_service: EventService,
    ) -> Template:
        """Create a new event."""
        require_profiles(request, ["admin", "organizer"])
        try:
            # Get form data from request
            form_data = await request.form()
            
            # Convert form data to EventCreate schema
            form_dict = {}
            
            # Basic fields
            form_dict["name"] = form_data.get("name", "")
            form_dict["description"] = form_data.get("description", "")
            
            # Handle checkbox - convert "on" or "true" to boolean
            is_recurring_value = form_data.get("is_recurring")
            form_dict["is_recurring"] = is_recurring_value in ["on", "true", True]
            
            # Handle datetime fields for single events
            single_start = form_data.get("single_start")
            if single_start:
                form_dict["single_start"] = datetime.fromisoformat(single_start)
            
            single_end = form_data.get("single_end")
            if single_end:
                form_dict["single_end"] = datetime.fromisoformat(single_end)
                
            # Handle date fields for recurring events
            recurrence_start_date = form_data.get("recurrence_start_date")
            if recurrence_start_date:
                form_dict["recurrence_start_date"] = date.fromisoformat(recurrence_start_date)
            
            recurrence_end_date = form_data.get("recurrence_end_date")
            if recurrence_end_date:
                form_dict["recurrence_end_date"] = date.fromisoformat(recurrence_end_date)
                
            # Handle recurrence rule
            recurrence_rule = {}
            if form_data.get("recurrence_rule.weekdays"):
                # Parse weekdays (comma-separated string to list)
                weekdays_str = form_data.get("recurrence_rule.weekdays", "")
                weekdays = [day.strip() for day in weekdays_str.split(",") if day.strip()]
                recurrence_rule["weekdays"] = weekdays
                
            if form_data.get("recurrence_rule.time_windows"):
                # Parse time windows (comma-separated HH:MM-HH:MM format)
                time_windows_str = form_data.get("recurrence_rule.time_windows", "")
                time_windows = [window.strip() for window in time_windows_str.split(",") if window.strip()]
                recurrence_rule["time_windows"] = time_windows
                
            form_dict["recurrence_rule"] = recurrence_rule
            form_dict["occurrences"] = []  # Empty list as default
            
            # Create EventCreate instance
            event_data = EventCreate(**form_dict)
            
            obj = await events_service.create(event_data)
            
            # Flash success message
            flash(request, "Evento criado com sucesso!", category="success")
            
            # Return updated event list
            results, total = await events_service.list_and_count()
            events_data = events_service.to_schema(results, total, schema_type=EventRead)
            
            context = {
                "events": events_data.items,
                "total": events_data.total,
                "has_events": len(events_data.items) > 0
            }
            
            return HTMXTemplate(template_name="event_list_content.html", context=context)
            
        except Exception as e:
            # Flash error message
            flash(request, f"Erro ao criar evento: {str(e)}", category="error")
            
            # Return the form with error
            return HTMXTemplate(template_name="event_form.html")
    

    @get(path="/events/{event_id:int}/edit")
    async def edit_event_form(
        self,
        request: Request,
        events_service: EventService,
        event_id: int = Parameter(
            title="Event ID",
            description="The event to edit.",
        ),
    ) -> Template:
        """Render the event edit form."""
        require_profiles(request, ["admin", "organizer"])
        event = await events_service.get(event_id)
        context = {
            "event": event
        }
        return HTMXTemplate(template_name="event_form.html", context=context)
    

    @patch(path="/events/{event_id:int}")
    async def update_event(
        self,
        request: HTMXRequest,
        events_service: EventService,
        event_id: int = Parameter(
            title="Event ID",
            description="The event to update.",
        ),
    ) -> Template:
        """Update an event."""
        require_profiles(request, ["admin", "organizer"])
        try:
            # Get form data from request
            form_data = await request.form()

            # Convert form data to EventUpdate schema
            form_dict = {}

            # Basic fields
            form_dict["name"] = form_data.get("name", "")
            form_dict["description"] = form_data.get("description", "")

            # Handle checkbox - convert "on" or "true" to boolean
            is_recurring_value = form_data.get("is_recurring")
            form_dict["is_recurring"] = is_recurring_value in ["on", "true", True]

            # Handle datetime fields for single events
            single_start = form_data.get("single_start")
            if single_start:
                form_dict["single_start"] = datetime.fromisoformat(single_start)

            single_end = form_data.get("single_end")
            if single_end:
                form_dict["single_end"] = datetime.fromisoformat(single_end)

            # Handle date fields for recurring events
            recurrence_start_date = form_data.get("recurrence_start_date")
            if recurrence_start_date:
                form_dict["recurrence_start_date"] = date.fromisoformat(recurrence_start_date)

            recurrence_end_date = form_data.get("recurrence_end_date")
            if recurrence_end_date:
                form_dict["recurrence_end_date"] = date.fromisoformat(recurrence_end_date)

            # Handle recurrence rule
            recurrence_rule = {}
            if form_data.get("recurrence_rule.weekdays"):
                # Parse weekdays (comma-separated string to list)
                weekdays_str = form_data.get("recurrence_rule.weekdays", "")
                weekdays = [day.strip() for day in weekdays_str.split(",") if day.strip()]
                recurrence_rule["weekdays"] = weekdays

            if form_data.get("recurrence_rule.time_windows"):
                # Parse time windows (comma-separated HH:MM-HH:MM format)
                time_windows_str = form_data.get("recurrence_rule.time_windows", "")
                time_windows = [window.strip() for window in time_windows_str.split(",") if window.strip()]
                recurrence_rule["time_windows"] = time_windows

            form_dict["recurrence_rule"] = recurrence_rule

            # Create EventUpdate instance
            event_data = EventUpdate(**form_dict)

            obj = await events_service.update(event_data, item_id=event_id, auto_commit=True)

            # Flash success message
            flash(request, "Evento atualizado com sucesso!", category="success")

            # Return updated event list
            results, total = await events_service.list_and_count()
            events_data = events_service.to_schema(results, total, schema_type=EventRead)

            context = {
                "events": events_data.items,
                "total": events_data.total,
                "has_events": len(events_data.items) > 0
            }

            return HTMXTemplate(template_name="event_list_content.html", context=context)

        except Exception as e:
            # Flash error message
            flash(request, f"Erro ao atualizar evento: {str(e)}", category="error")

            # Return the form with error
            event = await events_service.get(event_id)
            context = {"event": event}
            return HTMXTemplate(template_name="event_form.html", context=context)
    

    @delete(path="/events/{event_id:int}", status_code=HTTP_200_OK)
    async def delete_event(
        self,
        request: HTMXRequest,
        events_service: EventService,
        event_id: int = Parameter(
            title="Event ID",
            description="The event to delete.",
        ),
    ) -> Template:
        """Delete an event from the system."""
        require_profiles(request, ["admin", "organizer"])
        try:
            await events_service.delete(event_id)
            
            # Flash success message
            flash(request, "Evento excluído com sucesso!", category="success")
            
            # Return updated event list
            results, total = await events_service.list_and_count()
            events_data = events_service.to_schema(results, total, schema_type=EventRead)
            
            context = {
                "events": events_data.items,
                "total": events_data.total,
                "has_events": len(events_data.items) > 0
            }
            
            return HTMXTemplate(template_name="event_list_content.html", context=context)
            
        except Exception as e:
            # Flash error message
            flash(request, f"Erro ao excluir evento: {str(e)}", category="error")
            
            # Return current event list
            results, total = await events_service.list_and_count()
            events_data = events_service.to_schema(results, total, schema_type=EventRead)
            
            context = {
                "events": events_data.items,
                "total": events_data.total,
                "has_events": len(events_data.items) > 0
            }
            
            return HTMXTemplate(template_name="event_list_content.html", context=context)