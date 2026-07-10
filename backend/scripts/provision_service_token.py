"""安全创建或轮换项目级服务令牌。"""

import argparse
import asyncio
import os
from dataclasses import dataclass, field

from app.database import AsyncSessionLocal
from app.services.service_token_service import READ_SCOPE, provision_service_token


@dataclass(frozen=True)
class ProvisionConfig:
    project_slug: str
    name: str
    raw_token: str = field(repr=False)
    scope: str = READ_SCOPE


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} environment variable is required")
    return value


def load_config() -> ProvisionConfig:
    return ProvisionConfig(
        project_slug=_required_env("PROMPTHUB_SERVICE_TOKEN_PROJECT_SLUG"),
        name=_required_env("PROMPTHUB_SERVICE_TOKEN_NAME"),
        raw_token=_required_env("PROMPTHUB_SERVICE_TOKEN"),
        scope=os.environ.get("PROMPTHUB_SERVICE_TOKEN_SCOPE", READ_SCOPE),
    )


async def run(*, apply: bool) -> None:
    config = load_config()
    async with AsyncSessionLocal() as session:
        result = await provision_service_token(
            session,
            project_slug=config.project_slug,
            name=config.name,
            raw_token=config.raw_token,
            scope=config.scope,
            apply=apply,
        )
        if apply:
            await session.commit()
        else:
            await session.rollback()

    mode = "apply" if apply else "dry-run"
    print(f"服务令牌配置 {mode}: action={result.action}, project={config.project_slug}, name={config.name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="只显示将执行的动作")
    mode.add_argument("--apply", action="store_true", help="创建或轮换服务令牌")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run(apply=args.apply))
