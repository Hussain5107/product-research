from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.core import BaseModel, TimestampsMixin


class EmailAccount(BaseModel, TimestampsMixin):
    __tablename__ = "email_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(String(128), nullable=False, default="Primary Email")
    sender_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    sender_email: Mapped[str] = mapped_column(String(320), nullable=False)
    smtp_host: Mapped[str] = mapped_column(String(256), nullable=False)
    smtp_port: Mapped[int] = mapped_column(Integer, nullable=False, default=587)
    smtp_username: Mapped[str | None] = mapped_column(String(320), nullable=True)
    smtp_password: Mapped[str | None] = mapped_column(Text, nullable=True)
    use_tls: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
