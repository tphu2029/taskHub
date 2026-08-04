from datetime import datetime

from pydantic import UUID4, BaseModel, ConfigDict, Field

from app.models.project import ProjectStatus


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class ProjectResponse(BaseModel):
    id: UUID4
    workspace_id: UUID4
    name: str
    description: str | None
    status: ProjectStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: ProjectStatus | None = None