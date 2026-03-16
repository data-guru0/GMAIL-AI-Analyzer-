import json
import logging
import os
from flask import current_app
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from .ai_agent.prompts import REQUIREMENTS_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)

def extract_text_from_file(filepath: str) -> str:
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".pdf":
        return _extract_pdf(filepath)
    elif ext in (".docx", ".doc"):
        return _extract_docx(filepath)
    elif ext in (".txt", ".md"):
        return _extract_txt(filepath)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Please upload PDF, DOCX, or TXT.")

def _extract_pdf(filepath: str) -> str:
    try:
        import fitz
        doc = fitz.open(filepath)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except ImportError:
        raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")

def _extract_docx(filepath: str) -> str:
    try:
        from docx import Document
        doc = Document(filepath)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs).strip()
    except ImportError:
        raise ImportError("python-docx not installed. Run: pip install python-docx")

def _extract_txt(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        return f.read().strip()

def parse_requirements_with_ai(raw_text: str) -> dict:
    if not raw_text:
        return {
            "categories": [],
            "global_keywords": [],
            "allowed_senders": [],
            "blocked_senders": [],
            "summary": "No requirements provided.",
        }

    try:
        llm = ChatOpenAI(
            model=current_app.config["OPENAI_MODEL"],
            api_key=current_app.config["OPENAI_API_KEY"],
            temperature=0,
            response_format={"type": "json_object"},
        )

        messages = [
            SystemMessage(content=REQUIREMENTS_EXTRACTION_PROMPT),
            HumanMessage(content=f"USER DOCUMENT:\n\n{raw_text[:8000]}"),
        ]

        response = llm.invoke(messages)
        parsed = json.loads(response.content)

        return {
            "categories": parsed.get("categories", []),
            "global_keywords": parsed.get("global_keywords", []),
            "allowed_senders": parsed.get("allowed_senders", []),
            "blocked_senders": parsed.get("blocked_senders", []),
            "summary": parsed.get("summary", ""),
        }

    except Exception as e:
        logger.error(f"Requirements parsing failed: {e}")
        return {
            "categories": [],
            "global_keywords": [],
            "allowed_senders": [],
            "blocked_senders": [],
            "summary": f"Parsing failed: {str(e)}",
        }

def extract_label_names(requirements: dict) -> list:
    return [cat["name"] for cat in requirements.get("categories", [])]
