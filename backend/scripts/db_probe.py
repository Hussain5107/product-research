from __future__ import annotations

import asyncio
import selectors

import psycopg

CANDIDATES = [
    ("localhost:5432/producthunter", "producthunter", "producthunter_local_dev_password"),
    ("localhost:5432/postgres", "postgres", "postgres"),
    ("localhost:5432/postgres", "postgres", "admin"),
    ("localhost:5432/postgres", "producthunter", "producthunter_local_dev_password"),
]


def _selector_loop() -> asyncio.AbstractEventLoop:
    return asyncio.SelectorEventLoop(selectors.SelectSelector())


async def probe() -> None:
    print("Probing local PostgreSQL candidates (SelectorEventLoop)...")
    for dsn_suffix, user, password in CANDIDATES:
        dsn = f"postgresql://{user}:{password}@{dsn_suffix}"
        try:
            conn = await psycopg.AsyncConnection.connect(dsn, connect_timeout=3)
            async with conn:
                async with conn.cursor() as cur:
                    await cur.execute("select version()")
                    row = await cur.fetchone()
            print(f"OK    {dsn_suffix} as {user} -> {row[0][:60]}")
        except Exception as exc:
            print(f"FAIL  {dsn_suffix} as {user} -> {type(exc).__name__}: {str(exc)[:120]}")


if __name__ == "__main__":
    asyncio.run(probe(), loop_factory=_selector_loop)
