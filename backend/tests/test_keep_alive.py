import asyncio
import httpx
import pytest

from backend.src.services import keep_alive
from backend.src.services.keep_alive import get_keep_alive_url, ping_once, run_keep_alive


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in ["KEEP_ALIVE_ENABLED", "KEEP_ALIVE_URL", "RENDER_EXTERNAL_URL", "KEEP_ALIVE_INTERVAL_SECONDS"]:
        monkeypatch.delenv(key, raising=False)


def test_disabled_when_not_on_render():
    assert get_keep_alive_url() is None


def test_uses_render_external_url(monkeypatch):
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://ai-csa-backend.onrender.com/")
    assert get_keep_alive_url() == "https://ai-csa-backend.onrender.com/health"


def test_keep_alive_url_overrides_render_url(monkeypatch):
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://render.example")
    monkeypatch.setenv("KEEP_ALIVE_URL", "https://custom.example")
    assert get_keep_alive_url() == "https://custom.example/health"


def test_can_be_switched_off(monkeypatch):
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://render.example")
    monkeypatch.setenv("KEEP_ALIVE_ENABLED", "false")
    assert get_keep_alive_url() is None


def _client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_ping_once_success():
    async with _client(lambda req: httpx.Response(200, json={"status": "ok"})) as client:
        assert await ping_once(client, "https://x/health") is True


@pytest.mark.asyncio
async def test_ping_once_bad_status():
    async with _client(lambda req: httpx.Response(503)) as client:
        assert await ping_once(client, "https://x/health") is False


@pytest.mark.asyncio
async def test_ping_once_network_error():
    def boom(req):
        raise httpx.ConnectError("down")
    async with _client(boom) as client:
        assert await ping_once(client, "https://x/health") is False


@pytest.mark.asyncio
async def test_loop_keeps_pinging_after_failures(monkeypatch):
    calls = []

    def handler(req):
        calls.append(str(req.url))
        return httpx.Response(500 if len(calls) == 1 else 200)

    sleeps = 0
    real_sleep = asyncio.sleep

    async def fake_sleep(seconds):
        nonlocal sleeps
        sleeps += 1
        if sleeps > 3:
            raise asyncio.CancelledError
        await real_sleep(0)

    monkeypatch.setattr(keep_alive.asyncio, "sleep", fake_sleep)
    async with _client(handler) as client:
        with pytest.raises(asyncio.CancelledError):
            await run_keep_alive("https://x/health", 600, client=client)
    assert calls == ["https://x/health"] * 3
