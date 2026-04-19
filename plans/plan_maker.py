"""
Procedural Plan Maker — does everything that does NOT require AI judgment.

Pipeline:
  build_skeleton(profile) -> dict {
      split, sessions:[ {name, template_key, slots:[{role, category, optional}]}, ... ],
      volume_targets, max_slots, filtered_pool, limitations
  }

The skeleton is what we hand to the AI in step 1 (exercise selection).
"""
from intake.muscle_index import EXERCISE_MUSCLE_INDEX, MUSCLE_GROUPS
from .exercise_pool import (
    POOL, BY_NAME, SESSION_TEMPLATES, filter_pool,
)
from .volume_targets import get_volume_targets


# ---------------------------------------------------------------------------
# Split selection
# ---------------------------------------------------------------------------

def select_split(days_per_week: int, sex: str,
                  body_part_priority: str = "balanced") -> tuple[str, list[str]]:
    """
    Returns (split_id, [template_keys per session]).
    Template keys must exist in SESSION_TEMPLATES.
    Priority affects the split choice — lower_priority gets more lower
    sessions, upper_priority gets more upper sessions.
    """
    # Female-specific splits: lower days + full_body_f (replaces upper)
    if sex == "female":
        if days_per_week <= 2:
            return "lower_full_2x_f", ["lower_f1", "full_body_f"]
        if days_per_week == 3:
            return "lower_full_lower_3x_f", ["lower_f1", "full_body_f", "lower_f2"]
        if days_per_week == 4:
            return "lower_full_2x_4x_f", ["lower_f1", "full_body_f", "lower_f2", "full_body_f"]
        if days_per_week == 5:
            return "lower_full_5x_f", ["lower_f1", "full_body_f", "lower_f2", "full_body_f", "lower_f1"]
        # 6+
        return "lower_full_6x_f", ["lower_f1", "full_body_f", "lower_f2", "full_body_f", "lower_f1", "full_body_f"]

    is_lower = body_part_priority == "lower_priority"
    is_upper = body_part_priority == "upper_priority"

    if days_per_week <= 2:
        return "full_body_2x", ["full_body", "full_body"]

    if days_per_week == 3:
        if is_upper:
            return "upper_legs_upper_3x", ["upper_1", "legs", "upper_2"]
        if is_lower:
            return "lower_upper_lower_3x", ["lower_1", "upper", "lower_2"]
        return "ppl_3x", ["push", "pull", "legs"]

    if days_per_week == 4:
        if is_lower:
            return "lower_upper_lower_fb_4x", ["lower_1", "upper", "lower_2", "full_body"]
        if is_upper:
            return "upper_lower_push_pull_4x", ["upper", "lower_1", "push", "pull"]
        return "upper_lower_2x", ["upper_1", "lower_1", "upper_2", "lower_2"]

    if days_per_week == 5:
        if is_lower:
            return "fb_lower_upper_lower_fb_5x", ["full_body", "lower_1", "upper", "lower_2", "full_body"]
        if is_upper:
            return "upper_lower_push_pull_lower_5x", ["upper", "lower_1", "push", "pull", "lower_2"]
        return "upper_lower_plus_5x", ["upper_1", "lower_1", "upper_2", "lower_2", "full_body"]

    # 6+
    if is_lower:
        return "fb_lower_upper_lower_fb_upper_6x", ["full_body", "lower_1", "upper_1", "lower_2", "full_body", "upper_2"]
    if is_upper:
        return "upper_lower_push_pull_lower_upper_6x", ["upper", "lower_1", "push", "pull", "lower_2", "upper_2"]
    return "ppl_2x", ["push", "pull", "legs", "push", "pull", "legs"]


# ---------------------------------------------------------------------------
# Slot budget
# ---------------------------------------------------------------------------

def slot_budget(max_session_minutes: int) -> int:
    """
    Max exercise slots per session. Conservative — assumes ~4-5 min per
    exercise slot (warm-up sets + working sets + rest). Better to slightly
    under-fill than to consistently run over time.
    """
    # Calibrated from 35 weeks of real training data:
    #   45 min: 5 exercises, isolations at 2 sets  (~13 sets)
    #   60 min: 5 exercises, all 3 sets            (~15 sets)
    #   75 min: 6 exercises, some isolations at 2  (~16 sets)
    #   90 min: 6 exercises, all 3 sets            (~18 sets)
    #  120 min: 7 exercises, high volume option     (~21 sets)
    if max_session_minutes <= 45:
        return 5
    if max_session_minutes <= 60:
        return 5
    if max_session_minutes <= 75:
        return 6
    if max_session_minutes <= 90:
        return 6
    return 7


# ---------------------------------------------------------------------------
# Session skeleton
# ---------------------------------------------------------------------------

def _build_session(template_key: str, max_slots: int) -> dict:
    """
    Take a session template from the pool and trim it to max_slots,
    dropping `optional: true` slots first.
    """
    raw = SESSION_TEMPLATES.get(template_key)
    if not raw:
        return {"template_key": template_key, "slots": []}

    slots = list(raw["slots"])

    # Trim: drop optional slots first, then trailing slots, until we fit.
    while len(slots) > max_slots:
        opt_idx = next(
            (i for i in range(len(slots) - 1, -1, -1) if slots[i].get("optional")),
            None,
        )
        if opt_idx is not None:
            slots.pop(opt_idx)
        else:
            slots.pop()  # drop last (lowest priority)

    return {
        "template_key": template_key,
        "description": raw.get("description", ""),
        "slots": [
            {
                "slot": i + 1,
                "role": s["role"],
                "category": s["category"],
                "note": s.get("note", ""),
            }
            for i, s in enumerate(slots)
        ],
    }


def _session_display_name(template_key: str, occurrence: int) -> str:
    base = {
        "push": "Push", "pull": "Pull", "legs": "Legs",
        "upper": "Upper", "lower": "Lower",
        "upper_1": "Upper 1", "upper_2": "Upper 2",
        "lower_1": "Lower 1", "lower_2": "Lower 2",
        "full_body": "Full Body",
        # female templates
        "lower_f1": "Lower 1", "lower_f2": "Lower 2",
        "full_body_f": "Full Body",
    }.get(template_key, template_key.title())
    if occurrence > 1:
        return f"{base} {occurrence}"
    return base


# ---------------------------------------------------------------------------
# Volume from a built plan (effective sets)
# ---------------------------------------------------------------------------

def compute_actual_volume(sessions: list[dict]) -> dict[str, float]:
    """
    sessions = [{exercises: [{name, sets}, ...]}, ...]
    Returns effective sets per muscle: sets * (score/100) summed.
    """
    out = {m: 0.0 for m in MUSCLE_GROUPS}
    for sess in sessions:
        for ex in sess.get("exercises", []):
            name = ex.get("name")
            sets = ex.get("sets", 0)
            scores = EXERCISE_MUSCLE_INDEX.get(name)
            if not scores:
                continue
            for muscle, score in scores.items():
                out[muscle] += sets * (score / 100)
    return {k: round(v, 2) for k, v in out.items()}


# ---------------------------------------------------------------------------
# Top-level skeleton builder
# ---------------------------------------------------------------------------

def build_skeleton(profile) -> dict:
    """
    profile is an IntakeProfile instance.
    Returns the skeleton dict ready to be passed to the AI.
    """
    sex = profile.sex
    days = profile.days_per_week_available
    minutes = profile.max_session_minutes
    priority = profile.body_part_priority

    split_id, template_keys = select_split(days, sex, priority)
    max_slots = slot_budget(minutes)

    # Apply per-session-type slot caps from session pattern lengths,
    # but never exceed user's time budget.
    sessions = []
    seen_counts: dict[str, int] = {}
    for i, key in enumerate(template_keys):
        seen_counts[key] = seen_counts.get(key, 0) + 1
        sess = _build_session(key, max_slots)
        sess["order"] = i + 1
        sess["name"] = _session_display_name(key, seen_counts[key])
        sessions.append(sess)

    targets = get_volume_targets(sex, priority, days)

    # Limitations from ai_analysis
    ai = profile.ai_analysis or {}
    lims = ai.get("limitations", {}) if isinstance(ai, dict) else {}
    avoid_movements = lims.get("avoid_movements", []) or []
    avoid_body_parts = lims.get("avoid_body_parts", []) or []

    pool = filter_pool(
        avoid_movements=avoid_movements,
        avoid_body_parts=avoid_body_parts,
        sex=sex,
    )

    return {
        "split_id": split_id,
        "max_slots": max_slots,
        "sessions": sessions,
        "volume_targets": targets,
        "filtered_pool": pool,
        "limitations": {
            "avoid_movements": avoid_movements,
            "avoid_body_parts": avoid_body_parts,
            "notes": lims.get("notes", ""),
            "severity": lims.get("severity", "none"),
        },
        "profile_summary": {
            "sex": sex,
            "age": profile.age,
            "days_per_week": days,
            "max_session_minutes": minutes,
            "primary_goal": profile.primary_goal,
            "body_part_priority": priority,
            "experience": profile.training_experience_level,
        },
    }


# ---------------------------------------------------------------------------
# Validation — compares actual vs target volume
# ---------------------------------------------------------------------------

# Tolerances vs target (effective sets)
UNDER_TOL = 0.80  # below this fraction of target → flagged under
OVER_TOL = 1.30   # above this → flagged over

# Muscles that accumulate heavy indirect work from compounds — wider OVER
# tolerance so we don't flag completely normal synergist volume as a problem.
_LENIENT_OVER = {
    "biceps":        1.60,   # hit by every pull
    "prednje_rame":  1.60,   # hit by every press
    "srednje_rame":  1.60,   # hit by lateral + pressing + some pulls
    "straznje_rame": 1.60,   # hit by every row
    "donja_leda":    1.60,   # hit by hinges + rows + squats
    "trbuh":         1.60,   # hit by many compounds as stabilizer
}


def validate_volume(actual: dict[str, float], target: dict[str, float]) -> dict:
    """
    Returns a structured report with under/over/ok per muscle and a
    short text summary the AI can read.
    """
    issues = {"under": [], "over": [], "ok": []}
    for m, t in target.items():
        a = actual.get(m, 0.0)
        if t <= 0:
            continue
        ratio = a / t
        over_tol = _LENIENT_OVER.get(m, OVER_TOL)
        rec = {"muscle": m, "target": t, "actual": a, "ratio": round(ratio, 2)}
        if ratio < UNDER_TOL:
            issues["under"].append(rec)
        elif ratio > over_tol:
            issues["over"].append(rec)
        else:
            issues["ok"].append(rec)

    summary_parts = []
    if issues["under"]:
        names = ", ".join(
            f"{x['muscle']}({x['actual']}/{x['target']})" for x in issues["under"]
        )
        summary_parts.append(f"UNDER target: {names}")
    if issues["over"]:
        names = ", ".join(
            f"{x['muscle']}({x['actual']}/{x['target']})" for x in issues["over"]
        )
        summary_parts.append(f"OVER target: {names}")
    if not summary_parts:
        summary_parts.append("All muscle groups within tolerance.")

    return {
        "issues": issues,
        "summary": " | ".join(summary_parts),
        "needs_refinement": bool(issues["under"] or issues["over"]),
    }


def validate_constraints(plan_sessions: list[dict],
                         filtered_pool: list[dict],
                         skeleton_sessions: list[dict] | None = None) -> list[str]:
    """
    Hard checks:
      - every exercise must exist in the filtered pool
      - if skeleton_sessions is provided, exercise role+category must match
        the corresponding slot in the skeleton (slot order)
      - no duplicate exercises within one session

    Returns list of error strings (empty = OK).
    """
    by_name = {ex["name"]: ex for ex in filtered_pool}
    errors = []

    skel_by_order = {}
    for s in (skeleton_sessions or []):
        skel_by_order[s.get("order")] = s

    for sess in plan_sessions:
        seen = set()
        slots = []
        if skel_by_order:
            skel = skel_by_order.get(sess.get("order"))
            if skel:
                slots = skel.get("slots", [])

        for i, ex in enumerate(sess.get("exercises", [])):
            name = ex.get("name")
            if name not in by_name:
                errors.append(
                    f"Session '{sess.get('name')}' slot {i+1}: '{name}' "
                    f"is not in the allowed pool."
                )
                continue
            if name in seen:
                errors.append(
                    f"Session '{sess.get('name')}': duplicate exercise '{name}'."
                )
            seen.add(name)

            if i < len(slots):
                slot = slots[i]
                pool_ex = by_name[name]
                if pool_ex.get("role") != slot.get("role"):
                    errors.append(
                        f"Session '{sess.get('name')}' slot {i+1}: '{name}' "
                        f"has role={pool_ex.get('role')} but slot expects "
                        f"role={slot.get('role')}."
                    )
                if pool_ex.get("movement_category") != slot.get("category"):
                    errors.append(
                        f"Session '{sess.get('name')}' slot {i+1}: '{name}' "
                        f"has category={pool_ex.get('movement_category')} but "
                        f"slot expects category={slot.get('category')}."
                    )
    return errors
