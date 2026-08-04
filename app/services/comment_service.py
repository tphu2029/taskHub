import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.models.project import Project
from app.models.task import Task
from app.models.user import User, UserRole
from app.models.workspace import WorkspaceMember
from app.schemas.comment import CommentCreate


class CommentService:
    @staticmethod
    async def _check_workspace_membership_for_task(db: AsyncSession, current_user: User, task_id: uuid.UUID) -> Task:
        task = (await db.execute(select(Task).where(Task.id == task_id))).scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

        if current_user.role == UserRole.ADMIN:
            return task

        project = (await db.execute(select(Project).where(Project.id == task.project_id))).scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        member = (await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == project.workspace_id,
                WorkspaceMember.user_id == current_user.id
            )
        )).scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions in the workspace for this task"
            )
        return task

    @staticmethod
    async def create_comment(db: AsyncSession, current_user: User, task_id: uuid.UUID, comment_in: CommentCreate) -> Comment:
        await CommentService._check_workspace_membership_for_task(db, current_user, task_id)

        new_comment = Comment(
            task_id=task_id,
            author_id=current_user.id,
            content=comment_in.content,
        )
        db.add(new_comment)
        await db.commit()
        await db.refresh(new_comment)
        return new_comment

    @staticmethod
    async def get_comments_by_task(db: AsyncSession, current_user: User, task_id: uuid.UUID) -> list[Comment]:
        await CommentService._check_workspace_membership_for_task(db, current_user, task_id)

        stmt = select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def delete_comment(db: AsyncSession, current_user: User, comment_id: uuid.UUID) -> None:
        comment = (await db.execute(select(Comment).where(Comment.id == comment_id))).scalar_one_or_none()
        if not comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

        await CommentService._check_workspace_membership_for_task(db, current_user, comment.task_id)

        if comment.author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the author can delete this comment"
            )

        await db.delete(comment)
        await db.commit()
