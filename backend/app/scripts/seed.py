from __future__ import annotations

import asyncio
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.models.product import Region, WatchlistStatus
from app.settings import get_settings


async def main() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.postgres_dsn, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(_startup)

    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        await _ensure_defaults(session)

    await engine.dispose()


def _startup(connection) -> None:
    # migrations should handle schema; this is only a fallback helper.
    pass


async def _ensure_defaults(session: AsyncSession) -> None:
    region_result = await session.execute(select(Region).where(Region.code == "US"))
    if not region_result.scalar_one_or_none():
        region = Region(
            code="US",
            name="United States",
            currency_code="USD",
            default_language="en",
            is_primary=True,
        )
        session.add(region)

    status_codes = [
        ("researching", "Researching"),
        ("supplier_verification", "Supplier Verification"),
        ("sample_ordered", "Sample Ordered"),
        ("testing", "Testing"),
        ("approved", "Approved"),
        ("launched", "Launched"),
        ("paused", "Paused"),
        ("rejected", "Rejected"),
    ]
    for code, label in status_codes:
        existing = await session.execute(select(WatchlistStatus).where(WatchlistStatus.code == code))
        if not existing.scalar_one_or_none():
            session.add(WatchlistStatus(code=code, label=label))

    await session.commit()
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(main())
