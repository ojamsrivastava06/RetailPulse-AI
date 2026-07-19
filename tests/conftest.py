from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

import pytest

SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class ASGIResponse:
    def __init__(self, status_code: int, headers: dict[str, str], content: bytes) -> None:
        self.status_code = status_code
        self.headers = headers
        self.content = content

    def json(self):
        return json.loads(self.content.decode("utf-8"))


async def _asgi_get(path: str, headers: dict[str, str] | None = None) -> ASGIResponse:
    from api.main import app

    parsed = urlsplit(path)
    sent: list[dict] = []

    async def receive() -> dict:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict) -> None:
        sent.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": parsed.path,
        "raw_path": parsed.path.encode("utf-8"),
        "query_string": parsed.query.encode("utf-8"),
        "headers": [(key.lower().encode("utf-8"), value.encode("utf-8")) for key, value in (headers or {}).items()],
        "client": ("127.0.0.1", 50000),
        "server": ("testserver", 80),
    }
    await app(scope, receive, send)

    start = next(message for message in sent if message["type"] == "http.response.start")
    body = b"".join(message.get("body", b"") for message in sent if message["type"] == "http.response.body")
    response_headers = {key.decode("utf-8").lower(): value.decode("utf-8") for key, value in start.get("headers", [])}
    return ASGIResponse(start["status"], response_headers, body)


@pytest.fixture
def api_get():
    def _get(path: str, *, auth: bool = True, headers: dict[str, str] | None = None) -> ASGIResponse:
        request_headers = dict(headers or {})
        if auth:
            request_headers.setdefault("X-API-Key", "retailpulse-dev-api-key")
        return asyncio.run(_asgi_get(path, request_headers))

    return _get
