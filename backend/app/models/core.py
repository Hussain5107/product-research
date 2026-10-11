from __future__ import annotations

import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class BaseModel(DeclarativeBase):
    pass


class TimestampsMixin:
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        server_default=func.now(),
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )


def utc_now() -> datetime.datetime:
    return datetime.datetime.utcnow()
