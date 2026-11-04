import logging
from dataclasses import dataclass, field

from openai import OpenAIError
from sqlalchemy.orm import Session

from app.services.llm import answer_from_web, generate_answer, rewrite_queries
from app.services.retrieval import get_document_overviews, search_chunks

logger = logging.getLogger(__name__)

NOT_FOUND_ANSWER = "לא מצאתי מידע על כך במסמכים שלך."
WEB_PREFIX = "במסמכים שלך אין מידע על כך, אבל מחיפוש באינטרנט הגעתי לתוצאות הבאות:\n\n"


@dataclass
class RagResult:
    answer: str
    sources: list[dict]
    found: bool
    used_web: bool
    chunks: list[dict] = field(default_factory=list)
    queries: list[str] = field(default_factory=list)


def answer_question(
    db: Session,
    user_id: int,
    question: str,
    history: list[dict],
    allow_web: bool = True,
) -> RagResult:
    """כל צינור ה-RAG במקום אחד. משמש גם את ה-endpoint וגם את סקריפט ההערכה."""
    queries = rewrite_queries(question, history)
    chunks = search_chunks(db, user_id, queries)
    overviews = get_document_overviews(db, user_id)
    result = generate_answer(question, chunks, overviews, history)

    answer = result["answer"].strip() or NOT_FOUND_ANSWER
    sources: list[dict] = []
    used_web = False

    if result["found"]:
        # רק מקורות שהמודל באמת השתמש בהם, בלי כפילויות
        unique: dict[tuple, dict] = {}
        for i in result["used"]:
            c = chunks[i - 1]
            key = (c["filename"], c["page"])
            if key not in unique or c["score"] > unique[key]["score"]:
                unique[key] = {
                    "filename": c["filename"],
                    "page": c["page"],
                    "score": round(c["score"], 3),
                    "url": None,
                }
        sources = list(unique.values())

    elif result["needs_web"] and allow_web:
        try:
            web_text, links = answer_from_web(question)
        except OpenAIError:
            logger.exception("web search failed")  # לא קריטי, נשארים עם התשובה מהמסמכים
        else:
            if web_text.strip():
                answer = WEB_PREFIX + web_text.strip()
                sources = [{"filename": l["title"], "page": 0, "score": 0.0, "url": l["url"]}
                           for l in links]
                used_web = True

    logger.info(
        "rag queries=%d chunks=%d found=%s web=%s sources=%d",
        len(queries), len(chunks), result["found"], used_web, len(sources),
    )
    return RagResult(
        answer=answer,
        sources=sources,
        found=result["found"],
        used_web=used_web,
        chunks=chunks,
        queries=queries,
    )