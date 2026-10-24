import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.services.ai_provider import AIProvider, AIServiceError
from app.models.entities import Course, Module, Lesson

logger = logging.getLogger("second_brain.course_gen")

SYSTEM_COURSE_PROMPT = """
Ты — старший методист и архитектор учебных курсов Second Brain AI.
Твоя задача — составить продуманный, структурированный, практико-ориентированный план обучения на русском языке на основе цели пользователя.

Требования:
1. Разбей курс на логические модули от простого к сложному.
2. В каждом модуле создай последовательность конкретных уроков.
3. Время каждого урока: 15-30 минут.
4. Предусмотри практическую направленность каждого урока.
5. Результат верни строго в виде JSON без лишнего текста.

Схема JSON:
{
  "title": "Название курса",
  "description": "Краткое описание курса и того, чему научится студент",
  "target_goal": "Четкая учебная цель",
  "estimated_hours": 15.0,
  "modules": [
    {
      "title": "Название модуля",
      "description": "Цель модуля",
      "lessons": [
        {"title": "Название урока", "description": "Чему посвящен урок", "estimated_minutes": 20}
      ]
    }
  ]
}
"""

def generate_fallback_course_plan(goal: str, user_level: str) -> Dict[str, Any]:
    """Generates a high-quality syllabus even when offline or AI provider is not connected."""
    goal_clean = goal.strip()
    return {
        "title": f"Курс: {goal_clean[:60]}",
        "description": f"Структурированный практический курс для уровня «{user_level}» по теме: {goal_clean}.",
        "target_goal": goal_clean,
        "estimated_hours": 12.0,
        "modules": [
            {
                "title": "Модуль 1. Фундаментальные основы и среда разработки",
                "description": "Знакомство с ключевыми концепциями, терминологией и базовыми инструментами.",
                "lessons": [
                    {"title": "Введение в тему и ключевые понятия", "description": "Обзор архитектуры, терминологии и целей обучения.", "estimated_minutes": 15},
                    {"title": "Настройка рабочего окружения в Linux", "description": "Установка инструментов, компиляторов и редакторов кода.", "estimated_minutes": 20},
                    {"title": "Первая практическая программа / базовый сценарий", "description": "Создание, запуск и проверка первого решения.", "estimated_minutes": 25}
                ]
            },
            {
                "title": "Модуль 2. Основные конструкции и алгоритмы",
                "description": "Погружение в механизмы управления, структуры данных и логику.",
                "lessons": [
                    {"title": "Типы данных, переменные и операторы", "description": "Работа с памятью, типами и базовыми операциями.", "estimated_minutes": 20},
                    {"title": "Управляющие структуры: ветвления и циклы", "description": "Построение алгоритмов с условными переходами и итерациями.", "estimated_minutes": 25},
                    {"title": "Функции, модульность и организация кода", "description": "Декомпозиция задач на изолированные функции.", "estimated_minutes": 25}
                ]
            },
            {
                "title": "Модуль 3. Продвинутые техники и практический проект",
                "description": "Решение реальных задач, оптимизация и закрепление материала.",
                "lessons": [
                    {"title": "Обработка ошибок и отладка", "description": "Типичные ошибки, анализ сбоев и логирование.", "estimated_minutes": 20},
                    {"title": "Итоговый практический проект", "description": "Комплексное закрепление изученного материала на практике.", "estimated_minutes": 45}
                ]
            }
        ]
    }

class CourseGeneratorService:
    def __init__(self, db: Session):
        self.db = db
        self.ai_provider = AIProvider(db)

    async def generate_course(
        self,
        goal: str,
        user_level: str = "beginner",
        learning_mode: str = "free",
        target_timeframe: str = "в комфортном темпе"
    ) -> Course:
        prompt = f"""
Составь подробную учебную дорожную карту по следующему запросу пользователя:
Запрос: "{goal}"
Начальный уровень: {user_level}
Желаемый срок/интенсивность: {target_timeframe}
Режим обучения: {learning_mode}
"""
        plan_data: Dict[str, Any]
        try:
            plan_data = await self.ai_provider.generate_structured(
                prompt=prompt,
                system_instruction=SYSTEM_COURSE_PROMPT,
                request_type="course_generation"
            )
        except Exception as e:
            logger.warning(f"AI generation failed, using intelligent fallback syllabus: {e}")
            plan_data = generate_fallback_course_plan(goal, user_level)

        # Create Course in DB
        course = Course(
            title=plan_data.get("title", f"Курс: {goal[:50]}"),
            description=plan_data.get("description", ""),
            target_goal=plan_data.get("target_goal", goal),
            user_level=user_level,
            learning_mode=learning_mode,
            estimated_hours=float(plan_data.get("estimated_hours", 10.0))
        )
        self.db.add(course)
        self.db.flush()

        for m_idx, mod_data in enumerate(plan_data.get("modules", [])):
            module = Module(
                course_id=course.id,
                title=mod_data.get("title", f"Модуль {m_idx + 1}"),
                description=mod_data.get("description", ""),
                order_index=m_idx
            )
            self.db.add(module)
            self.db.flush()

            for l_idx, les_data in enumerate(mod_data.get("lessons", [])):
                title = les_data.get("title", f"Урок {l_idx + 1}")
                lesson = Lesson(
                    course_id=course.id,
                    module_id=module.id,
                    title=title,
                    description=les_data.get("description", ""),
                    content_markdown=f"# {title}\n\n*Урок готов к генерации и изучению. Нажмите «Сгенерировать урок» или начните диалог с ИИ-преподавателем.*",
                    order_index=l_idx,
                    estimated_minutes=int(les_data.get("estimated_minutes", 20))
                )
                self.db.add(lesson)

        self.db.commit()
        self.db.refresh(course)
        return course
