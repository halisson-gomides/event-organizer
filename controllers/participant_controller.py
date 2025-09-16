from typing import Annotated

from litestar import Controller, get, post, patch, delete
from litestar.params import Dependency, Parameter, Body
from advanced_alchemy.extensions.litestar import filters, providers, service
from services.participant_service import ParticipantService
from schemas import ParticipantRead, ParticipantCreate, ParticipantUpdate
from models import ParticipantModel


class ParticipantController(Controller):
    """Participant CRUD endpoints"""

    dependencies = providers.create_service_dependencies(
        ParticipantService,
        "participants_service",
        load=[ParticipantModel.guardian],
        filters={"pagination_type": "limit_offset", "id_filter": int, "search": "full_name", "search_ignore_case": True},
    )


    @get(path="/participants", response_model=service.OffsetPagination[ParticipantRead])
    async def list_participants(
        self,
        participants_service: ParticipantService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[ParticipantRead]:
        """List all participants with pagination."""
        results, total = await participants_service.list_and_count(*filters)
        return participants_service.to_schema(results, total, filters=filters, schema_type=ParticipantRead)
    

    @post(path="/participants")
    async def create_participant(
        self,
        participants_service: ParticipantService,
        data: Annotated[ParticipantCreate, Body()],
    ) -> ParticipantRead:
        """Create a new participant."""
        obj = await participants_service.create(data)
        return participants_service.to_schema(obj, schema_type=ParticipantRead)
    

    @get(path="/participants/{participant_id:int}")
    async def get_participant(
        self,
        participants_service: ParticipantService,
        participant_id: int = Parameter(
            title="Participant ID",
            description="The participant to retrieve.",
        ),
    ) -> ParticipantRead:
        """Get an existing participant."""
        obj = await participants_service.get(participant_id)
        return participants_service.to_schema(obj, schema_type=ParticipantRead)
    

    @patch(path="/participants/{participant_id:int}")
    async def update_participant(
        self,
        participants_service: ParticipantService,
        data: Annotated[ParticipantUpdate, Body()],
        participant_id: int = Parameter(
            title="Participant ID",
            description="The participant to update.",
        ),
    ) -> ParticipantRead:
        """Update a participant."""
        obj = await participants_service.update(data, item_id=participant_id, auto_commit=True)
        return participants_service.to_schema(obj, schema_type=ParticipantRead)
    

    @delete(path="/participants/{participant_id:int}")
    async def delete_participant(
        self,
        participants_service: ParticipantService,
        participant_id: int = Parameter(
            title="Participant ID",
            description="The participant to delete.",
        ),
    ) -> None:
        """Delete a participant from the system."""
        _ = await participants_service.delete(participant_id)