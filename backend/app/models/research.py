from __future__ import annotations

import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, Numeric, Integer, Boolean, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.core import BaseModel, TimestampsMixin

if TYPE_CHECKING:
    from app.models.product import Product


class ResearchStatus(str, PyEnum):
    queued = "queued"
    running = "running"
    completed = "completed"
    partially_completed = "partially_completed"
    failed = "failed"
    cancelled = "cancelled"


class ResearchRun(BaseModel, TimestampsMixin):
    __tablename__ = "research_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    marketplace: Mapped[str] = mapped_column(String(32), nullable=False, default="both")
    region_code: Mapped[str] = mapped_column(String(16), nullable=False, default="US")

    status: Mapped[ResearchStatus] = mapped_column(
        Enum(ResearchStatus, name="research_status"),
        nullable=False,
        default=ResearchStatus.queued,
    )

    mode: Mapped[str] = mapped_column(String(64), nullable=False, default="automatic_discovery")
    user_query: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    categories: Mapped[str | None] = mapped_column(String(512), nullable=True)
    filters_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    source_names: Mapped[str | None] = mapped_column(String(512), nullable=True)

    candidates_discovered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    candidates_rejected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    products_analyzed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    suppliers_checked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    sources_checked_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    warnings: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    errors: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    current_stage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    progress_message: Mapped[str | None] = mapped_column(String(512), nullable=True)

    estimated_api_cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(12, 6), nullable=False, default=Decimal("0.000000")
    )
    actual_api_cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(12, 6), nullable=False, default=Decimal("0.000000")
    )

    research_start: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    research_end: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    findings: Mapped[list["ResearchFinding"]] = relationship(back_populates="research_run", lazy="selectin")
    scores: Mapped[list["OpportunityScore"]] = relationship(back_populates="research_run", lazy="selectin")


class ResearchFinding(BaseModel, TimestampsMixin):
    __tablename__ = "research_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    research_run_id: Mapped[int | None] = mapped_column(ForeignKey("research_runs.id"), nullable=True)

    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)

    candidate_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    candidate_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    action: Mapped[str] = mapped_column(String(32), nullable=False, default="keep")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    research_run: Mapped["ResearchRun"] = relationship(back_populates="findings", lazy="selectin")


class OpportunityScore(BaseModel, TimestampsMixin):
    __tablename__ = "opportunity_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    research_run_id: Mapped[int | None] = mapped_column(ForeignKey("research_runs.id"), nullable=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)

    marketplace: Mapped[str] = mapped_column(String(32), nullable=False)

    total_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confidence_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    weights_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    component_scores_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    missing_fields_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    normalization_method: Mapped[str] = mapped_column(String(64), nullable=False, default="min_max")
    scoring_model_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    calculated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    research_run: Mapped["ResearchRun"] = relationship(back_populates="scores", lazy="selectin")
    product: Mapped["Product"] = relationship(back_populates="scores", lazy="selectin")


class MarketObservation(BaseModel, TimestampsMixin):
    __tablename__ = "market_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    product_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    source_name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    metric_name: Mapped[str] = mapped_column(String(128), nullable=False)
    value_text: Mapped[str] = mapped_column(String(512), nullable=False)
    numeric_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)

    retrieval_timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_classification: Mapped[str] = mapped_column(String(32), nullable=False, default="unverified")
    period: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class SocialMediaObservation(BaseModel, TimestampsMixin):
    __tablename__ = "social_media_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    product_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    content_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    publication_date: Mapped[str | None] = mapped_column(String(64), nullable=True)
    view_count_text: Mapped[str | None] = mapped_column(String(64), nullable=True)
    view_count_numeric: Mapped[int | None] = mapped_column(Integer, nullable=True)
    like_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comment_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    share_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_example_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    advertising_activity_indicators: Mapped[str | None] = mapped_column(String(128), nullable=True)
    trend_direction: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")

    retrieval_timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_classification: Mapped[str] = mapped_column(String(32), nullable=False, default="unverified")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class Competitor(BaseModel, TimestampsMixin):
    __tablename__ = "competitors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    product_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    source_name: Mapped[str] = mapped_column(String(128), nullable=False)
    competitor_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    asin: Mapped[str | None] = mapped_column(String(64), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(256), nullable=True)
    title: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    selling_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    sales_rank_text: Mapped[str | None] = mapped_column(String(256), nullable=True)
    estimated_sales_text: Mapped[str | None] = mapped_column(String(128), nullable=True)
    differentiation: Mapped[str | None] = mapped_column(Text, nullable=True)

    data_classification: Mapped[str] = mapped_column(String(32), nullable=False, default="unverified")
    retrieval_timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class FinancialScenario(BaseModel, TimestampsMixin):
    __tablename__ = "financial_scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    product_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    research_run_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    scenario_name: Mapped[str] = mapped_column(String(64), nullable=False)

    selling_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))
    purchase_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))
    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))
    packaging_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))
    other_landed_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))

    payment_processing_rate: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False, default=Decimal("0.0000"))
    payment_processing_fixed: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))
    marketplace_fee_rate: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False, default=Decimal("0.0000"))
    marketplace_fee_fixed: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))
    expected_return_rate: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False, default=Decimal("0.0000"))

    customer_acquisition_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))
    advertising_rate: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)

    landed_fulfillment_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))
    variable_costs: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))
    contribution_before_advertising: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False, default=Decimal("0.0000")
    )
    contribution_after_advertising: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False, default=Decimal("0.0000")
    )
    contribution_margin_after_advertising: Mapped[Decimal] = mapped_column(
        Numeric(6, 4), nullable=False, default=Decimal("0.0000")
    )
    break_even_cac: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))
    break_even_roas: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)

    assumptions_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
