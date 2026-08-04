import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.label import Label
from app.models.project import Project
from app.models.task import Task
from app.models.user import User, UserRole
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.schemas.label import LabelCreate, LabelUpdate
from app.services.task_service import TaskService


class LabelService:
    @staticmethod
    async def _check_workspace_membership_for_project(
        db: AsyncSession, current_user: User, project_id: uuid.UUID, min_role: WorkspaceRole | None = None
    ) -> Project:
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
                detail="VIEWER role does not have permission to modify labels"
            )

        return project

    @staticmethod
    async def create_label(db: AsyncSession, current_user: User, project_id: uuid.UUID, label_in: LabelCreate) -> Label:
        await LabelService._check_workspace_membership_for_project(
            db, current_user, project_id, min_role=WorkspaceRole.EDITOR
        )

        new_label = Label(
            project_id=project_id,
            name=label_in.name,
            color=label_in.color,
        )
        db.add(new_label)
        await db.commit()
        await db.refresh(new_label)
        return new_label

    @staticmethod
    async def get_labels_by_project(db: AsyncSession, current_user: User, project_id: uuid.UUID) -> list[Label]:
        await LabelService._check_workspace_membership_for_project(db, current_user, project_id)

        stmt = select(Label).where(Label.project_id == project_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_label(db: AsyncSession, current_user: User, label_id: uuid.UUID, label_in: LabelUpdate) -> Label:
        label = (await db.execute(select(Label).where(Label.id == label_id))).scalar_one_or_none()
        if not label:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Label not found")

        await LabelService._check_workspace_membership_for_project(
            db, current_user, label.project_id, min_role=WorkspaceRole.EDITOR
        )

        update_data = label_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(label, field, value)

        db.add(label)
        await db.commit()
        await db.refresh(label)

        await TaskService.invalidate_project_tasks_cache(label.project_id)
        return label

    @staticmethod
    async def delete_label(db: AsyncSession, current_user: User, label_id: uuid.UUID) -> None:
        label = (await db.execute(select(Label).where(Label.id == label_id))).scalar_one_or_none()
        if not label:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Label not found")

        project_id = label.project_id
        await LabelService._check_workspace_membership_for_project(
            db, current_user, project_id, min_role=WorkspaceRole.EDITOR
        )

        await db.delete(label)
        await db.commit()

        await TaskService.invalidate_project_tasks_cache(project_id)

    @staticmethod
    async def assign_label_to_task(db: AsyncSession, current_user: User, task_id: uuid.UUID, label_id: uuid.UUID) -> Task:
        task = (await db.execute(
            select(Task).options(selectinload(Task.labels)).where(Task.id == task_id)
        )).scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        await LabelService._check_workspace_membership_for_project(
            db, current_user, task.project_id, min_role=WorkspaceRole.EDITOR
        )

        label = (await db.execute(select(Label).where(Label.id == label_id))).scalar_one_or_none()
        if not label:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Label not found")

        if label.project_id != task.project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Label does not belong to the same project as the task"
            )

        if label not in task.labels:
            task.labels.append(label)
            db.add(task)
            await db.commit()
            await db.refresh(task)
            await TaskService.invalidate_project_tasks_cache(task.project_id)

        return task

    @staticmethod
    async def remove_label_from_task(db: AsyncSession, current_user: User, task_id: uuid.UUID, label_id: uuid.UUID) -> Task:
        task = (await db.execute(
            select(Task).options(selectinload(Task.labels)).where(Task.id == task_id)
        )).scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        await LabelService._check_workspace_membership_for_project(
            db, current_user, task.project_id, min_role=WorkspaceRole.EDITOR
        )

        label = (await db.execute(select(Label).where(Label.id == label_id))).scalar_one_or_none()
        if not label:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Label not found")

        if label in task.labels:
            task.labels.remove(label)
            db.add(task)
            await db.commit()
            await db.refresh(task)
            await TaskService.invalidate_project_tasks_cache(task.project_id)

        return task
