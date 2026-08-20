from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from app.db.database import Base, engine
from app.models import user, document, chat  # noqa: F401
from app.api import auth, documents, chat as chat_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CampusMind Backend",
    description="Enterprise Academic AI & Knowledge Retrieval Platform API",
    version="1.0.0"
)

# CORS Configuration
# Supports comma-separated origins from environment variables or defaults to all origins
allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "*")
if allowed_origins_env == "*":
    origins = ["*"]
else:
    origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat_router.router)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "CampusMind backend is running"}
