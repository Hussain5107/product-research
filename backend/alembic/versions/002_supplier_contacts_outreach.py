from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002_supplier_contacts_outreach"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "supplier_contacts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("contact_name", sa.String(length=256), nullable=True),
        sa.Column("role_title", sa.String(length=256), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("whatsapp", sa.String(length=64), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("country", sa.String(length=128), nullable=True),
        sa.Column("language", sa.String(length=64), nullable=True),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("data_classification", sa.String(length=32), nullable=False, server_default=sa.text("'user_supplied'")),
        sa.Column("verification_status", sa.String(length=32), nullable=False, server_default=sa.text("'unverified'")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"]),
    )
    op.create_index("ix_supplier_contacts_supplier_id", "supplier_contacts", ["supplier_id"])
    op.create_index("ix_supplier_contacts_email", "supplier_contacts", ["email"])
    op.create_index("ix_supplier_contacts_whatsapp", "supplier_contacts", ["whatsapp"])

    op.create_table(
        "supplier_outreach",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=True),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("channel", sa.String(length=32), nullable=False, server_default=sa.text("'email'")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("subject", sa.String(length=512), nullable=True),
        sa.Column("message_body", sa.Text(), nullable=False),
        sa.Column("negotiation_goal", sa.String(length=512), nullable=True),
        sa.Column("requested_terms_json", sa.JSON(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("external_message_id", sa.String(length=256), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"]),
        sa.ForeignKeyConstraint(["contact_id"], ["supplier_contacts.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
    )
    op.create_index("ix_supplier_outreach_supplier_id", "supplier_outreach", ["supplier_id"])
    op.create_index("ix_supplier_outreach_status", "supplier_outreach", ["status"])


def downgrade() -> None:
    op.drop_index("ix_supplier_outreach_status", table_name="supplier_outreach")
    op.drop_index("ix_supplier_outreach_supplier_id", table_name="supplier_outreach")
    op.drop_table("supplier_outreach")
    op.drop_index("ix_supplier_contacts_whatsapp", table_name="supplier_contacts")
    op.drop_index("ix_supplier_contacts_email", table_name="supplier_contacts")
    op.drop_index("ix_supplier_contacts_supplier_id", table_name="supplier_contacts")
    op.drop_table("supplier_contacts")
