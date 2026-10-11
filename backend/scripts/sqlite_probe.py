from __future__ import annotations

import asyncio

from app.database import engine


async def main() -> None:
    async with engine.connect() as connection:
        result = await connection.exec_driver_sql("select 1")
        print(result.fetchone())


asyncio.run(main())
