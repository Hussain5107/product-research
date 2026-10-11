from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "regions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("currency_code", sa.String(length=8), nullable=False, server_default=sa.text("'USD'")),
        sa.Column("default_language", sa.String(length=16), nullable=False, server_default=sa.text("'en'")),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("region_id", sa.Integer(), nullable=False),
        sa.Column("external_key", sa.String(length=256), nullable=True),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=128), nullable=True),
        sa.Column("brand", sa.String(length=256), nullable=True),
        sa.Column("upc", sa.String(length=64), nullable=True),
        sa.Column("asin", sa.String(length=64), nullable=True),
        sa.Column("ean", sa.String(length=64), nullable=True),
        sa.Column("product_url", sa.String(length=2048), nullable=True),
        sa.Column("image_url", sa.String(length=2048), nullable=True),
        sa.Column("thumbnail_url", sa.String(length=2048), nullable=True),
        sa.Column("supplier_cost", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("shipping_cost", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("packaging_cost", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("other_landed_cost", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("suggested_retail_price", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("weight_kg", sa.Numeric(precision=10, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("is_lightweight", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_fragile", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("contains_liquid", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("contains_batteries", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("requires_electricity", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("us_warehouse_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("us_warehouse_verification_status", sa.String(length=32), nullable=False, server_default=sa.text("'unverified'")),
        sa.Column("us_warehouse_verification_note", sa.Text(), nullable=True),
        sa.Column("estimated_delivery_days", sa.Integer(), nullable=True),
        sa.Column("amazon_fulfillment_suitable", sa.String(length=32), nullable=False, server_default=sa.text("'needs_review'")),
        sa.Column("amazon_compliance_note", sa.Text(), nullable=True),
        sa.Column("trend_classification", sa.String(length=32), nullable=False, server_default=sa.text("'insufficient_evidence'")),
        sa.Column("viral_potential", sa.String(length=16), nullable=False, server_default=sa.text("'low'")),
        sa.Column("primary_competition_level", sa.String(length=16), nullable=False, server_default=sa.text("'unknown'")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'candidate'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"]),
    )

    op.create_table(
        "product_variants",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("sku", sa.String(length=128), nullable=True),
        sa.Column("name", sa.String(length=512), nullable=True),
        sa.Column("attributes", sa.Text(), nullable=True),
        sa.Column("supplier_cost", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("shipping_cost", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
    )

    op.create_table(
        "product_sources",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("source_name", sa.String(length=128), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("retrieval_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_value", sa.Text(), nullable=True),
        sa.Column("data_classification", sa.String(length=32), nullable=False, server_default=sa.text("'unverified'")),
        sa.Column("observation_period", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
    )

    op.create_table(
        "watchlist_status",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("platform", sa.String(length=128), nullable=False),
        sa.Column("website_url", sa.String(length=2048), nullable=True),
        sa.Column("supports_shopify", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("supports_automation", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provides_tracking", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("supports_returns", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("return_policy_note", sa.Text(), nullable=True),
        sa.Column("us_warehouse_capable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("us_warehouse_note", sa.Text(), nullable=True),
        sa.Column("reliability_status", sa.String(length=32), nullable=False, server_default=sa.text("'unassessed'")),
        sa.Column("reliability_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "supplier_products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("supplier_product_url", sa.String(length=2048), nullable=True),
        sa.Column("supplier_product_name", sa.String(length=1024), nullable=True),
        sa.Column("purchase_cost", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("shipping_cost", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("processing_fee", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("currency_code", sa.String(length=8), nullable=False, server_default=sa.text("'USD'")),
        sa.Column("warehouse_origin", sa.String(length=256), nullable=True),
        sa.Column("warehouse_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("warehouse_verification_status", sa.String(length=32), nullable=False, server_default=sa.text("'unverified'")),
        sa.Column("warehouse_verification_note", sa.Text(), nullable=True),
        sa.Column("stock_available", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("stock_quantity", sa.String(length=64), nullable=True),
        sa.Column("processing_time_days", sa.Integer(), nullable=True),
        sa.Column("delivery_estimate_days", sa.Integer(), nullable=True),
        sa.Column("shipping_service", sa.String(length=128), nullable=True),
        sa.Column("destination_zip", sa.String(length=16), nullable=True),
        sa.Column("evidence_status", sa.String(length=32), nullable=False, server_default=sa.text("'unverified'")),
        sa.Column("verification_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
    )

    op.create_table(
        "warehouse_inventory",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("supplier_product_id", sa.Integer(), nullable=False),
        sa.Column("region_code", sa.String(length=16), nullable=False),
        sa.Column("inventory_status", sa.String(length=64), nullable=False),
        sa.Column("quantity_text", sa.String(length=64), nullable=True),
        sa.Column("last_observed", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["supplier_product_id"], ["supplier_products.id"]),
    )

    op.create_table(
        "shipping_quotes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("supplier_product_id", sa.Integer(), nullable=False),
        sa.Column("destination_zip", sa.String(length=16), nullable=False),
        sa.Column("shipping_cost", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("currency_code", sa.String(length=8), nullable=False, server_default=sa.text("'USD'")),
        sa.Column("delivery_days_min", sa.Integer(), nullable=True),
        sa.Column("delivery_days_max", sa.Integer(), nullable=True),
        sa.Column("service_name", sa.String(length=128), nullable=True),
        sa.Column("is_us_origin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["supplier_product_id"], ["supplier_products.id"]),
    )

    op.create_table(
        "research_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("marketplace", sa.String(length=32), nullable=False, server_default=sa.text("'both'")),
        sa.Column("region_code", sa.String(length=16), nullable=False, server_default=sa.text("'US'")),
        sa.Column("status", sa.Enum("queued", "running", "completed", "partially_completed", "failed", "cancelled", name="research_status"), nullable=False, server_default=sa.text("'queued'")),
        sa.Column("mode", sa.String(length=64), nullable=False, server_default=sa.text("'automatic_discovery'")),
        sa.Column("user_query", sa.String(length=2048), nullable=True),
        sa.Column("categories", sa.String(length=512), nullable=True),
        sa.Column("filters_json", sa.JSON(), nullable=True),
        sa.Column("source_names", sa.String(length=512), nullable=True),
        sa.Column("candidates_discovered", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("candidates_rejected", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("products_analyzed", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("suppliers_checked", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("sources_checked_json", sa.JSON(), nullable=True),
        sa.Column("warnings", sa.JSON(), nullable=True),
        sa.Column("errors", sa.JSON(), nullable=True),
        sa.Column("current_stage", sa.String(length=64), nullable=True),
        sa.Column("progress_message", sa.String(length=512), nullable=True),
        sa.Column("estimated_api_cost_usd", sa.Numeric(precision=12, scale=6), nullable=False, server_default=sa.text("0.000000")),
        sa.Column("actual_api_cost_usd", sa.Numeric(precision=12, scale=6), nullable=False, server_default=sa.text("0.000000")),
        sa.Column("research_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("research_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "research_findings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("research_run_id", sa.Integer(), nullable=True),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("candidate_name", sa.String(length=512), nullable=True),
        sa.Column("candidate_description", sa.Text(), nullable=True),
        sa.Column("action", sa.String(length=32), nullable=False, server_default=sa.text("'keep'")),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["research_run_id"], ["research_runs.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
    )

    op.create_table(
        "opportunity_scores",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("research_run_id", sa.Integer(), nullable=True),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("marketplace", sa.String(length=32), nullable=False),
        sa.Column("total_score", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("confidence_score", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("weights_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("component_scores_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("missing_fields_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("normalization_method", sa.String(length=64), nullable=False, server_default=sa.text("'min_max'")),
        sa.Column("scoring_model_version", sa.String(length=32), nullable=False, server_default=sa.text("'1.0.0'")),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["research_run_id"], ["research_runs.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
    )

    op.create_table(
        "market_observations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("source_name", sa.String(length=128), nullable=False),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("metric_name", sa.String(length=128), nullable=False),
        sa.Column("value_text", sa.String(length=512), nullable=False),
        sa.Column("numeric_value", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("retrieval_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_classification", sa.String(length=32), nullable=False, server_default=sa.text("'unverified'")),
        sa.Column("period", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
    )

    op.create_table(
        "social_media_observations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("platform", sa.String(length=64), nullable=False),
        sa.Column("content_url", sa.String(length=2048), nullable=True),
        sa.Column("publication_date", sa.String(length=64), nullable=True),
        sa.Column("view_count_text", sa.String(length=64), nullable=True),
        sa.Column("view_count_numeric", sa.Integer(), nullable=True),
        sa.Column("like_count", sa.Integer(), nullable=True),
        sa.Column("comment_count", sa.Integer(), nullable=True),
        sa.Column("share_count", sa.Integer(), nullable=True),
        sa.Column("content_example_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("advertising_activity_indicators", sa.String(length=128), nullable=True),
        sa.Column("trend_direction", sa.String(length=32), nullable=False, server_default=sa.text("'unknown'")),
        sa.Column("retrieval_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_classification", sa.String(length=32), nullable=False, server_default=sa.text("'unverified'")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
    )

    op.create_table(
        "competitors",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("source_name", sa.String(length=128), nullable=False),
        sa.Column("competitor_url", sa.String(length=2048), nullable=True),
        sa.Column("asin", sa.String(length=64), nullable=True),
        sa.Column("brand", sa.String(length=256), nullable=True),
        sa.Column("title", sa.String(length=1024), nullable=True),
        sa.Column("selling_price", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("review_count", sa.Integer(), nullable=True),
        sa.Column("rating", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("sales_rank_text", sa.String(length=256), nullable=True),
        sa.Column("estimated_sales_text", sa.String(length=128), nullable=True),
        sa.Column("differentiation", sa.Text(), nullable=True),
        sa.Column("data_classification", sa.String(length=32), nullable=False, server_default=sa.text("'unverified'")),
        sa.Column("retrieval_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
    )

    op.create_table(
        "financial_scenarios",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("research_run_id", sa.Integer(), nullable=True),
        sa.Column("scenario_name", sa.String(length=64), nullable=False),
        sa.Column("selling_price", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("purchase_cost", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("shipping_cost", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("packaging_cost", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("other_landed_cost", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("payment_processing_rate", sa.Numeric(precision=6, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("payment_processing_fixed", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("marketplace_fee_rate", sa.Numeric(precision=6, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("marketplace_fee_fixed", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("expected_return_rate", sa.Numeric(precision=6, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("customer_acquisition_cost", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("advertising_rate", sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column("landed_fulfillment_cost", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("variable_costs", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("contribution_before_advertising", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("contribution_after_advertising", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("contribution_margin_after_advertising", sa.Numeric(precision=6, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("break_even_cac", sa.Numeric(precision=12, scale=4), nullable=False, server_default=sa.text("0.0000")),
        sa.Column("break_even_roas", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("assumptions_json", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["research_run_id"], ["research_runs.id"]),
    )

    op.execute(
        sa.text(
            "INSERT INTO watchlist_status (code, label) VALUES "
            "('researching', 'Researching'), "
            "('supplier_verification', 'Supplier Verification'), "
            "('sample_ordered', 'Sample Ordered'), "
            "('testing', 'Testing'), "
            "('approved', 'Approved'), "
            "('launched', 'Launched'), "
            "('paused', 'Paused'), "
            "('rejected', 'Rejected')"
        )
    )

    op.execute(
        sa.text(
            "INSERT INTO regions (code, name, currency_code, is_primary) VALUES "
            "('US', 'United States', 'USD', true)"
        )
    )
