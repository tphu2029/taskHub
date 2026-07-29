import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.project import ProjectResponse, ProjectUpdate
from app.services.project_service import ProjectService
from app.schemas.task import TaskCreate


router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("/{id}", response_model=ProjectResponse)
async def get_project(
    id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await ProjectService.get_project(db, current_user, id)

@router.put("/{id}", response_model=ProjectResponse)
async def update_project(
    id: uuid.UUID,
    project_in: ProjectUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await ProjectService.update_project(db, current_user, id, project_in)

@router.patch("/{id}/archive", response_model=ProjectResponse)
async def archive_project(
    id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await ProjectService.archive_project(db, current_user, id)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await ProjectService.delete_project(db, current_user, id)

# --- Tasks endpoints ---

TaskResponse = None

@router.get("/{id}/tasks", response_model=list[TaskResponse])
async def get_tasks(
    id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    TaskService = None
    return await TaskService.get_tasks(db, current_user, id)


@router.post("/{id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    id: uuid.UUID,
    task_in: TaskCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    TaskService = None
    return await TaskService.create_task(db, current_user, id, task_in)