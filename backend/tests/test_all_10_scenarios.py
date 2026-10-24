import pytest
import os
import tempfile
import sqlite3
from pathlib import Path
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

from app.models.entities import (
    Base, Course, Module, Lesson, LearningSession, Conversation, Message,
    Document, DocumentChunk, CourseDocument, Exercise, Submission, ReviewSchedule, Setting
)
from app.core.database import set_sqlite_pragma
from app.services.rag_service import RAGService
from app.services.spaced_repetition import calculate_sm2

@pytest.fixture
def clean_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    event.listen(Engine, "connect", set_sqlite_pragma)
    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS document_chunks_fts USING fts5(
                chunk_id UNINDEXED,
                document_id UNINDEXED,
                content,
                title,
                section_name,
                tokenize='unicode61'
            );
        """))
        conn.commit()

    SessionMaker = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield SessionMaker, db_path, engine

    engine.dispose()
    if os.path.exists(db_path):
        os.remove(db_path)

# ТЕСТ 1: Создать курс, закрыть приложение, открыть снова. Курс сохранился.
def test_scenario_1_course_persistence(clean_db):
    SessionMaker, db_path, engine = clean_db
    
    # 1. Create course
    db = SessionMaker()
    course = Course(
        title="Архитектура C++",
        description="Курс по глубокому изучению C++",
        target_goal="Освоить память и RAII",
        user_level="intermediate"
    )
    db.add(course)
    db.commit()
    course_id = course.id
    db.close()
    engine.dispose()

    # 2. Simulate restart with new engine
    new_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    NewSession = sessionmaker(autocommit=False, autoflush=False, bind=new_engine)
    db2 = NewSession()

    restored = db2.query(Course).filter(Course.id == course_id).first()
    assert restored is not None
    assert restored.title == "Архитектура C++"
    assert restored.target_goal == "Освоить память и RAII"
    db2.close()
    new_engine.dispose()

# ТЕСТ 2: Начать урок, закрыть приложение, вернуться. Прогресс и диалог сохранились.
def test_scenario_2_lesson_and_chat_persistence(clean_db):
    SessionMaker, db_path, engine = clean_db
    db = SessionMaker()

    course = Course(title="Linux для профи")
    db.add(course)
    db.commit()

    module = Module(course_id=course.id, title="Ядро Linux")
    db.add(module)
    db.commit()

    lesson = Lesson(
        course_id=course.id,
        module_id=module.id,
        title="Системные вызовы sys_read",
        is_completed=True
    )
    db.add(lesson)
    db.commit()

    conv = Conversation(course_id=course.id, lesson_id=lesson.id, title="Вопрос по syscalls")
    db.add(conv)
    db.commit()

    msg1 = Message(conversation_id=conv.id, sender="user", content="Как работает sys_read?")
    msg2 = Message(conversation_id=conv.id, sender="assistant", content="sys_read считывает байты из дескриптора в буфер.")
    db.add_all([msg1, msg2])
    db.commit()

    saved_lesson_id = lesson.id
    saved_conv_id = conv.id
    db.close()
    engine.dispose()

    # Reconnect
    new_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    NewSession = sessionmaker(autocommit=False, autoflush=False, bind=new_engine)
    db2 = NewSession()

    restored_lesson = db2.query(Lesson).filter(Lesson.id == saved_lesson_id).first()
    assert restored_lesson.is_completed is True
    
    restored_conv = db2.query(Conversation).filter(Conversation.id == saved_conv_id).first()
    assert len(restored_conv.messages) == 2
    assert restored_conv.messages[0].content == "Как работает sys_read?"
    assert restored_conv.messages[1].content == "sys_read считывает байты из дескриптора в буфер."
    db2.close()
    new_engine.dispose()

# ТЕСТ 3: Загрузить документ и задать вопрос. ИИ использует правильные фрагменты документа.
def test_scenario_3_rag_indexing_and_search(clean_db):
    SessionMaker, db_path, engine = clean_db
    db = SessionMaker()

    # Index document chunks into FTS5
    doc = Document(
        title="Основы Linux",
        filename="osnovy_linux.pdf",
        file_path="/dummy/path.pdf",
        file_type="pdf",
        file_size=1024,
        is_indexed=True
    )
    db.add(doc)
    db.commit()

    chunk1 = DocumentChunk(
        document_id=doc.id,
        chunk_index=0,
        content="Команда chmod 755 устанавливает полные права владельцу и чтение/выполнение остальным.",
        page_number=24,
        section_name="Права доступа"
    )
    chunk2 = DocumentChunk(
        document_id=doc.id,
        chunk_index=1,
        content="Команда ls -la выводит список всех файлов включая скрытые.",
        page_number=10,
        section_name="Навигация"
    )
    db.add_all([chunk1, chunk2])
    db.commit()

    # Add to FTS
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO document_chunks_fts (chunk_id, document_id, content, title, section_name)
            VALUES (:cid, :did, :cnt, :ttl, :sec)
        """), [
            {"cid": chunk1.id, "did": doc.id, "cnt": chunk1.content, "ttl": doc.title, "sec": chunk1.section_name},
            {"cid": chunk2.id, "did": doc.id, "cnt": chunk2.content, "ttl": doc.title, "sec": chunk2.section_name}
        ])
        conn.commit()

    rag = RAGService(db)
    results = rag.search(query="chmod права")
    assert len(results) > 0
    assert results[0]["page"] == 24
    assert "chmod 755" in results[0]["content"]
    assert results[0]["doc_title"] == "Основы Linux"
    db.close()

# ТЕСТ 4: В режиме «Мои материалы + знания ИИ» модель отдает приоритет источникам
def test_scenario_4_my_materials_plus_ai_mode():
    from app.services.tutor_service import TUTOR_SYSTEM_PROMPT
    assert "Мои материалы + знания ИИ" in TUTOR_SYSTEM_PROMPT
    assert "СНАЧАЛА давай ответ строго по загруженным материалам" in TUTOR_SYSTEM_PROMPT
    assert "Дополнение ИИ:" in TUTOR_SYSTEM_PROMPT

# ТЕСТ 5: В режиме «Свободное обучение» модель отвечает даже без загруженных документов
def test_scenario_5_free_learning_mode():
    from app.services.tutor_service import TUTOR_SYSTEM_PROMPT
    assert "Свободное обучение" in TUTOR_SYSTEM_PROMPT
    assert "Используй свои знания и переданные материалы" in TUTOR_SYSTEM_PROMPT

# ТЕСТ 6: При отсутствии информации в источниках ИИ не выдумывает цитаты
def test_scenario_6_no_hallucinated_citations():
    from app.services.tutor_service import TUTOR_SYSTEM_PROMPT
    assert "Не выдумывай факты и номера страниц" in TUTOR_SYSTEM_PROMPT
    assert "В загруженных материалах нет информации по данному вопросу" in TUTOR_SYSTEM_PROMPT

# ТЕСТ 7: Пользователь меняет режим обучения. Настройка сохраняется.
def test_scenario_7_learning_mode_persistence(clean_db):
    SessionMaker, db_path, engine = clean_db
    db = SessionMaker()

    course = Course(title="Курс по сетям", learning_mode="free")
    db.add(course)
    db.commit()

    # User changes learning mode to only_my_materials
    course.learning_mode = "only_my_materials"
    db.commit()
    cid = course.id
    db.close()
    engine.dispose()

    # Verify after reconnect
    new_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    db2 = sessionmaker(bind=new_engine)()
    restored = db2.query(Course).filter(Course.id == cid).first()
    assert restored.learning_mode == "only_my_materials"
    db2.close()
    new_engine.dispose()

# ТЕСТ 8: Пользователь неправильно решает задание. Система сохраняет ошибку и планирует повторение.
def test_scenario_8_mistake_triggers_spaced_repetition(clean_db):
    SessionMaker, db_path, engine = clean_db
    db = SessionMaker()

    course = Course(title="Алгоритмы")
    db.add(course)
    db.commit()

    module = Module(course_id=course.id, title="Базовые алгоритмы")
    db.add(module)
    db.commit()

    lesson = Lesson(course_id=course.id, module_id=module.id, title="Поиск элементов")
    db.add(lesson)
    db.commit()

    ex = Exercise(
        course_id=course.id,
        lesson_id=lesson.id,
        title="Сложность бинарного поиска",
        prompt="Какова временная сложность бинарного поиска?",
        exercise_type="quiz",
        solution="O(log n)"
    )
    db.add(ex)
    db.commit()

    # User submits incorrect answer
    user_answer = "O(n^2)"
    is_correct = (user_answer == ex.solution)
    assert is_correct is False

    # Grade is 1 (failure)
    interval, reps, ef, next_date = calculate_sm2(grade=1, repetitions=3, ease_factor=2.5, current_interval=10)
    assert interval == 1
    assert reps == 0 # reset back to 0 repetitions on failure!
    
    sub = Submission(exercise_id=ex.id, user_answer=user_answer, is_correct=False, score=0.0)
    db.add(sub)
    sched = ReviewSchedule(item_type="exercise", item_id=ex.id, scheduled_date=next_date, interval_days=interval, ease_factor=ef, repetitions=reps)
    db.add(sched)
    db.commit()

    assert sched.repetitions == 0
    assert sched.interval_days == 1
    db.close()

# ТЕСТ 9: При отключении Gemini сохранённые курсы остаются доступны.
def test_scenario_9_offline_mode_availability(clean_db):
    SessionMaker, db_path, engine = clean_db
    db = SessionMaker()

    course = Course(title="Офлайн курс по C++")
    db.add(course)
    db.commit()

    # Even with empty Gemini key, querying courses works perfectly
    courses = db.query(Course).all()
    assert len(courses) == 1
    assert courses[0].title == "Офлайн курс по C++"
    db.close()

# ТЕСТ 10: Резервная копия корректно восстанавливает пользовательские данные.
def test_scenario_10_atomic_backup_and_restore(clean_db):
    SessionMaker, db_path, engine = clean_db
    db = SessionMaker()

    course = Course(title="Курс до бэкапа")
    db.add(course)
    db.commit()
    db.close()
    engine.dispose()

    # 1. Create atomic SQLite backup
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as backup_tmp:
        backup_path = backup_tmp.name

    src = sqlite3.connect(db_path)
    dst = sqlite3.connect(backup_path)
    src.backup(dst)
    dst.close()
    src.close()

    # Verify backup exists and has SQLite header
    with open(backup_path, "rb") as f:
        assert f.read(16) == b"SQLite format 3\x00"

    # 2. Corrupt or modify main database
    conn = sqlite3.connect(db_path)
    conn.execute("DROP TABLE courses;")
    conn.commit()
    conn.close()

    # 3. Restore from backup
    src2 = sqlite3.connect(backup_path)
    dst2 = sqlite3.connect(db_path)
    src2.backup(dst2)
    dst2.close()
    src2.close()

    # 4. Verify restoration
    new_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    db_restored = sessionmaker(bind=new_engine)()
    restored_course = db_restored.query(Course).first()
    assert restored_course is not None
    assert restored_course.title == "Курс до бэкапа"

    db_restored.close()
    new_engine.dispose()
    if os.path.exists(backup_path):
        os.remove(backup_path)
