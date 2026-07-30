import uuid
from sqlalchemy import String, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TaskLabel(Base):
    __tablename__ = "task_labels"

    task_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    label_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True)


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    color: Mapped[str | None] = mapped_column(String(50), nullable=True)

    project = relationship("Project", back_populates="labels")
    tasks = relationship("Task", secondary="task_labels", back_populates="labels")
