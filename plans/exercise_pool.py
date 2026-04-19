"""
Exercise pool loader. Reads plans/data/exercise_pool.yaml once at import.

Provides:
  POOL              — list[dict] of all exercises
  BY_NAME           — dict[name → exercise]
  SESSION_TEMPLATES — dict[template_name → list of slots]
  SPLIT_CONFIGS     — dict[config_name → {sessions_per_week, rotation, ...}]
  COVERAGE_MAP      — dict[template_name → {muscle: count}]

Plus filter helpers used by plan_maker.
"""
from pathlib import Path
import yaml

_DATA_FILE = Path(__file__).parent / "data" / "exercise_pool.yaml"

with _DATA_FILE.open("r", encoding="utf-8") as f:
    _RAW = yaml.safe_load(f)

POOL = _RAW.get("exercises", [])
BY_NAME = {ex["name"]: ex for ex in POOL}
SESSION_TEMPLATES = _RAW.get("session_templates", {})
SPLIT_CONFIGS = _RAW.get("split_configs", {})
COVERAGE_MAP = _RAW.get("coverage_map", {})


def filter_pool(avoid_movements: list[str] | None = None,
                avoid_body_parts: list[str] | None = None,
                avoid_categories: list[str] | None = None,
                sex: str = "both") -> list[dict]:
    """
    Return exercises with anything in avoid lists removed.

    avoid_movements   — exact exercise names (case-insensitive substring match also)
    avoid_body_parts  — muscle group keys; exercises whose PRIMARY muscles
                        intersect this list are removed (secondary is allowed)
    avoid_categories  — movement_category strings to remove entirely
    sex               — 'male' | 'female' | 'both'; exercises tagged sex='male'
                        are excluded when sex='female' and vice-versa
    """
    avoid_movements = [m.lower() for m in (avoid_movements or [])]
    avoid_body_parts = set(avoid_body_parts or [])
    avoid_categories = set(avoid_categories or [])

    out = []
    for ex in POOL:
        name_l = ex["name"].lower()
        if any(m in name_l or name_l in m for m in avoid_movements):
            continue
        if ex.get("movement_category") in avoid_categories:
            continue
        primary = set(ex.get("primary_muscles", []))
        if primary & avoid_body_parts:
            continue
        # Sex filter: skip exercises tagged for the opposite sex
        ex_sex = ex.get("sex", "both")
        if sex == "female" and ex_sex == "male":
            continue
        if sex == "male" and ex_sex == "female":
            continue
        out.append(ex)
    return out


def by_category(pool: list[dict], category: str) -> list[dict]:
    return [ex for ex in pool if ex.get("movement_category") == category]


def by_role(pool: list[dict], role: str) -> list[dict]:
    return [ex for ex in pool if ex.get("role") == role]
