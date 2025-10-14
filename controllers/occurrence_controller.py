from typing import Annotated
import secrets
import hashlib
from datetime import datetime

from litestar import Controller, get, post, Request
from litestar.params import Parameter
from litestar.plugins.htmx import HTMXRequest, HTMXTemplate
from litestar.plugins.flash import flash
from litestar.response import Template
from advanced_alchemy.extensions.litestar import providers
from services.occurrence_service import OccurrenceService
from services.attendance_service import AttendanceService
from services.participant_service import ParticipantService
from models import EventOccurrenceModel, AttendanceModel, ParticipantModel
from middleware import require_profiles


class OccurrenceController(Controller):
    """Event Occurrence and Check-in/Check-out endpoints"""
    
    path = "/occurrences"
    
    occurrences_dep = providers.create_service_dependencies(
        OccurrenceService,
        "occurrences_service",
        load=[EventOccurrenceModel.event]
    )
    attendance_dep = providers.create_service_dependencies(
        AttendanceService,
        "attendance_service",
        load=[AttendanceModel.participant]
    )
    participants_dep = providers.create_service_dependencies(
        ParticipantService,
        "participants_service",
        load=[ParticipantModel.guardian]
    )

    dependencies = {**occurrences_dep, **attendance_dep, **participants_dep}


    async def _get_base_context(self, occurrence_id: int, occurrences_service: OccurrenceService, participants_service: ParticipantService) -> dict:
        """Get base context for forms."""
        occurrence = await occurrences_service.get(occurrence_id)
        participants, _ = await participants_service.list_and_count()
        return {
            "occurrence": occurrence,
            "participants": participants,
        }
    

    @get(path="/{occurrence_id:int}/checkin")
    async def checkin_form(
        self,
        request: Request,
        occurrences_service: OccurrenceService,
        participants_service: ParticipantService,
        occurrence_id: int = Parameter(
            title="Occurrence ID",
            description="The occurrence for check-in.",
        ),
    ) -> Template:
        """Render the check-in form."""
        require_profiles(request, ["admin", "organizer", "volunteer"])
        base_context = await self._get_base_context(occurrence_id, occurrences_service, participants_service)
        context = {
            **base_context,
            "checkin_ok": False,
            "error": None,
            "code": None
        }
        return HTMXTemplate(template_name="checkin.html", context=context)
    

    @post(path="/{occurrence_id:int}/checkin")
    async def checkin(
        self,
        request: HTMXRequest,
        occurrences_service: OccurrenceService,
        attendance_service: AttendanceService,
        participants_service: ParticipantService,
        occurrence_id: int = Parameter(
            title="Occurrence ID",
            description="The occurrence for check-in.",
        ),
    ) -> Template:
        """Process check-in."""
        require_profiles(request, ["admin", "organizer", "volunteer"])
        try:
            form_data = await request.form()
            participant_id_str = form_data.get("participant_id")
            if not participant_id_str:
                flash(request, "ID do participante é obrigatório", category="error")
                base_context = await self._get_base_context(occurrence_id, occurrences_service, participants_service)
                context = {
                    **base_context,
                    "checkin_ok": False,
                    "error": "ID do participante é obrigatório",
                    "code": None
                }
                return HTMXTemplate(template_name="checkin.html", context=context)
            participant_id = int(participant_id_str)

            occurrence = await occurrences_service.get(occurrence_id)
            participant = await participants_service.get(participant_id)
            participants, _ = await participants_service.list_and_count()
            
            # Check if already checked in
            existing_attendance = await attendance_service.get_by_occurrence_and_participant(occurrence_id, participant_id)
            
            if existing_attendance:
                context = {
                    "occurrence": occurrence,
                    "participants": participants,
                    "checkin_ok": False,
                    "error": f"{participant.full_name} já fez check-in neste evento.",
                    "code": None
                }
                return HTMXTemplate(template_name="checkin.html", context=context)
            
            # Generate security code for children (under 18)
            from datetime import date
            today = date.today()
            code = None
            code_hash = None
            
            if participant.age_on(today) < 18:
                code = secrets.token_hex(3).upper()  # 6-character code
                code_hash = hashlib.sha256(code.encode()).hexdigest()
            
            # Create attendance record
            attendance_data = {
                "occurrence_id": occurrence_id,
                "participant_id": participant_id,
                "checkin_at": datetime.now(),
                "code_hash": code_hash
            }
            
            await attendance_service.create(attendance_data)
            
            context = {
                "occurrence": occurrence,
                "participants": participants,
                "checkin_ok": True,
                "error": None,
                "code": code
            }
            return HTMXTemplate(template_name="checkin.html", context=context)
            
        except Exception as e:
            base_context = await self._get_base_context(occurrence_id, occurrences_service, participants_service)
            context = {
                **base_context,
                "checkin_ok": False,
                "error": f"Erro no check-in: {str(e)}",
                "code": None
            }
            return HTMXTemplate(template_name="checkin.html", context=context)
        

    @get(path="/{occurrence_id:int}/checkout")
    async def checkout_form(
        self,
        request: Request,
        occurrences_service: OccurrenceService,
        participants_service: ParticipantService,
        occurrence_id: int = Parameter(
            title="Occurrence ID",
            description="The occurrence for check-out.",
        ),
    ) -> Template:
        """Render the check-out form."""
        require_profiles(request, ["admin", "organizer", "volunteer"])
        base_context = await self._get_base_context(occurrence_id, occurrences_service, participants_service)
        context = {
            **base_context,
            "checkout_ok": False,
            "error": None
        }
        return HTMXTemplate(template_name="checkout.html", context=context)


    @post(path="/{occurrence_id:int}/checkout")
    async def checkout(
        self,
        request: HTMXRequest,
        occurrences_service: OccurrenceService,
        attendance_service: AttendanceService,
        participants_service: ParticipantService,
        occurrence_id: int = Parameter(
            title="Occurrence ID",
            description="The occurrence for check-out.",
        ),
    ) -> Template:
        """Process check-out."""
        require_profiles(request, ["admin", "organizer", "volunteer"])
        try:
            form_data = await request.form()
            participant_id_str = form_data.get("participant_id")
            if not participant_id_str:
                flash(request, "ID do participante é obrigatório", category="error")
                occurrence = await occurrences_service.get(occurrence_id)
                participants, _ = await participants_service.list_and_count()
                context = {
                    "occurrence": occurrence,
                    "participants": participants,
                    "checkout_ok": False,
                    "error": "ID do participante é obrigatório"
                }
                return HTMXTemplate(template_name="checkout.html", context=context)
            participant_id = int(participant_id_str)
            checkout_by_participant_id_str = form_data.get("checkout_by_participant_id")
            if not checkout_by_participant_id_str:
                flash(request, "ID do responsável pelo check-out é obrigatório", category="error")
                occurrence = await occurrences_service.get(occurrence_id)
                participants, _ = await participants_service.list_and_count()
                context = {
                    "occurrence": occurrence,
                    "participants": participants,
                    "checkout_ok": False,
                    "error": "ID do responsável pelo check-out é obrigatório"
                }
                return HTMXTemplate(template_name="checkout.html", context=context)
            checkout_by_participant_id = int(checkout_by_participant_id_str)
            code = form_data.get("code", "").strip()
            
            occurrence = await occurrences_service.get(occurrence_id)
            participant = await participants_service.get(participant_id)
            checkout_by = await participants_service.get(checkout_by_participant_id)
            participants, _ = await participants_service.list_and_count()
            
            # Find attendance record
            attendance = await attendance_service.get_by_occurrence_and_participant(occurrence_id, participant_id)
            
            if not attendance:
                context = {
                    "occurrence": occurrence,
                    "participants": participants,
                    "checkout_ok": False,
                    "error": f"{participant.full_name} não fez check-in neste evento."
                }
                return HTMXTemplate(template_name="checkout.html", context=context)
            
            if attendance.checkout_at:
                context = {
                    "occurrence": occurrence,
                    "participants": participants,
                    "checkout_ok": False,
                    "error": f"{participant.full_name} já fez check-out."
                }
                return HTMXTemplate(template_name="checkout.html", context=context)
            
            # Validate code for children
            from datetime import date
            today = date.today()
            
            if participant.age_on(today) < 18:
                if not code:
                    context = {
                        "occurrence": occurrence,
                        "participants": participants,
                        "checkout_ok": False,
                        "error": "Código é obrigatório para menores de idade."
                    }
                    return HTMXTemplate(template_name="checkout.html", context=context)
                
                # Verify code
                code_hash = hashlib.sha256(code.encode()).hexdigest()
                if attendance.code_hash != code_hash:
                    context = {
                        "occurrence": occurrence,
                        "participants": participants,
                        "checkout_ok": False,
                        "error": "Código inválido."
                    }
                    return HTMXTemplate(template_name="checkout.html", context=context)
            
            # Update attendance with checkout info
            update_data = {
                "checkout_at": datetime.now(),
                "checkout_by_participant_id": checkout_by_participant_id
            }
            
            await attendance_service.update(
                update_data,
                item_id=(occurrence_id, participant_id),
                auto_commit=True
            )
            
            context = {
                "occurrence": occurrence,
                "participants": participants,
                "checkout_ok": True,
                "error": None
            }
            return HTMXTemplate(template_name="checkout.html", context=context)
            
        except Exception as e:
            base_context = await self._get_base_context(occurrence_id, occurrences_service, participants_service)
            context = {
                **base_context,
                "checkout_ok": False,
                "error": f"Erro no check-out: {str(e)}"
            }
            return HTMXTemplate(template_name="checkout.html", context=context)