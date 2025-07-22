import os
import asyncpg
from dotenv import load_dotenv

from typing import AsyncGenerator

# Load environment variables from .env
load_dotenv()

DATABASE_URL = os.environ.get("POSTGRES_URL")

if not DATABASE_URL:
    raise RuntimeError("POSTGRES_URL must be set in environment")

# PUBLIC_INTERFACE
async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    """Yields a connection from asyncpg's connection pool."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        await conn.close()
