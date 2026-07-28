import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.schemas.workspace import WorkspaceCreate, WorkspaceMemberAdd, WorkspaceUpdate


class WorkspaceService:
    @staticmethod
    async def create_workspace(
        db: AsyncSession, current_user: User, ws_in: WorkspaceCreate
    ) -> Workspace:
        workspace = Workspace(
            name=ws_in.name,
            owner_id=current_user.id,
        )
        db.add(workspace)
        await db.flush()

        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=current_user.id,
            role=WorkspaceRole.OWNER,
        )
        db.add(member)
        await db.commit()
        await db.refresh(workspace)
        return workspace

    @staticmethod
    async def list_my_workspaces(
        db: AsyncSession, current_user: User
    ) -> list[Workspace]:
        stmt = (
            select(Workspace)
            .join(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
            .where(WorkspaceMember.user_id == current_user.id)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_workspace(
        db: AsyncSession, current_user: User, workspace_id: uuid.UUID
    ) -> Workspace:
        stmt = (
            select(Workspace)
            .join(WorkspaceMember, Workspace.id == WorkspaceMember.workspace_id)
            .where(
                Workspace.id == workspace_id,
                WorkspaceMember.user_id == current_user.id,
            )
        )
        result = await db.execute(stmt)
        workspace = result.scalar_one_or_none()
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found or access denied",
            )
        return workspace

    @staticmethod
    async def update_workspace(
        db: AsyncSession, current_user: User, workspace_id: uuid.UUID, ws_in: WorkspaceUpdate
    ) -> Workspace:
        stmt = select(Workspace).where(Workspace.id == workspace_id)
        result = await db.execute(stmt)
        workspace = result.scalar_one_or_none()

        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
            )
        if workspace.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only workspace owner can perform this action",
            )

        workspace.name = ws_in.name
        db.add(workspace)
        await db.commit()
        await db.refresh(workspace)
        return workspace

    @staticmethod
    async def delete_workspace(
        db: AsyncSession, current_user: User, workspace_id: uuid.UUID
    ) -> None:
        stmt = select(Workspace).where(Workspace.id == workspace_id)
        result = await db.execute(stmt)
        workspace = result.scalar_one_or_none()

        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
            )
        if workspace.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only workspace owner can delete workspace",
            )

        await db.delete(workspace)
        await db.commit()
        return None

    @staticmethod
    async def add_member(
        db: AsyncSession,
        current_user: User,
        workspace_id: uuid.UUID,
        member_in: WorkspaceMemberAdd,
    ) -> WorkspaceMember:
        stmt = select(Workspace).where(Workspace.id == workspace_id)
        result = await db.execute(stmt)
        workspace = result.scalar_one_or_none()

        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
            )
        if workspace.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only workspace owner can add members",
            )

        user_stmt = select(User).where(User.id == member_in.user_id)
        target_user = (await db.execute(user_stmt)).scalar_one_or_none()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found"
            )

        mem_stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == member_in.user_id,
        )
        existing_mem = (await db.execute(mem_stmt)).scalar_one_or_none()
        if existing_mem:
            existing_mem.role = member_in.role
            db.add(existing_mem)
            await db.commit()
            await db.refresh(existing_mem)
            return existing_mem

        new_mem = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=member_in.user_id,
            role=member_in.role,
        )
        db.add(new_mem)
        await db.commit()
        await db.refresh(new_mem)
        return new_mem

    @staticmethod
    async def remove_member(
        db: AsyncSession, current_user: User, workspace_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        stmt = select(Workspace).where(Workspace.id == workspace_id)
        result = await db.execute(stmt)
        workspace = result.scalar_one_or_none()

        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found"
            )
        if workspace.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only workspace owner can remove members",
            )

        if user_id == workspace.owner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove owner from workspace",
            )

        mem_stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        mem = (await db.execute(mem_stmt)).scalar_one_or_none()
        if not mem:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Member not found in workspace"
            )

        await db.delete(mem)
        await db.commit()
        return None
