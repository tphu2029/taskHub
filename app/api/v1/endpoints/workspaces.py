import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceMemberAdd,
    WorkspaceMemberResponse,
    WorkspaceResponse,
    WorkspaceUpdate,
)
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    ws_in: WorkspaceCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await WorkspaceService.create_workspace(db, current_user, ws_in)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await WorkspaceService.get_workspace(db, current_user, workspace_id)


@router.post("/{workspace_id}/members", response_model=WorkspaceMemberResponse)
async def add_workspace_member(
    workspace_id: uuid.UUID,
    member_in: WorkspaceMemberAdd,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await WorkspaceService.add_member(db, current_user, workspace_id, member_in)


@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_workspace_member(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await WorkspaceService.remove_member(db, current_user, workspace_id, user_id)


from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.project_service import ProjectService

@router.post("/{workspace_id}/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    workspace_id: uuid.UUID,
    project_in: ProjectCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await ProjectService.create_project(db, current_user, workspace_id, project_in)
