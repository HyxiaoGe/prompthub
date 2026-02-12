from fastapi import APIRouter

from app.api import projects, prompts, scenes, shared, versions
from app.config import settings

api_router = APIRouter(prefix=settings.API_PREFIX)

api_router.include_router(prompts.router, prefix="/prompts", tags=["prompts"])
api_router.include_router(versions.router, prefix="/prompts", tags=["versions"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(scenes.router, prefix="/scenes", tags=["scenes"])
api_router.include_router(shared.router, prefix="/shared", tags=["shared"])
