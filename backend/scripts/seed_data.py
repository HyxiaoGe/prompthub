"""Seed default admin user for local development."""

import asyncio
import os

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User

ADMIN_EMAIL = "admin@prompthub.dev"
ADMIN_NAME = "Admin"
ADMIN_ROLE = "admin"


def get_admin_api_key() -> str:
    api_key = os.environ.get("PROMPTHUB_SEED_ADMIN_API_KEY")
    if not api_key:
        raise RuntimeError("PROMPTHUB_SEED_ADMIN_API_KEY environment variable is required")
    return api_key


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == ADMIN_EMAIL))
        if result.scalar_one_or_none() is not None:
            print(f"User '{ADMIN_EMAIL}' already exists, skipping.")
            return

        api_key = get_admin_api_key()
        user = User(
            email=ADMIN_EMAIL,
            name=ADMIN_NAME,
            role=ADMIN_ROLE,
            api_key=api_key,
        )
        session.add(user)
        await session.commit()
        print(f"Created admin user: {ADMIN_EMAIL}")


if __name__ == "__main__":
    asyncio.run(seed())
