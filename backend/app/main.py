from fastapi import FastAPI
import os

DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
