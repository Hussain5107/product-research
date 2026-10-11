from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool

from app.database import engine
from app.models.core import BaseModel

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = BaseModel.metadata


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


# psycopg async mode cannot run on Windows' default ProactorEventLoop.
try:
    asyncio.run(
        run_async_migrations(),
        loop_factory=lambda: asyncio.SelectorEventLoop(__import__("selectors").SelectSelector()),
    )
except TypeError:  # Python < 3.13 has no loop_factory
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_async_migrations())
