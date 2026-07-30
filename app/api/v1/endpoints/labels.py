import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.label import LabelResponse, LabelUpdate
from app.services.label_service import LabelService


router = APIRouter(prefix="/labels", tags=["Labels"])


@router.patch("/{id}", response_model=LabelResponse)
async def update_label(
    id: uuid.UUID,
    label_in: LabelUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await LabelService.update_label(db, current_user, id, label_in)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label(
    id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await LabelService.delete_label(db, current_user, id)
