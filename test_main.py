"""
Simple FastAPI test app
"""

from fastapi import FastAPI

app = FastAPI(
    title="GreenLightPA API Test",
    description="Test API",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    return {"status": "healthy"} 