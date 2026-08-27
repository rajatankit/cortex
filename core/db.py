"""
core/db.py

Shared async Postgres connection pool for CORTEX tools that need to
read real Battle Crown data (the same Neon database the Next.js app
uses via Prisma).

IMPORTANT:
- This uses the SAME DATABASE_URL as the Next.js app for now (per
  explicit instruction). That means these tools have WRITE access
  to production data at the database-user level, even though every
  query below is read-only (SELECT). Nothing here issues an
  INSERT/UPDATE/DELETE. When convenient, replace DATABASE_URL with a
  read-only Neon role/connection string as an extra safety net -
  no code changes needed elsewhere, just the env var.
- Prisma's `User` model has no @map on its fields, so Postgres
  column names are the exact camelCase names Prisma declares
  (e.g. "depositWallet", not deposit_wallet). Because Postgres
  folds unquoted identifiers to lowercase, every camelCase
  identifier (table AND column) MUST be double-quoted in raw SQL,
  or Postgres will fail to find it / silently match the wrong
  (legacy lowercase) table.
"""

from __future__ import annotations

import os

import asyncpg

DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "CORTEX needs this to read real Battle Crown data."
    )

# Neon requires SSL; asyncpg needs this hint when the URL doesn't
# already carry ?sslmode=require.
_DSN = DATABASE_URL
if "sslmode=" not in _DSN:
    _DSN += ("&" if "?" in _DSN else "?") + "sslmode=require"

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """
    Lazily create (once) and return the shared connection pool.
    Reused across every tool call for the lifetime of the process.
    """
    global _pool

    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=_DSN,
            min_size=1,
            max_size=5,
            command_timeout=10,
        )

    return _pool


async def fetch(query: str, *args) -> list[asyncpg.Record]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)


async def fetchrow(query: str, *args) -> asyncpg.Record | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)