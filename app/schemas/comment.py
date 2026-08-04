from datetime import datetime

from pydantic import UUID4, BaseModel, ConfigDict, Field


class CommentCreate(BaseModel):
    content: str = Field(min_length=1)


class CommentResponse(BaseModel):
    id: UUID4
    task_id: UUID4
    author_id: UUID4
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
