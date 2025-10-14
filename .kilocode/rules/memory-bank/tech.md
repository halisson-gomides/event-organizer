# Technology Stack & Development Setup

## Technologies Used

### Backend Framework
- **Python 3.12+**: Core programming language
- **Litestar 2.17.0+**: Modern async web framework
- **Advanced Alchemy 1.6.2+**: SQLAlchemy wrapper with Litestar integration
- **AsyncPG**: PostgreSQL async driver

### Frontend Technologies
- **HTMX 1.9.12**: Dynamic web interactions without JavaScript
- **Jinja2**: Server-side templating engine
- **CSS3**: Responsive styling with custom design system

### Database & Storage
- **PostgreSQL**: Primary relational database
- **Alembic**: Database migration management
- **SQLAlchemy**: ORM for database operations

### Security & Authentication
- **PassLib[Bcrypt]**: Password hashing
- **Server-side Sessions**: Session management via Advanced Alchemy
- **UUID7**: Secure session identifiers

### Data Validation
- **msgspec 0.19.0+**: High-performance data validation and serialization

### Development Tools
- **uv**: Fast Python package manager
- **Docker & Docker Compose**: Containerization and local database
- **Dev Containers**: Consistent development environment

## Development Setup

### Prerequisites
- Python 3.12+
- PostgreSQL (or Docker)
- uv package manager
- VS Code with Dev Containers (optional)

### Installation Steps

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd events-organizer
   ```

2. **Install uv Package Manager**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install Dependencies**
   ```bash
   uv sync
   source .venv/bin/activate
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with database credentials
   ```

5. **Database Setup**
   - **Using Docker:**
     ```bash
     docker-compose up -d db
     ```
   - **Using Local PostgreSQL:**
     - Ensure PostgreSQL is running
     - Update DATABASE_URL in .env

6. **Initialize Database**
   ```bash
   uv run python init_db.py
   ```
   Or run migrations:
   ```bash
   litestar database init
   litestar database make-migrations
   litestar database upgrade
   ```

7. **Start Development Server**
   ```bash
   uv run uvicorn app:app --reload
   ```

8. **Access Application**
   - URL: http://localhost:8000
   - Default login: admin / admin123

### Dev Container Setup (VS Code)

1. Open project in VS Code
2. Click "Reopen in Container" when prompted
3. Run initialization: `python init_db.py`
4. Start server: `uvicorn app:app --reload --host 0.0.0.0`

## Project Structure

```
events-organizer/
├── app.py                 # Main application entry point
├── config.py             # Configuration management
├── database.py           # Database connection setup
├── init_db.py            # Database initialization script
├── middleware.py         # Authentication middleware
├── models.py             # SQLAlchemy models
├── schemas.py            # Data validation schemas
├── pyproject.toml        # Project dependencies
├── uv.lock              # Dependency lock file
├── alembic.ini          # Database migration config
├── .env.example         # Environment template
├── controllers/         # Route handlers
│   ├── auth_controller.py
│   ├── event_controller.py
│   ├── occurrence_controller.py
│   ├── participant_controller.py
│   └── user_controller.py
├── services/            # Business logic layer
│   ├── attendance_service.py
│   ├── event_service.py
│   ├── occurrence_service.py
│   ├── participant_service.py
│   └── user_service.py
├── templates/           # Jinja2 templates
│   ├── base.html
│   ├── event_form.html
│   ├── event_list.html
│   └── ...
├── static/              # Static assets
│   ├── css/
│   │   └── styles.css
│   └── img/
├── migrations/          # Database migrations
│   ├── versions/
│   └── env.py
└── .kilocode/           # Project documentation
    └── rules/
        └── memory-bank/
```

## Key Configuration Files

### Environment Variables (.env)
```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/events_organizer

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production

# Application
DEBUG=true

# Optional: Timezone
TZ=America/Sao_Paulo
```

### pyproject.toml Dependencies
- Core web framework: litestar[standard]
- Database: advanced-alchemy[cli], asyncpg
- Security: passlib[bcrypt], python-dotenv
- Validation: msgspec
- Utilities: uuid-utils

## Development Workflow

### Running Tests
```bash
uv run pytest
```

### Database Operations
```bash
# Create new migration
litestar database make-migrations

# Apply migrations
litestar database upgrade

# Rollback migration
litestar database downgrade
```

### Code Quality
- **Linting**: ruff (configured in hooks)
- **Formatting**: black (via pre-commit hooks)
- **Type Checking**: mypy (recommended)

## Deployment Considerations

### Production Requirements
- **WSGI Server**: gunicorn or uvicorn workers
- **Reverse Proxy**: nginx
- **SSL/TLS**: Let's Encrypt certificates
- **Database**: Managed PostgreSQL instance
- **Environment**: Docker containers
- **Monitoring**: Application logs and database monitoring

### Security Hardening
- Change default SECRET_KEY
- Use strong DATABASE_URL credentials
- Enable HTTPS in production
- Configure session timeouts
- Implement rate limiting
- Regular security updates