from litestar import Litestar, get, post, Request
from litestar.middleware.session.server_side import ServerSideSessionConfig
from litestar.plugins.htmx import HTMXPlugin, HTMXTemplate, HTMXRequest
from litestar.plugins.flash import FlashPlugin, FlashConfig, flash
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.template.config import TemplateConfig
from litestar.static_files import create_static_files_router
from litestar.response import Template, Redirect
from litestar.status_codes import HTTP_302_FOUND
from litestar.exceptions import PermissionDeniedException
from advanced_alchemy.extensions.litestar import filters, providers
from advanced_alchemy.extensions.litestar.session import SQLAlchemyAsyncSessionBackend
from config import settings
from database import alchemy_plugin, alchemy_config
from models import UserSessionModel, EventModel
from controllers.user_controller import UserController
from controllers.event_controller import EventController
from controllers.participant_controller import ParticipantController
from controllers.auth_controller import AuthController
from controllers.occurrence_controller import OccurrenceController
from controllers.registration_controller import RegistrationController
from services.event_service import EventService
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
# import logging

# # Configure logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# Import middleware classes
from litestar.middleware.session.base import SessionMiddleware
from litestar.middleware.base import DefineMiddleware

# Create a minimal session config for the backend
_temp_session_config = ServerSideSessionConfig(
    key=settings.secret_key,
    max_age=3600,
)

# Session backend using SQLAlchemy - stores sessions in user_sessions table
session_backend = SQLAlchemyAsyncSessionBackend(
    config=_temp_session_config,
    alchemy_config=alchemy_config,
    model=UserSessionModel,
)

# Create session middleware with our SQLAlchemy backend
# The middleware only needs the backend - other config is in the backend itself
session_middleware = DefineMiddleware(
    SessionMiddleware,
    backend=session_backend,
)

# Jinja2 filters
def to_local_time(dt: datetime, fmt: str = '%d/%m/%Y %H:%M', tz: str = "America/Sao_Paulo") -> str:
    """Convert UTC datetime to local timezone and format it."""
    if dt is None:
        return ""
    if dt.tzinfo is None:
        # Assume UTC if no timezone info
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    local_dt = dt.astimezone(ZoneInfo(tz))
    return local_dt.strftime(fmt)

# Create Jinja2 engine instance with custom filters
jinja_engine = JinjaTemplateEngine(directory=Path("templates"))
jinja_engine.engine.filters["to_local_time"] = to_local_time

# Template Configuration
template_config = TemplateConfig(
    directory=Path("templates"),
    engine=JinjaTemplateEngine,
)

# Statics Files Configuration
statics = create_static_files_router(path="/static", directories=[Path("static")])

# Routes
index_dependencies = providers.create_service_dependencies(
    EventService,
    "events_service",
    load=[EventModel.occurrences],
    filters={"pagination_type": "limit_offset"},
)

@get(path="/", name="index", dependencies=index_dependencies)
async def index(request: HTMXRequest, events_service: EventService) -> Template:
    """Index Page"""
    # if request.htmx:
    #     print(request.htmx)  # HTMXDetails instance
    #     print(request.htmx.current_url)

    data, total = await events_service.list_and_count(filters.LimitOffset(limit=10, offset=0))
    context = {
        "events": data,
        "total": total,
        "has_events": total > 0
        }
    return HTMXTemplate(template_name="event_list.html", context=context, push_url="/")


# Exception Handlers
def permission_denied_handler(request: Request, exc: PermissionDeniedException) -> Redirect:
    """Handle permission denied exceptions with a friendly redirect and message."""
    flash(request, str(exc.detail), category="error")
    
    # Redirect to the referring page or home
    referer = request.headers.get("referer", "/")
    return Redirect(path=referer, status_code=HTTP_302_FOUND)


# Flash Messages Configuration
flash_config = FlashConfig(template_config=template_config)

# Application
app = Litestar(
    route_handlers=[index, statics, UserController, EventController, ParticipantController, AuthController, OccurrenceController, RegistrationController],
    plugins=[alchemy_plugin, HTMXPlugin(), FlashPlugin(flash_config)],
    middleware=[session_middleware],
    template_config=TemplateConfig(
        directory=Path("templates"),
        engine=jinja_engine,
    ),
    request_class=HTMXRequest,
    exception_handlers={PermissionDeniedException: permission_denied_handler},
    debug=True,  # Enable debug mode
)