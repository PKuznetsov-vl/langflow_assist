from fastapi import APIRouter

from app.api.v1.assistants import router as assistants_router

api_router = APIRouter()
api_router.include_router(assistants_router)
