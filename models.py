from datetime import date, datetime
from typing import Optional, List, Dict, Any
from advanced_alchemy.extensions.litestar import base
from advanced_alchemy.extensions.litestar.session import SessionModelMixin
from sqlalchemy import (
    String, Integer, Date, DateTime, Boolean, ForeignKey, UniqueConstraint, JSON, func, Index, text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


class ParticipantModel(base.DefaultBase):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(15), nullable=True)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    observations: Mapped[str] = mapped_column(String(200), nullable=True)
    guardian_id: Mapped[Optional[int]] = mapped_column(ForeignKey("participants.id"), nullable=True)

    guardian: Mapped[Optional["ParticipantModel"]] = relationship(remote_side=[id], backref="dependents")

    # helper para calcular idade numa data de referência
    def age_on(self, on_date: date) -> int:
        years = on_date.year - self.birth_date.year
        before_birthday = (on_date.month, on_date.day) < (self.birth_date.month, self.birth_date.day)
        return years - int(before_birthday)


class EventModel(base.DefaultBase):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000))
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Para evento avulso
    single_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    single_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Para recorrente
    recurrence_start_date: Mapped[Optional[date]] = mapped_column(Date)
    recurrence_end_date: Mapped[Optional[date]] = mapped_column(Date)
    # Regra JSON e.g.:
    # {
    #   "frequency": "weekly",
    #   "weekdays": [0],      # 0=Monday ... 6=Sunday (padrão Python)
    #   "time_windows": [{"start": "10:00", "end": "12:00"}, {"start": "18:00", "end": "20:00"}]
    # }
    recurrence_rule: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    occurrences: Mapped[List["EventOccurrenceModel"]] = relationship(back_populates="event", cascade="all, delete-orphan", lazy="selectin")


class EventOccurrenceModel(base.DefaultBase):
    __tablename__ = "event_occurrences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    event: Mapped[EventModel] = relationship(back_populates="occurrences", lazy="joined", innerjoin=True, viewonly=True)
    attendances: Mapped[List["AttendanceModel"]] = relationship(back_populates="occurrence", cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("event_id", "start_at", "end_at", name="uq_occurrence_unique_window"),
        Index("ix_occurrence_start", "start_at"),
    )


class AttendanceModel(base.DefaultBase):
    __tablename__ = "attendance"

    occurrence_id: Mapped[int] = mapped_column(
        ForeignKey("event_occurrences.id", ondelete="CASCADE"), primary_key=True
    )
    participant_id: Mapped[int] = mapped_column(
        ForeignKey("participants.id", ondelete="CASCADE"), primary_key=True
    )
    checkin_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    checkout_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Código de segurança: guardamos apenas o hash
    code_hash: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Quem realizou o checkout (opcional; para criança deve ser o guardião)
    checkout_by_participant_id: Mapped[Optional[int]] = mapped_column(ForeignKey("participants.id"))

    participant: Mapped[ParticipantModel] = relationship(foreign_keys=[participant_id])
    checkout_by_participant: Mapped[Optional[ParticipantModel]] = relationship(foreign_keys=[checkout_by_participant_id])
    occurrence: Mapped[EventOccurrenceModel] = relationship(back_populates="attendances", lazy="joined", innerjoin=True, viewonly=True)

    __table_args__ = (
        UniqueConstraint("occurrence_id", "participant_id", name="uq_attendance_once"),
        Index("ix_attendance_checkin", "checkin_at"),
    )


class UserSessionModel(SessionModelMixin):
    __tablename__ = "user_sessions"

    # The mixin provides these fields automatically:
    # - id: UUIDv7 primary key
    # - session_id: String(255) session identifier
    # - data: LargeBinary session data
    # - expires_at: DateTime expiration timestamp
    # - created_at, updated_at: Audit timestamps


class UserModel(base.DefaultBase):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    profile: Mapped[str] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default=text('false'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)

    __table_args__ = (
        UniqueConstraint("username", name="uq_users_username"),
        UniqueConstraint("email", name="uq_users_email"),
        
        Index("ix_users_created_at_desc", text("created_at DESC")),
    )

    def set_password(self, raw_password: str) -> None:        
        from passlib.hash import bcrypt
        self.password_hash = bcrypt.hash(raw_password)

