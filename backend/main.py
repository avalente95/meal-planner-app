from fastapi import FastAPI

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
