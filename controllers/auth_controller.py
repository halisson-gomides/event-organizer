from typing import Annotated

from litestar import Controller, get, post
from litestar.params import Body
from litestar.plugins.htmx import HTMXRequest, HTMXTemplate
from litestar.plugins.flash import flash
from litestar.response import Template, Redirect
from litestar.status_codes import HTTP_302_FOUND
from advanced_alchemy.extensions.litestar import providers
from services.user_service import UserService
from schemas import UserCreate
from models import UserModel
from passlib.hash import bcrypt


class AuthController(Controller):
    """Authentication endpoints"""
    
    path = "/auth"
    
    dependencies = providers.create_service_dependencies(
        UserService,
        "users_service",
    )

    @get(path="/login")
    async def login_form(self) -> Template:
        """Render the login form."""
        return HTMXTemplate(template_name="login.html")

    @post(path="/login")
    async def login(
        self,
        request: HTMXRequest,
        users_service: UserService,
    ) -> Template | Redirect:
        """Process login."""
        try:
            form_data = await request.form()
            username = form_data.get("username")
            password = form_data.get("password")
            
            if not username or not password:
                flash(request, "Usuário e senha são obrigatórios", category="error")
                return HTMXTemplate(template_name="login.html")
            
            # Find user by username
            users, _ = await users_service.list_and_count()
            user = next((u for u in users if u.username == username), None)
            
            if not user or not bcrypt.verify(password, user.password_hash):
                flash(request, "Usuário ou senha inválidos", category="error")
                return HTMXTemplate(template_name="login.html")
            
            if not user.is_active:
                flash(request, "Conta desativada. Entre em contato com o administrador.", category="error")
                return HTMXTemplate(template_name="login.html")
            
            # Store user in session
            request.session["user_id"] = user.id
            request.session["username"] = user.username
            request.session["profile"] = user.profile
            
            flash(request, f"Bem-vindo, {user.username}!", category="success")
            return Redirect(path="/", status_code=HTTP_302_FOUND)
            
        except Exception as e:
            flash(request, f"Erro no login: {str(e)}", category="error")
            return HTMXTemplate(template_name="login.html")

    @get(path="/register")
    async def register_form(self) -> Template:
        """Render the registration form."""
        return HTMXTemplate(template_name="register.html")

    @post(path="/register")
    async def register(
        self,
        request: HTMXRequest,
        users_service: UserService,
    ) -> Template | Redirect:
        """Process registration."""
        try:
            form_data = await request.form()
            username = form_data.get("username")
            email = form_data.get("email")
            password = form_data.get("password")
            password_confirm = form_data.get("password_confirm")
            profile = form_data.get("profile") or None
            
            # Validation
            if not all([username, email, password, password_confirm]):
                flash(request, "Todos os campos obrigatórios devem ser preenchidos", category="error")
                return HTMXTemplate(template_name="register.html")
            
            if password != password_confirm:
                flash(request, "As senhas não coincidem", category="error")
                return HTMXTemplate(template_name="register.html")
            
            if len(password) < 6:
                flash(request, "A senha deve ter pelo menos 6 caracteres", category="error")
                return HTMXTemplate(template_name="register.html")
            
            # Check if username or email already exists
            users, _ = await users_service.list_and_count()
            if any(u.username == username for u in users):
                flash(request, "Nome de usuário já existe", category="error")
                return HTMXTemplate(template_name="register.html")
            
            if any(u.email == email for u in users):
                flash(request, "Email já está cadastrado", category="error")
                return HTMXTemplate(template_name="register.html")
            
            # Create user
            user_data = UserCreate(
                username=username,
                email=email,
                is_active=True,  # Auto-activate for now
                profile=profile
            )
            
            user = await users_service.create(user_data)
            
            # Set password (using the model method)
            user.set_password(password)
            await users_service.repository.session.commit()
            
            flash(request, f"Conta criada com sucesso! Bem-vindo, {username}!", category="success")
            
            # Auto-login after registration
            request.session["user_id"] = user.id
            request.session["username"] = user.username
            request.session["profile"] = user.profile
            
            return Redirect(path="/", status_code=HTTP_302_FOUND)
            
        except Exception as e:
            flash(request, f"Erro ao criar conta: {str(e)}", category="error")
            return HTMXTemplate(template_name="register.html")

    @post(path="/logout")
    async def logout(self, request: HTMXRequest) -> Redirect:
        """Process logout."""
        request.session.clear()
        flash(request, "Logout realizado com sucesso!", category="success")
        return Redirect(path="/auth/login", status_code=HTTP_302_FOUND)