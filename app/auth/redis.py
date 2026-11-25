# app/auth/redis.py

import redis.asyncio as redis
import time
from app.core.config import get_settings

settings = get_settings()


async def get_redis():
    if not hasattr(get_redis, "redis"):
        get_redis.redis = await aioredis.from_url(
            settings.REDIS_URL or "redis://localhost",
            decode_responses=True
        )

    return get_redis.redis


async def add_to_blacklist(jti: str, exp: int):
    """Add a token's JTI to the blacklist until expiration."""

    redis = await get_redis()

    remaining_time = int(exp - time.time())

    if remaining_time > 0:
        await redis.set(
            f"blacklist:{jti}",
            "1",
            ex=remaining_time
        )


async def is_blacklisted(jti: str) -> bool:
    """Check if a token's JTI is blacklisted."""

    redis = await get_redis()

    return bool(await redis.exists(f"blacklist:{jti}"))
