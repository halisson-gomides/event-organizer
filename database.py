from sqlalchemy.pool import AsyncAdaptedQueuePool
from advanced_alchemy.extensions.litestar import (
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
    SQLAlchemyPlugin,
    EngineConfig
)
from config import settings


db_session_config = AsyncSessionConfig(expire_on_commit=False)

alchemy_config = SQLAlchemyAsyncConfig(
    connection_string=settings.database_url,
    engine_config=EngineConfig(
        poolclass=AsyncAdaptedQueuePool,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
    ),
    before_send_handler="autocommit",
    session_config=db_session_config,
    create_all=True,
)
alchemy_plugin = SQLAlchemyPlugin(config=alchemy_config)