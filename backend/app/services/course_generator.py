import logging
import uuid
import datetime
from pathlib import Path
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.services.ai_provider import AIProvider, AIServiceError
from app.services.material_finder import find_learning_materials
from app.services.rag_service import RAGService
from app.models.entities import Course, Module, Lesson, Document, CourseDocument, LearningSession
from app.core.config import settings

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

def detect_domain(topic: str) -> str:
    t = topic.lower()
    tech_keywords = [
        "python", "javascript", "js", "typescript", "ts", "c++", "cpp", "c#", "java", "go", "golang",
        "rust", "php", "ruby", "swift", "kotlin", "html", "css", "react", "vue", "angular", "node",
        "sql", "postgres", "mysql", "docker", "kubernetes", "linux", "git", "bash", "django", "fastapi",
        "программирован", "алгоритм", "веб-разработк", "devops", "backend", "frontend", "код", "игры"
    ]
    history_keywords = [
        "истори", "рим", "греци", "войн", "импери", "век", "эпох", "революци", "союз", "царь", "философи", "литератур", "археолог"
    ]
    science_keywords = [
        "физик", "математик", "хими", "биолог", "астрономи", "анатоми", "медицин", "квантов", "геометри", "алгебр", "генетик"
    ]
    business_keywords = [
        "бизнес", "маркетинг", "экономик", "финанс", "инвестиц", "стартап", "продаж", "менеджмент", "бухгалтер", "криптовалют"
    ]
    language_keywords = [
        "английск", "немецк", "испанск", "французск", "китайск", "итальянск", "японск", "корейск", "язык", "грамматик", "словарь"
    ]

    for k in tech_keywords:
        if k in t:
            return "tech"
    for k in history_keywords:
        if k in t:
            return "history"
    for k in science_keywords:
        if k in t:
            return "science"
    for k in business_keywords:
        if k in t:
            return "business"
    for k in language_keywords:
        if k in t:
            return "language"
    return "general"

def generate_domain_tailored_course_plan(goal: str, user_level: str, mat_title: str) -> Dict[str, Any]:
    """Generates an authentic syllabus tailored specifically to the requested subject."""
    topic = mat_title or goal.strip()
    domain = detect_domain(goal + " " + topic)

    if domain == "tech":
        return {
            "title": f"Курс: {topic}",
            "description": f"Комплексный практический курс по теме «{topic}» для уровня {user_level}. Включает синтаксис, архитектуру, инструменты и реальный проект.",
            "target_goal": goal,
            "estimated_hours": 14.0,
            "modules": [
                {
                    "title": f"Модуль 1. Введение и базовый инструментарий {topic}",
                    "description": f"Знакомство с концепциями, средой разработки и первым кодом на {topic}.",
                    "lessons": [
                        {"title": f"Введение в {topic}: архитектура и ключевые понятия", "description": "Назначение технологии, обзор экосистемы и принципы работы.", "estimated_minutes": 20},
                        {"title": f"Настройка рабочего окружения и первый скрипт", "description": "Установка компиляторов, интерпретаторов и запуск первой программы.", "estimated_minutes": 25},
                        {"title": "Переменные, базовые типы данных и операторы", "description": "Работа с памятью, литералами, вычислениями и преобразованием типов.", "estimated_minutes": 20}
                    ]
                },
                {
                    "title": f"Модуль 2. Логика, функции и структуры данных в {topic}",
                    "description": "Построение алгоритмов, управление потоком выполнения и декомпозиция кода.",
                    "lessons": [
                        {"title": "Управляющие конструкции: условия и циклы", "description": "Ветвление логики, итерации, обработка коллекций.", "estimated_minutes": 25},
                        {"title": "Функции, параметры и организация чистой архитектуры", "description": "Декомпозиция задач, область видимости и модули.", "estimated_minutes": 25},
                        {"title": "Работа с ключевыми структурами данных", "description": "Списки, массивы, словари/карты и быстрый поиск.", "estimated_minutes": 30}
                    ]
                },
                {
                    "title": f"Модуль 3. Продвинутые техники и практический проект",
                    "description": "Обработка ошибок, оптимизация и создание завершенного решения.",
                    "lessons": [
                        {"title": "Обработка ошибок, исключения и надежность", "description": "Анализ граничных случаев, отладка и логирование.", "estimated_minutes": 25},
                        {"title": f"Итоговый практический проект по теме «{topic}»", "description": "Реализация комплексного проекта для закрепления всех навыков.", "estimated_minutes": 45}
                    ]
                }
            ]
        }
    elif domain == "history":
        return {
            "title": f"Курс: {topic}",
            "description": f"Увлекательное историческое исследование темы «{topic}»: предпосылки, ключевые эпохи, события и уроки для современности.",
            "target_goal": goal,
            "estimated_hours": 12.0,
            "modules": [
                {
                    "title": f"Модуль 1. Истоки, предпосылки и рождение эпохи",
                    "description": f"Анализ предпосылок, географического и социально-экономического контекста темы «{topic}».",
                    "lessons": [
                        {"title": f"Введение в {topic}: периодизация и контекст", "description": "Временные рамки, ключевые источники и историческое окружение.", "estimated_minutes": 20},
                        {"title": "Общественный строй, культура и материальная база", "description": "Как жили люди, религиозные и культурные представления.", "estimated_minutes": 20},
                        {"title": "Ключевые исторические свидетельства и документы", "description": "Анализ артефактов, хроник и трудов историков.", "estimated_minutes": 25}
                    ]
                },
                {
                    "title": f"Модуль 2. Главные события, конфликты и поворотные моменты",
                    "description": "Погружение в решающие события, масштабные битвы, реформы и судьбы лидеров.",
                    "lessons": [
                        {"title": "Золотой век и определяющие завоевания / преобразования", "description": "Пик влияния, институциональные реформы и победы.", "estimated_minutes": 25},
                        {"title": "Ключевые личности и их влияние на ход событий", "description": "Анализ решений правителей, полководцев и мыслителей.", "estimated_minutes": 25},
                        {"title": "Кризисы, внутренние конфликты и трансформация", "description": "Причины кризисов, переломы и эволюция общества.", "estimated_minutes": 30}
                    ]
                },
                {
                    "title": f"Модуль 3. Наследие {topic} и исторические выводы",
                    "description": "Влияние на мировую цивилизацию, культуру, право и наше время.",
                    "lessons": [
                        {"title": "Вклад в мировую культуру, государственность и право", "description": "Что современный мир унаследовал из этой эпохи.", "estimated_minutes": 25},
                        {"title": "Итоговый исторический разбор и выводы", "description": "Обобщение пройденного материала и ответы на главные вопросы.", "estimated_minutes": 30}
                    ]
                }
            ]
        }
    elif domain == "science":
        return {
            "title": f"Курс: {topic}",
            "description": f"Глубокий научно-образовательный курс по направлению «{topic}»: фундаментальные законы, формулы, модели и практическое применение.",
            "target_goal": goal,
            "estimated_hours": 15.0,
            "modules": [
                {
                    "title": f"Модуль 1. Фундаментальные понятия и законы {topic}",
                    "description": "Определение предмета исследования, базовые аксиомы и понятийный аппарат.",
                    "lessons": [
                        {"title": f"Введение в {topic}: предмет и основные постулаты", "description": "Ключевая терминология, физический/биологический смысл явлений.", "estimated_minutes": 20},
                        {"title": "Базовые законы, уравнения и принципы сохранения", "description": "Математическое и концептуальное описание процессов.", "estimated_minutes": 25},
                        {"title": "Методы измерений, наблюдений и лабораторный инструментарий", "description": "Как ученые получают данные и проверяют теории.", "estimated_minutes": 25}
                    ]
                },
                {
                    "title": f"Модуль 2. Моделирование процессов и решение задач",
                    "description": "Прикладные задачи, системный анализ и разбор конкретных физических явлений.",
                    "lessons": [
                        {"title": "Системные взаимодействия и анализ состояний", "description": "Поведение систем в различных условиях и граничные режимы.", "estimated_minutes": 25},
                        {"title": "Типовые расчетные задачи и пошаговый алгоритм решения", "description": "Практика решения прикладных научных задач.", "estimated_minutes": 30},
                        {"title": "Анализ ошибок, погрешности и экспериментальные данные", "description": "Интерпретация результатов и статистическая оценка.", "estimated_minutes": 25}
                    ]
                },
                {
                    "title": f"Модуль 3. Современное состояние и прикладные открытия",
                    "description": "Передовые технологии, открытые вопросы и практический проект.",
                    "lessons": [
                        {"title": "Современные прорывы и инновационные применения", "description": "Где и как сегодня используются эти научные открытия.", "estimated_minutes": 25},
                        {"title": "Итоговая практическая работа и защита гипотезы", "description": "Самостоятельное исследование или разбор сложной задачи.", "estimated_minutes": 40}
                    ]
                }
            ]
        }
    elif domain == "business":
        return {
            "title": f"Курс: {topic}",
            "description": f"Практический бизнес-курс по теме «{topic}»: инструменты, метрики, стратегия и реальные кейсы.",
            "target_goal": goal,
            "estimated_hours": 12.0,
            "modules": [
                {
                    "title": f"Модуль 1. Основы, экономика и принципы {topic}",
                    "description": "Понятийный аппарат, рыночные механизмы и определение ценности.",
                    "lessons": [
                        {"title": f"Введение в {topic}: законы рынка и базовые принципы", "description": "Ключевые термины, цели бизнеса и понимание целевой аудитории.", "estimated_minutes": 20},
                        {"title": "Анализ конкурентной среды и позиционирование", "description": "Поиск уникального преимущества и сегментация рынка.", "estimated_minutes": 25},
                        {"title": "Финансовая модель, юнит-экономика и метрики", "description": "Расчет прибыльности, CAC, LTV, ROI и точки безубыточности.", "estimated_minutes": 25}
                    ]
                },
                {
                    "title": f"Модуль 2. Стратегия, операции и масштабирование",
                    "description": "Пошаговая реализация, каналы привлечения и управление рисками.",
                    "lessons": [
                        {"title": "Каналы продвижения, продажи и конверсия", "description": "Построение воронки продаж и оптимизация ключевых этапов.", "estimated_minutes": 25},
                        {"title": "Управление операционными процессами и командами", "description": "Регламенты, мотивация и автоматизация рутины.", "estimated_minutes": 25},
                        {"title": "Управление рисками и стресс-тестирование бизнес-модели", "description": "Защита бизнеса от внешних и внутренних кризисов.", "estimated_minutes": 25}
                    ]
                },
                {
                    "title": f"Модуль 3. Практические кейсы и разработка плана",
                    "description": "Разбор успешных компаний и создание собственного плана.",
                    "lessons": [
                        {"title": "Разбор кейсов мировых лидеров отрасли", "description": "Уроки побед и фатальные ошибки крупных игроков.", "estimated_minutes": 30},
                        {"title": "Финальный проект: Запуск и защита бизнес-стратегии", "description": "Оформление готового пошагового плана к реализации.", "estimated_minutes": 45}
                    ]
                }
            ]
        }
    elif domain == "language":
        return {
            "title": f"Курс: {topic}",
            "description": f"Интенсивный курс освоения темы «{topic}»: произношение, базовая грамматика, лексика и живая речь.",
            "target_goal": goal,
            "estimated_hours": 15.0,
            "modules": [
                {
                    "title": "Модуль 1. Фонетика, чтение и базовые фразы",
                    "description": "Постановка правильного звукоизвлечения, правила чтения и базовые диалоги.",
                    "lessons": [
                        {"title": "Алфавит, правила чтения и базовые звуки", "description": "Постановка произношения и устранение акцента.", "estimated_minutes": 20},
                        {"title": "Приветствия, этикет и знакомство", "description": "Первые уверенные фразы в разговоре.", "estimated_minutes": 20},
                        {"title": "Базовая структура предложения и глагол-связка", "description": "Как строить правильные утверждения без ошибок.", "estimated_minutes": 25}
                    ]
                },
                {
                    "title": "Модуль 2. Основная грамматика и активный словарный запас",
                    "description": "Построение вопросов, отрицаний и овладение самыми частыми 500 словами.",
                    "lessons": [
                        {"title": "Настоящее время и ключевые глаголы действия", "description": "Описываем распорядок дня, привычки и факты.", "estimated_minutes": 25},
                        {"title": "Вопросы, отрицания и предлоги места/времени", "description": "Учимся спрашивать дорогу, время и выражать сомнение.", "estimated_minutes": 25},
                        {"title": "Разговорные темы: город, покупки, работа и семья", "description": "Живая речь в стандартных бытовых ситуациях.", "estimated_minutes": 30}
                    ]
                },
                {
                    "title": "Модуль 3. Расширенная речь и преодоление языкового барьера",
                    "description": "Прошедшее время, свободный диалог и закрепление навыков.",
                    "lessons": [
                        {"title": "Прошедшее время: рассказываем истории из жизни", "description": "Связка предложений, союзы и нарратив.", "estimated_minutes": 25},
                        {"title": "Финальный разговорный практикум и тест", "description": "Комплексная проверка всех навыков и диалог с ИИ.", "estimated_minutes": 35}
                    ]
                }
            ]
        }
    else:
        return {
            "title": f"Курс: {topic}",
            "description": f"Подробная структурированная программа обучения по теме «{topic}» для уровня {user_level}.",
            "target_goal": goal,
            "estimated_hours": 12.0,
            "modules": [
                {
                    "title": f"Модуль 1. Введение и основы {topic}",
                    "description": f"Погружение в тему «{topic}», ключевая терминология и базовые концепции.",
                    "lessons": [
                        {"title": f"Введение в {topic}: ключевые понятия и контекст", "description": "Зачем изучать эту тему и какие возможности она открывает.", "estimated_minutes": 20},
                        {"title": "Фундаментальные принципы и базовый инструментарий", "description": "Основные элементы и правила работы с предметом.", "estimated_minutes": 20},
                        {"title": "Первая практика: базовые упражнения и примеры", "description": "Закрепление фундаментальных основ на практических примерах.", "estimated_minutes": 25}
                    ]
                },
                {
                    "title": f"Модуль 2. Углубление в технику и практическое применение",
                    "description": "Методология, тонкости, разбор типовых ошибок и практические сценарии.",
                    "lessons": [
                        {"title": "Основные методики и эффективные приемы", "description": "Проверенные стратегии и лучшие практики мастеров.", "estimated_minutes": 25},
                        {"title": "Типичные ошибки начинающих и как их избежать", "description": "Анализ частых сбоев, заблуждений и пути их устранения.", "estimated_minutes": 25},
                        {"title": "Разбор практических кейсов и ситуаций", "description": "Решение реальных ситуационных задач.", "estimated_minutes": 30}
                    ]
                },
                {
                    "title": f"Модуль 3. Мастерство и итоговый проект",
                    "description": "Продвинутый уровень, самостоятельная работа и защита результатов.",
                    "lessons": [
                        {"title": "Продвинутые лайфхаки и советы профессионалов", "description": "Тонкие нюансы для достижения наивысшего результата.", "estimated_minutes": 25},
                        {"title": f"Итоговый практический проект по теме «{topic}»", "description": "Создание собственного проекта и комплексное закрепление материала.", "estimated_minutes": 45}
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
        target_timeframe: str = "в комфортном темпе",
        user_id: str = "default_user"
    ) -> Course:
        # 1. Search authoritative educational materials for the requested goal/topic
        materials = find_learning_materials(goal)
        mat_title = materials.get("title", goal.strip())
        mat_extract = materials.get("extract", "")
        mat_url = materials.get("source_url", "")

        prompt = f"""
Составь подробную учебную дорожную карту по следующему запросу пользователя:
Запрос: "{goal}"
Тематическая энциклопедия/материал: "{mat_title}"
Краткие вводные данные: {mat_extract[:1500]}
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
            logger.info(f"AI structured generation not available or failed: {e}. Generating specialized domain syllabus.")
            plan_data = generate_domain_tailored_course_plan(goal, user_level, mat_title)

        # 2. Create Course in DB
        course = Course(
            user_id=user_id,
            title=plan_data.get("title", f"Курс: {mat_title}"),
            description=plan_data.get("description", f"Учебный курс по теме «{mat_title}»"),
            target_goal=plan_data.get("target_goal", goal),
            user_level=user_level,
            learning_mode=learning_mode,
            estimated_hours=float(plan_data.get("estimated_hours", 12.0))
        )
        self.db.add(course)
        self.db.flush()

        # 3. Save found materials as an authoritative Document in the user's Library and attach to course
        if mat_extract and len(mat_extract.strip()) > 50:
            doc_uuid = uuid.uuid4().hex[:8]
            safe_filename = f"materials_{doc_uuid}.txt"
            doc_path = settings.UPLOADS_PATH / safe_filename
            with open(doc_path, "w", encoding="utf-8") as f:
                header = f"# Учебные материалы: {mat_title}\n\nИсточник: {mat_url or 'Second Brain Knowledge Base'}\nЦель обучения: {goal}\n\n"
                f.write(header + mat_extract)

            doc = Document(
                user_id=user_id,
                title=f"Материалы: {mat_title}",
                filename=safe_filename,
                file_path=str(doc_path.resolve()),
                file_type="txt",
                file_size=doc_path.stat().st_size,
                is_indexed=False
            )
            self.db.add(doc)
            self.db.flush()

            # Attach to course
            course_doc = CourseDocument(course_id=course.id, document_id=doc.id)
            self.db.add(course_doc)
            self.db.flush()

            # Index document with RAG
            try:
                rag_svc = RAGService(self.db)
                rag_svc.index_document(doc.id)
            except Exception as ex:
                logger.warning(f"RAG indexing during course creation warning: {ex}")

        # 4. Create Modules and Lessons
        first_lesson: Optional[Lesson] = None
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
                    content_markdown="",  # will be generated
                    order_index=l_idx,
                    estimated_minutes=int(les_data.get("estimated_minutes", 20))
                )
                self.db.add(lesson)
                self.db.flush()
                if first_lesson is None:
                    first_lesson = lesson

        # 5. Automatically generate rich content for the First Lesson and start learning session immediately!
        if first_lesson:
            from app.services.lesson_generator import LessonGeneratorService
            lesson_svc = LessonGeneratorService(self.db)
            sources = []
            if mat_extract:
                sources.append({
                    "doc_title": f"Материалы: {mat_title}",
                    "content": mat_extract[:2500],
                    "page": 1,
                    "section": "Введение"
                })
            
            try:
                await lesson_svc.generate_lesson_content(first_lesson.id, context_sources=sources)
            except Exception as e:
                logger.warning(f"Could not generate initial lesson content with AI: {e}")
                # Fallback to rich content with material
                intro_content = f"""# {first_lesson.title}

> Курс: **{course.title}** • Учебный материал: **{mat_title}**

## Введение и Цель урока
Добро пожаловать в первый урок вашего персонализированного курса! 
Цель этого занятия — освоить фундаментальные основы по теме «{mat_title}», понять ключевые концепции и подготовиться к решению практических задач.

## Теоретическая часть (Учебные материалы)
{mat_extract[:3000]}

## Ключевые выводы
- Изучение темы «{mat_title}» строится на последовательном переходе от базовых понятий к практике.
- Для успешного закрепления рекомендуется конспектировать основные термины и выполнять упражнения.

## Практическое задание для самопроверки
1. Объясните своими словами главную идею темы «{mat_title}».
2. Каковы основные сферы применения и ключевые инструменты в этой области?
3. Откройте чат с ИИ-преподавателем справа, чтобы задать уточняющие вопросы по прочитанному материалу.
"""
                first_lesson.content_markdown = intro_content

            first_lesson.last_accessed_at = datetime.datetime.now(datetime.timezone.utc)
            
            # Start active learning session
            session_rec = LearningSession(
                user_id=user_id,
                course_id=course.id,
                lesson_id=first_lesson.id,
                duration_seconds=0
            )
            self.db.add(session_rec)

        self.db.commit()
        self.db.refresh(course)
        return course
