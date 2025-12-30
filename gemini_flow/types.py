from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncIterator, Dict, Optional

Cookies = Dict[str, str]
AsyncTextStream = AsyncIterator[str]


@dataclass(frozen=True)
class GeminiTokens:
    snlm0e: str
    sid: Optional[str]


class GeminiWebFlowError(RuntimeError):
    pass


class MissingAuthError(GeminiWebFlowError):
    pass


class TokenFetchError(GeminiWebFlowError):
    pass


class RequestError(GeminiWebFlowError):
    pass
