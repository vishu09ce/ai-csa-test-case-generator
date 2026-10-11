import asyncio
import os
import httpx
from backend.src.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_INTERVAL_SECONDS = 600  # Render free tier sleeps after 15 minutes idle
REQUEST_TIMEOUT_SECONDS = 30


def get_keep_alive_url() -> str | None:
    """Health URL to ping, or None when keep-alive should not run.

    Render sets RENDER_EXTERNAL_URL automatically, so this only switches on
    when deployed there. KEEP_ALIVE_URL overrides it; KEEP_ALIVE_ENABLED=false
    turns it off.
    """
    if os.getenv("KEEP_ALIVE_ENABLED", "true").lower() == "false":
        return None
    base = os.getenv("KEEP_ALIVE_URL") or os.getenv("RENDER_EXTERNAL_URL")
    if not base:
        return None
    return base.rstrip("/") + "/health"


def get_interval_seconds() -> int:
    return int(os.getenv("KEEP_ALIVE_INTERVAL_SECONDS", DEFAULT_INTERVAL_SECONDS))


async def ping_once(client: httpx.AsyncClient, url: str) -> bool:
    try:
        response = await client.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    except httpx.HTTPError as e:
        logger.warning("Keep-alive ping to %s failed: %s", url, e)
        return False
    if response.status_code != 200:
        logger.warning("Keep-alive ping to %s returned %s", url, response.status_code)
        return False
    return True


async def run_keep_alive(url: str, interval_seconds: int, client: httpx.AsyncClient | None = None) -> None:
    # Ping through the public URL so Render counts it as inbound traffic.
    logger.info("Keep-alive started: pinging %s every %ss", url, interval_seconds)
    owns_client = client is None
    client = client or httpx.AsyncClient()
    try:
        while True:
            await asyncio.sleep(interval_seconds)
            await ping_once(client, url)
    finally:
        if owns_client:
            await client.aclose()
