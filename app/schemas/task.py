from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, UUID4
from app.models.task import TaskStatus, TaskPriority


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: datetime | None = None
    assignee_id: UUID4 | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None
    assignee_id: UUID4 | None = None


class TaskResponse(TaskBase):
    id: UUID4
    project_id: UUID4
    created_by: UUID4
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
