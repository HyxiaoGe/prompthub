"""Seed default admin user for local development."""

import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User

ADMIN_EMAIL = "admin@prompthub.dev"
ADMIN_NAME = "Admin"
ADMIN_ROLE = "admin"
ADMIN_API_KEY = "ph-dev-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == ADMIN_EMAIL))
        if result.scalar_one_or_none() is not None:
            print(f"User '{ADMIN_EMAIL}' already exists, skipping.")
            return

        user = User(
            email=ADMIN_EMAIL,
            name=ADMIN_NAME,
            role=ADMIN_ROLE,
            api_key=ADMIN_API_KEY,
        )
        session.add(user)
        await session.commit()
        print(f"Created admin user: {ADMIN_EMAIL} (api_key={ADMIN_API_KEY})")


if __name__ == "__main__":
    asyncio.run(seed())
