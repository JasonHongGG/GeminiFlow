from __future__ import annotations

import sys
from typing import Optional, Sequence, Tuple

import aiohttp

from ..providers.base import ChatProvider
from ..types import AsyncTextStream, Cookies, MissingAuthError, RequestError, TokenFetchError
from .protocol import (
    DEFAULT_HEADERS,
    GEMINI_BASE_URL,
    REQUEST_URL,
    GeminiRequest,
    REQUIRED_COOKIE_NAME,
    extract_text_delta_from_raw_line,
    extract_tokens,
)
from .upload import upload_images


class GeminiWebProvider(ChatProvider):
    async def fetch_tokens(
        self,
        *,
        session: aiohttp.ClientSession,
        cookies: Cookies,
        proxy: Optional[str] = None,
        debug: bool = False,
    ):
        try:
            async with session.get(GEMINI_BASE_URL, cookies=cookies, proxy=proxy) as resp:
                if resp.status >= 400:
                    raise TokenFetchError(f"Token page fetch failed: HTTP {resp.status}")
                html = await resp.text()
        except aiohttp.ClientError as e:
            raise TokenFetchError(f"Token page fetch failed: {e}") from e

        tokens = extract_tokens(html)
        if not tokens:
            if debug:
                preview = html[:800].replace("\r", "")
                print(f"[debug] Token page preview (first 800 chars):\n{preview}\n")
            raise TokenFetchError("SNlM0e token not found; cookies likely invalid/expired")
        return tokens

    async def stream_chat(
        self,
        *,
        model: str,
        prompt: str,
        cookies: Cookies,
        images: Optional[Sequence[Tuple[bytes, str]]] = None,
        language: str = "zh-TW",
        proxy: Optional[str] = None,
        debug: bool = False,
    ) -> AsyncTextStream:
        if REQUIRED_COOKIE_NAME not in cookies:
            raise MissingAuthError(f"Missing required cookie: {REQUIRED_COOKIE_NAME}")

        async with aiohttp.ClientSession(headers=DEFAULT_HEADERS) as token_session:
            tokens = await self.fetch_tokens(session=token_session, cookies=cookies, proxy=proxy, debug=debug)

        uploads = None
        if images:
            try:
                uploaded = await upload_images(images, proxy=proxy)
                uploads = [(u.upload_ref, u.name) for u in uploaded]
            except Exception as e:
                raise RequestError(f"Image upload failed: {e}") from e

        req = GeminiRequest(
            prompt=prompt,
            language=language,
            tokens=tokens,
            model=model,
            uploads=uploads,
        )

        async def gen():
            emitted_any = False
            preview = ""
            buffer = ""
            last_content = ""

            async with aiohttp.ClientSession(headers=DEFAULT_HEADERS, cookies=cookies) as client:
                try:
                    async with client.post(
                        REQUEST_URL,
                        params=req.params(),
                        data=req.data(),
                        headers=req.headers(),
                        proxy=proxy,
                    ) as resp:
                        if resp.status >= 400:
                            body = await resp.text()
                            raise RequestError(
                                f"StreamGenerate failed: HTTP {resp.status} body={body[:300]}"
                            )

                        async for chunk in resp.content.iter_any():
                            try:
                                part = chunk.decode("utf-8", errors="ignore")
                            except Exception:
                                continue

                            if debug and len(preview) < 800:
                                preview += part[: (800 - len(preview))].replace("\r", "")

                            buffer += part
                            while "\n" in buffer:
                                raw_line, buffer = buffer.split("\n", 1)
                                raw_line = raw_line.rstrip("\r")
                                delta, last_content = extract_text_delta_from_raw_line(
                                    raw_line, last_content
                                )
                                if delta:
                                    emitted_any = True
                                    yield delta

                except aiohttp.ClientError as e:
                    raise RequestError(f"StreamGenerate request failed: {e}") from e

            if buffer.strip():
                raw_line = buffer.rstrip("\r")
                delta, last_content = extract_text_delta_from_raw_line(raw_line, last_content)
                if delta:
                    emitted_any = True
                    yield delta

            if not emitted_any:
                if debug and preview:
                    print(
                        f"[debug] StreamGenerate response preview (first 800 chars):\n{preview}\n",
                        file=sys.stderr,
                    )
                raise RequestError(
                    "No text could be parsed from StreamGenerate response. "
                    "Try --debug and share the preview; response format may have changed."
                )

        return gen()
