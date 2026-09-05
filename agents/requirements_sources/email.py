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

"""Email (.eml) → requirement text."""

from __future__ import annotations

import email
import email.policy
from pathlib import Path


def load_eml(path: Path) -> str:
    """Extract subject + plain-text body from a single .eml file."""
    raw = path.read_bytes()
    msg = email.message_from_bytes(raw, policy=email.policy.default)
    subject = str(msg.get("subject") or path.stem).strip()
    body_parts: list[str] = []
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                try:
                    body_parts.append(part.get_content())
                except Exception:
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        body_parts.append(payload.decode("utf-8", errors="replace"))
            elif ctype == "text/html" and not body_parts:
                try:
                    html = part.get_content()
                except Exception:
                    payload = part.get_payload(decode=True)
                    html = payload.decode("utf-8", errors="replace") if isinstance(payload, bytes) else ""
                # Crude strip — enough for requirement parsing; not a browser.
                import re

                body_parts.append(re.sub(r"<[^>]+>", " ", html))
    else:
        try:
            body_parts.append(msg.get_content())
        except Exception:
            payload = msg.get_payload(decode=True)
            if isinstance(payload, bytes):
                body_parts.append(payload.decode("utf-8", errors="replace"))
            else:
                body_parts.append(str(msg.get_payload() or ""))
    body = "\n".join(p.strip() for p in body_parts if p and str(p).strip()).strip()
    return f"# {subject}\n\n{body}\n"


def load_paths(paths: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Returns (spec_contents, spec_paths, errors)."""
    contents: list[str] = []
    used: list[str] = []
    errors: list[str] = []
    for raw in paths:
        p = Path(raw)
        if not p.exists():
            errors.append(f"{raw}: not found")
            continue
        if p.suffix.lower() != ".eml":
            errors.append(f"{raw}: expected .eml")
            continue
        try:
            contents.append(load_eml(p))
            used.append(str(p))
        except Exception as exc:
            errors.append(f"{raw}: {exc}")
    return contents, used, errors
