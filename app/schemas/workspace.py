from datetime import datetime

from pydantic import UUID4, BaseModel, ConfigDict, Field

from app.models.workspace import WorkspaceRole


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


from pydantic import UUID4, AliasChoices, BaseModel, ConfigDict, Field


class WorkspaceMemberAdd(BaseModel):
    user_id: UUID4 = Field(validation_alias=AliasChoices("userId", "user_id"), serialization_alias="userId")
    role: WorkspaceRole = WorkspaceRole.VIEWER
    model_config = ConfigDict(populate_by_name=True)


class WorkspaceMemberResponse(BaseModel):
    workspace_id: UUID4
    user_id: UUID4
    role: WorkspaceRole

    model_config = ConfigDict(from_attributes=True)
