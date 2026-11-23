from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt
from app.core.config import settings

ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_access_token(user_id: int, remember: bool = False) -> str:
    """remember=True ("זכור אותי"): טוקן ארוך, כדי שהמשתמש יישאר מחובר גם אחרי סגירת הדפדפן."""
    lifetime = (
        timedelta(days=settings.remember_me_expire_days)
        if remember
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    expire = datetime.now(timezone.utc) + lifetime
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)