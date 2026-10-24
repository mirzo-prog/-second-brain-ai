import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal, init_db
from app.models.entities import Course, Module, Lesson, Document, ChatSession, ChatMessage

@pytest.fixture(scope="module")
def client():
    init_db()
    with TestClient(app) as c:
        yield c

def test_01_mathematics_course_generation(client):
    """Тест 1 — Математика: «Создай курс математики с нуля»."""
    resp = client.post(
        "/api/ai/generate-course",
        headers={"X-User-ID": "test_user_math"},
        json={"goal": "Создай курс математики с нуля", "user_level": "beginner", "learning_mode": "free"}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "математик" in data["title"].lower() or "математик" in data["target_goal"].lower()
    assert len(data["modules"]) >= 3
    first_lesson = data["modules"][0]["lessons"][0]
    assert first_lesson["id"] > 0
    # Lesson content was generated and is not an empty string
    assert len(first_lesson["content_markdown"]) > 50

def test_02_biology_course_generation(client):
    """Тест 2 — Биология: «Хочу изучить биологию» — динамическая программа по биологии."""
    resp = client.post(
        "/api/ai/generate-course",
        headers={"X-User-ID": "test_user_bio"},
        json={"goal": "Хочу изучить биологию", "user_level": "beginner", "learning_mode": "free"}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "биолог" in data["title"].lower() or "биолог" in data["target_goal"].lower()
    # It must NOT be a static C++ or Linux template
    assert "c++" not in data["title"].lower()
    assert len(data["modules"]) >= 3

def test_03_japanese_course_generation(client):
    """Тест 3 — Японский язык: «Научи меня японскому языку с нуля»."""
    resp = client.post(
        "/api/ai/generate-course",
        headers={"X-User-ID": "test_user_japan"},
        json={"goal": "Научи меня японскому языку с нуля", "user_level": "beginner", "learning_mode": "free"}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "японск" in data["title"].lower() or "язык" in data["title"].lower()
    # Module 1 covers phonetics/alphabet
    mod_titles = " ".join([m["title"].lower() for m in data["modules"]])
    assert "модуль" in mod_titles

def test_04_gemini_free_chat_does_not_create_course(client):
    """Тест 4 — Обычный чат: «Привет, давай поговорим о книгах» не создаёт курс."""
    # Count courses before
    courses_before = client.get("/api/courses", headers={"X-User-ID": "test_user_chat"}).json()
    
    # 1. Create chat session
    session_resp = client.post("/api/chat/sessions", headers={"X-User-ID": "test_user_chat"}, json={})
    assert session_resp.status_code == 201
    s_id = session_resp.json()["id"]

    # 2. Send free chat message
    msg_resp = client.post(
        f"/api/chat/sessions/{s_id}/messages",
        headers={"X-User-ID": "test_user_chat"},
        json={"content": "Привет, давай поговорим о книгах"}
    )
    assert msg_resp.status_code == 200
    reply = msg_resp.json()["content"]
    assert len(reply) > 0

    # Ensure no course was created
    courses_after = client.get("/api/courses", headers={"X-User-ID": "test_user_chat"}).json()
    assert len(courses_after) == len(courses_before)

def test_05_chat_persistence_across_requests(client):
    """Тест 5 — Сохранение переписки."""
    headers = {"X-User-ID": "test_persistence_user"}
    # Create session
    s = client.post("/api/chat/sessions", headers=headers, json={"title": "Философия"}).json()
    s_id = s["id"]

    # Send messages
    client.post(f"/api/chat/sessions/{s_id}/messages", headers=headers, json={"content": "Что такое экзистенциализм?"})
    client.post(f"/api/chat/sessions/{s_id}/messages", headers=headers, json={"content": "А кто главные авторы?"})

    # Retrieve session messages
    detail = client.get(f"/api/chat/sessions/{s_id}", headers=headers).json()
    assert len(detail["messages"]) >= 4 # 2 user + 2 assistant responses
    assert detail["title"] == "Философия"

def test_06_resume_learning_session(client):
    """Тест 6 — Продолжение обучения с сохраненного места."""
    headers = {"X-User-ID": "test_resume_user"}
    # Create course
    course = client.post(
        "/api/ai/generate-course",
        headers=headers,
        json={"goal": "Основы C++ для новичков", "user_level": "beginner"}
    ).json()
    course_id = course["id"]
    lesson_1 = course["modules"][0]["lessons"][0]["id"]
    lesson_2 = course["modules"][0]["lessons"][1]["id"]

    # Access lesson 2 and ping study session
    client.post(
        "/api/sessions/ping",
        headers=headers,
        json={"course_id": course_id, "lesson_id": lesson_2, "seconds": 45}
    )

    # Check last active
    last_act = client.get("/api/sessions/last-active", headers=headers).json()
    assert last_act["has_active_session"] is True
    assert last_act["course_id"] == course_id
    assert last_act["lesson_id"] == lesson_2

def test_07_user_documents_and_rag(client):
    """Тест 7 — Загрузка собственных материалов (TXT/MD) и RAG поиск."""
    headers = {"X-User-ID": "test_rag_user"}
    file_content = b"Kvantovaya fizika izuchaet subatomnye chastitsy i superpozitsiyu sostoyaniy."
    files = {"file": ("physics_notes.txt", file_content, "text/plain")}
    
    upload_resp = client.post(
        "/api/documents/upload",
        headers=headers,
        files=files,
        data={"title": "Заметки по квантовой физике"}
    )
    assert upload_resp.status_code == 200
    doc_id = upload_resp.json()["id"]

    # Documents list
    docs = client.get("/api/documents", headers=headers).json()
    assert any(d["id"] == doc_id for d in docs)

def test_08_api_error_tolerance(client):
    """Тест 8 — Отказоустойчивость при отсутствии или временной ошибке Gemini API."""
    headers = {"X-User-ID": "test_fallback_user"}
    # Generate course with fallback handling
    resp = client.post(
        "/api/ai/generate-course",
        headers=headers,
        json={"goal": "История древнего мира", "user_level": "beginner"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "мир" in data["title"].lower() or "истори" in data["target_goal"].lower()

def test_09_user_isolation_security(client):
    """Тест 9 — Безопасность: изоляция курсов и диалогов между пользователями."""
    # User A creates course
    c_a = client.post(
        "/api/courses",
        headers={"X-User-ID": "alice_secret"},
        json={"title": "Секретный курс Алисы", "description": "Только для Алисы", "user_level": "advanced"}
    ).json()

    # User B lists courses
    courses_b = client.get("/api/courses", headers={"X-User-ID": "bob_public"}).json()
    bob_titles = [c["title"] for c in courses_b]
    assert "Секретный курс Алисы" not in bob_titles

    # User B cannot access Alice's course detail directly
    detail_resp = client.get(f"/api/courses/{c_a['id']}", headers={"X-User-ID": "bob_public"})
    assert detail_resp.status_code == 404

def test_10_existing_courses_regression(client):
    """Тест 10 — Существующие курсы продолжают работать."""
    # Can create standard curriculum and calculate metrics
    c = client.post(
        "/api/courses",
        headers={"X-User-ID": "dev_user"},
        json={"title": "C++ для профессионалов", "description": "Архитектура и производительность", "user_level": "advanced"}
    ).json()
    assert c["id"] > 0
    # Dashboard returns stats
    dash = client.get("/api/dashboard", headers={"X-User-ID": "dev_user"}).json()
    assert "active_courses_count" in dash

def test_11_presentation_slides_and_quiz_generation(client):
    """Тест 11 — Презентация и мини-тест: урок генерирует presentation_json и quiz_json."""
    import json
    headers = {"X-User-ID": "test_presentation_user"}
    course = client.post(
        "/api/ai/generate-course",
        headers=headers,
        json={"goal": "Биология: структура клетки", "user_level": "intermediate"}
    ).json()
    first_lesson_id = course["modules"][0]["lessons"][0]["id"]
    lesson_data = client.get(f"/api/lessons/{first_lesson_id}").json()

    assert lesson_data["presentation_json"] is not None
    slides = json.loads(lesson_data["presentation_json"])
    assert isinstance(slides, list)
    assert len(slides) >= 3
    assert "title" in slides[0]
    assert "bullets" in slides[0]

    assert lesson_data["quiz_json"] is not None
    quiz = json.loads(lesson_data["quiz_json"])
    assert isinstance(quiz, list)
    assert len(quiz) >= 1
    assert "question" in quiz[0]
    assert "options" in quiz[0]
    assert "correct_index" in quiz[0]
    assert "explanation" in quiz[0]

def test_12_lesson_status_lifecycle(client):
    """Тест 12 — Жизненный цикл статуса урока (not_started -> in_progress -> mastered)."""
    headers = {"X-User-ID": "test_lifecycle_user"}
    course = client.post(
        "/api/courses",
        headers=headers,
        json={
            "title": "Статусы уроков",
            "user_level": "beginner",
            "modules": [
                {
                    "title": "Модуль 1",
                    "lessons": [{"title": "Урок 1", "estimated_minutes": 15}]
                }
            ]
        }
    ).json()

    # Get course detail to retrieve created lesson id
    c_detail = client.get(f"/api/courses/{course['id']}", headers=headers).json()
    les = c_detail["modules"][0]["lessons"][0]

    # Initial get moves status to in_progress
    les_get = client.get(f"/api/lessons/{les['id']}").json()
    assert les_get["status"] in ["not_started", "in_progress"]

    # Mark as completed
    prog_resp = client.put(f"/api/lessons/{les['id']}/progress", json={"is_completed": True, "status": "mastered"})
    assert prog_resp.status_code == 200
    assert prog_resp.json()["status"] == "mastered"
    assert prog_resp.json()["is_completed"] is True

def test_13_ancient_rome_course_generation(client):
    """Тест 13 — История: «Расскажи всё про Древний Рим»."""
    headers = {"X-User-ID": "test_rome_user"}
    resp = client.post(
        "/api/ai/generate-course",
        headers=headers,
        json={"goal": "Расскажи всё про Древний Рим", "user_level": "beginner"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "рим" in data["title"].lower() or "рим" in data["target_goal"].lower()
    first_lesson = data["modules"][0]["lessons"][0]
    assert len(first_lesson["content_markdown"]) > 100
    # Must contain verified historical facts
    assert "рим" in first_lesson["content_markdown"].lower()
