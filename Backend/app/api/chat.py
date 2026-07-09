from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag import answer_question

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/ask", response_model=ChatResponse)
def ask_question(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    history = [msg.model_dump() for msg in request.chat_history] if request.chat_history else None
    result = answer_question(request.question, chat_history=history)
    return result