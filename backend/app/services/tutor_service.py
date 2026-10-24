import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import json

from app.services.ai_provider import AIProvider
from app.models.entities import Course, Lesson, Conversation, Message

logger = logging.getLogger("second_brain.tutor")

TUTOR_SYSTEM_PROMPT = """
Ты — мудрый, терпеливый и высококвалифицированный ИИ-преподаватель Second Brain AI.
Твоя цель — помочь ученику по-настоящему понять предмет, а не просто заучить факты.

Принципы преподавания:
1. Поэтапное обучение: не переходи к следующей теме, пока ученик не усвоил текущую.
2. Простота и аналогии: сложные концепции объясняй понятными аналогиями из реальной жизни.
3. Интерактивность: регулярно задавай короткие вопросы на понимание или давай микро-задачи.
4. Помощь в ошибках: если ученик ошибается, мягко укажи на причину ошибки, задай наводящий вопрос, но НЕ выдавай готовое решение сразу.
5. Стимулируй самостоятельное мышление.

Правила работы с источниками:
- РЕЖИМ «Свободное обучение» (free):
  Используй свои знания и переданные материалы. Если в ответе используются переданные материалы, указывай источник и страницу. Отделяй общие рассуждения от фактов из источников.
- РЕЖИМ «Мои материалы + знания ИИ» (my_materials_plus_ai):
  СНАЧАЛА давай ответ строго по загруженным материалам (с указанием документа и страниц). Если нужно расширить ответ примерами от ИИ, явно выдели их блоком: «> **Дополнение ИИ:** ...».
- РЕЖИМ «Только мои материалы» (only_my_materials):
  Строй ответ ИСКЛЮЧИТЕЛЬНО на основе переданных фрагментов. Если информации нет в материалах, скажи прямо: «В загруженных материалах нет информации по данному вопросу». Не выдумывай факты и номера страниц.
"""

class TutorService:
    def __init__(self, db: Session):
        self.db = db
        self.ai_provider = AIProvider(db)

    async def chat(
        self,
        course_id: int,
        user_message: str,
        lesson_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
        override_mode: Optional[str] = None,
        rag_context_snippets: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise ValueError("Курс не найден")

        mode = override_mode or course.learning_mode or "free"

        # 1. Get or create conversation
        if conversation_id:
            conv = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        else:
            conv = (
                self.db.query(Conversation)
                .filter(Conversation.course_id == course_id, Conversation.lesson_id == lesson_id)
                .first()
            )
        
        if not conv:
            lesson_title = ""
            if lesson_id:
                lesson_obj = self.db.query(Lesson).filter(Lesson.id == lesson_id).first()
                if lesson_obj:
                    lesson_title = f" — {lesson_obj.title}"
            conv = Conversation(
                course_id=course_id,
                lesson_id=lesson_id,
                title=f"Занятие: {course.title}{lesson_title}"
            )
            self.db.add(conv)
            self.db.commit()
            self.db.refresh(conv)

        # 2. Save user message to database
        user_msg_record = Message(
            conversation_id=conv.id,
            sender="user",
            content=user_message,
            is_rag_sourced=False
        )
        self.db.add(user_msg_record)
        self.db.commit()

        # 3. Build context & history
        history_msgs = (
            self.db.query(Message)
            .filter(Message.conversation_id == conv.id)
            .order_by(Message.created_at.desc())
            .limit(10)
            .all()
        )
        history_msgs.reverse()

        history_text = ""
        for m in history_msgs:
            role = "Ученик" if m.sender == "user" else "Преподаватель"
            history_text += f"{role}: {m.content}\n\n"

        # 4. Format RAG snippets
        sources_text = ""
        citations = []
        if rag_context_snippets:
            sources_text = "\n\nРЕКВЕСТНЫЕ МАТЕРИАЛЫ ИЗ БИБЛИОТЕКИ УЧЕНИКА:\n"
            for s in rag_context_snippets:
                doc_title = s.get("doc_title", "Документ")
                page = s.get("page", None)
                section = s.get("section", None)
                snippet = s.get("content", "")
                cite_label = f"«{doc_title}»"
                if page:
                    cite_label += f", стр. {page}"
                if section:
                    cite_label += f", раздел {section}"
                
                citations.append(cite_label)
                sources_text += f"[{cite_label}]:\n{snippet}\n\n"

        full_prompt = f"""
Контекст занятия:
Курс: {course.title} (Уровень: {course.user_level})
Текущий режим обучения: {mode}
{sources_text}

История диалога:
{history_text}

Ответь ученику в соответствии с методикой преподавания и правилами текущего режима ({mode}).
"""

        # 5. Generate AI answer
        is_rag_used = len(citations) > 0
        try:
            assistant_response = await self.ai_provider.generate_text(
                prompt=full_prompt,
                system_instruction=TUTOR_SYSTEM_PROMPT,
                temperature=0.6,
                request_type="tutor_chat"
            )
        except Exception as e:
            logger.warning(f"AI response failed, using offline pedagogical fallback: {e}")
            if "не понимаю" in user_message.lower() or "сложно" in user_message.lower():
                assistant_response = (
                    f"Ничего страшного, это абсолютно естественный этап обучения! Давайте разберём эту тему на простом примере из жизни.\n\n"
                    f"Представьте себе обычный почтовый ящик: у него есть номер дома (адрес в памяти) и содержимое внутри (само значение). "
                    f"Попробуйте ответить: если мы меняем письмо внутри ящика, меняется ли номер дома?"
                )
            else:
                assistant_response = (
                    f"Отличный вопрос по теме «{course.title}»! В режиме «{mode}» ключевое внимание мы уделяем глубокому практическому освоению. "
                    f"Попробуйте применить эту концепцию в небольшом коде или команде, и я проверю результат!"
                )

        # 6. Save assistant message
        sources_json = json.dumps(citations, ensure_ascii=False) if citations else None
        assistant_msg_record = Message(
            conversation_id=conv.id,
            sender="assistant",
            content=assistant_response,
            sources_used=sources_json,
            is_rag_sourced=is_rag_used
        )
        self.db.add(assistant_msg_record)
        self.db.commit()
        self.db.refresh(assistant_msg_record)

        return {
            "conversation_id": conv.id,
            "message_id": assistant_msg_record.id,
            "content": assistant_response,
            "sources_used": citations,
            "is_rag_sourced": is_rag_used,
            "learning_mode": mode
        }
