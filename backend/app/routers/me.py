from fastapi import APIRouter, HTTPException, Query, status, Depends
from app.auth import get_current_user
from app.models import CurrentUser

router = APIRouter(prefix="/me", tags=["me"])

@router.get("")
def get_user(current_user: CurrentUser = Depends(get_current_user)):
    return current_user.id