from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any, Optional

from aiohttp import web

from gemini_flow import Gemini


def _json_dumps(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False)


def _json_error(message: str, *, status: int = 400) -> web.Response:
    return web.json_response({"error": message}, status=status, dumps=_json_dumps)


async def _read_json_object(request: web.Request) -> dict[str, Any]:
    raw = await request.read()
    if not raw:
        raise ValueError("empty request body")

    last_error: Optional[Exception] = None
    for encoding in ("utf-8", "utf-8-sig", "cp950", "big5"):
        try:
            text = raw.decode(encoding)
            obj = json.loads(text)
            if not isinstance(obj, dict):
                raise ValueError("body must be a JSON object")
            return obj
        except Exception as e:
            last_error = e

    content_type = request.headers.get("Content-Type") or ""
    raise ValueError(
        f"invalid JSON body (Content-Type={content_type!r}, bytes={len(raw)}). "
        f"Tip: send UTF-8 JSON and set Content-Type: application/json"
    ) from last_error


def _parse_images(payload: dict[str, Any]) -> Optional[list[str]]:
    images = payload.get("images")
    if images is None:
        return None
    if not isinstance(images, list) or not all(isinstance(x, str) for x in images):
        raise ValueError("images must be a list of strings (local file paths)")
    return images


async def _run_gemini_stream(*, payload: dict[str, Any]):
    prompt = payload.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt is required")

    model = payload.get("model")
    if model is not None and not isinstance(model, str):
        raise ValueError("model must be a string")

    language = payload.get("language")
    if language is not None and not isinstance(language, str):
        raise ValueError("language must be a string")

    auto_refresh_cookies = payload.get("auto_refresh_cookies", True)
    if not isinstance(auto_refresh_cookies, bool):
        raise ValueError("auto_refresh_cookies must be a boolean")

    images = _parse_images(payload)

    ai = Gemini(
        model=model or "gemini-3-pro",
        language=language or "zh-TW",
        auto_refresh_cookies=auto_refresh_cookies,
    )

    stream = await ai.astream_chat(
        prompt,
        model=model,
        images=images,
        language=language,
    )
    return stream


async def health(_: web.Request) -> web.Response:
    return web.json_response({"ok": True}, dumps=_json_dumps)


async def chat(request: web.Request) -> web.Response:
    try:
        payload = await _read_json_object(request)
    except Exception as e:
        return _json_error(str(e))

    try:
        stream = await _run_gemini_stream(payload=payload)
    except Exception as e:
        return _json_error(str(e), status=400)

    text_parts: list[str] = []
    images_saved: list[str] = []

    try:
        async for chunk in stream:
            if isinstance(chunk, str) and chunk.startswith("[image saved] "):
                continue
            if isinstance(chunk, str) and chunk.startswith("[image url] "):
                url = chunk[len("[image url] ") :].strip()
                if url:
                    images_saved.append(url)
                continue
            text_parts.append(str(chunk))
    except Exception as e:
        return _json_error(str(e), status=500)

    return web.json_response({"text": "".join(text_parts), "images": images_saved}, dumps=_json_dumps)


def _sse_format(*, event: str, data: object) -> bytes:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")


async def stream(request: web.Request) -> web.StreamResponse:
    try:
        payload = await _read_json_object(request)
    except Exception as e:
        return web.Response(status=400, text=str(e))

    resp = web.StreamResponse(
        status=200,
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
    await resp.prepare(request)

    try:
        gemini_stream = await _run_gemini_stream(payload=payload)
        async for chunk in gemini_stream:
            if isinstance(chunk, str) and chunk.startswith("[image saved] "):
                path = chunk[len("[image saved] ") :].strip()
                await resp.write(_sse_format(event="image", data={"path": path}))
            elif isinstance(chunk, str) and chunk.startswith("[image url] "):
                url = chunk[len("[image url] ") :].strip()
                await resp.write(_sse_format(event="image", data={"url": url}))
            else:
                await resp.write(_sse_format(event="text", data={"chunk": str(chunk)}))

        await resp.write(_sse_format(event="done", data={}))
    except ConnectionResetError:
        return resp
    except Exception as e:
        try:
            await resp.write(_sse_format(event="error", data={"error": str(e)}))
        except Exception:
            pass

    return resp


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", health)
    app.router.add_post("/chat", chat)
    app.router.add_post("/stream", stream)
    return app


async def _serve(*, host: str, port: int) -> None:
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=host, port=port)
    await site.start()

    print(f"[server] listening on http://{host}:{port}")
    print("[server] endpoints: GET /health, POST /chat, POST /stream (SSE)")

    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await runner.cleanup()


def main() -> None:
    p = argparse.ArgumentParser(description="gemini_flow HTTP server")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    args = p.parse_args()

    asyncio.run(_serve(host=args.host, port=args.port))


if __name__ == "__main__":
    main()
