#!/usr/bin/env python3
"""
Database initialization script for Events Organizer.
This script creates the database tables and optionally adds sample data.
"""

import asyncio
from datetime import date, datetime, timedelta
from advanced_alchemy.extensions.litestar import create_engine_from_config
from config import settings
from database import alchemy_config
from models import UserModel, ParticipantModel, EventModel, EventOccurrenceModel
from sqlalchemy.ext.asyncio import AsyncSession


async def init_database():
    """Initialize the database with tables and sample data."""
    
    # Create engine
    engine = create_engine_from_config(alchemy_config)
    
    # Create all tables
    async with engine.begin() as conn:
        # Import all models to ensure they're registered
        from models import (
            UserModel, ParticipantModel, EventModel, 
            EventOccurrenceModel, AttendanceModel, UserSessionModel
        )
        
        # Create all tables
        await conn.run_sync(alchemy_config.metadata.create_all)
        print("✅ Database tables created successfully!")
    
    # Add sample data
    async with AsyncSession(engine) as session:
        # Create admin user
        admin_user = UserModel(
            username="admin",
            email="admin@example.com",
            is_active=True,
            profile="admin"
        )
        admin_user.set_password("admin123")
        session.add(admin_user)
        
        # Create sample participants
        participants = [
            ParticipantModel(
                full_name="João Silva",
                birth_date=date(1985, 3, 15),
                phone="(11) 99999-1111",
                observations="Responsável"
            ),
            ParticipantModel(
                full_name="Maria Santos",
                birth_date=date(1990, 7, 22),
                phone="(11) 99999-2222",
                observations="Organizadora"
            ),
            ParticipantModel(
                full_name="Pedro Silva",
                birth_date=date(2015, 5, 10),
                phone=None,
                observations="Filho do João",
                guardian_id=1  # Will be set after João is saved
            ),
            ParticipantModel(
                full_name="Ana Santos",
                birth_date=date(2012, 12, 3),
                phone=None,
                observations="Filha da Maria",
                guardian_id=2  # Will be set after Maria is saved
            )
        ]
        
        for participant in participants:
            session.add(participant)
        
        # Create sample events
        today = datetime.now()
        
        # Single event
        single_event = EventModel(
            name="Workshop de Python",
            description="Introdução ao desenvolvimento web com Python e Litestar",
            is_recurring=False,
            single_start=today + timedelta(days=7, hours=2),
            single_end=today + timedelta(days=7, hours=6)
        )
        session.add(single_event)
        
        # Recurring event
        recurring_event = EventModel(
            name="Aula de Música",
            description="Aulas semanais de música para crianças",
            is_recurring=True,
            recurrence_start_date=today.date(),
            recurrence_end_date=today.date() + timedelta(days=90),
            recurrence_rule={
                "frequency": "weekly",
                "weekdays": [1, 3],  # Tuesday and Thursday
                "time_windows": [{"start": "14:00", "end": "16:00"}]
            }
        )
        session.add(recurring_event)
        
        await session.commit()
        print("✅ Sample data added successfully!")
        
        print("\n🎉 Database initialization complete!")
        print("\n📋 Sample login credentials:")
        print("   Username: admin")
        print("   Password: admin123")
        print("\n🚀 You can now start the application with: python -m uvicorn app:app --reload")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_database())