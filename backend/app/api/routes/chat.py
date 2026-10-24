import datetime
import logging
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user_id
from app.models.entities import ChatSession, ChatMessage
from app.services.ai_provider import AIProvider, AIServiceError

logger = logging.getLogger("second_brain.chat")

router = APIRouter(prefix="/chat", tags=["Gemini Chat"])

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

class ChatMessageCreate(BaseModel):
    content: str

class ChatSessionCreate(BaseModel):
    title: Optional[str] = None

class ChatSessionRename(BaseModel):
    title: str

class ChatMessageOut(BaseModel):
    id: int
    session_id: int
    sender: str
    content: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class ChatSessionSummary(BaseModel):
    id: int
    title: str
    message_count: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class ChatSessionDetail(BaseModel):
    id: int
    title: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    messages: List[ChatMessageOut]

    class Config:
        from_attributes = True

SYSTEM_FREE_CHAT_PROMPT = """
Ты — Gemini, универсальный, эрудированный, дружелюбный и внимательный ИИ-собеседник.
Твоя роль в этом чате — свободное, естественное и непринужденное общение с пользователем.

Правила:
1. Отвечай прямо, содержательно и по существу вопроса.
2. Не навязывай создание учебных курсов и не превращай каждый разговор в урок, если пользователь просто хочет пообщаться.
3. Поддерживай любые темы: книги, наука, программирование, искусство, философия, советы, бытовые ситуации.
4. Используй красивый Markdown: выделяй главное, структурируй списки, для формул используй LaTeX, для кода — блоки кода с указанием языка.
5. Если чего-то не знаешь или информация неоднозначна, честно сообщай об этом без выдумывания фактов.
6. Общайся на том языке, на котором обращается пользователь (по умолчанию русский).
"""

@router.get("/sessions", response_model=List[ChatSessionSummary])
def list_sessions(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )
    result = []
    for s in sessions:
        result.append(ChatSessionSummary(
            id=s.id,
            title=s.title,
            message_count=len(s.messages),
            created_at=s.created_at,
            updated_at=s.updated_at
        ))
    return result

@router.post("/sessions", response_model=ChatSessionDetail, status_code=201)
def create_session(
    payload: Optional[ChatSessionCreate] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    title = (payload.title if payload and payload.title else "Новый диалог").strip()
    session = ChatSession(
        user_id=user_id,
        title=title or "Новый диалог"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return ChatSessionDetail(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[]
    )

@router.get("/sessions/{session_id}", response_model=ChatSessionDetail)
def get_session(
    session_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Диалог не найден")
    return ChatSessionDetail.model_validate(session)

@router.put("/sessions/{session_id}", response_model=ChatSessionSummary)
def rename_session(
    session_id: int,
    payload: ChatSessionRename,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Диалог не найден")
    
    new_title = payload.title.strip()
    if not new_title:
        raise HTTPException(status_code=400, detail="Название не может быть пустым")
    
    session.title = new_title
    session.updated_at = utcnow()
    db.commit()
    db.refresh(session)
    return ChatSessionSummary(
        id=session.id,
        title=session.title,
        message_count=len(session.messages),
        created_at=session.created_at,
        updated_at=session.updated_at
    )

@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Диалог не найден")
    db.delete(session)
    db.commit()
    return None

@router.post("/sessions/{session_id}/messages", response_model=ChatMessageOut)
async def send_message(
    session_id: int,
    payload: ChatMessageCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Диалог не найден")

    clean_content = payload.content.strip()
    if not clean_content:
        raise HTTPException(status_code=400, detail="Сообщение не может быть пустым")

    # 1. Save user message
    user_msg = ChatMessage(
        session_id=session.id,
        sender="user",
        content=clean_content
    )
    db.add(user_msg)
    
    # Auto-generate title if this is the first message or still named 'Новый диалог'
    if session.title in ("Новый диалог", "Новая беседа", ""):
        snippet = clean_content.split("\n")[0].strip()
        if len(snippet) > 40:
            snippet = snippet[:40].rstrip() + "..."
        session.title = snippet or "Беседа с Gemini"

    session.updated_at = utcnow()
    db.commit()

    # 2. Build dialogue context (last 12 messages for performance and context)
    history_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    if len(history_messages) > 12:
        history_messages = history_messages[-12:]

    dialogue_text = ""
    for m in history_messages:
        role = "Пользователь" if m.sender == "user" else "Gemini"
        dialogue_text += f"{role}: {m.content}\n\n"

    ai_provider = AIProvider(db)
    try:
        reply_text = await ai_provider.generate_text(
            prompt=f"{dialogue_text}Gemini:",
            system_instruction=SYSTEM_FREE_CHAT_PROMPT,
            temperature=0.7,
            request_type="free_chat"
        )
    except AIServiceError as e:
        reply_text = f"⚠️ {str(e)}"
    except Exception as e:
        logger.error(f"Error in Gemini free chat: {e}", exc_info=True)
        reply_text = f"Извините, произошла временная ошибка связи с Gemini: {str(e)}. Пожалуйста, попробуйте снова через несколько секунд."

    # 3. Save assistant message
    bot_msg = ChatMessage(
        session_id=session.id,
        sender="assistant",
        content=reply_text
    )
    db.add(bot_msg)
    session.updated_at = utcnow()
    db.commit()
    db.refresh(bot_msg)

    return ChatMessageOut.model_validate(bot_msg)

@router.post("/sessions/{session_id}/regenerate", response_model=ChatMessageOut)
async def regenerate_message(
    session_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Диалог не найден")

    # Find the last message
    last_msg = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.desc())
        .first()
    )
    if not last_msg:
        raise HTTPException(status_code=400, detail="В диалоге нет сообщений")

    # If last message was assistant, delete it to regenerate
    if last_msg.sender == "assistant":
        db.delete(last_msg)
        db.commit()

    # Re-fetch history
    history_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    if not history_messages:
        raise HTTPException(status_code=400, detail="Нет сообщений пользователя для ответа")

    dialogue_text = ""
    for m in history_messages[-10:]:
        role = "Пользователь" if m.sender == "user" else "Gemini"
        dialogue_text += f"{role}: {m.content}\n\n"

    ai_provider = AIProvider(db)
    try:
        reply_text = await ai_provider.generate_text(
            prompt=f"{dialogue_text}Gemini:",
            system_instruction=SYSTEM_FREE_CHAT_PROMPT,
            temperature=0.8,
            request_type="free_chat"
        )
    except AIServiceError as e:
        reply_text = f"⚠️ {str(e)}"
    except Exception as e:
        reply_text = f"Извините, произошла ошибка генерации ответа: {str(e)}"

    bot_msg = ChatMessage(
        session_id=session.id,
        sender="assistant",
        content=reply_text
    )
    db.add(bot_msg)
    session.updated_at = utcnow()
    db.commit()
    db.refresh(bot_msg)

    return ChatMessageOut.model_validate(bot_msg)
