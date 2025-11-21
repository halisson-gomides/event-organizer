from typing import Annotated
import secrets
import hashlib
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

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
from config import settings


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
    

    def _is_checkin_available(self, occurrence: EventOccurrenceModel) -> bool:
        """Check if check-in window is open for this occurrence.

        Check-in opens 2 hours before event starts and closes 40 minutes before event ends.
        """
        # Get current time in the same timezone as the event
        if occurrence.start_at.tzinfo:
            now = datetime.now(occurrence.start_at.tzinfo)
        else:
            # If no timezone info, assume UTC and convert to local timezone
            now = datetime.now(ZoneInfo("UTC")).astimezone(ZoneInfo(settings.timezone))

        # Check-in opens 2 hours before start
        checkin_open = occurrence.start_at - timedelta(hours=2)
        # Check-in closes 40 minutes before end
        checkin_close = occurrence.end_at - timedelta(minutes=40)

        return checkin_open <= now <= checkin_close
    

    def _is_checkout_available(self, occurrence: EventOccurrenceModel) -> bool:
        """Check if check-out window is open for this occurrence.

        Check-out can only be done after event starts and before it ends.
        """
        # Get current time in the same timezone as the event
        if occurrence.start_at.tzinfo:
            now = datetime.now(occurrence.start_at.tzinfo)
        else:
            # If no timezone info, assume UTC and convert to local timezone
            now = datetime.now(ZoneInfo("UTC")).astimezone(ZoneInfo(settings.timezone))

        # Check-out opens when event starts
        checkout_open = occurrence.start_at
        # Check-out closes when event ends
        checkout_close = occurrence.end_at

        return checkout_open <= now <= checkout_close
    

    def _get_occurrence_status(self, occurrence: EventOccurrenceModel) -> dict:
        """Get current status of occurrence for check-in/check-out.

        Returns dict with:
        - checkin_available: bool
        - checkout_available: bool
        - checkin_opens_at: datetime
        - checkin_closes_at: datetime
        - checkout_opens_at: datetime
        - checkout_closes_at: datetime
        - status_text: str (human-readable status)
        - status: str (CSS class status)
        """
        checkin_opens = occurrence.start_at - timedelta(hours=2)
        checkin_closes = occurrence.end_at - timedelta(minutes=40)
        checkout_opens = occurrence.start_at
        checkout_closes = occurrence.end_at

        # Get current time in the same timezone as the event
        if occurrence.start_at.tzinfo:
            now = datetime.now(occurrence.start_at.tzinfo)
        else:
            # If no timezone info, assume UTC and convert to local timezone
            now = datetime.now(ZoneInfo("UTC")).astimezone(ZoneInfo(settings.timezone))

        checkin_available = self._is_checkin_available(occurrence)
        checkout_available = self._is_checkout_available(occurrence)

        # Determine status text and CSS class
        if now < checkin_opens:
            status_text = "Check-in abre em breve"
            status = "event_not_started"
        elif now > checkout_closes:
            status_text = "Evento finalizado"
            status = "event_ended"
        elif checkin_available:
            status_text = "Check-in disponível"
            status = "checkin_available"
        elif checkout_available:
            status_text = "Check-out disponível"
            status = "checkout_available"
        else:
            status_text = "Check-in fechado"
            status = "checkin_closed"

        return {
            "checkin_available": checkin_available,
            "checkout_available": checkout_available,
            "checkin_opens_at": checkin_opens,
            "checkin_closes_at": checkin_closes,
            "checkout_opens_at": checkout_opens,
            "checkout_closes_at": checkout_closes,
            "status_text": status_text,
            "status": status,
        }


    @get(path="/checkin-checkout")
    async def list_occurrences_for_checkin_checkout(
        self,
        request: Request,
        occurrences_service: OccurrenceService,
    ) -> Template:
        """List all occurrences with check-in/check-out availability status."""
        require_profiles(request, ["admin", "organizer", "volunteer"])
        
        try:
            # Sort occurrences by start_at descending (most recent first)
            from sqlalchemy import asc
            occurrences, _ = await occurrences_service.list_and_count(order_by=[asc(EventOccurrenceModel.start_at)])
            
            # Add status information to each occurrence
            occurrences_with_status = []
            for occurrence in occurrences:
                status = self._get_occurrence_status(occurrence)
                # Create a dynamic object with status attributes
                occurrence_with_status = type('OccurrenceWithStatus', (), {
                    'id': occurrence.id,
                    'event': occurrence.event,
                    'start_at': occurrence.start_at,
                    'end_at': occurrence.end_at,
                    'status': status['status'],
                    'can_checkin': status['checkin_available'],
                    'can_checkout': status['checkout_available'],
                    'checkin_window': {
                        'open': status['checkin_opens_at'],
                        'close': status['checkin_closes_at']
                    } if status['checkin_opens_at'] and status['checkin_closes_at'] else None,
                    'checkout_window': {
                        'open': status['checkout_opens_at'],
                        'close': status['checkout_closes_at']
                    } if status['checkout_opens_at'] and status['checkout_closes_at'] else None,
                })()
                occurrences_with_status.append(occurrence_with_status)

            context = {
                "occurrences": occurrences_with_status,
                "has_occurrences": len(occurrences_with_status) > 0
            }
            
            return HTMXTemplate(template_name="checkin_checkout_selection.html", context=context)
        
        except Exception as e:
            flash(request, f"Erro ao listar ocorrências: {str(e)}", category="error")
            context = {
                "occurrences_with_status": [],
                "has_occurrences": False
            }
            return HTMXTemplate(template_name="checkin_checkout_selection.html", context=context)


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
        
        try:
            base_context = await self._get_base_context(occurrence_id, occurrences_service, participants_service)
            occurrence = base_context["occurrence"]
            
            # Check if check-in is available
            if not self._is_checkin_available(occurrence):
                status = self._get_occurrence_status(occurrence)
                context = {
                    **base_context,
                    "checkin_ok": False,
                    "error": f"Check-in não está disponível. {status['status_text']}",
                    "code": None
                }
                return HTMXTemplate(template_name="checkin.html", context=context)
            
            context = {
                **base_context,
                "checkin_ok": False,
                "error": None,
                "code": None
            }
            return HTMXTemplate(template_name="checkin.html", context=context)
        
        except Exception as e:
            flash(request, f"Erro ao carregar formulário de check-in: {str(e)}", category="error")
            context = {
                "occurrence": None,
                "participants": [],
                "checkin_ok": False,
                "error": f"Erro: {str(e)}",
                "code": None
            }
            return HTMXTemplate(template_name="checkin.html", context=context)
        

    @get(path="/{occurrence_id:int}/search-participants", sync_to_thread=False)
    async def search_participants(
        self,
        request: Request,
        occurrences_service: OccurrenceService,
        participants_service: ParticipantService,
        attendance_service: AttendanceService,
        occurrence_id: int = Parameter(
            title="Occurrence ID",
            description="The occurrence for check-in.",
        ),
        search: str = "",
    ) -> Template:
        """Search participants by name or phone digits."""

        require_profiles(request, ["admin", "organizer", "volunteer"])

        base_context = await self._get_base_context(occurrence_id, occurrences_service, participants_service)
        occurrence = base_context["occurrence"]
        if not occurrence:
            return Template("checkin_search_result.html", context={
                "participants": [],
                "search_query": search,
            })

        # Get all participants
        if search and len(search) >= 2:
            # Search by name or last 4 phone digits
            search_lower = search.lower()

            participants_list = base_context["participants"]

            # Filter by name or phone
            filtered = [
                p for p in participants_list
                if (search_lower in p.full_name.lower() or
                    (p.phone and search in p.phone[-4:]))
            ]

            # Check which ones already did checkin
            from datetime import date

            for participant in filtered:
                existing_attendance = await attendance_service.get_by_occurrence_and_participant(occurrence_id, participant.id)
                participant.already_checked_in = existing_attendance is not None
                participant.is_adult = participant.age_on(date.today()) >= 18
        else:
            filtered = []

        return Template("checkin_search_result.html", context={
            "participants": filtered,
            "search_query": search,
            "occurrence": occurrence,
        })


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
            
            # Validate check-in window
            if not self._is_checkin_available(occurrence):
                status = self._get_occurrence_status(occurrence)
                participant = await participants_service.get(participant_id)
                participants, _ = await participants_service.list_and_count()
                context = {
                    "occurrence": occurrence,
                    "participants": participants,
                    "checkin_ok": False,
                    "error": f"Check-in não está disponível. {status['status_text']}",
                    "code": None
                }
                return HTMXTemplate(template_name="checkin.html", context=context)
            
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
                "checkin_at": datetime.now(ZoneInfo("UTC")),
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
        
        try:
            base_context = await self._get_base_context(occurrence_id, occurrences_service, participants_service)
            occurrence = base_context["occurrence"]
            
            # Check if check-out is available
            if not self._is_checkout_available(occurrence):
                status = self._get_occurrence_status(occurrence)
                context = {
                    **base_context,
                    "checkout_ok": False,
                    "error": f"Check-out não está disponível. {status['status_text']}"
                }
                return HTMXTemplate(template_name="checkout.html", context=context)
            
            context = {
                **base_context,
                "checkout_ok": False,
                "error": None
            }
            return HTMXTemplate(template_name="checkout.html", context=context)
        
        except Exception as e:
            flash(request, f"Erro ao carregar formulário de check-out: {str(e)}", category="error")
            context = {
                "occurrence": None,
                "participants": [],
                "checkout_ok": False,
                "error": f"Erro: {str(e)}"
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
            
            # Validate check-out window
            if not self._is_checkout_available(occurrence):
                status = self._get_occurrence_status(occurrence)
                participant = await participants_service.get(participant_id)
                participants, _ = await participants_service.list_and_count()
                context = {
                    "occurrence": occurrence,
                    "participants": participants,
                    "checkout_ok": False,
                    "error": f"Check-out não está disponível. {status['status_text']}"
                }
                return HTMXTemplate(template_name="checkout.html", context=context)
            
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
                "checkout_at": datetime.now(ZoneInfo("UTC")),
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
