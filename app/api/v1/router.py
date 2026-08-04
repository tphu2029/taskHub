from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    comments,
    labels,
    project,
    tasks,
    users,
    workspaces,
)
from app.schemas.error import COMMON_RESPONSES

api_router = APIRouter(prefix="/api/v1", responses=COMMON_RESPONSES)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(workspaces.router)
api_router.include_router(project.router)
api_router.include_router(tasks.router)
api_router.include_router(labels.router)
api_router.include_router(comments.router)
