from fastapi import APIRouter, FastAPI
import config
from routers import ingredients

ENVIRONMENT = config.get_settings().environment

app = FastAPI() if ENVIRONMENT == "development" else FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
router = APIRouter();


@app.get("/health")
def health_check():
    return {"status": "healthy"}



app.include_router(ingredients.router, prefix="/api/v1")