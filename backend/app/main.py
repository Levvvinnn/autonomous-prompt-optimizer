import asyncio
import sys
import logging

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(level=logging.INFO)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.api.routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)

app.include_router(router)

@app.get("/")
def root() -> dict:
    """Root health endpoint returning service status."""
    return {"status": "running"}

@app.get("/health")
def health() -> dict:
    """Simple health check endpoint."""
    return {"status": "ok"}

