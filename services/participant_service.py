from advanced_alchemy.extensions.litestar import repository, service
from models import ParticipantModel


class ParticipantService(service.SQLAlchemyAsyncRepositoryService[ParticipantModel]):
    """Participant service."""
    class Repo(repository.SQLAlchemyAsyncRepository[ParticipantModel]):
        """Participant repository."""
        model_type = ParticipantModel
    repository_type = Repo