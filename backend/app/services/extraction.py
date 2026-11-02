from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


def extract_pages(path: Path) -> list[dict]:
    """מחזירה רשימה של {"page": מספר עמוד, "text": הטקסט שלו}."""
    ext = path.suffix.lower()

    if ext == ".pdf":
        reader = PdfReader(str(path))
        return [
            {"page": i + 1, "text": page.extract_text() or ""}
            for i, page in enumerate(reader.pages)
        ]

    if ext == ".docx":
        doc = DocxDocument(str(path))
        text = "\n".join(p.text for p in doc.paragraphs)
        return [{"page": 1, "text": text}]

    raise ValueError(f"Unsupported file type: {ext}")