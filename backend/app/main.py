
from fastapi import FastAPI, Depends, Request

from app.config import get_settings
from app.logging_config import configure_logging
from app.logging_middleware import RequestLoggingMiddleware
from app.routers import ingredients, recipes, me
from app.auth import get_current_user


ENVIRONMENT = get_settings().environment

app = FastAPI() if ENVIRONMENT == "development" else FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
configure_logging(ENVIRONMENT, "INFO")
app.add_middleware(RequestLoggingMiddleware)


@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.middleware("http")
async def add_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    if (ENVIRONMENT != "development"):
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response



app.include_router(ingredients.router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(recipes.router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(me.router, prefix="/api/v1")