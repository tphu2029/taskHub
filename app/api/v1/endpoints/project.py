import json
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.redis import redis_client
from app.models.task import TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.label import LabelCreate, LabelResponse
from app.schemas.project import ProjectResponse, ProjectUpdate
from app.schemas.task import TaskCreate, TaskResponse
from app.services.email_service import send_task_assignment_email
from app.services.label_service import LabelService
from app.services.project_service import ProjectService
from app.services.task_service import TaskService

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
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: TaskStatus | None = Query(None, alias="status"),
    priority: TaskPriority | None = Query(None, alias="priority"),
    assignee: uuid.UUID | None = Query(None, alias="assignee"),
):
    # Try to get from cache first
    cache_key = f"project_{id}_tasks_p{page}_l{limit}_s{status}_pr{priority}_a{assignee}"
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)

    tasks = await TaskService.get_tasks(
        db=db, 
        current_user=current_user, 
        project_id=id,
        page=page,
        limit=limit,
        status_filter=status,
        priority=priority,
        assignee_id=assignee,
    )
    
    result = [TaskResponse.model_validate(task).model_dump(mode="json") for task in tasks]
    
    await redis_client.set(cache_key, json.dumps(result), ex=300)
    
    return [TaskResponse.model_validate(task) for task in tasks]


@router.post("/{id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    id: uuid.UUID,
    task_in: TaskCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
):
    task = await TaskService.create_task(db, current_user, id, task_in)
    if task.assignee_id:
        background_tasks.add_task(send_task_assignment_email, task.assignee_id, task.title, db)
    return task

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