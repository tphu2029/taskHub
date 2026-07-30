import uuid
import json
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.redis import redis_client
from app.models.user import User
from app.models.task import TaskStatus, TaskPriority
from app.schemas.project import ProjectResponse, ProjectUpdate
from app.services.project_service import ProjectService
from app.schemas.task import TaskCreate, TaskResponse
from app.services.task_service import TaskService
from app.schemas.label import LabelCreate, LabelResponse
from app.services.label_service import LabelService


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

@router.get("/{id}/tasks", response_model=list[TaskResponse])
async def get_tasks(
    id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    task_status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    assignee_id: Optional[uuid.UUID] = None
):
    # Try to get from cache first
    cache_key = f"project_{id}_tasks_{skip}_{limit}_{task_status}_{priority}_{assignee_id}"
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    tasks = await TaskService.get_tasks(
        db=db, 
        current_user=current_user, 
        project_id=id,
        skip=skip,
        limit=limit,
        task_status=task_status,
        priority=priority,
        assignee_id=assignee_id
    )
    
    result = [TaskResponse.model_validate(task).model_dump(mode="json") for task in tasks]
    
    await redis_client.set(cache_key, json.dumps(result), ex=300)
    
    return tasks


@router.post("/{id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    id: uuid.UUID,
    task_in: TaskCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await TaskService.create_task(db, current_user, id, task_in)

# --- Labels endpoints for project ---

@router.post("/{id}/labels", response_model=LabelResponse, status_code=status.HTTP_201_CREATED)
async def create_label(
    id: uuid.UUID,
    label_in: LabelCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await LabelService.create_label(db, current_user, id, label_in)


@router.get("/{id}/labels", response_model=list[LabelResponse])
async def get_labels(
    id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await LabelService.get_labels_by_project(db, current_user, id)