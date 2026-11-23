from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.account import AccountDelete, PasswordChange, ProfileUpdate, UsageOut
from app.schemas.user import UserOut
from app.services import account as service

# כל הנתיבים כאן פועלים על המשתמשת המחוברת בלבד, ולכן אין בהם מזהה
router = APIRouter(prefix="/auth/me", tags=["account"])


@router.get("", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("", response_model=UserOut)
def update_me(
    data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.update_display_name(db, current_user, data.display_name)


@router.get("/usage", response_model=UsageOut)
def get_usage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.usage(db, current_user)


@router.post("/password", status_code=204)
def change_password(
    data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.change_password(db, current_user, data.current_password, data.new_password)
    return Response(status_code=204)


@router.delete("", status_code=204)
def delete_me(
    data: AccountDelete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service.delete_account(db, current_user, data.confirm_email)
    return Response(status_code=204)
