import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.services.ai_provider import AIProvider
from app.models.entities import Course, Lesson

logger = logging.getLogger("second_brain.lesson_gen")

SYSTEM_LESSON_PROMPT = """
Ты — профессиональный ИИ-преподаватель Second Brain AI.
Твоя задача — составить подробный, интерактивный, понятный урок в формате Markdown на русском языке.

Структура урока:
1. # Название урока
2. ## Введение и Цель (зачем это нужно, жизненная аналогия)
3. ## Теоретическая часть (чётко, структурированно, без воды)
4. ## Примеры / Практические иллюстрации
5. ## Типичные ошибки и подводные камни
6. ## Практические упражнения для самопроверки
7. ## Резюме урока

Правила режимов:
- В режиме «Свободное обучение»: используй свои знания модели и цитируй материалы, если они переданы.
- В режиме «Мои материалы + знания ИИ»: в первую очередь опирайся на переданные фрагменты документов, а собственные пояснения четко маркируй блоком «> [!NOTE] Дополнение ИИ».
- В режиме «Только мои материалы»: используй исключительно факты из переданных фрагментов. Если информации не хватает, явно напиши об этом.
"""

def generate_fallback_lesson_content(
    lesson_title: str,
    course_title: str,
    context_sources: Optional[List[Dict[str, Any]]] = None
) -> str:
    extracted_text = ""
    if context_sources:
        for s in context_sources:
            content = s.get("content", "").strip()
            if content:
                extracted_text += f"\n\n### Материал из источника «{s.get('doc_title', 'Библиотека')}»:\n{content[:2000]}\n"

    theory_block = extracted_text if extracted_text else f"""
В этом уроке детально исследуются фундаментальные основы и прикладные аспекты темы «{lesson_title}». 
Понимание этих механизмов необходимо для формирования системного мышления и уверенного перехода к последующим модулям.

### Ключевые положения:
1. **Фундаментальное определение:** Сущность, предмет и границы применения темы.
2. **Практическая польза:** Почему и в каких реальных проектах это используется.
3. **Системные взаимосвязи:** Как концепции этого урока связаны с общим курсом «{course_title}».
"""

    return f"""# {lesson_title}

> Курс: **{course_title}** • Статус: **Материал урока готов к изучению**

## Введение и Цель
Добро пожаловать в урок **«{lesson_title}»**! 
Наша цель — разобрать базовые принципы, закрепить терминологию и сформировать практическое понимание темы без абстрактной воды.

## Теоретическая часть
{theory_block}

## Практический пример и разбор ситуации
Рассмотрим стандартный сценарий применения принципов **«{lesson_title}»**:
- **Шаг 1:** Выявление исходных условий и постановка задачи.
- **Шаг 2:** Применение ключевого метода и пошаговая реализация.
- **Шаг 3:** Проверка корректности результата и сопоставление с эталоном.

## Типичные ошибки и подводные камни
1. Поверхностное ознакомление без фиксации определений и конспекта.
2. Пропуск базовых шагов в надежде сразу перейти к сложным задачам.
3. Недостаток практической проверки полученных знаний на реальных примерах.

## Практические упражнения для самопроверки
1. Сформулируйте своими словами 3 главных тезиса этого урока.
2. Приведите один жизненный или рабочий пример, где применяется концепция «{lesson_title}».
3. Используйте чат с **ИИ-преподавателем** в правой панели, чтобы задать любые вопросы или запросить дополнительный тест по материалу!

## Резюме урока
Вы успешно изучили ключевые положения урока «{lesson_title}». Переходите к закреплению материала в конспектах и к следующему шагу учебного плана!
"""

class LessonGeneratorService:
    def __init__(self, db: Session):
        self.db = db
        self.ai_provider = AIProvider(db)

    async def generate_lesson_content(
        self,
        lesson_id: int,
        context_sources: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        lesson = self.db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            raise ValueError("Урок не найден")

        course = self.db.query(Course).filter(Course.id == lesson.course_id).first()
        course_title = course.title if course else "Вводный курс"
        learning_mode = course.learning_mode if course else "free"

        # If context sources not passed, look up attached documents from Course
        if not context_sources and course:
            from app.models.entities import CourseDocument, Document, DocumentChunk
            doc_ids = [cd.document_id for cd in course.course_documents]
            if doc_ids:
                docs = self.db.query(Document).filter(Document.id.in_(doc_ids)).all()
                context_sources = []
                for d in docs:
                    # Grab chunks or first 2000 chars of file
                    chunks = self.db.query(DocumentChunk).filter(DocumentChunk.document_id == d.id).limit(3).all()
                    chunk_text = "\n".join([c.content for c in chunks])
                    if chunk_text:
                        context_sources.append({
                            "doc_title": d.title,
                            "content": chunk_text,
                            "page": 1,
                            "section": "Материалы"
                        })

        sources_block = ""
        if context_sources:
            sources_block = "\n\nДоступные фрагменты из учебных материалов пользователя:\n"
            for s in context_sources:
                sources_block += f"- Источник: «{s.get('doc_title', 'Документ')}» (стр. {s.get('page', 'Н/Д')}, раздел: {s.get('section', 'Основной')}):\n{s.get('content', '')}\n\n"

        prompt = f"""
Тема урока: {lesson.title}
Описание: {lesson.description}
Курс: {course_title}
Режим обучения: {learning_mode}
{sources_block}

Сгенерируй исчерпывающий, профессиональный урок в формате Markdown.
"""
        try:
            content = await self.ai_provider.generate_text(
                prompt=prompt,
                system_instruction=SYSTEM_LESSON_PROMPT,
                temperature=0.6,
                request_type="lesson_generation"
            )
        except Exception as e:
            logger.info(f"AI lesson generation not available or failed: {e}. Using specialized structured template.")
            content = generate_fallback_lesson_content(lesson.title, course_title, context_sources)

        lesson.content_markdown = content
        self.db.commit()
        self.db.refresh(lesson)
        return content
