import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
)
from sqlalchemy.orm import relationship
from app.core.database import Base

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, default="Пользователь")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), index=True, default="default_user", nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_goal = Column(Text, nullable=True)
    user_level = Column(String(50), default="beginner") # beginner, intermediate, advanced
    learning_mode = Column(String(50), default="free") # free, my_materials_plus_ai, only_my_materials
    is_archived = Column(Boolean, default=False)
    estimated_hours = Column(Float, default=10.0)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan", order_by="Module.order_index")
    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")
    sessions = relationship("LearningSession", back_populates="course", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="course", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="course", cascade="all, delete-orphan")
    course_documents = relationship("CourseDocument", back_populates="course", cascade="all, delete-orphan")

class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    course = relationship("Course", back_populates="modules")
    lessons = relationship("Lesson", back_populates="module", cascade="all, delete-orphan", order_by="Lesson.order_index")

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    module_id = Column(Integer, ForeignKey("modules.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content_markdown = Column(Text, nullable=True, default="")
    presentation_json = Column(Text, nullable=True, default="[]")
    quiz_json = Column(Text, nullable=True, default="[]")
    order_index = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    status = Column(String(50), default="not_started") # not_started, in_progress, viewed, practice_completed, mastered
    last_accessed_at = Column(DateTime, nullable=True)
    estimated_minutes = Column(Integer, default=20)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    module = relationship("Module", back_populates="lessons")
    course = relationship("Course", back_populates="lessons")
    exercises = relationship("Exercise", back_populates="lesson", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="lesson", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="lesson", cascade="all, delete-orphan")

class LearningSession(Base):
    __tablename__ = "learning_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), index=True, default="default_user", nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True)
    started_at = Column(DateTime, default=utcnow)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    course = relationship("Course", back_populates="sessions")
    lesson = relationship("Lesson")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), default="Беседа с ИИ-преподавателем")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    course = relationship("Course", back_populates="conversations")
    lesson = relationship("Lesson", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    sender = Column(String(20), nullable=False) # user, assistant, system
    content = Column(Text, nullable=False)
    sources_used = Column(Text, nullable=True) # JSON array of citations
    is_rag_sourced = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), index=True, default="default_user", nullable=False)
    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False) # pdf, docx, txt, md, cpp, py, sh, png, jpg, web
    file_size = Column(Integer, default=0) # in bytes
    is_indexed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    course_documents = relationship("CourseDocument", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    section_name = Column(String(255), nullable=True)
    char_start = Column(Integer, nullable=True)
    char_end = Column(Integer, nullable=True)
    embedding_json = Column(Text, nullable=True) # Vector stored as JSON list of floats
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    document = relationship("Document", back_populates="chunks")

class CourseDocument(Base):
    __tablename__ = "course_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    attached_at = Column(DateTime, default=utcnow)

    # Relationships
    course = relationship("Course", back_populates="course_documents")
    document = relationship("Document", back_populates="course_documents")

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), index=True, default="default_user", nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(String(255), default="")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    course = relationship("Course", back_populates="notes")
    lesson = relationship("Lesson", back_populates="notes")

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    module_id = Column(Integer, ForeignKey("modules.id", ondelete="SET NULL"), nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    prompt = Column(Text, nullable=False)
    exercise_type = Column(String(50), default="quiz") # quiz, code, open_question
    initial_code = Column(Text, nullable=True)
    solution = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    difficulty = Column(String(20), default="medium") # easy, medium, hard
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    lesson = relationship("Lesson", back_populates="exercises")
    submissions = relationship("Submission", back_populates="exercise", cascade="all, delete-orphan")

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False)
    user_answer = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    score = Column(Float, default=0.0)
    feedback = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=utcnow)

    # Relationships
    exercise = relationship("Exercise", back_populates="submissions")

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    score = Column(Float, default=0.0)
    total_questions = Column(Integer, default=0)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), default="Общие")
    prerequisites_json = Column(Text, default="[]")
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    progress = relationship("SkillProgress", back_populates="skill", uselist=False, cascade="all, delete-orphan")

class SkillProgress(Base):
    __tablename__ = "skill_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), unique=True, nullable=False)
    status = Column(String(50), default="not_started") # not_started, learning, needs_practice, mastered, needs_review
    confidence_level = Column(Float, default=0.0) # 0.0 to 100.0%
    last_practiced_at = Column(DateTime, nullable=True)
    next_review_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    skill = relationship("Skill", back_populates="progress")

class SkillRelationship(Base):
    __tablename__ = "skill_relationships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    target_skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    relation_type = Column(String(50), default="depends_on") # depends_on, relates_to

class ReviewSchedule(Base):
    __tablename__ = "review_schedule"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_type = Column(String(50), nullable=False) # skill, lesson, exercise
    item_id = Column(Integer, nullable=False)
    scheduled_date = Column(DateTime, nullable=False)
    interval_days = Column(Integer, default=1)
    ease_factor = Column(Float, default=2.5)
    repetitions = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

class AIUsage(Base):
    __tablename__ = "ai_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(50), nullable=False) # gemini, ollama
    model = Column(String(100), nullable=False)
    tokens_in = Column(Integer, default=0)
    tokens_out = Column(Integer, default=0)
    cost_estimate = Column(Float, default=0.0)
    request_type = Column(String(50), default="chat") # chat, course_gen, lesson_gen, rag
    created_at = Column(DateTime, default=utcnow)

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), index=True, default="default_user", nullable=False)
    title = Column(String(255), default="Новый диалог")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    sender = Column(String(20), nullable=False) # user, assistant, system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")
