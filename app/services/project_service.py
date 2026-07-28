import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.user import User
from app.models.workspace import WorkspaceMember
from app.schemas.project import ProjectCreate


class ProjectService:
    @staticmethod
    async def create_project(db: AsyncSession, current_user: User, workspace_id: uuid.UUID, project_in: ProjectCreate) -> Project:
        # Check if user is a member of the workspace
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id
        )
        result = await db.execute(stmt)
        member = result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions in this workspace",
            )

        new_project = Project(
            workspace_id=workspace_id,
            name=project_in.name,
            description=project_in.description
        )
        db.add(new_project)
        await db.commit()
        await db.refresh(new_project)
        return new_project
