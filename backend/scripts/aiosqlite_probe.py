from __future__ import annotations

import asyncio

import aiosqlite


async def main() -> None:
    async with aiosqlite.connect("producthunter_aiosqlite_probe.db") as db:
        cursor = await db.execute("select 1")
        print(await cursor.fetchone())


asyncio.run(main())
