from fastapi import FastAPI
from app.db.database import Base, engine
from app.models import user  # noqa: F401
from app.api import auth

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CampusMind Backend")

app.include_router(auth.router)

@app.get("/health")
def health_check():
    return {"status": "CampusMind backend is running"}