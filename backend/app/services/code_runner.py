import subprocess
import tempfile
import os
import resource
import time
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger("second_brain.sandbox")

TIMEOUT_SECONDS = 4
MAX_MEMORY_BYTES = 128 * 1024 * 1024 # 128 MB

def set_limits():
    """Restricts CPU time and memory for the child process."""
    try:
        # Limit CPU time (seconds)
        resource.setrlimit(resource.RLIMIT_CPU, (TIMEOUT_SECONDS, TIMEOUT_SECONDS + 1))
        # Limit virtual memory
        resource.setrlimit(resource.RLIMIT_AS, (MAX_MEMORY_BYTES, MAX_MEMORY_BYTES))
        # Prevent core dumps
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        # Limit file size written
        resource.setrlimit(resource.RLIMIT_FSIZE, (10 * 1024 * 1024, 10 * 1024 * 1024))
    except Exception as e:
        logger.warning(f"Could not set resource limits: {e}")

class CodeSandbox:
    @staticmethod
    def execute(language: str, code: str, stdin_input: str = "") -> Dict[str, Any]:
        lang = language.lower().strip()
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            if lang in ["cpp", "c++"]:
                return CodeSandbox._run_cpp(tmppath, code, stdin_input)
            elif lang in ["python", "py"]:
                return CodeSandbox._run_python(tmppath, code, stdin_input)
            elif lang in ["bash", "sh"]:
                return CodeSandbox._run_bash(tmppath, code, stdin_input)
            else:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": f"Язык {language} не поддерживается для прямого запуска.",
                    "exit_code": -1,
                    "execution_time_ms": 0
                }

    @staticmethod
    def _run_cpp(tmppath: Path, code: str, stdin_input: str) -> Dict[str, Any]:
        src_file = tmppath / "main.cpp"
        bin_file = tmppath / "app_exec"
        src_file.write_text(code, encoding="utf-8")

        # Compile
        compile_start = time.time()
        try:
            compile_proc = subprocess.run(
                ["g++", "-O2", "-std=c++20", str(src_file), "-o", str(bin_file)],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(tmppath)
            )
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Превышено время компиляции C++ (timeout > 10s)",
                "exit_code": 1,
                "execution_time_ms": 10000
            }

        if compile_proc.returncode != 0:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Ошибка компиляции:\n{compile_proc.stderr}",
                "exit_code": compile_proc.returncode,
                "execution_time_ms": int((time.time() - compile_start) * 1000)
            }

        # Run
        run_start = time.time()
        try:
            run_proc = subprocess.run(
                [str(bin_file)],
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                preexec_fn=set_limits,
                cwd=str(tmppath)
            )
            exec_time = int((time.time() - run_start) * 1000)
            return {
                "success": run_proc.returncode == 0,
                "stdout": run_proc.stdout,
                "stderr": run_proc.stderr,
                "exit_code": run_proc.returncode,
                "execution_time_ms": exec_time
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Превышен лимит времени выполнения ({TIMEOUT_SECONDS} сек). Возможно бесконечный цикл.",
                "exit_code": 124,
                "execution_time_ms": TIMEOUT_SECONDS * 1000
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Ошибка выполнения: {str(e)}",
                "exit_code": -1,
                "execution_time_ms": 0
            }

    @staticmethod
    def _run_python(tmppath: Path, code: str, stdin_input: str) -> Dict[str, Any]:
        src_file = tmppath / "script.py"
        src_file.write_text(code, encoding="utf-8")

        start = time.time()
        try:
            proc = subprocess.run(
                ["python3", str(src_file)],
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                preexec_fn=set_limits,
                cwd=str(tmppath)
            )
            return {
                "success": proc.returncode == 0,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "exit_code": proc.returncode,
                "execution_time_ms": int((time.time() - start) * 1000)
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Превышен лимит времени выполнения ({TIMEOUT_SECONDS} сек).",
                "exit_code": 124,
                "execution_time_ms": TIMEOUT_SECONDS * 1000
            }

    @staticmethod
    def _run_bash(tmppath: Path, code: str, stdin_input: str) -> Dict[str, Any]:
        src_file = tmppath / "script.sh"
        src_file.write_text(code, encoding="utf-8")

        start = time.time()
        try:
            proc = subprocess.run(
                ["bash", str(src_file)],
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                preexec_fn=set_limits,
                cwd=str(tmppath)
            )
            return {
                "success": proc.returncode == 0,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "exit_code": proc.returncode,
                "execution_time_ms": int((time.time() - start) * 1000)
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Превышен лимит времени выполнения ({TIMEOUT_SECONDS} сек).",
                "exit_code": 124,
                "execution_time_ms": TIMEOUT_SECONDS * 1000
            }
