import pytest
import os
import tempfile
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.entities import Base, Course, Module, Lesson, LearningSession, Setting
from app.core.database import set_sqlite_pragma
from sqlalchemy.engine import Engine
from sqlalchemy import event

@pytest.fixture
def test_db():
    # Create temporary database file to verify real file persistence
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    event.listen(Engine, "connect", set_sqlite_pragma)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield TestingSession, db_path, engine

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)

def test_course_creation_and_progress_calculation(test_db):
    TestingSession, db_path, engine = test_db
    db = TestingSession()

    # 1. Create a course with 1 module and 2 lessons
    course = Course(
        title="Основы C++",
        description="Курс по основам языка C++",
        target_goal="Освоить синтаксис и базовые алгоритмы",
        user_level="beginner",
        learning_mode="free"
    )
    db.add(course)
    db.commit()
    db.refresh(course)

    module = Module(course_id=course.id, title="Введение в C++", order_index=0)
    db.add(module)
    db.commit()
    db.refresh(module)

    lesson1 = Lesson(
        course_id=course.id,
        module_id=module.id,
        title="Переменные и типы данных",
        order_index=0,
        estimated_minutes=15
    )
    lesson2 = Lesson(
        course_id=course.id,
        module_id=module.id,
        title="Условные операторы if/else",
        order_index=1,
        estimated_minutes=20
    )
    db.add_all([lesson1, lesson2])
    db.commit()

    # Verify initial progress: 0/2 (0.0%)
    db.refresh(course)
    assert len(course.lessons) == 2
    completed = sum(1 for l in course.lessons if l.is_completed)
    assert completed == 0

    # 2. Complete Lesson 1
    lesson1.is_completed = True
    db.commit()

    # Verify updated progress: 1/2 (50.0%)
    db.refresh(course)
    completed = sum(1 for l in course.lessons if l.is_completed)
    assert completed == 1
    progress_pct = (completed / len(course.lessons)) * 100.0
    assert progress_pct == 50.0

    db.close()

def test_persistence_across_app_restart(test_db):
    """Verifies that closing the database connection and reopening it restores all state."""
    TestingSession, db_path, engine = test_db

    # Session 1: User works on a course
    db1 = TestingSession()
    course = Course(
        title="Linux и Bash",
        description="Администрирование Linux",
        target_goal="Научиться работать в терминале Omarchy",
        user_level="intermediate"
    )
    db1.add(course)
    db1.commit()
    db1.refresh(course)

    mod = Module(course_id=course.id, title="Файловая система", order_index=0)
    db1.add(mod)
    db1.commit()

    lesson = Lesson(
        course_id=course.id,
        module_id=mod.id,
        title="Права доступа chmod и chown",
        order_index=0,
        content_markdown="# Права доступа в Linux\nРазбор rwx...",
        is_completed=True
    )
    db1.add(lesson)
    db1.commit()
    db1.refresh(lesson)

    saved_course_id = course.id
    saved_lesson_id = lesson.id

    # Simulate app close: close session and dispose engine
    db1.close()
    engine.dispose()

    # Session 2: App starts up again, reconnects to the exact same file
    new_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    NewSession = sessionmaker(autocommit=False, autoflush=False, bind=new_engine)
    db2 = NewSession()

    restored_course = db2.query(Course).filter(Course.id == saved_course_id).first()
    assert restored_course is not None
    assert restored_course.title == "Linux и Bash"
    assert len(restored_course.lessons) == 1
    assert restored_course.lessons[0].id == saved_lesson_id
    assert restored_course.lessons[0].title == "Права доступа chmod и chown"
    assert restored_course.lessons[0].is_completed is True
    assert "# Права доступа в Linux" in restored_course.lessons[0].content_markdown

    db2.close()
    new_engine.dispose()
