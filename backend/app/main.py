from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import auth, documents, conversations

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

# מבנה המסד מנוהל ב-Alembic (backend/alembic). לפני הפעלה: alembic upgrade head

app = FastAPI(title="DocuMind")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(conversations.router)

@app.get("/health")
def health():
    return {"status": "ok"}