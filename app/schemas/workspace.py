from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, UUID4
from app.models.workspace import WorkspaceRole
from app.schemas.user import UserResponse


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class WorkspaceUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class WorkspaceResponse(BaseModel):
    id: UUID4
    name: str
    owner_id: UUID4
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkspaceMemberAdd(BaseModel):
    user_id: UUID4
    role: WorkspaceRole = WorkspaceRole.VIEWER


class WorkspaceMemberResponse(BaseModel):
    workspace_id: UUID4
    user_id: UUID4
    role: WorkspaceRole

    model_config = ConfigDict(from_attributes=True)
