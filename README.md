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

2. **Install dependencies and active virtual environment**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   uv sync
   source .venv/bin/activate
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
&nbsp;&nbsp;or

 **Run database migrations**
   ```bash
   litestar database init
   litestar database make-migrations
   litestar database upgrade
   ```

6. **Start the application**
   ```bash
   uv run uvicorn app:app --reload
   ```

7. **Access the application**
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

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.

## 🆘 Support

For questions or issues:
1. Check the existing issues on GitHub
2. Create a new issue with detailed information
3. Include steps to reproduce any bugs

---
