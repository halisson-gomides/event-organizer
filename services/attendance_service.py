from advanced_alchemy.extensions.litestar import repository, service
from models import AttendanceModel


class AttendanceService(service.SQLAlchemyAsyncRepositoryService[AttendanceModel]):
    """Attendance service."""
    class Repo(repository.SQLAlchemyAsyncRepository[AttendanceModel]):
        """Attendance repository."""
        model_type = AttendanceModel
    repository_type = Repo

    async def get_by_occurrence_and_participant(self, occurrence_id: int, participant_id: int) -> AttendanceModel | None:
        """Get attendance record by occurrence and participant."""
        return await self.repository.get_one_or_none(
            occurrence_id=occurrence_id,
            participant_id=participant_id
        )