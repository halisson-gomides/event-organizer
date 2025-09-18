from typing import Annotated
from datetime import datetime, date
from litestar import Controller, get, post, patch, delete
from litestar.params import Dependency, Parameter, Body
from litestar.plugins.htmx import HTMXRequest, HTMXTemplate
from litestar.plugins.flash import flash
from litestar.response import Template
from litestar.status_codes import HTTP_200_OK
from advanced_alchemy.extensions.litestar import filters, providers
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


    @get(path="/participants")
    async def list_participants(
        self,
        request: HTMXRequest,
        participants_service: ParticipantService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> Template:
        """List all participants with pagination."""
        results, total = await participants_service.list_and_count(*filters)

        
        context = {
            "participants": results,
            "total": total,
            "has_participants": total > 0,
            "now": datetime.now().date()
        }
        
        if request.htmx:
            return HTMXTemplate(template_name="participant_list_content.html", context=context)
        return HTMXTemplate(template_name="participant_list.html", context=context)
    

    @get(path="/participants/new")
    async def new_participant_form(self, participants_service: ParticipantService) -> Template:
        """Render the participant creation form."""
        # Get potential guardians (adults)

        today = date.today()
        adult_age = 18
        
        all_participants, _ = await participants_service.list_and_count()
        guardians = [p for p in all_participants if p.age_on(today) >= adult_age]
        
        context = {
            "participant": None,
            "guardians": guardians
        }
        return HTMXTemplate(template_name="participant_form.html", context=context)


    @post(path="/participants")
    async def create_participant(
        self,
        request: HTMXRequest,
        participants_service: ParticipantService,
    ) -> Template:
        """Create a new participant."""
        try:
            # Get form data from request
            form_data = await request.form()

            # Convert form data to ParticipantCreate schema
            form_dict = {}

            # Basic fields
            form_dict["full_name"] = form_data.get("full_name", "")
            form_dict["phone"] = form_data.get("phone", "")
            form_dict["observations"] = form_data.get("observations", "")

            # Handle date field
            birth_date = form_data.get("birth_date")
            if birth_date:
                form_dict["birth_date"] = date.fromisoformat(birth_date)

            # Handle guardian_id
            guardian_id_str = form_data.get("guardian_id")
            if guardian_id_str:
                form_dict["guardian_id"] = int(guardian_id_str)
            else:
                form_dict["guardian_id"] = None

            # Create ParticipantCreate instance
            from schemas import ParticipantCreate
            participant_data = ParticipantCreate(**form_dict)

            obj = await participants_service.create(participant_data)
            flash(request, f"Participante {obj.full_name} criado com sucesso!", category="success")
            
            # Return updated participant list
            results, total = await participants_service.list_and_count()
            context = {
                "participants": results,
                "total": total,
                "has_participants": total > 0,
                "now": datetime.now().date()
            }
            return HTMXTemplate(template_name="participant_list_content.html", context=context)
            
        except Exception as e:
            flash(request, f"Erro ao criar participante: {str(e)}", category="error")
            
            # Return form with error
            today = date.today()
            adult_age = 18
            
            all_participants, _ = await participants_service.list_and_count()
            guardians = [p for p in all_participants if p.age_on(today) >= adult_age]
            
            context = {
                "participant": None,
                "guardians": guardians
            }
            return HTMXTemplate(template_name="participant_form.html", context=context)
    

    @get(path="/participants/{participant_id:int}/edit")
    async def edit_participant_form(
        self,
        participants_service: ParticipantService,
        participant_id: int = Parameter(
            title="Participant ID",
            description="The participant to edit.",
        ),
    ) -> Template:
        """Render the participant edit form."""
        participant = await participants_service.get(participant_id)
        
        # Get potential guardians (adults, excluding self)
        today = date.today()
        adult_age = 18
        
        all_participants, _ = await participants_service.list_and_count()
        guardians = [p for p in all_participants if p.age_on(today) >= adult_age and p.id != participant_id]
        
        context = {
            "participant": participant,
            "guardians": guardians
        }
        return HTMXTemplate(template_name="participant_form.html", context=context)


    @patch(path="/participants/{participant_id:int}")
    async def update_participant(
        self,
        request: HTMXRequest,
        participants_service: ParticipantService,
        participant_id: int = Parameter(
            title="Participant ID",
            description="The participant to update.",
        ),
    ) -> Template:
        """Update a participant."""
        try:
            # Get form data from request
            form_data = await request.form()

            # Convert form data to ParticipantUpdate schema
            form_dict = {}

            # Basic fields
            form_dict["full_name"] = form_data.get("full_name", "")
            form_dict["phone"] = form_data.get("phone", "")
            form_dict["observations"] = form_data.get("observations", "")

            # Handle date field
            birth_date = form_data.get("birth_date")
            if birth_date:
                form_dict["birth_date"] = date.fromisoformat(birth_date)

            # Handle guardian_id
            guardian_id_str = form_data.get("guardian_id")
            if guardian_id_str:
                form_dict["guardian_id"] = int(guardian_id_str)
            else:
                form_dict["guardian_id"] = None

            # Create ParticipantUpdate instance
            from schemas import ParticipantUpdate
            participant_data = ParticipantUpdate(**form_dict)

            obj = await participants_service.update(participant_data, item_id=participant_id, auto_commit=True)
            flash(request, f"Participante {obj.full_name} atualizado com sucesso!", category="success")

            # Return updated participant list
            results, total = await participants_service.list_and_count()
            context = {
                "participants": results,
                "total": total,
                "has_participants": total > 0,
                "now": datetime.now().date()
            }
            return HTMXTemplate(template_name="participant_list.html", context=context)

        except Exception as e:
            flash(request, f"Erro ao atualizar participante: {str(e)}", category="error")

            # Return form with error
            participant = await participants_service.get(participant_id)
            today = date.today()
            adult_age = 18

            all_participants, _ = await participants_service.list_and_count()
            guardians = [p for p in all_participants if p.age_on(today) >= adult_age and p.id != participant_id]

            context = {
                "participant": participant,
                "guardians": guardians
            }
            return HTMXTemplate(template_name="participant_form.html", context=context)
    

    @delete(path="/participants/{participant_id:int}", status_code=HTTP_200_OK)
    async def delete_participant(
        self,
        request: HTMXRequest,
        participants_service: ParticipantService,
        participant_id: int = Parameter(
            title="Participant ID",
            description="The participant to delete.",
        ),
    ) -> Template:
        """Delete a participant from the system."""
        try:
            participant = await participants_service.get(participant_id)
            participant_name = participant.full_name
            await participants_service.delete(participant_id)
            
            flash(request, f"Participante {participant_name} excluído com sucesso!", category="success")
            
        except Exception as e:
            flash(request, f"Erro ao excluir participante: {str(e)}", category="error")
        
        # Return updated participant list
        results, total = await participants_service.list_and_count()
        context = {
            "participants": results,
            "total": total,
            "has_participants": total > 0,
            "now": datetime.now().date()
        }
        return HTMXTemplate(template_name="participant_list.html", context=context)