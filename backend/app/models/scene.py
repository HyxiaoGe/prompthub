from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.call_log import CallLog
    from app.models.project import Project
    from app.models.user import User


class Scene(Base):
    __tablename__ = "scenes"
    __table_args__ = (
        UniqueConstraint("project_id", "slug", name="uq_scenes_project_slug"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    pipeline: Mapped[dict] = mapped_column(JSONB, nullable=False)
    merge_strategy: Mapped[str] = mapped_column(
        String(20), server_default="concat"
    )
    separator: Mapped[str] = mapped_column(String(50), server_default="'\\n\\n'")
    output_format: Mapped[str | None] = mapped_column(String(50))
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

    # relationships
    project: Mapped[Project] = relationship(back_populates="scenes")
    creator: Mapped[User | None] = relationship(
        back_populates="created_scenes",
        foreign_keys=[created_by],
    )
    call_logs: Mapped[list[CallLog]] = relationship(back_populates="scene")
