from datetime import datetime, date
import msgspec


class BaseSchema(
    msgspec.Struct,
    omit_defaults=True,
    forbid_unknown_fields=True,
    rename="kebab",
):
    pass

# ################################################
# -- User

class UserRead(BaseSchema):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    profile: str | None = None
    updated_at: datetime | None = None


class UserCreate(BaseSchema):
    username: str
    email: str
    is_active: bool
    profile: str | None = None


class UserUpdate(BaseSchema):
    username: str
    email: str
    is_active: bool
    profile: str | None = None


# ################################################
# -- Event

class AttendanceRead(BaseSchema):
    checkin_at: datetime
    checkout_at: datetime
    code_hash: str | None = None
    checkout_by_participant_id: int | None = None
    

class EventOccurrenceRead(BaseSchema):
    id: int
    event_id: int
    start_at: datetime
    end_at: datetime
    attendances: list[AttendanceRead] = []


class EventRead(BaseSchema):
    id: int
    name: str
    description: str
    is_recurring: bool | None = None
    single_start: datetime | None = None
    single_end: datetime | None = None
    recurrence_start_date: date | None = None
    recurrence_end_date: date | None = None
    recurrence_rule: dict[str, list[str]] = {}
    occurrences: list[EventOccurrenceRead] = []


class EventCreate(BaseSchema):
    name: str
    description: str
    is_recurring: bool | None = None
    single_start: datetime | None = None
    single_end: datetime | None = None
    recurrence_start_date: date | None = None
    recurrence_end_date: date | None = None
    recurrence_rule: dict[str, list[str]] = {}
    occurrences: list[EventOccurrenceRead] = []


class EventUpdate(BaseSchema):
    name: str
    description: str
    is_recurring: bool | None = None
    single_start: datetime | None = None
    single_end: datetime | None = None
    recurrence_start_date: date | None = None
    recurrence_end_date: date | None = None
    recurrence_rule: dict[str, list[str]] = {}
    occurrences: list[EventOccurrenceRead] = []


# ################################################
# -- Participant

class ParticipantRead(BaseSchema):
    id: int
    full_name: str
    birth_date: date
    phone: str | None = None
    observations: str | None = None
    guardian_id: int | None = None


class ParticipantCreate(BaseSchema):
    full_name: str
    birth_date: date
    phone: str | None = None
    observations: str | None = None
    guardian_id: int | None = None


class ParticipantUpdate(BaseSchema):
    full_name: str
    birth_date: date
    phone: str | None = None
    observations: str | None = None
    guardian_id: int | None = None