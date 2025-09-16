from advanced_alchemy.extensions.litestar import repository, service
from models import EventModel


class EventService(service.SQLAlchemyAsyncRepositoryService[EventModel]):
    """Event service."""
    class Repo(repository.SQLAlchemyAsyncRepository[EventModel]):
        """Event repository."""
        model_type = EventModel
    repository_type = Repo