from dataclasses import dataclass
from litestar.dto import DataclassDTO, DTOConfig
from typing import Optional
from datetime import datetime


@dataclass
class UserSchema:
    """User response schema."""
    id: int
    username: str
    email: str
    profile: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    

class UserRead(DataclassDTO[UserSchema]):
    config = DTOConfig(exclude={"updated_at"})


class UserCreate(DataclassDTO[UserSchema]):
    config = DTOConfig(exclude={"id", "created_at", "updated_at"})


class UserUpdate(DataclassDTO[UserSchema]):
    config = DTOConfig(exclude={"id", "created_at", "updated_at"})