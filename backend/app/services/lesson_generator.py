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
4. ## Примеры кода / Команды (с подробными комментариями)
5. ## Типичные ошибки и подводные камни
6. ## Практические упражнения для самопроверки
7. ## Резюме урока

Правила режимов:
- В режиме «Свободное обучение»: используй свои знания модели и цитируй материалы, если они переданы.
- В режиме «Мои материалы + знания ИИ»: в первую очередь опирайся на переданные фрагменты документов, а собственные пояснения четко маркируй блоком «> [!NOTE] Дополнение ИИ».
- В режиме «Только мои материалы»: используй исключительно факты из переданных фрагментов. Если информации не хватает, явно напиши об этом.
"""

def generate_fallback_lesson_content(lesson_title: str, course_title: str) -> str:
    return f"""# {lesson_title}

> Курс: **{course_title}**

## Введение и Цель
В этом уроке мы разберём ключевые аспекты темы «{lesson_title}». Понимание этих концепций необходимо для уверенного владения материалом и перехода к более сложным практическим задачам.

## Основные концепции
- **Базовый принцип:** структурированное понимание алгоритма или команды.
- **Практическое назначение:** решение типовых задач в реальных проектах.
- **Ключевые сущности:** синтаксис, параметры и возвращаемые значения.

```cpp
// Пример базовой структуры решения
#include <iostream>

int main() {{
    std::cout << "Second Brain AI: Изучение темы {lesson_title}" << std::endl;
    return 0;
}}
```

## Типичные ошибки
1. Преждевременная оптимизация без понимания базового синтаксиса.
2. Игнорирование проверки граничных условий и сообщений компилятора/интерпретатора.

## Упражнение для самопроверки
Попробуйте объяснить своими словами или реализовать небольшую программу, демонстрирующую основной механизм темы «{lesson_title}».
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
            logger.warning(f"AI lesson generation failed, using structured template: {e}")
            content = generate_fallback_lesson_content(lesson.title, course_title)

        lesson.content_markdown = content
        self.db.commit()
        self.db.refresh(lesson)
        return content
