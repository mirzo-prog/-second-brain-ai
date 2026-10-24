import os
from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger("second_brain.parser")

class ParsedChunk:
    def __init__(self, content: str, page_number: int = None, section_name: str = None, char_start: int = 0, char_end: int = 0):
        self.content = content
        self.page_number = page_number
        self.section_name = section_name
        self.char_start = char_start
        self.char_end = char_end

def chunk_text(text: str, page_number: int = None, section_name: str = None, chunk_size: int = 800, overlap: int = 150) -> List[ParsedChunk]:
    chunks = []
    text = text.strip()
    if not text:
        return chunks

    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        # Try to break at newline or period if possible
        if end < text_len:
            last_break = max(text.rfind("\n", start, end), text.rfind(". ", start, end))
            if last_break > start + (chunk_size // 2):
                end = last_break + 1

        chunk_str = text[start:end].strip()
        if chunk_str:
            chunks.append(ParsedChunk(
                content=chunk_str,
                page_number=page_number,
                section_name=section_name,
                char_start=start,
                char_end=end
            ))

        if end >= text_len:
            break
        start = max(end - overlap, start + 1)

    return chunks

class DocumentParser:
    @staticmethod
    def parse_file(file_path: Path, file_type: str) -> List[ParsedChunk]:
        ft = file_type.lower().replace(".", "")
        if ft == "pdf":
            return DocumentParser._parse_pdf(file_path)
        elif ft == "docx":
            return DocumentParser._parse_docx(file_path)
        elif ft in ["md", "markdown"]:
            return DocumentParser._parse_markdown(file_path)
        elif ft in ["txt", "text", "c", "cpp", "py", "sh", "bash"]:
            return DocumentParser._parse_plaintext(file_path)
        else:
            return DocumentParser._parse_plaintext(file_path)

    @staticmethod
    def _parse_pdf(file_path: Path) -> List[ParsedChunk]:
        import pypdf
        chunks = []
        try:
            reader = pypdf.PdfReader(str(file_path))
            for page_idx, page in enumerate(reader.pages):
                page_num = page_idx + 1
                page_text = page.extract_text() or ""
                if page_text.strip():
                    page_chunks = chunk_text(page_text, page_number=page_num, section_name=f"Страница {page_num}")
                    chunks.extend(page_chunks)
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            raise
        return chunks

    @staticmethod
    def _parse_docx(file_path: Path) -> List[ParsedChunk]:
        import docx
        chunks = []
        try:
            doc = docx.Document(str(file_path))
            current_section = "Введение"
            accumulated_text = []

            for p in doc.paragraphs:
                text = p.text.strip()
                if not text:
                    continue
                if p.style and "heading" in p.style.name.lower():
                    if accumulated_text:
                        full_sec_text = "\n".join(accumulated_text)
                        chunks.extend(chunk_text(full_sec_text, section_name=current_section))
                        accumulated_text = []
                    current_section = text
                else:
                    accumulated_text.append(text)

            if accumulated_text:
                chunks.extend(chunk_text("\n".join(accumulated_text), section_name=current_section))
        except Exception as e:
            logger.error(f"Error parsing DOCX {file_path}: {e}")
            raise
        return chunks

    @staticmethod
    def _parse_markdown(file_path: Path) -> List[ParsedChunk]:
        chunks = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            current_section = "Основной текст"
            accumulated = []

            for line in lines:
                if line.startswith("#"):
                    if accumulated:
                        chunks.extend(chunk_text("\n".join(accumulated), section_name=current_section))
                        accumulated = []
                    current_section = line.strip("# \t\r\n")
                accumulated.append(line)

            if accumulated:
                chunks.extend(chunk_text("\n".join(accumulated), section_name=current_section))
        except Exception as e:
            logger.error(f"Error parsing Markdown {file_path}: {e}")
            raise
        return chunks

    @staticmethod
    def _parse_plaintext(file_path: Path) -> List[ParsedChunk]:
        chunks = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            chunks = chunk_text(text, section_name="Документ")
        except Exception as e:
            logger.error(f"Error parsing plaintext {file_path}: {e}")
            raise
        return chunks
