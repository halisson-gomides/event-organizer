from advanced_alchemy.extensions.litestar import (
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
    SQLAlchemyPlugin,
)
from config import settings

session_config = AsyncSessionConfig(expire_on_commit=False)
alchemy_config = SQLAlchemyAsyncConfig(
    connection_string=settings.database_url,
    before_send_handler="autocommit",
    session_config=session_config,
    create_all=True,
)
alchemy_plugin = SQLAlchemyPlugin(config=alchemy_config)