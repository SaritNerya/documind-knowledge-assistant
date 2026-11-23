from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
import app
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.user import UserCreate, UserOut, Token
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserOut
import hmac
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if settings.invite_code and not hmac.compare_digest(data.invite_code, settings.invite_code):
        raise HTTPException(status_code=403, detail="Invalid invitation code")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=data.email, hashed_password=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    remember: bool = Form(False),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user.id, remember))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    """המשתמש המחובר. משמש את הפרונט כדי להציג את תפריט המשתמש."""
    return current_user
