from __future__ import annotations

import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, Numeric, Integer, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.core import BaseModel, TimestampsMixin

if TYPE_CHECKING:
    from app.models.research import OpportunityScore, ResearchFinding
    from app.models.source import ProductSource
    from app.models.supplier import SupplierProduct
    from app.models.observation import MarketObservation


class Region(BaseModel):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    default_language: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    products: Mapped[list["Product"]] = relationship(back_populates="region", lazy="selectin")


class Product(BaseModel, TimestampsMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id"), nullable=False)

    external_key: Mapped[str | None] = mapped_column(String(256), nullable=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)

    brand: Mapped[str | None] = mapped_column(String(256), nullable=True)
    upc: Mapped[str | None] = mapped_column(String(64), nullable=True)
    asin: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ean: Mapped[str | None] = mapped_column(String(64), nullable=True)

    product_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    supplier_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))
    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))
    packaging_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))
    other_landed_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))

    suggested_retail_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))

    weight_kg: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=Decimal("0.0000"))
    is_lightweight: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_fragile: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    contains_liquid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    contains_batteries: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_electricity: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    us_warehouse_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    us_warehouse_verification_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="unverified"
    )
    us_warehouse_verification_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    estimated_delivery_days: Mapped[int] = mapped_column(Integer, nullable=True)

    amazon_fulfillment_suitable: Mapped[str] = mapped_column(
        String(32), nullable=False, default="needs_review"
    )
    amazon_compliance_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    trend_classification: Mapped[str] = mapped_column(
        String(32), nullable=False, default="insufficient_evidence"
    )
    viral_potential: Mapped[str] = mapped_column(String(16), nullable=False, default="low")

    primary_competition_level: Mapped[str] = mapped_column(
        String(16), nullable=False, default="unknown"
    )

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="candidate")

    region: Mapped["Region"] = relationship(back_populates="products", lazy="selectin")
    variants: Mapped[list["ProductVariant"]] = relationship(back_populates="product", lazy="selectin")
    sources: Mapped[list["ProductSource"]] = relationship(back_populates="product", lazy="selectin")
    supplier_products: Mapped[list["SupplierProduct"]] = relationship(back_populates="product", lazy="selectin")
    scores: Mapped[list["OpportunityScore"]] = relationship(
        "OpportunityScore", back_populates="product", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} name={self.name!r} region={self.region.code}>"


class ProductVariant(BaseModel, TimestampsMixin):
    __tablename__ = "product_variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)

    sku: Mapped[str | None] = mapped_column(String(128), nullable=True)
    name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    attributes: Mapped[str | None] = mapped_column(Text, nullable=True)

    supplier_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))
    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    product: Mapped["Product"] = relationship(back_populates="variants", lazy="selectin")


class ProductSource(BaseModel, TimestampsMixin):
    __tablename__ = "product_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)

    source_name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    retrieval_timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    raw_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_classification: Mapped[str] = mapped_column(String(32), nullable=False, default="unverified")
    observation_period: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    product: Mapped["Product"] = relationship(back_populates="sources", lazy="selectin")


class WatchlistStatus(BaseModel):
    __tablename__ = "watchlist_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
