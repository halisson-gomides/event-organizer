from advanced_alchemy.extensions.litestar import repository, service
from models import EventOccurrenceModel


class OccurrenceService(service.SQLAlchemyAsyncRepositoryService[EventOccurrenceModel]):
    """Event Occurrence service."""
    class Repo(repository.SQLAlchemyAsyncRepository[EventOccurrenceModel]):
        """Event Occurrence repository."""
        model_type = EventOccurrenceModel
    repository_type = Repo