import os
from pydantic_settings import BaseSettings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(BASE_DIR, ".env")

class Settings(BaseSettings):
    SECRET_KEY: str = "supersecretkeycampusmind2026jwtsecret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days persistence
    DATABASE_URL: str = f"sqlite:///{os.path.join(BASE_DIR, 'campusmind.db')}"
    GROQ_API_KEY: str = ""
    CHROMA_DIR: str = os.path.join(BASE_DIR, "chroma_db")
    UPLOAD_DIR: str = os.path.join(BASE_DIR, "uploaded_docs")

    class Config:
        env_file = ENV_PATH
        extra = "ignore"

settings = Settings()
