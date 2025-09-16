from typing import Annotated

from litestar import Controller, get, post, patch, delete
from litestar.params import Dependency, Parameter
from advanced_alchemy.extensions.litestar import filters, providers, service
from services.user_service import UserService
from schemas import UserRead, UserCreate, UserUpdate
from models import UserModel

class UserController(Controller):
    """User CRUD endpoints"""

    dependencies = providers.create_service_dependencies(
        UserService,
        "users_service",
        load=[UserModel.username],
        filters={"pagination_type": "limit_offset", "id_filter": int, "search": "email", "search_ignore_case": True},
    )

    @get(path="/users", response_model=service.OffsetPagination[UserRead])
    async def list_users(
        self,
        users_service: UserService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[UserRead]:
        """List all users with pagination."""
        results, total = await users_service.list_and_count(*filters)
        return users_service.to_schema(results, total, filters=filters, schema_type=UserRead)
    

    @post(path="/users")
    async def create_user(
        self,
        users_service: UserService,
        data: UserCreate,
    ) -> UserRead:
        """Create a new user."""
        obj = await users_service.create(data)
        return users_service.to_schema(obj, schema_type=UserRead)
    

    @get(path="/users/{user_id:int}")
    async def get_user(
        self,
        users_service: UserService,
        user_id: int = Parameter(
            title="User ID",
            description="The user to retrieve.",
        ),
    ) -> UserRead:
        """Get an existing user."""
        obj = await users_service.get(user_id)
        return users_service.to_schema(obj, schema_type=UserRead)
    

    @patch(path="/users/{user_id:int}")
    async def update_user(
        self,
        users_service: UserService,
        data: UserUpdate,
        user_id: int = Parameter(
            title="User ID",
            description="The user to update.",
        ),
    ) -> UserRead:
        """Update an user."""
        obj = await users_service.update(data, item_id=user_id, auto_commit=True)
        return users_service.to_schema(obj, schema_type=UserRead)