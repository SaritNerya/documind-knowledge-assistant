from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.openai_api_key)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536


def embed_texts(texts: list[str]) -> list[list[float]]:
    """מקבלת רשימת טקסטים ומחזירה וקטור לכל אחד, בקריאה אחת ל-API."""
    if not texts:
        return []
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]