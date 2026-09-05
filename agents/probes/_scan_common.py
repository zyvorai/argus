# Copyright 2026 ZyvorAI Labs Private Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Shared helpers for engagement-gated network-attack / DAST probes."""

from __future__ import annotations

from typing import Callable, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

Log = Optional[Callable[[str], None]]


def client(insecure: bool = False, timeout: float = 15):
    import httpx

    return httpx.Client(timeout=timeout, verify=not insecure, follow_redirects=False)


def origin(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def hostname(url: str) -> str:
    return urlparse(url).hostname or ""


def with_query(url: str, updates: dict[str, str]) -> str:
    """Return url with query params merged/overwritten by ``updates``."""
    p = urlparse(url)
    q = dict(parse_qsl(p.query, keep_blank_values=True))
    q.update(updates)
    return urlunparse((p.scheme, p.netloc, p.path, p.params, urlencode(q), p.fragment))


def emit(log: Log, message: str) -> None:
    if log:
        log(message)
