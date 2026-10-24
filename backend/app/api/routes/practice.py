from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import datetime

from app.core.database import get_db
from app.models.entities import Exercise, Submission, ReviewSchedule, Skill, SkillProgress, Course
from app.services.code_runner import CodeSandbox
from app.services.spaced_repetition import calculate_sm2

router = APIRouter(prefix="/practice", tags=["Practice & Sandbox"])

class RunCodeRequest(BaseModel):
    language: str # cpp, python, bash
    code: str
    stdin_input: Optional[str] = ""

class SubmitExerciseRequest(BaseModel):
    exercise_id: int
    user_answer: str

def seed_default_exercises_if_empty(db: Session):
    if db.query(Exercise).count() == 0:
        # Check if any course exists to attach
        first_course = db.query(Course).first()
        cid = first_course.id if first_course else 1
        
        sample_exercises = [
            Exercise(
                course_id=cid,
                lesson_id=1,
                title="C++: Вывод в консоль",
                prompt="Напишите программу на C++, которая выводит на экран строку 'Hello, Second Brain AI!' с переводом строки.",
                exercise_type="code",
                initial_code='#include <iostream>\n\nint main() {\n    // Ваш код здесь\n    \n    return 0;\n}',
                solution='#include <iostream>\n\nint main() {\n    std::cout << "Hello, Second Brain AI!" << std::endl;\n    return 0;\n}',
                explanation="Для вывода в консоль используется поток std::cout из библиотеки <iostream>.",
                difficulty="easy"
            ),
            Exercise(
                course_id=cid,
                lesson_id=1,
                title="Linux: Права доступа",
                prompt="Какая числовая маска соответствует правам чтения и записи для владельца, и только чтения для остальных (rw-r--r--)?",
                exercise_type="quiz",
                initial_code="",
                solution="644",
                explanation="Владелец: r(4) + w(2) = 6. Группа: r(4) = 4. Остальные: r(4) = 4. Итого: 644.",
                difficulty="medium"
            ),
            Exercise(
                course_id=cid,
                lesson_id=1,
                title="C++: Указатели и адреса",
                prompt="Какой оператор в C++ используется для получения адреса переменной в памяти?",
                exercise_type="quiz",
                initial_code="",
                solution="&",
                explanation="Оператор & (амперсанд) возвращает адрес переменной, а оператор * (звёздочка) выполняет разыменование.",
                difficulty="easy"
            )
        ]
        db.add_all(sample_exercises)
        try:
            db.commit()
        except Exception:
            db.rollback()

@router.get("/exercises")
def list_exercises(
    course_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    seed_default_exercises_if_empty(db)
    query = db.query(Exercise)
    if course_id:
        query = query.filter(Exercise.course_id == course_id)
    exercises = query.all()
    
    return [
        {
            "id": e.id,
            "course_id": e.course_id,
            "lesson_id": e.lesson_id,
            "title": e.title,
            "prompt": e.prompt,
            "exercise_type": e.exercise_type,
            "initial_code": e.initial_code,
            "difficulty": e.difficulty
        }
        for e in exercises
    ]

@router.post("/run-code")
def run_code_in_sandbox(payload: RunCodeRequest):
    result = CodeSandbox.execute(
        language=payload.language,
        code=payload.code,
        stdin_input=payload.stdin_input or ""
    )
    return result

@router.post("/submit")
def submit_exercise(payload: SubmitExerciseRequest, db: Session = Depends(get_db)):
    exercise = db.query(Exercise).filter(Exercise.id == payload.exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Задание не найдено")

    user_ans = payload.user_answer.strip()
    sol = (exercise.solution or "").strip()

    is_correct = False
    score = 0.0
    feedback = ""

    if exercise.exercise_type == "quiz":
        if user_ans.lower() == sol.lower():
            is_correct = True
            score = 100.0
            feedback = f"Верно! {exercise.explanation or ''}"
        else:
            is_correct = False
            score = 0.0
            feedback = f"Не совсем так. Попробуйте еще раз. Подсказка: {exercise.explanation or ''}"
    elif exercise.exercise_type == "code":
        # Run code in sandbox to verify
        run_res = CodeSandbox.execute(language="cpp", code=user_ans)
        if run_res["exit_code"] != 0:
            is_correct = False
            score = 0.0
            feedback = f"Код не выполнился:\n{run_res['stderr']}"
        else:
            # Check output against expected keywords or exact match
            if "hello, second brain ai" in run_res["stdout"].lower() or run_res["success"]:
                is_correct = True
                score = 100.0
                feedback = f"Отлично! Программа успешно скомпилирована и вывела:\n{run_res['stdout']}"
            else:
                is_correct = False
                score = 50.0
                feedback = f"Код выполнился, но вывод отличается от ожидаемого:\n{run_res['stdout']}"

    # Record submission
    sub = Submission(
        exercise_id=exercise.id,
        user_answer=user_ans,
        is_correct=is_correct,
        score=score,
        feedback=feedback
    )
    db.add(sub)

    # Schedule spaced repetition review via SM-2
    grade = 5 if is_correct else 1
    sched = (
        db.query(ReviewSchedule)
        .filter(ReviewSchedule.item_type == "exercise", ReviewSchedule.item_id == exercise.id)
        .first()
    )
    reps = sched.repetitions if sched else 0
    ef = sched.ease_factor if sched else 2.5
    interval = sched.interval_days if sched else 1

    new_interval, new_reps, new_ef, next_date = calculate_sm2(grade, reps, ef, interval)

    if not sched:
        sched = ReviewSchedule(
            item_type="exercise",
            item_id=exercise.id,
            scheduled_date=next_date,
            interval_days=new_interval,
            ease_factor=new_ef,
            repetitions=new_reps,
            is_completed=False
        )
        db.add(sched)
    else:
        sched.scheduled_date = next_date
        sched.interval_days = new_interval
        sched.ease_factor = new_ef
        sched.repetitions = new_reps
        sched.is_completed = False

    db.commit()

    return {
        "is_correct": is_correct,
        "score": score,
        "feedback": feedback,
        "next_review_in_days": new_interval
    }
