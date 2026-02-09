from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.prompt import Prompt


class PromptRef(Base):
    __tablename__ = "prompt_refs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    source_prompt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_prompt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id"),
    )
    target_project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id"),
    )
    ref_type: Mapped[str] = mapped_column(String(20), nullable=False)
    override_config: Mapped[dict | None] = mapped_column(
        JSONB, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )

    # relationships — use foreign_keys to disambiguate
    source_prompt: Mapped[Prompt] = relationship(
        back_populates="source_refs",
        foreign_keys=[source_prompt_id],
    )
    target_prompt: Mapped[Prompt] = relationship(
        back_populates="target_refs",
        foreign_keys=[target_prompt_id],
    )
    source_project: Mapped[Project | None] = relationship(
        foreign_keys=[source_project_id],
    )
    target_project: Mapped[Project | None] = relationship(
        foreign_keys=[target_project_id],
    )
