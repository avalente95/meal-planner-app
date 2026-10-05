from fastapi import APIRouter

router = APIRouter(prefix="/ingredients", tags=["Ingredients"])

@router.get("")
def test_endpoint():
    return {"message": "Test endpoint is working!"}