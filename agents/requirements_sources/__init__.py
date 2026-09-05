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

"""Pluggable requirement sources beyond github/local/document.

Each connector returns a list of plain-text specs for parse_requirements.
Live SaaS connectors use env credentials; file modes work offline for CI.
"""

from __future__ import annotations

from agents.requirements_sources import email as email_src
from agents.requirements_sources import jira as jira_src
from agents.requirements_sources import transcript as transcript_src

__all__ = ["email_src", "jira_src", "transcript_src"]
