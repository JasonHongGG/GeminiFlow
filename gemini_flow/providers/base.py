from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence, Tuple

from ..types import AsyncTextStream, Cookies


class ChatProvider(ABC):
    @abstractmethod
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
        save_images: bool = True,
    ) -> AsyncTextStream:
        raise NotImplementedError
