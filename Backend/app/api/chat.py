from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.chat import Conversation, Message
from app.schemas.chat import ChatRequest, ChatResponse, ConversationOut, ConversationDetail
from app.services.rag import answer_question

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/ask", response_model=ChatResponse)
def ask_question(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if request.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == request.conversation_id,
            Conversation.user_id == current_user.id,
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation(
            user_id=current_user.id,
            title=request.question[:50],
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    previous_messages = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.created_at).all()

    chat_history = []
    for m in previous_messages[-10:]:
        content = m.content or ""
        if len(content) > 4000:
            content = content[:4000] + "..."
        chat_history.append({"role": m.role, "content": content})

    result = answer_question(
        question=request.question,
        user_id=current_user.id,
        document_id=request.document_id,
        chat_history=chat_history,
    )

    user_msg = Message(conversation_id=conversation.id, role="user", content=request.question)
    db.add(user_msg)

    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=result["answer"],
        sources=",".join(result["sources"]),
    )
    db.add(assistant_msg)
    db.commit()

    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "conversation_id": conversation.id,
    }


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.created_at.desc()).all()


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation
