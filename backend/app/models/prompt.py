from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.call_log import CallLog
    from app.models.project import Project
    from app.models.prompt_ref import PromptRef
    from app.models.user import User
    from app.models.version import PromptVersion


class Prompt(Base):
    __tablename__ = "prompts"
    __table_args__ = (
        UniqueConstraint("project_id", "slug", name="uq_prompts_project_slug"),
        Index("ix_prompts_tags", "tags", postgresql_using="gin"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    format: Mapped[str] = mapped_column(String(20), server_default="text")
    template_engine: Mapped[str] = mapped_column(String(20), server_default="jinja2")
    variables: Mapped[dict | None] = mapped_column(JSONB, server_default="[]")
    tags: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), server_default="{}"
    )
    category: Mapped[str | None] = mapped_column(String(100))
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_shared: Mapped[bool] = mapped_column(Boolean, server_default="false")
    current_version: Mapped[str] = mapped_column(
        String(20), server_default="1.0.0"
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, index=True,
    )

    # relationships
    project: Mapped[Project] = relationship(back_populates="prompts")
    creator: Mapped[User | None] = relationship(
        back_populates="created_prompts",
        foreign_keys=[created_by],
    )
    versions: Mapped[list[PromptVersion]] = relationship(
        back_populates="prompt",
        cascade="all, delete-orphan",
    )
    source_refs: Mapped[list[PromptRef]] = relationship(
        back_populates="source_prompt",
        foreign_keys="PromptRef.source_prompt_id",
        cascade="all, delete-orphan",
    )
    target_refs: Mapped[list[PromptRef]] = relationship(
        back_populates="target_prompt",
        foreign_keys="PromptRef.target_prompt_id",
        cascade="all, delete-orphan",
    )
    call_logs: Mapped[list[CallLog]] = relationship(back_populates="prompt")
