from advanced_alchemy.extensions.litestar import repository, service
from models import RegistrationRequestModel


class RegistrationService(service.SQLAlchemyAsyncRepositoryService[RegistrationRequestModel]):
    """Registration request service."""
    class Repo(repository.SQLAlchemyAsyncRepository[RegistrationRequestModel]):
        """Registration request repository."""
        model_type = RegistrationRequestModel
    repository_type = Repo