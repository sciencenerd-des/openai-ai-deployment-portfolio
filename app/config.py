"""Runtime configuration.

The app runs in two modes:

* **live**  — calls the OpenAI Responses API via the Agents SDK (needs OPENAI_API_KEY)
* **mock**  — returns deterministic fixtures so the full pipeline, UI, tests and
  evals run with zero network access and zero cost.

Mock mode is selected automatically when no API key is present, or explicitly
with ``USE_MOCK=1``. This is what lets reviewers and CI run the project in one
command without secrets.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    model: str
    force_mock: bool

    @property
    def use_mock(self) -> bool:
        return self.force_mock or not self.openai_api_key

    @property
    def mode(self) -> str:
        return "mock" if self.use_mock else "live"


def load_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        # gpt-4o-mini is multimodal, cheap, and a sensible default for a demo.
        model=os.getenv("BDI_MODEL", "gpt-4o-mini"),
        force_mock=os.getenv("USE_MOCK", "").lower() in {"1", "true", "yes"},
    )


settings = load_settings()
