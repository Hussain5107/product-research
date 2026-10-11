from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


DEFAULT_CATEGORIES = [
    "Outdoor camping",
    "Desert picnic accessories",
    "Car accessories",
    "Home and kitchen",
    "Storage and organization",
]


@dataclass(frozen=True)
class ResearchConfig:
    gemini_api_key: str | None
    gemini_model: str
    supabase_url: str | None
    supabase_service_role_key: str | None
    mode: str
    marketplace: str
    products_per_run: int
    categories: list[str] = field(default_factory=lambda: DEFAULT_CATEGORIES.copy())
    report_output_dir: Path = Path("reports")

    @property
    def use_sample_data(self) -> bool:
        return self.mode.lower() in {"sample", "fixture", "dev"}


def load_config() -> ResearchConfig:
    load_dotenv()
    categories_raw = os.getenv("RESEARCH_CATEGORIES", ",".join(DEFAULT_CATEGORIES))
    categories = [item.strip() for item in categories_raw.split(",") if item.strip()]
    return ResearchConfig(
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        supabase_url=os.getenv("SUPABASE_URL") or None,
        supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY") or None,
        mode=os.getenv("RESEARCH_MODE", "sample"),
        marketplace=os.getenv("RESEARCH_MARKETPLACE", "amazon.ae"),
        products_per_run=max(1, int(os.getenv("RESEARCH_PRODUCTS_PER_RUN", "20"))),
        categories=categories or DEFAULT_CATEGORIES.copy(),
        report_output_dir=Path(os.getenv("REPORT_OUTPUT_DIR", "reports")),
    )

