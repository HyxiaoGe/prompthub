from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.prompt import Prompt
    from app.models.scene import Scene
    from app.models.version import PromptVersion


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), server_default="editor")
    api_key: Mapped[str | None] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )

    # relationships
    created_projects: Mapped[list[Project]] = relationship(
        back_populates="creator",
        foreign_keys="Project.created_by",
    )
    created_prompts: Mapped[list[Prompt]] = relationship(
        back_populates="creator",
        foreign_keys="Prompt.created_by",
    )
    created_versions: Mapped[list[PromptVersion]] = relationship(
        back_populates="creator",
        foreign_keys="PromptVersion.created_by",
    )
    created_scenes: Mapped[list[Scene]] = relationship(
        back_populates="creator",
        foreign_keys="Scene.created_by",
    )
