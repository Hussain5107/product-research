from __future__ import annotations

import datetime

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.core import BaseModel, TimestampsMixin


class ConnectorConfig(BaseModel, TimestampsMixin):
    __tablename__ = "connector_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)
    connector_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="planned")
    base_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_checked_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AutomationJob(BaseModel, TimestampsMixin):
    __tablename__ = "automation_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    job_type: Mapped[str] = mapped_column(String(64), nullable=False, default="research")
    schedule_label: Mapped[str] = mapped_column(String(128), nullable=False, default="manual")
    query: Mapped[str] = mapped_column(String(2048), nullable=False)
    filters_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="paused")
    last_run_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_note: Mapped[str | None] = mapped_column(String(512), nullable=True)
    last_result_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class ExportRecord(BaseModel, TimestampsMixin):
    __tablename__ = "export_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    export_type: Mapped[str] = mapped_column(String(32), nullable=False)
    dataset: Mapped[str] = mapped_column(String(64), nullable=False)
    filename: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="created")
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
