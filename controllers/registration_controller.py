from typing import Annotated
from datetime import datetime

from litestar import Controller, get, post, patch
from litestar.params import Body
from litestar.di import Provide
from litestar.plugins.htmx import HTMXRequest, HTMXTemplate
from litestar.plugins.flash import flash
from litestar.response import Template, Redirect
from litestar.status_codes import HTTP_302_FOUND
from advanced_alchemy.extensions.litestar import providers
from services.registration_service import RegistrationService
from services.user_service import UserService
from models import RegistrationRequestModel, UserModel
from middleware import require_profiles


class RegistrationController(Controller):
    """Registration request management endpoints (admin only)"""
    
    path = "/registrations"
    
    dependencies = {
        **providers.create_service_dependencies(RegistrationService, "registration_service"),
        **providers.create_service_dependencies(UserService, "users_service"),
    }

    @get(path="")
    async def list_requests(
        self,
        request: HTMXRequest,
        registration_service: RegistrationService,
    ) -> Template:
        """List all registration requests (admin only)."""
        require_profiles(request, ["admin"])
        
        # Get all registration requests, ordered by most recent first
        requests, _ = await registration_service.list_and_count()
        requests = sorted(requests, key=lambda r: r.requested_at, reverse=True)
        
        return HTMXTemplate(
            template_name="registration_list.html",
            context={"requests": requests}
        )

    @get(path="/{request_id:int}")
    async def view_request(
        self,
        request: HTMXRequest,
        request_id: int,
        registration_service: RegistrationService,
    ) -> Template:
        """View and edit a specific registration request (admin only)."""
        require_profiles(request, ["admin"])
        
        registration_request = await registration_service.get(request_id)
        
        if not registration_request:
            flash(request, "Solicitação de registro não encontrada", category="error")
            return Redirect(path="/registrations", status_code=HTTP_302_FOUND)
        
        return HTMXTemplate(
            template_name="registration_edit.html",
            context={"registration_request": registration_request}
        )


    @post(path="/{request_id:int}/approve")
    async def approve_request(
        self,
        request: HTMXRequest,
        request_id: int,
        registration_service: RegistrationService,
        users_service: UserService,
    ) -> Redirect:
        """Approve a registration request and create the user (admin only)."""
        require_profiles(request, ["admin"])
        
        try:
            # Get the registration request
            registration_request = await registration_service.get(request_id)
            
            if not registration_request:
                flash(request, "Solicitação de registro não encontrada", category="error")
                return Redirect(path="/registrations", status_code=HTTP_302_FOUND)
            
            if registration_request.status != "pending":
                flash(request, "Esta solicitação já foi processada", category="warning")
                return Redirect(path="/registrations", status_code=HTTP_302_FOUND)
            
            # Get form data for any edits made by admin
            form_data = await request.form()
            username = form_data.get("username", registration_request.username)
            email = form_data.get("email", registration_request.email)
            profile = form_data.get("profile", registration_request.profile)
            
            # Convert empty string to None for profile
            if profile == "":
                profile = None
            
            # Check if username or email already exists in users
            users, _ = await users_service.list_and_count()
            if any(u.username == username for u in users):
                flash(request, "Nome de usuário já existe. Por favor, edite antes de aprovar.", category="error")
                return Redirect(path=f"/registrations/{request_id}", status_code=HTTP_302_FOUND)
            
            if any(u.email == email for u in users):
                flash(request, "Email já está cadastrado. Por favor, edite antes de aprovar.", category="error")
                return Redirect(path=f"/registrations/{request_id}", status_code=HTTP_302_FOUND)
            
            # Create the user
            user = UserModel(
                username=username,
                email=email,
                password_hash=registration_request.password_hash,  # Use the hashed password from request
                profile=profile,
                is_active=True
            )
            
            # Add user to database
            users_service.repository.session.add(user)
            await users_service.repository.session.flush()
            
            # Update registration request status
            registration_request.status = "approved"
            registration_request.reviewed_at = datetime.now()
            registration_request.reviewed_by_user_id = request.session.get("user_id")
            
            await registration_service.repository.session.commit()
            
            flash(request, f"Solicitação aprovada! Usuário {username} criado com sucesso.", category="success")
            return Redirect(path="/registrations", status_code=HTTP_302_FOUND)
            
        except Exception as e:
            flash(request, f"Erro ao aprovar solicitação: {str(e)}", category="error")
            return Redirect(path="/registrations", status_code=HTTP_302_FOUND)


    @post(path="/{request_id:int}/reject")
    async def reject_request(
        self,
        request: HTMXRequest,
        request_id: int,
        registration_service: RegistrationService,
    ) -> Redirect:
        """Reject a registration request (admin only)."""
        require_profiles(request, ["admin"])
        
        try:
            # Get the registration request
            registration_request = await registration_service.get(request_id)
            
            if not registration_request:
                flash(request, "Solicitação de registro não encontrada", category="error")
                return Redirect(path="/registrations", status_code=HTTP_302_FOUND)
            
            if registration_request.status != "pending":
                flash(request, "Esta solicitação já foi processada", category="warning")
                return Redirect(path="/registrations", status_code=HTTP_302_FOUND)
            
            # Get rejection reason from form
            form_data = await request.form()
            rejection_reason = form_data.get("rejection_reason", "")
            
            # Update registration request status
            registration_request.status = "rejected"
            registration_request.reviewed_at = datetime.now()
            registration_request.reviewed_by_user_id = request.session.get("user_id")
            registration_request.rejection_reason = rejection_reason if rejection_reason else None
            
            await registration_service.repository.session.commit()
            
            flash(request, f"Solicitação de {registration_request.username} rejeitada.", category="info")
            return Redirect(path="/registrations", status_code=HTTP_302_FOUND)
            
        except Exception as e:
            flash(request, f"Erro ao rejeitar solicitação: {str(e)}", category="error")
            return Redirect(path="/registrations", status_code=HTTP_302_FOUND)


    @patch(path="/{request_id:int}/update")
    async def update_request(
        self,
        request: HTMXRequest,
        request_id: int,
        registration_service: RegistrationService,
    ) -> Template:
        """Update registration request details before approval (admin only)."""
        require_profiles(request, ["admin"])

        try:
            # Get the registration request
            registration_request = await registration_service.get(request_id)

            if not registration_request:
                flash(request, "Solicitação de registro não encontrada", category="error")
                return HTMXTemplate(
                    template_name="registration_edit.html",
                    context={"registration_request": None}
                )

            if registration_request.status != "pending":
                flash(request, "Apenas solicitações pendentes podem ser editadas", category="warning")
                return HTMXTemplate(
                    template_name="registration_edit.html",
                    context={"registration_request": registration_request}
                )

            # Get form data
            form_data = await request.form()
            username = form_data.get("username")
            email = form_data.get("email")
            profile = form_data.get("profile")

            # Convert empty string to None for profile
            if profile == "":
                profile = None

            # Update fields
            if username:
                registration_request.username = username
            if email:
                registration_request.email = email
            if profile is not None:
                registration_request.profile = profile

            await registration_service.repository.session.commit()

            flash(request, "Solicitação atualizada com sucesso", category="success")

            # Always return the template for HTMX requests to show flash messages
            return HTMXTemplate(
                template_name="registration_edit.html",
                context={"registration_request": registration_request}
            )

        except Exception as e:
            flash(request, f"Erro ao atualizar solicitação: {str(e)}", category="error")
            return HTMXTemplate(
                template_name="registration_edit.html",
                context={"registration_request": registration_request}
            )