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

"""Meeting transcript (.vtt / .srt / .txt) → requirement text."""

from __future__ import annotations

import re
from pathlib import Path

_SUPPORTED = {".vtt", ".srt", ".txt", ".md"}


def _strip_vtt(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.upper().startswith("WEBVTT"):
            continue
        if re.match(r"^\d+$", s):
            continue
        if re.match(r"^\d{2}:\d{2}", s) or "-->" in s:
            continue
        lines.append(s)
    return "\n".join(lines)


def _strip_srt(text: str) -> str:
    return _strip_vtt(text)


def load_transcript(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    suffix = path.suffix.lower()
    if suffix == ".vtt":
        body = _strip_vtt(raw)
    elif suffix == ".srt":
        body = _strip_srt(raw)
    else:
        body = raw.strip()
    title = path.stem.replace("_", " ").replace("-", " ").strip() or path.stem
    return f"# Meeting transcript: {title}\n\n{body}\n"


def load_paths(paths: list[str]) -> tuple[list[str], list[str], list[str]]:
    contents: list[str] = []
    used: list[str] = []
    errors: list[str] = []
    for raw in paths:
        p = Path(raw)
        if not p.exists():
            errors.append(f"{raw}: not found")
            continue
        if p.suffix.lower() not in _SUPPORTED:
            errors.append(f"{raw}: unsupported transcript type (use .vtt/.srt/.txt/.md)")
            continue
        try:
            contents.append(load_transcript(p))
            used.append(str(p))
        except Exception as exc:
            errors.append(f"{raw}: {exc}")
    return contents, used, errors
