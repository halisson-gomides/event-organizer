# 📅 Events Organizer

A modern web application for organizing and managing presential events, built with Python, Litestar, and HTMX.

## ✨ Features

- **Event Management**: Create single or recurring events with flexible scheduling
- **Participant Management**: Register participants with guardian relationships for minors
- **Check-in/Check-out System**: Secure attendance tracking with safety codes for children
- **User Authentication**: Login/register system with role-based access
- **Responsive Design**: Mobile-friendly interface with HTMX for smooth interactions
- **PostgreSQL Database**: Robust data storage with Alembic migrations

## 🛠️ Tech Stack

- **Backend**: Python 3.12+ with Litestar framework
- **Database**: PostgreSQL with Advanced Alchemy ORM
- **Frontend**: HTMX + Jinja2 templates + CSS
- **Validation**: msgspec for data validation
- **Authentication**: Session-based with bcrypt password hashing
- **Containerization**: Docker & Docker Compose ready

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL (or use Docker)
- uv (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd events-organizer
   ```

2. **Install dependencies**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   uv sync
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Start the database** (using Docker)
   ```bash
   docker-compose up -d db
   ```

5. **Initialize the database**
   ```bash
   uv run python init_db.py
   ```
or

> **Run database migrations**
   ```bash
   alchemy --config app.alchemy_config init
   litestar database make-migrations
   litestar database upgrade
   ```

7. **Start the application**
   ```bash
   uv run uvicorn app:app --reload
   ```

8. **Access the application**
   - Open http://localhost:8000
   - Login with: `admin` / `admin123`

### Using Dev Container

If you prefer using VS Code with Dev Containers:

1. Open the project in VS Code
2. Click "Reopen in Container" when prompted
3. Run the initialization script: `python init_db.py`
4. Start the app: `uvicorn app:app --reload --host 0.0.0.0`

## 📖 Usage

### Managing Events

- **Single Events**: Create one-time events with specific start/end times
- **Recurring Events**: Set up weekly events with multiple time slots
- **Event Occurrences**: System automatically generates occurrence instances

### Managing Participants

- **Adult Participants**: Full registration with contact information
- **Minor Participants**: Linked to adult guardians for safety
- **Guardian Relationships**: Adults can be responsible for multiple children

### Check-in/Check-out Process

1. **Check-in**: Select participant and event occurrence
   - Children receive a security code for pickup
2. **Check-out**: Verify identity and security code (for minors)
   - Record who performed the checkout

### User Management

- **Registration**: Create new user accounts with role assignment
- **Authentication**: Session-based login system
- **Roles**: Admin, Organizer, Volunteer profiles

## 🏗️ Project Structure

```
events-organizer/
├── controllers/          # HTTP route handlers
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
├── templates/           # Jinja2 HTML templates
│   ├── base.html
│   ├── event_*.html
│   ├── participant_*.html
│   ├── checkin.html
│   ├── checkout.html
│   ├── login.html
│   └── register.html
├── static/             # CSS, JS, images
├── migrations/         # Alembic database migrations
├── models.py          # SQLAlchemy data models
├── schemas.py         # msgspec validation schemas
├── database.py        # Database configuration
├── config.py          # Application settings
├── middleware.py      # Custom middleware
├── app.py            # Main application entry point
└── init_db.py        # Database initialization script
```

## 🔧 Configuration

Key environment variables in `.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/events_organizer

# Security
SECRET_KEY=your-secret-key-here

# Application
DEBUG=true
```

## 🧪 Development

### Running Tests

```bash
uv run pytest
```

### Database Migrations

Create a new migration:
```bash
uv run alembic revision --autogenerate -m "Description"
```

Apply migrations:
```bash
uv run alembic upgrade head
```

### Code Formatting

```bash
uv run black .
uv run ruff check .
```

## 📝 API Endpoints

### Authentication
- `GET /auth/login` - Login form
- `POST /auth/login` - Process login
- `GET /auth/register` - Registration form  
- `POST /auth/register` - Process registration
- `POST /auth/logout` - Logout

### Events
- `GET /events` - List events
- `GET /events/new` - New event form
- `POST /events` - Create event
- `GET /events/{id}/edit` - Edit event form
- `POST /events/{id}` - Update event
- `DELETE /events/{id}` - Delete event

### Participants
- `GET /participants` - List participants
- `GET /participants/new` - New participant form
- `POST /participants` - Create participant
- `GET /participants/{id}/edit` - Edit participant form
- `POST /participants/{id}` - Update participant
- `DELETE /participants/{id}` - Delete participant

### Check-in/Check-out
- `GET /occurrences/{id}/checkin` - Check-in form
- `POST /occurrences/{id}/checkin` - Process check-in
- `GET /occurrences/{id}/checkout` - Check-out form
- `POST /occurrences/{id}/checkout` - Process check-out

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the GNU GPL License - see the LICENSE file for details.

## 🆘 Support

For questions or issues:
1. Check the existing issues on GitHub
2. Create a new issue with detailed information
3. Include steps to reproduce any bugs

---
