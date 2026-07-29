import json
import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus, TaskPriority
from app.models.project import Project
from app.models.user import User
from app.models.workspace import WorkspaceMember
from app.schemas.task import TaskCreate, TaskUpdate
from app.core.redis import redis_client


class TaskService:
    @staticmethod
    async def _check_workspace_membership_for_project(db: AsyncSession, user_id: uuid.UUID, project_id: uuid.UUID) -> None:
        """Check if user is a member of the workspace that owns the project"""
        project = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        member = (await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == project.workspace_id,
                WorkspaceMember.user_id == user_id
            )
        )).scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions in the workspace for this project"
            )
        return project

    @staticmethod
    async def _check_workspace_membership_for_task(db: AsyncSession, user_id: uuid.UUID, task_id: uuid.UUID) -> Task:
        """Check if user has access to the task and return the task"""
        task = (await db.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        
        await TaskService._check_workspace_membership_for_project(db, user_id, task.project_id)
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
        await TaskService._check_workspace_membership_for_project(db, current_user.id, project_id)

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
        
        # Invalidate cache
        await TaskService.invalidate_project_tasks_cache(project_id)
        
        return new_task

    @staticmethod
    async def get_tasks(
        db: AsyncSession, 
        current_user: User, 
        project_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        task_status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assignee_id: Optional[uuid.UUID] = None
    ) -> list[Task]:
        await TaskService._check_workspace_membership_for_project(db, current_user.id, project_id)

        stmt = select(Task).where(Task.project_id == project_id)
        
        if task_status:
            stmt = stmt.where(Task.status == task_status)
        if priority:
            stmt = stmt.where(Task.priority == priority)
        if assignee_id:
            stmt = stmt.where(Task.assignee_id == assignee_id)
            
        stmt = stmt.offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_task(db: AsyncSession, current_user: User, task_id: uuid.UUID, task_in: TaskUpdate) -> Task:
        task = await TaskService._check_workspace_membership_for_task(db, current_user.id, task_id)
        
        update_data = task_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        db.add(task)
        await db.commit()
        await db.refresh(task)
        
        # Invalidate cache
        await TaskService.invalidate_project_tasks_cache(task.project_id)
        
        return task

    @staticmethod
    async def delete_task(db: AsyncSession, current_user: User, task_id: uuid.UUID) -> None:
        task = await TaskService._check_workspace_membership_for_task(db, current_user.id, task_id)
        
        project_id = task.project_id
        await db.delete(task)
        await db.commit()
        
        # Invalidate cache
        await TaskService.invalidate_project_tasks_cache(project_id)
        return None
