from litestar import Litestar, get, post
from litestar.connection import ASGIConnection
from litestar.middleware.session.server_side import ServerSideSessionConfig
from advanced_alchemy.extensions.litestar.session import SQLAlchemyAsyncSessionBackend
from config import settings
from database import alchemy_plugin, alchemy_config
from models import UserSessionModel
from controllers.user_controller import UserController

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


# Application
app = Litestar(
    route_handlers=[UserController],
    plugins=[alchemy_plugin],
    middleware=[session_config.middleware],
)