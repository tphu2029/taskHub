import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.task import TaskResponse, TaskUpdate
from app.services.task_service import TaskService


router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.patch("/{id}", response_model=TaskResponse)
async def update_task(
    id: uuid.UUID,
    task_in: TaskUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await TaskService.update_task(db, current_user, id, task_in)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await TaskService.delete_task(db, current_user, id)
