import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentResponse
from app.schemas.task import TaskResponse, TaskUpdate
from app.services.comment_service import CommentService
from app.services.email_service import send_task_assignment_email
from app.services.label_service import LabelService
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.patch("/{id}", response_model=TaskResponse)
async def update_task(
    id: uuid.UUID,
    task_in: TaskUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
):
    task = await TaskService.update_task(db, current_user, id, task_in)
    if task_in.assignee_id is not None and task.assignee_id:
        background_tasks.add_task(send_task_assignment_email, task.assignee_id, task.title, db)
    return task

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

# --- Comment endpoints ---

@router.post("/{id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    id: uuid.UUID,
    comment_in: CommentCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await CommentService.create_comment(db, current_user, id, comment_in)

@router.get("/{id}/comments", response_model=list[CommentResponse])
async def get_comments(
    id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await CommentService.get_comments_by_task(db, current_user, id)
