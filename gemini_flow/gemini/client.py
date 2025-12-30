from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence

from ..cookies import load_google_cookies
from ..types import AsyncTextStream
from .provider import GeminiWebProvider


class GeminiWebClient:
    def __init__(self, *, provider: Optional[GeminiWebProvider] = None):
        self._provider = provider or GeminiWebProvider()

    @classmethod
    def from_cookies_dir(cls, cookies_dir: Path) -> "GeminiWebClient":
        client = cls()
        client._cookies_dir = cookies_dir
        return client

    async def chat(
        self,
        *,
        prompt: str,
        model: str,
        language: str = "zh-TW",
        cookies_dir: Path,
        images: Optional[Sequence[Path]] = None,
        proxy: Optional[str] = None,
        debug: bool = False,
    ) -> AsyncTextStream:
        cookies = load_google_cookies(cookies_dir)
        image_payload = None
        if images:
            image_payload = []
            for path in images:
                data = path.read_bytes()
                image_payload.append((data, path.name))
        return await self._provider.stream_chat(
            model=model,
            prompt=prompt,
            cookies=cookies,
            images=image_payload,
            language=language,
            proxy=proxy,
            debug=debug,
        )
