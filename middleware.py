from typing import Any, Optional
from litestar import Request, Response
from litestar.middleware.base import AbstractMiddleware
from litestar.response import Redirect
from litestar.status_codes import HTTP_302_FOUND, HTTP_403_FORBIDDEN
from litestar.exceptions import PermissionDeniedException


class AuthMiddleware(AbstractMiddleware):
    """Simple authentication middleware."""
    
    # Routes that don't require authentication
    EXEMPT_ROUTES = {
        "/auth/login",
        "/auth/register", 
        "/static",
        "/favicon.ico"
    }
    
    def __init__(self, app: Any) -> None:
        super().__init__(app)
    
    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        request = Request(scope)
        
        # Skip authentication for exempt routes
        if any(request.url.path.startswith(route) for route in self.EXEMPT_ROUTES):
            await self.app(scope, receive, send)
            return
        
        # Skip authentication for static files and API endpoints
        if (request.url.path.startswith("/static/") or 
            request.url.path.endswith((".css", ".js", ".ico", ".png", ".jpg", ".jpeg", ".gif"))):
            await self.app(scope, receive, send)
            return
        
        # Check if user is authenticated
        user_id = request.session.get("user_id")
        
        if not user_id:
            # Redirect to login page
            response = Redirect(path="/auth/login", status_code=HTTP_302_FOUND)
            await response(scope, receive, send)
            return
        
        # User is authenticated, continue with request
        await self.app(scope, receive, send)


def get_user_profile(request: Request) -> Optional[str]:
    """Get the current user's profile from session."""
    return request.session.get("profile")


def require_profiles(request: Request, allowed_profiles: list[str]) -> None:
    """
    Check if user has one of the allowed profiles.
    Raises PermissionDeniedException if not authorized.
    
    Args:
        request: The current request
        allowed_profiles: List of allowed profile names (e.g., ["admin", "organizer"])
    """
    user_profile = get_user_profile(request)
    
    if not user_profile or user_profile not in allowed_profiles:
        raise PermissionDeniedException(
            detail=f"Acesso negado. Perfis permitidos: {', '.join(allowed_profiles)}"
        )


def is_admin_or_organizer(request: Request) -> bool:
    """Check if user is Administrator or Organizer."""
    profile = get_user_profile(request)
    return profile in ["admin", "organizer"]


def can_checkin_checkout(request: Request) -> bool:
    """Check if user can perform check-in/check-out operations."""
    profile = get_user_profile(request)
    return profile in ["admin", "organizer", "volunteer"]