from pydantic import UUID4, BaseModel, ConfigDict, Field


class LabelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    color: str | None = Field(default=None, max_length=50)


class LabelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    color: str | None = Field(default=None, max_length=50)


class LabelResponse(BaseModel):
    id: UUID4
    project_id: UUID4
    name: str
    color: str | None = None

    model_config = ConfigDict(from_attributes=True)
