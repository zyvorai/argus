#!/usr/bin/env bash
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

# Entrypoint for the `zyvorai/argus` GitHub Action (see action.yml).
#
# GitHub Actions always sets ACTION_* even when an input was left at its empty
# default, so this only forwards a value into the real argus env var when
# the action input was actually provided — otherwise an empty ACTION_TARGET_URL
# would stomp the image's baked-in ZYVOR_BASE_URL default.
set -uo pipefail

COMMAND="${1:-test exec}"
EXTRA_ARGS="${2:-}"

set_if_present() {
  local value="$1" target="$2"
  if [ -n "$value" ]; then
    export "$target"="$value"
  fi
}

set_if_present "${ACTION_TARGET_URL:-}" ZYVOR_BASE_URL
set_if_present "${ACTION_GREP:-}" ZYVOR_GREP
set_if_present "${ACTION_SHARD:-}" ZYVOR_SHARD
set_if_present "${ACTION_ZYVOR_ENV:-}" ZYVOR_ENV
set_if_present "${ACTION_TARGET_ALLOWLIST:-}" ZYVOR_TARGET_ALLOWLIST
set_if_present "${ACTION_ALLOW_PRIVATE_TARGETS:-}" ZYVOR_ALLOW_PRIVATE_TARGETS
set_if_present "${ACTION_ALLOW_HTTP_TARGETS:-}" ZYVOR_ALLOW_HTTP_TARGETS
set_if_present "${ACTION_LLM_PROVIDER:-}" LLM_PROVIDER
set_if_present "${ACTION_OPENAI_API_KEY:-}" OPENAI_API_KEY
set_if_present "${ACTION_ANTHROPIC_API_KEY:-}" ANTHROPIC_API_KEY

# shellcheck disable=SC2086
# COMMAND is intentionally unquoted: it may be a multi-word subcommand path
# (e.g. "test run", "vision route-sweep") that must word-split into separate args.
argus $COMMAND $EXTRA_ARGS
EXIT_CODE=$?

SUMMARY="reports/summary.json"
if [ -n "${GITHUB_OUTPUT:-}" ]; then
  {
    echo "exit-code=$EXIT_CODE"
    if [ -f "$SUMMARY" ] && command -v jq >/dev/null 2>&1; then
      echo "passed=$(jq -r '.passed // 0' "$SUMMARY")"
      echo "failed=$(jq -r '.failed // 0' "$SUMMARY")"
    fi
    echo "summary-path=$SUMMARY"
  } >> "$GITHUB_OUTPUT"
fi

if [ "${ACTION_FAIL_ON_ERROR:-true}" = "false" ]; then
  exit 0
fi
exit "$EXIT_CODE"
