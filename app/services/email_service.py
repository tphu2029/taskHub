import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

logger = logging.getLogger(__name__)


async def send_task_assignment_email(user_id: uuid.UUID, task_title: str, db: AsyncSession) -> None:
    try:
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if user and user.email:
          
            logger.info(
                f"[EMAIL NOTIFICATION] Task '{task_title}' assigned to {user.email} (User ID: {user_id})"
            )
        
    except Exception as e:  
        logger.error(f"Failed to send email notification to user {user_id}: {e}")
