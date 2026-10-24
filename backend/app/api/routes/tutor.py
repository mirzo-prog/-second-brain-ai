from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import json

from app.core.database import get_db
from app.models.entities import Conversation, Message
from app.schemas.schemas import ChatSendRequest, ConversationResponse, MessageResponse
from app.services.tutor_service import TutorService

router = APIRouter(prefix="/tutor", tags=["AI Tutor"])

@router.post("/chat")
async def chat_with_tutor(payload: ChatSendRequest, db: Session = Depends(get_db)):
    service = TutorService(db)
    
    # Check if we should fetch RAG snippets from attached documents
    rag_snippets = []
    try:
        from app.services.rag_service import RAGService
        rag_svc = RAGService(db)
        rag_snippets = rag_svc.search(
            query=payload.message,
            course_id=payload.course_id,
            limit=4
        )
    except Exception:
        # RAG is optional if no documents uploaded yet
        pass

    try:
        result = await service.chat(
            course_id=payload.course_id,
            user_message=payload.message,
            lesson_id=payload.lesson_id,
            conversation_id=payload.conversation_id,
            override_mode=payload.learning_mode,
            rag_context_snippets=rag_snippets
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка в работе ИИ-преподавателя: {str(e)}")

@router.get("/conversations/{course_id}", response_model=List[ConversationResponse])
def get_course_conversations(
    course_id: int,
    lesson_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Conversation).filter(Conversation.course_id == course_id)
    if lesson_id:
        query = query.filter(Conversation.lesson_id == lesson_id)
    convs = query.order_by(Conversation.updated_at.desc()).all()
    return convs

@router.get("/conversation/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Диалог не найден")
    return conv
