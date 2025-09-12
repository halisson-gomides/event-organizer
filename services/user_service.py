from advanced_alchemy.extensions.litestar import repository, service
from models import UserModel


class UserService(service.SQLAlchemyAsyncRepositoryService[UserModel]):
    """User service."""
    class Repo(repository.SQLAlchemyAsyncRepository[UserModel]):
        """Author repository."""
        model_type = UserModel
    repository_type = Repo