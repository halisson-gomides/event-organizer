from litestar import Litestar, get, post
from litestar.middleware.session.server_side import ServerSideSessionConfig
from litestar.plugins.htmx import HTMXPlugin, HTMXTemplate, HTMXRequest
from litestar.plugins.flash import FlashPlugin, FlashConfig
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.template.config import TemplateConfig
from litestar.static_files import create_static_files_router
from litestar.response import Template
from advanced_alchemy.extensions.litestar import filters, providers
from advanced_alchemy.extensions.litestar.session import SQLAlchemyAsyncSessionBackend
from config import settings
from database import alchemy_plugin, alchemy_config
from models import UserSessionModel, EventModel
from controllers.user_controller import UserController
from controllers.event_controller import EventController
from controllers.participant_controller import ParticipantController
from services.event_service import EventService
from pathlib import Path
# import logging

# # Configure logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# Session configuration
session_config = ServerSideSessionConfig(
    key=settings.secret_key,
    max_age=3600,  # 1 hour
)

# Session backend
session_backend = SQLAlchemyAsyncSessionBackend(
    config=session_config,
    alchemy_config=alchemy_config,
    model=UserSessionModel,
)

# Template Configuration
template_config=TemplateConfig(
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
    if request.htmx:
        print(request.htmx)  # HTMXDetails instance
        print(request.htmx.current_url)

    data, total = await events_service.list_and_count(filters.LimitOffset(limit=10, offset=0))
    context = {
        "events": data,
        "total": total,
        "has_events": total > 0
        }
    return HTMXTemplate(template_name="event_list.html", context=context, push_url="/")


# Flash Messages Configuration
flash_config = FlashConfig(template_config=template_config)

# Application
app = Litestar(
    route_handlers=[index, statics, UserController, EventController, ParticipantController],
    plugins=[alchemy_plugin, HTMXPlugin(), FlashPlugin(flash_config)],
    middleware=[session_config.middleware],
    template_config=template_config,
    request_class=HTMXRequest,
    debug=True,  # Enable debug mode
)