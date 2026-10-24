import pytest
import os
import tempfile
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.entities import (
    Base, Course, Module, Lesson, LearningSession, Document, DocumentChunk,
    CourseDocument, Conversation, Message, Skill, SkillProgress, ReviewSchedule
)
from app.services.spaced_repetition import calculate_sm2
from app.services.code_runner import CodeSandbox
from app.services.document_parser import chunk_text

def test_sm2_algorithm():
    # Successful recall on first review (grade 5)
    interval, reps, ef, next_date = calculate_sm2(grade=5, repetitions=0, ease_factor=2.5, current_interval=1)
    assert interval == 1
    assert reps == 1
    assert ef >= 2.5

    # Second review success
    interval2, reps2, ef2, next_date2 = calculate_sm2(grade=5, repetitions=1, ease_factor=ef, current_interval=interval)
    assert interval2 == 6
    assert reps2 == 2

    # Third review success: interval should grow exponentially
    interval3, reps3, ef3, _ = calculate_sm2(grade=4, repetitions=2, ease_factor=ef2, current_interval=interval2)
    assert interval3 > 6
    assert reps3 == 3

    # Failure (grade 1) resets repetitions to 0 and interval to 1
    interval_fail, reps_fail, ef_fail, _ = calculate_sm2(grade=1, repetitions=reps3, ease_factor=ef3, current_interval=interval3)
    assert interval_fail == 1
    assert reps_fail == 0
    assert ef_fail < ef3
    assert ef_fail >= 1.3 # minimum bound preserved

def test_code_sandbox_cpp():
    code = """
    #include <iostream>
    int main() {
        std::cout << "Second Brain Sandbox OK" << std::endl;
        return 0;
    }
    """
    res = CodeSandbox.execute("cpp", code)
    assert res["success"] is True
    assert "Second Brain Sandbox OK" in res["stdout"]
    assert res["exit_code"] == 0

def test_code_sandbox_python():
    code = "print(2 + 2 * 10)"
    res = CodeSandbox.execute("python", code)
    assert res["success"] is True
    assert "22" in res["stdout"].strip()

def test_code_sandbox_timeout_safety():
    # Infinite loop must terminate safely without freezing the server
    code = """
    int main() {
        while(true) {}
        return 0;
    }
    """
    res = CodeSandbox.execute("cpp", code)
    assert res["success"] is False
    assert res["exit_code"] != 0

def test_text_chunking():
    sample = "Это первый параграф учебника по Linux.\n\nЭто второй параграф с подробным описанием команды chmod 755.\n\nТретий параграф про права доступа."
    chunks = chunk_text(sample, page_number=1, section_name="Права доступа", chunk_size=60, overlap=10)
    assert len(chunks) >= 2
    for c in chunks:
        assert c.page_number == 1
        assert c.section_name == "Права доступа"
        assert len(c.content) > 0
