from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field

# Profile
class ProfileResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    class Config:
        from_attributes = True

# Lessons
class LessonCreate(BaseModel):
    title: str
    description: Optional[str] = None
    content_markdown: Optional[str] = ""
    order_index: int = 0
    estimated_minutes: int = 20

class LessonUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content_markdown: Optional[str] = None
    order_index: Optional[int] = None
    is_completed: Optional[bool] = None
    estimated_minutes: Optional[int] = None

class LessonProgressUpdate(BaseModel):
    is_completed: bool

class LessonResponse(BaseModel):
    id: int
    module_id: int
    course_id: int
    title: str
    description: Optional[str] = None
    content_markdown: Optional[str] = ""
    order_index: int
    is_completed: bool
    last_accessed_at: Optional[datetime] = None
    estimated_minutes: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Modules
class ModuleCreate(BaseModel):
    title: str
    description: Optional[str] = None
    order_index: int = 0
    lessons: Optional[List[LessonCreate]] = []

class ModuleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    order_index: Optional[int] = None

class ModuleResponse(BaseModel):
    id: int
    course_id: int
    title: str
    description: Optional[str] = None
    order_index: int
    lessons: List[LessonResponse] = []
    created_at: datetime
    class Config:
        from_attributes = True

# Courses
class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    target_goal: Optional[str] = None
    user_level: str = "beginner" # beginner, intermediate, advanced
    learning_mode: str = "free" # free, my_materials_plus_ai, only_my_materials
    estimated_hours: float = 10.0
    modules: Optional[List[ModuleCreate]] = []

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    target_goal: Optional[str] = None
    user_level: Optional[str] = None
    learning_mode: Optional[str] = None
    is_archived: Optional[bool] = None
    estimated_hours: Optional[float] = None

class CourseSummaryResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    target_goal: Optional[str] = None
    user_level: str
    learning_mode: str
    is_archived: bool
    estimated_hours: float
    total_lessons: int = 0
    completed_lessons: int = 0
    progress_percentage: float = 0.0
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class CourseDetailResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    target_goal: Optional[str] = None
    user_level: str
    learning_mode: str
    is_archived: bool
    estimated_hours: float
    total_lessons: int = 0
    completed_lessons: int = 0
    progress_percentage: float = 0.0
    modules: List[ModuleResponse] = []
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Sessions
class SessionPingRequest(BaseModel):
    course_id: int
    lesson_id: Optional[int] = None
    seconds: int = 60 # elapsed study seconds to record

class LastActiveSessionResponse(BaseModel):
    has_active_session: bool
    course_id: Optional[int] = None
    course_title: Optional[str] = None
    lesson_id: Optional[int] = None
    lesson_title: Optional[str] = None
    last_accessed_at: Optional[datetime] = None
    welcome_message: str

# Notes
class NoteCreate(BaseModel):
    course_id: Optional[int] = None
    lesson_id: Optional[int] = None
    title: str
    content: str
    tags: Optional[str] = ""

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None

class NoteResponse(BaseModel):
    id: int
    course_id: Optional[int] = None
    lesson_id: Optional[int] = None
    title: str
    content: str
    tags: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# Dashboard
class RecentActivity(BaseModel):
    type: str # "lesson", "quiz", "course"
    title: str
    course_title: str
    timestamp: datetime

class DashboardStatsResponse(BaseModel):
    active_courses_count: int
    total_lessons_count: int
    completed_lessons_count: int
    average_progress: float
    total_study_minutes: int
    weak_skills_count: int
    due_reviews_count: int
    last_active: Optional[LastActiveSessionResponse] = None
    active_courses: List[CourseSummaryResponse] = []
    ai_recommendations: List[str] = []
    recent_notes: List[NoteResponse] = []

# Settings
class SettingsResponse(BaseModel):
    gemini_api_key_configured: bool
    gemini_model: str
    ollama_base_url: str
    ollama_model: str
    active_provider: str
    default_learning_mode: str
    database_size_bytes: int
    backup_count: int

class SettingsUpdateRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    ollama_base_url: Optional[str] = None
    ollama_model: Optional[str] = None
    active_provider: Optional[str] = None
    default_learning_mode: Optional[str] = None

# Messages / Chat
class MessageResponse(BaseModel):
    id: int
    sender: str
    content: str
    sources_used: Optional[str] = None
    is_rag_sourced: bool
    created_at: datetime
    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: int
    course_id: int
    lesson_id: Optional[int] = None
    title: str
    messages: List[MessageResponse] = []
    created_at: datetime
    class Config:
        from_attributes = True

class ChatSendRequest(BaseModel):
    course_id: int
    lesson_id: Optional[int] = None
    conversation_id: Optional[int] = None
    message: str
    learning_mode: Optional[str] = None # if None, course default is used

# Documents
class DocumentResponse(BaseModel):
    id: int
    title: str
    filename: str
    file_type: str
    file_size: int
    is_indexed: bool
    chunks_count: int = 0
    attached_courses_count: int = 0
    created_at: datetime
    class Config:
        from_attributes = True

# Skills
class SkillResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    category: str
    status: str
    confidence_level: float
    last_practiced_at: Optional[datetime] = None
    next_review_at: Optional[datetime] = None
    prerequisites: List[str] = []
    class Config:
        from_attributes = True

class SkillCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str = "Общие"
    prerequisites: Optional[List[str]] = []

class SkillProgressUpdate(BaseModel):
    status: str
    confidence_level: float

# Practice & Exercises
class ExerciseResponse(BaseModel):
    id: int
    lesson_id: int
    course_id: int
    title: str
    prompt: str
    exercise_type: str
    initial_code: Optional[str] = None
    difficulty: str
    created_at: datetime
    class Config:
        from_attributes = True

class SubmissionRequest(BaseModel):
    user_answer: str

class SubmissionResultResponse(BaseModel):
    is_correct: bool
    score: float
    feedback: str
    explanation: Optional[str] = None

# Review Schedule
class ReviewItemResponse(BaseModel):
    id: int
    item_type: str
    item_id: int
    title: str
    scheduled_date: datetime
    repetitions: int
    interval_days: int
    ease_factor: float
    is_due: bool
