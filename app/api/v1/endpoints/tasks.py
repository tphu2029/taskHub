import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.task import TaskResponse, TaskUpdate
from app.services.task_service import TaskService
from app.services.label_service import LabelService


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

# --- Label assignment endpoints ---

@router.post("/{id}/labels/{label_id}", response_model=TaskResponse)
async def assign_label_to_task(
    id: uuid.UUID,
    label_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await LabelService.assign_label_to_task(db, current_user, id, label_id)

@router.delete("/{id}/labels/{label_id}", response_model=TaskResponse)
async def remove_label_from_task(
    id: uuid.UUID,
    label_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await LabelService.remove_label_from_task(db, current_user, id, label_id)
