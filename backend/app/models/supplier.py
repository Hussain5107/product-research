from __future__ import annotations

import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, Numeric, Integer, Boolean, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.core import BaseModel, TimestampsMixin

if TYPE_CHECKING:
    from app.models.product import Product


class Supplier(BaseModel, TimestampsMixin):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    platform: Mapped[str] = mapped_column(String(128), nullable=False)
    website_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    supports_shopify: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_automation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    provides_tracking: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_returns: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    return_policy_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    us_warehouse_capable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    us_warehouse_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    reliability_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="unassessed"
    )
    reliability_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    supplier_products: Mapped[list["SupplierProduct"]] = relationship(
        back_populates="supplier", lazy="selectin"
    )
    contacts: Mapped[list["SupplierContact"]] = relationship(
        back_populates="supplier", lazy="selectin"
    )
    outreach_messages: Mapped[list["SupplierOutreach"]] = relationship(
        back_populates="supplier", lazy="selectin"
    )


class SupplierProduct(BaseModel, TimestampsMixin):
    __tablename__ = "supplier_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)

    supplier_product_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    supplier_product_name: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    purchase_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))
    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))
    processing_fee: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))
    currency_code: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")

    warehouse_origin: Mapped[str | None] = mapped_column(String(256), nullable=True)
    warehouse_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    warehouse_verification_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="unverified"
    )
    warehouse_verification_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    stock_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    stock_quantity: Mapped[str | None] = mapped_column(String(64), nullable=True)

    processing_time_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    delivery_estimate_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shipping_service: Mapped[str | None] = mapped_column(String(128), nullable=True)
    destination_zip: Mapped[str | None] = mapped_column(String(16), nullable=True)

    evidence_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="unverified"
    )
    verification_timestamp: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    supplier: Mapped["Supplier"] = relationship(back_populates="supplier_products", lazy="selectin")
    product: Mapped["Product"] = relationship("Product", lazy="selectin")

    def __repr__(self) -> str:
        return f"<SupplierProduct id={self.id} supplier={self.supplier.name}>"


class WarehouseInventory(BaseModel, TimestampsMixin):
    __tablename__ = "warehouse_inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    supplier_product_id: Mapped[int] = mapped_column(ForeignKey("supplier_products.id"), nullable=False)
    region_code: Mapped[str] = mapped_column(String(16), nullable=False)

    inventory_status: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity_text: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_observed: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class ShippingQuote(BaseModel, TimestampsMixin):
    __tablename__ = "shipping_quotes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    supplier_product_id: Mapped[int] = mapped_column(ForeignKey("supplier_products.id"), nullable=False)
    destination_zip: Mapped[str] = mapped_column(String(16), nullable=False)

    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=Decimal("0.0000"))
    currency_code: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    delivery_days_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    delivery_days_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    service_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_us_origin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class SupplierContact(BaseModel, TimestampsMixin):
    __tablename__ = "supplier_contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)

    contact_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    role_title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    whatsapp: Mapped[str | None] = mapped_column(String(64), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    country: Mapped[str | None] = mapped_column(String(128), nullable=True)
    language: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    data_classification: Mapped[str] = mapped_column(String(32), nullable=False, default="user_supplied")
    verification_status: Mapped[str] = mapped_column(String(32), nullable=False, default="unverified")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    supplier: Mapped["Supplier"] = relationship(back_populates="contacts", lazy="selectin")


class SupplierOutreach(BaseModel, TimestampsMixin):
    __tablename__ = "supplier_outreach"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("supplier_contacts.id"), nullable=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)

    channel: Mapped[str] = mapped_column(String(32), nullable=False, default="email")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    subject: Mapped[str | None] = mapped_column(String(512), nullable=True)
    message_body: Mapped[str] = mapped_column(Text, nullable=False)
    negotiation_goal: Mapped[str | None] = mapped_column(String(512), nullable=True)
    requested_terms_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sent_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    external_message_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    supplier: Mapped["Supplier"] = relationship(back_populates="outreach_messages", lazy="selectin")
