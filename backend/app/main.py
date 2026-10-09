import hashlib

from fastapi import FastAPI, Depends, HTTPException, status, Header
from typing import Annotated
from app.config import get_settings
from app.routers import ingredients, recipes
from secrets import compare_digest

ENVIRONMENT = get_settings().environment
API_KEY = get_settings().api_key
if API_KEY == "":
    raise KeyError

print(len(API_KEY))
print(hashlib.sha256(API_KEY.encode()).hexdigest()[:8])

app = FastAPI() if ENVIRONMENT == "development" else FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

def verify_token(x_api_key: str | None = None):
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authorized")
    if not compare_digest(x_api_key.encode(), API_KEY.encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authorized")


@app.get("/health")
def health_check():
    return {"status": "healthy"}


app.include_router(ingredients.router, prefix="/api/v1", dependencies=[Depends(verify_token)])
app.include_router(recipes.router, prefix="/api/v1", dependencies=[Depends(verify_token)])