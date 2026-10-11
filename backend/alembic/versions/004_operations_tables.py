from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "004_operations_tables"
down_revision: Union[str, None] = "003_email_accounts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "connector_configs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=256), nullable=False),
        sa.Column("connector_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'planned'")),
        sa.Column("base_url", sa.String(length=2048), nullable=True),
        sa.Column("api_key", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "automation_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("job_type", sa.String(length=64), nullable=False, server_default=sa.text("'research'")),
        sa.Column("schedule_label", sa.String(length=128), nullable=False, server_default=sa.text("'manual'")),
        sa.Column("query", sa.String(length=2048), nullable=False),
        sa.Column("filters_json", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'paused'")),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_note", sa.String(length=512), nullable=True),
        sa.Column("last_result_json", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "export_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("export_type", sa.String(length=32), nullable=False),
        sa.Column("dataset", sa.String(length=64), nullable=False),
        sa.Column("filename", sa.String(length=256), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'created'")),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("export_records")
    op.drop_table("automation_jobs")
    op.drop_table("connector_configs")
