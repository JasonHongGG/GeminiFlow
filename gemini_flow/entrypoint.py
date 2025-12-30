from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Callable, Optional, Sequence, Union

from .gemini.client import GeminiWebClient


PathLike = Union[str, Path]


class Gemini:
    def __init__(
        self,
        *,
        cookies_dir: PathLike = "user_cookies",
        model: str = "gemini-2.5-pro",
        language: str = "zh-TW",
        proxy: Optional[str] = None,
        debug: bool = False,
        auto_refresh_cookies: bool = True,
        client: Optional[GeminiWebClient] = None,
    ):
        self.cookies_dir = Path(cookies_dir)
        self.model = model
        self.language = language
        self.proxy = proxy
        self.debug = debug
        self.auto_refresh_cookies = auto_refresh_cookies
        self._client = client or GeminiWebClient()

    async def astream_chat(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        images: Optional[Sequence[PathLike]] = None,
        language: Optional[str] = None,
        proxy: Optional[str] = None,
        debug: Optional[bool] = None,
    ):
        image_paths = None
        if images:
            image_paths = [Path(p) for p in images]
        return await self._client.chat(
            prompt=prompt,
            model=model or self.model,
            language=language or self.language,
            cookies_dir=self.cookies_dir,
            images=image_paths,
            proxy=proxy if proxy is not None else self.proxy,
            debug=debug if debug is not None else self.debug,
            auto_refresh_cookies=self.auto_refresh_cookies,
        )

    async def achat(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        images: Optional[Sequence[PathLike]] = None,
        language: Optional[str] = None,
        proxy: Optional[str] = None,
        debug: Optional[bool] = None,
    ) -> str:
        stream = await self.astream_chat(
            prompt,
            model=model,
            images=images,
            language=language,
            proxy=proxy,
            debug=debug,
        )
        parts: list[str] = []
        async for chunk in stream:
            parts.append(chunk)
        return "".join(parts)

    def chat(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        images: Optional[Sequence[PathLike]] = None,
        language: Optional[str] = None,
        proxy: Optional[str] = None,
        debug: Optional[bool] = None,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> str:
        async def _run() -> str:
            stream = await self.astream_chat(
                prompt,
                model=model,
                images=images,
                language=language,
                proxy=proxy,
                debug=debug,
            )
            parts: list[str] = []
            async for chunk in stream:
                if on_chunk is not None:
                    on_chunk(chunk)
                parts.append(chunk)
            return "".join(parts)

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_run())
        raise RuntimeError(
            "Gemini.chat() cannot be called from within an active event loop. "
            "Use `await Gemini.achat(...)` or `await Gemini.astream_chat(...)` instead."
        )
