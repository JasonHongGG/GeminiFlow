from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

import aiohttp


UPLOAD_IMAGE_URL = "https://content-push.googleapis.com/upload/"

# Mirrors g4f's working Gemini web upload headers.
UPLOAD_IMAGE_HEADERS = {
    "authority": "content-push.googleapis.com",
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.7",
    "authorization": "Basic c2F2ZXM6cyNMdGhlNmxzd2F2b0RsN3J1d1U=",
    "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
    "origin": "https://gemini.google.com",
    "push-id": "feeds/mcudyrk2a4khkz",
    "referer": "https://gemini.google.com/",
    "x-goog-upload-command": "start",
    "x-goog-upload-header-content-length": "",
    "x-goog-upload-protocol": "resumable",
    "x-tenant-id": "bard-storage",
}


@dataclass(frozen=True)
class UploadedImage:
    upload_ref: str
    name: str


async def upload_images(
    images: Iterable[Tuple[bytes, str]],
    *,
    proxy: Optional[str] = None,
) -> List[UploadedImage]:
    """Upload local image bytes for Gemini web-flow.

    Returns a list of upload references usable in StreamGenerate payload.
    """

    async def upload_one(session: aiohttp.ClientSession, image_bytes: bytes, image_name: str) -> UploadedImage:
        # OPTIONS preflight (kept for parity with the working g4f implementation)
        async with session.options(UPLOAD_IMAGE_URL, proxy=proxy) as resp:
            if resp.status >= 400:
                raise RuntimeError(f"Image upload preflight failed: HTTP {resp.status}")

        headers = {
            "size": str(len(image_bytes)),
            "x-goog-upload-command": "start",
        }
        data = f"File name: {image_name}" if image_name else None
        async with session.post(UPLOAD_IMAGE_URL, headers=headers, data=data, proxy=proxy) as resp:
            if resp.status >= 400:
                body = await resp.text()
                raise RuntimeError(f"Image upload start failed: HTTP {resp.status} body={body[:300]}")
            upload_url = resp.headers.get("X-Goog-Upload-Url")
            if not upload_url:
                raise RuntimeError("Image upload start failed: missing X-Goog-Upload-Url")

        async with session.options(upload_url, headers=headers, proxy=proxy) as resp:
            if resp.status >= 400:
                raise RuntimeError(f"Image upload URL preflight failed: HTTP {resp.status}")

        headers["x-goog-upload-command"] = "upload, finalize"
        headers["X-Goog-Upload-Offset"] = "0"
        async with session.post(upload_url, headers=headers, data=image_bytes, proxy=proxy) as resp:
            if resp.status >= 400:
                body = await resp.text()
                raise RuntimeError(f"Image upload finalize failed: HTTP {resp.status} body={body[:300]}")
            upload_ref = await resp.text()

        return UploadedImage(upload_ref=upload_ref, name=image_name)

    images_list = list(images)
    if not images_list:
        return []

    async with aiohttp.ClientSession(headers=UPLOAD_IMAGE_HEADERS) as session:
        return await asyncio.gather(
            *[upload_one(session, image_bytes, image_name) for image_bytes, image_name in images_list]
        )
