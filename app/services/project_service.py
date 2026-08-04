import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectStatus
from app.models.user import User, UserRole
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    @staticmethod
    async def create_project(db: AsyncSession, current_user: User, workspace_id: uuid.UUID, project_in: ProjectCreate) -> Project:
        if current_user.role != UserRole.ADMIN:
            stmt = select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == current_user.id
            )
            result = await db.execute(stmt)
            member = result.scalar_one_or_none()

            if not member:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Workspace not found or you are not a member",
                )
            
            # Only OWNER and EDITOR can create projects
            if member.role not in [WorkspaceRole.OWNER, WorkspaceRole.EDITOR]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only workspace OWNER or EDITOR can create projects",
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

    @staticmethod
    async def get_projects_by_workspace(db: AsyncSession, current_user: User, workspace_id: uuid.UUID) -> list[Project]:
        mem_stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id
        )
        mem_result = await db.execute(mem_stmt)
        member = mem_result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found or you are not a member",
            )
            
        proj_stmt = select(Project).where(Project.workspace_id == workspace_id)
        proj_result = await db.execute(proj_stmt)
        return list(proj_result.scalars().all())

    @staticmethod
    async def get_project(db: AsyncSession, current_user: User, project_id: uuid.UUID) -> Project:
        # Get project
        stmt = select(Project).where(Project.id == project_id)
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Check membership
        mem_stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == project.workspace_id,
            WorkspaceMember.user_id == current_user.id
        )
        mem_result = await db.execute(mem_stmt)
        member = mem_result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this project",
            )

        return project

    @staticmethod
    async def update_project(db: AsyncSession, current_user: User, project_id: uuid.UUID, project_in: ProjectUpdate) -> Project:
        project = await ProjectService.get_project(db, current_user, project_id)

        # Check membership role
        mem_stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == project.workspace_id,
            WorkspaceMember.user_id == current_user.id
        )
        mem_result = await db.execute(mem_stmt)
        member = mem_result.scalar_one_or_none()
        
        if not member or member.role not in [WorkspaceRole.OWNER, WorkspaceRole.EDITOR]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only workspace OWNER or EDITOR can update projects",
            )

        update_data = project_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)

        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project

    @staticmethod
    async def archive_project(db: AsyncSession, current_user: User, project_id: uuid.UUID) -> Project:
        project = await ProjectService.get_project(db, current_user, project_id)

        mem_stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == project.workspace_id,
            WorkspaceMember.user_id == current_user.id
        )
        mem_result = await db.execute(mem_stmt)
        member = mem_result.scalar_one_or_none()
        
        if not member or member.role not in [WorkspaceRole.OWNER, WorkspaceRole.EDITOR]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only workspace OWNER or EDITOR can archive projects",
            )

        project.status = ProjectStatus.ARCHIVED
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project
        
    @staticmethod
    async def delete_project(db: AsyncSession, current_user: User, project_id: uuid.UUID) -> None:
        project = await ProjectService.get_project(db, current_user, project_id)

        mem_stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == project.workspace_id,
            WorkspaceMember.user_id == current_user.id
        )
        mem_result = await db.execute(mem_stmt)
        member = mem_result.scalar_one_or_none()
        
        if not member or member.role not in [WorkspaceRole.OWNER, WorkspaceRole.EDITOR]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only workspace OWNER or EDITOR can delete projects",
            )

        await db.delete(project)
        await db.commit()
