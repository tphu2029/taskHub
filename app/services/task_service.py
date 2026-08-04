import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.redis import redis_client
from app.models.project import Project
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User, UserRole
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    @staticmethod
    async def _check_workspace_membership_for_project(
        db: AsyncSession, current_user: User, project_id: uuid.UUID, min_role: WorkspaceRole | None = None
    ) -> Project:
        """Check if user is a member of the workspace that owns the project with required role"""
        project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        if current_user.role == UserRole.ADMIN:
            return project

        member = (await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == project.workspace_id,
                WorkspaceMember.user_id == current_user.id
            )
        )).scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions in the workspace for this project"
            )

        if min_role == WorkspaceRole.EDITOR and member.role not in [WorkspaceRole.OWNER, WorkspaceRole.EDITOR]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="VIEWER role does not have permission to modify tasks"
            )

        return project

    @staticmethod
    async def _check_workspace_membership_for_task(
        db: AsyncSession, current_user: User, task_id: uuid.UUID, min_role: WorkspaceRole | None = None
    ) -> Task:
        """Check if user has access to the task and return the task"""
        task = (await db.execute(
            select(Task).options(selectinload(Task.labels)).where(Task.id == task_id)
        )).scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        
        await TaskService._check_workspace_membership_for_project(db, current_user, task.project_id, min_role=min_role)
        return task

    @staticmethod
    async def invalidate_project_tasks_cache(project_id: uuid.UUID) -> None:
        """Delete all cache keys related to a project's tasks"""
        pattern = f"project_{project_id}_tasks_*"
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)

    @staticmethod
    async def create_task(db: AsyncSession, current_user: User, project_id: uuid.UUID, task_in: TaskCreate) -> Task:
        await TaskService._check_workspace_membership_for_project(
            db, current_user, project_id, min_role=WorkspaceRole.EDITOR
        )

        new_task = Task(
            project_id=project_id,
            title=task_in.title,
            description=task_in.description,
            status=task_in.status,
            priority=task_in.priority,
            due_date=task_in.due_date,
            assignee_id=task_in.assignee_id,
            created_by=current_user.id
        )
        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)

        # Reload with labels
        new_task = (await db.execute(
            select(Task).options(selectinload(Task.labels)).where(Task.id == new_task.id)
        )).scalar_one()

        # Invalidate cache
        await TaskService.invalidate_project_tasks_cache(project_id)
        
        return new_task

    @staticmethod
    async def get_tasks(
        db: AsyncSession, 
        current_user: User, 
        project_id: uuid.UUID,
        page: int = 1,
        limit: int = 10,
        status_filter: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        assignee_id: uuid.UUID | None = None
    ) -> list[Task]:
        await TaskService._check_workspace_membership_for_project(db, current_user, project_id)

        stmt = select(Task).options(selectinload(Task.labels)).where(Task.project_id == project_id)
        
        if status_filter:
            stmt = stmt.where(Task.status == status_filter)
        if priority:
            stmt = stmt.where(Task.priority == priority)
        if assignee_id:
            stmt = stmt.where(Task.assignee_id == assignee_id)
            
        skip = (page - 1) * limit
        stmt = stmt.offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_task(db: AsyncSession, current_user: User, task_id: uuid.UUID, task_in: TaskUpdate) -> Task:
        task = await TaskService._check_workspace_membership_for_task(
            db, current_user, task_id, min_role=WorkspaceRole.EDITOR
        )
        
        update_data = task_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        db.add(task)
        await db.commit()
        await db.refresh(task)

        # Reload with labels
        task = (await db.execute(
            select(Task).options(selectinload(Task.labels)).where(Task.id == task.id)
        )).scalar_one()
        
        # Invalidate cache
        await TaskService.invalidate_project_tasks_cache(task.project_id)
        
        return task

    @staticmethod
    async def delete_task(db: AsyncSession, current_user: User, task_id: uuid.UUID) -> None:
        task = await TaskService._check_workspace_membership_for_task(
            db, current_user, task_id, min_role=WorkspaceRole.EDITOR
        )
        
        project_id = task.project_id
        await db.delete(task)
        await db.commit()
        
        # Invalidate cache
        await TaskService.invalidate_project_tasks_cache(project_id)
