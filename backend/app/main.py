from fastapi import FastAPI
from app.core.database import Base, engine
from app.models import user, document
from app.api import auth, documents, chat

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DocuMind")
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)

@app.get("/health")
def health():
    return {"status": "ok"}