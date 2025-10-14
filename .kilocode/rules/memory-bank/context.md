# Current Work Context

## Current Focus
Implementing role-based access control and improving navigation for check-in/check-out functionality.

## Recent Changes
- Added check-in and check-out menu items to base.html navigation
- Implemented authorization helper functions in middleware.py:
  - `require_profiles()`: Enforces role-based access control
  - `get_user_profile()`: Retrieves user profile from session
  - `is_admin_or_organizer()`: Helper for admin/organizer checks
  - `can_checkin_checkout()`: Helper for check-in/check-out permission checks
- Added role-based restrictions to event controller (create, edit, delete require Administrador or Organizador)
- Added role-based restrictions to participant controller (create, edit, delete require Administrador or Organizador)
- Added role-based restrictions to occurrence controller (check-in/check-out require Administrador, Organizador, or Voluntário)
- Updated memory bank documentation to reflect authorization implementation

## Next Steps
- Test the authorization implementation with different user profiles
- Consider adding visual indicators in the UI for restricted actions
- Add comprehensive testing suite
- Improve error handling in controllers

## Project State
The project is in a functional state with:
- Complete backend implementation (Python/Litestar)
- Database schema with migrations
- Authentication system with session management
- Role-based authorization system with three profiles:
  - Administrador: Full access
  - Organizador: Can manage events, participants, and perform check-in/check-out
  - Voluntário: Can only perform check-in/check-out
- CRUD operations for events and participants (restricted to admin/organizer)
- Check-in/check-out functionality with safety codes (accessible to all profiles)
- Responsive HTMX frontend with navigation menu
- Sample data initialization

## Known Issues/Areas for Improvement
- No comprehensive testing suite
- Limited error handling in some controllers
- No API documentation
- Missing deployment configuration
- UI could show/hide buttons based on user permissions