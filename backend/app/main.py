from fastapi import FastAPI
from sqlalchemy import text

from app.core.database import Base, engine
from app.models import user, document, chunk  # noqa: כדי שהטבלאות יירשמו
from app.api import auth, documents, chat

with engine.begin() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DocuMind")
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)

@app.get("/health")
def health():
    return {"status": "ok"}