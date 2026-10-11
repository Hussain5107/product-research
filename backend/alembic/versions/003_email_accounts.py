from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003_email_accounts"
down_revision: Union[str, None] = "002_supplier_contacts_outreach"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "email_accounts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False, server_default=sa.text("'Primary Email'")),
        sa.Column("sender_name", sa.String(length=256), nullable=True),
        sa.Column("sender_email", sa.String(length=320), nullable=False),
        sa.Column("smtp_host", sa.String(length=256), nullable=False),
        sa.Column("smtp_port", sa.Integer(), nullable=False, server_default=sa.text("587")),
        sa.Column("smtp_username", sa.String(length=320), nullable=True),
        sa.Column("smtp_password", sa.Text(), nullable=True),
        sa.Column("use_tls", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("email_accounts")
