from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.prompt import Prompt
    from app.models.scene import Scene


class CallLog(Base):
    __tablename__ = "call_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    prompt_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("prompts.id"),
    )
    scene_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("scenes.id"),
    )
    prompt_version: Mapped[str | None] = mapped_column(String(20))
    caller_system: Mapped[str | None] = mapped_column(String(100))
    caller_ip: Mapped[str | None] = mapped_column(String(45))
    input_variables: Mapped[dict | None] = mapped_column(JSONB)
    rendered_content: Mapped[str | None] = mapped_column(Text)
    token_count: Mapped[int | None] = mapped_column(Integer)
    response_time_ms: Mapped[int | None] = mapped_column(Integer)
    quality_score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        index=True,
    )

    # relationships
    prompt: Mapped[Prompt | None] = relationship(back_populates="call_logs")
    scene: Mapped[Scene | None] = relationship(back_populates="call_logs")
