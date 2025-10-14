# System Architecture

## Overview
Events Organizer is a modern web application built with a layered architecture using Python, Litestar framework, and HTMX for dynamic frontend interactions. The system follows a service-oriented architecture with clear separation of concerns.

## Architecture Components

### 1. Presentation Layer (Frontend)
- **HTMX + Jinja2 Templates**: Dynamic web interface with server-side rendering
- **CSS**: Responsive styling with mobile-first approach
- **Static Assets**: Images, icons, and client-side resources

### 2. Application Layer (Controllers)
- **AuthController**: Handles user authentication and session management
- **EventController**: CRUD operations for events and occurrences
- **ParticipantController**: Participant management with guardian relationships
- **OccurrenceController**: Check-in/check-out functionality with safety codes
- **UserController**: User management (API endpoints)

### 3. Service Layer
- **EventService**: Business logic for event management
- **ParticipantService**: Participant operations and age calculations
- **AttendanceService**: Check-in/check-out logic with security codes
- **OccurrenceService**: Event occurrence management
- **UserService**: User authentication and management

### 4. Data Access Layer
- **Advanced Alchemy ORM**: Database abstraction and query building
- **SQLAlchemy Models**: Database schema definitions
- **Repository Pattern**: Data access abstraction

### 5. Infrastructure Layer
- **PostgreSQL Database**: Primary data storage
- **Alembic Migrations**: Database schema versioning
- **Session Management**: Server-side session storage
- **Configuration**: Environment-based settings

## Key Design Patterns

### Repository Pattern
All data access is abstracted through repository classes that provide a consistent interface for database operations.

### Service Layer Pattern
Business logic is encapsulated in service classes that coordinate between controllers and repositories.

### Dependency Injection
Litestar provides service dependencies to controllers, enabling loose coupling and testability.

### Middleware Pattern
Authentication middleware intercepts requests to enforce security policies. Authorization helpers provide role-based access control at the controller level.

## Data Flow

1. **Request Processing**:
   - HTTP request → Litestar routing → Controller method
   - Controller receives injected services
   - Service executes business logic
   - Repository handles data access
   - Response rendered via HTMX templates

2. **Authentication Flow**:
   - Request → AuthMiddleware → Session validation
   - User data stored in session
   - Controllers check session for authorization

3. **Check-in/Check-out Flow**:
   - Participant selection → Age verification
   - Security code generation (minors) → Hash storage
   - Attendance record creation → Code verification for checkout

## Security Architecture

### Authentication
- Session-based authentication with server-side storage
- Password hashing using bcrypt
- Session expiration and cleanup

### Authorization
- Role-based access control with three profiles:
  - **Administrador**: Full access to all features
  - **Organizador**: Can manage events, participants, and perform check-in/check-out
  - **Voluntário**: Can only perform check-in/check-out operations
- Controller-level authorization checks using `require_profiles()` helper
- Route-level middleware protection for authentication
- Guardian verification for child check-out

### Data Security
- Hash-based safety codes for children
- Input validation with msgspec schemas
- SQL injection prevention via ORM

## Database Schema

### Core Entities
- **Users**: System users with roles
- **Participants**: Event attendees with guardian relationships
- **Events**: Single or recurring event definitions
- **EventOccurrences**: Generated instances of events
- **Attendance**: Check-in/check-out records
- **UserSessions**: Session storage

### Relationships
- Participants can have guardians (self-referencing)
- Events generate multiple occurrences
- Attendance links participants to occurrences
- Users have sessions for authentication

## Component Relationships

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Controllers   │────│    Services     │────│  Repositories   │
│                 │    │                 │    │                 │
│ • Auth          │    │ • Event         │    │ • SQLAlchemy    │
│ • Event         │    │ • Participant   │    │ • Models        │
│ • Participant   │    │ • Attendance    │    │ • Queries       │
│ • Occurrence    │    │ • User          │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Database      │
                    │   PostgreSQL    │
                    └─────────────────┘
```

## Critical Implementation Paths

### Event Creation Flow
1. EventController.create_event() receives form data
2. EventService.create() validates and saves event
3. Occurrence generation logic creates EventOccurrence records
4. Response updates UI via HTMX

### Check-in Flow
1. OccurrenceController.checkin() validates participant
2. Age calculation determines security code requirement
3. AttendanceService creates attendance record
4. Security code displayed to user

### Check-out Flow
1. OccurrenceController.checkout() receives participant and code
2. AttendanceService retrieves existing attendance
3. Code verification for minors
4. Attendance record updated with checkout time

## Performance Considerations

- **Database Indexing**: Strategic indexes on frequently queried fields
- **Connection Pooling**: Async connection management
- **Lazy Loading**: Selective data loading in relationships
- **Pagination**: Limit-offset pagination for large datasets

## Scalability Features

- **Async Operations**: Full async/await support throughout
- **Stateless Design**: Session-based state management
- **Modular Architecture**: Clear separation enabling horizontal scaling
- **Database Optimization**: Efficient queries and indexing strategy