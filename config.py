import os
from dataclasses import dataclass
from dotenv import load_dotenv
import secrets

load_dotenv()

@dataclass
class Settings:
    database_url: str = os.getenv("DATABASE_URL")
    secret_key: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))

settings = Settings()