from fastapi import FastAPI
from app.db.database import Base, engine
from app.models import user, document, chat  # noqa: F401
from app.api import auth, documents, chat as chat_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CampusMind Backend")

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat_router.router)

@app.get("/health")
def health_check():
    return {"status": "CampusMind backend is running"}
