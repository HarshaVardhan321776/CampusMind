import os
from pydantic_settings import BaseSettings

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str
    GROQ_API_KEY: str

    class Config:
        env_file = ENV_PATH
        extra = "ignore"

settings = Settings()