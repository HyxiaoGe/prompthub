"""增加版本渲染配置快照

Revision ID: 1ec3d94a768f
Revises: 8b6e2b32f1c4
Create Date: 2026-07-10 00:00:01
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "1ec3d94a768f"
down_revision: str | Sequence[str] | None = "8b6e2b32f1c4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("prompt_versions", sa.Column("format", sa.String(length=20), nullable=True))
    op.add_column("prompt_versions", sa.Column("template_engine", sa.String(length=20), nullable=True))
    op.execute(
        """
        UPDATE prompt_versions AS version
        SET format = prompt.format,
            template_engine = prompt.template_engine
        FROM prompts AS prompt
        WHERE version.prompt_id = prompt.id
        """
    )
    op.alter_column(
        "prompt_versions",
        "format",
        nullable=False,
        server_default="text",
    )
    op.alter_column(
        "prompt_versions",
        "template_engine",
        nullable=False,
        server_default="jinja2",
    )


def downgrade() -> None:
    op.drop_column("prompt_versions", "template_engine")
    op.drop_column("prompt_versions", "format")
