"""
End-to-end orchestrator: takes an IntakeProfile (and optional overrides),
runs the full pipeline, saves a WeeklyPlan, returns the plan.

Pipeline:
  1. build_skeleton (procedural)
  2. draft_plan (AI #1)
  3. compute actual volume + validate against targets (procedural)
  4. refine_plan (AI #2)
  5. constraint check (role/category/dup)
  6. save WeeklyPlan + sessions + exercises (with first-plan rep rule)
"""
from django.db import transaction

from .plan_maker import (
    build_skeleton, compute_actual_volume,
    validate_volume, validate_constraints,
)
from .plan_ai import draft_plan, refine_plan
from .rep_ranges import get_prescription
from .exercise_pool import BY_NAME
from .models import WeeklyPlan, PlannedSession, PlannedExercise


def _sanitize_sessions(sessions: list[dict], filtered_pool: list[dict],
                        skeleton_sessions: list[dict] | None = None) -> list[dict]:
    """
    Two-pass sanitization:
    Pass 1 — slot constraint enforcement (requires skeleton_sessions):
        Each exercise must match the role+category of its template slot.
        If it doesn't, replace it with the best pool exercise that does.
    Pass 2 — pool membership:
        Any exercise not in filtered_pool is replaced with the highest-frequency
        allowed exercise of the same role+movement_category.
    Logs a warning for each replacement so we can audit AI drift.
    """
    import logging
    log = logging.getLogger(__name__)

    pool_by_name = {ex["name"]: ex for ex in filtered_pool}

    from collections import defaultdict
    by_slot: dict[tuple, list] = defaultdict(list)
    for ex in filtered_pool:
        key = (ex.get("role"), ex.get("movement_category"))
        by_slot[key].append(ex)
    for key in by_slot:
        by_slot[key].sort(key=lambda e: e.get("log_frequency", 0), reverse=True)

    # Build skeleton slot index by session order
    skel_by_order: dict[int, list] = {}
    for s in (skeleton_sessions or []):
        skel_by_order[s.get("order")] = s.get("slots", [])

    for sess in sessions:
        used: set[str] = set()
        slots = skel_by_order.get(sess.get("order"), [])

        exercises = sess.get("exercises", [])
        for i, ex in enumerate(exercises):
            name = ex.get("name")

            # --- Pass 1: slot constraint check ---
            if i < len(slots):
                expected_role = slots[i].get("role")
                expected_cat = slots[i].get("category")
                pool_entry = pool_by_name.get(name, {})
                actual_role = pool_entry.get("role") or ex.get("role")
                actual_cat = pool_entry.get("movement_category") or ex.get("movement_category")

                if actual_role != expected_role or actual_cat != expected_cat:
                    key = (expected_role, expected_cat)
                    candidates = [c for c in by_slot.get(key, []) if c["name"] not in used]
                    if candidates:
                        replacement = candidates[0]
                        log.warning(
                            "Slot %d of '%s': AI picked '%s' (role=%s cat=%s) "
                            "but slot expects role=%s cat=%s — replaced with '%s'",
                            i + 1, sess.get("name"), name,
                            actual_role, actual_cat, expected_role, expected_cat,
                            replacement["name"],
                        )
                        ex["name"] = replacement["name"]
                        ex["role"] = replacement["role"]
                        ex["movement_category"] = replacement.get("movement_category", "")
                        name = replacement["name"]
                    else:
                        log.warning(
                            "No replacement for slot %d role=%s cat=%s in '%s'",
                            i + 1, expected_role, expected_cat, sess.get("name"),
                        )

            # --- Pass 2: pool membership check ---
            if name not in pool_by_name:
                key = (ex.get("role"), ex.get("movement_category"))
                candidates = [c for c in by_slot.get(key, []) if c["name"] not in used]
                if candidates:
                    replacement = candidates[0]
                    log.warning(
                        "Session '%s' slot %d: '%s' not in pool — replaced with '%s'",
                        sess.get("name"), i + 1, name, replacement["name"],
                    )
                    ex["name"] = replacement["name"]
                    ex["role"] = replacement["role"]
                    ex["movement_category"] = replacement.get("movement_category", "")
                    name = replacement["name"]

            used.add(name)
    return sessions


# ---------------------------------------------------------------------------
# Post-processing: sort exercises by fatigue cost + role (hardest first)
# ---------------------------------------------------------------------------

_ROLE_ORDER = {"main_compound": 0, "secondary_compound": 1, "isolation": 2}
_FATIGUE_ORDER = {"high": 0, "medium": 1, "low": 2}


_RDL_NAMES = {"Rumunjsko mrtvo dizanje", "Stiff leg deadlift"}
_HIP_THRUST_NAMES = {"Hip thrust"}

# Priority order within a session (lower = earlier):
#   0 — RDL / stiff leg (heaviest hip hinge, must be fresh)
#   1 — Hip thrust (glute compound, high neural demand)
#   2 — all other main compounds
#   3 — secondary compounds
#   4 — isolations
# Within each tier, sort by fatigue_cost desc.


def _sort_exercises(sessions: list[dict]) -> list[dict]:
    """
    Sort exercises within each session.
    Hard priority rules:
      1st  — RDL / Stiff leg deadlift (always slot 1 if present)
      2nd  — Hip thrust (always before other compounds)
      rest — main compounds by fatigue desc, then secondary, then isolations
    """
    for sess in sessions:
        exercises = sess.get("exercises", [])
        for ex in exercises:
            pool_entry = BY_NAME.get(ex.get("name"), {})
            fatigue_ord = _FATIGUE_ORDER.get(
                pool_entry.get("fatigue_cost", "medium"), 1
            )
            name = ex.get("name")
            if name in _RDL_NAMES:
                tier = 0
            elif name in _HIP_THRUST_NAMES:
                tier = 1
            else:
                tier = 2 + _ROLE_ORDER.get(ex.get("role"), 1)
            ex["_sort"] = (tier, fatigue_ord)
        exercises.sort(key=lambda e: e["_sort"])
        for ex in exercises:
            ex.pop("_sort", None)
    return sessions


# Set allocation rules by session duration (from real training data):
#   45 min: compounds 3, isolations 2
#   60 min: all 3
#   75 min: compounds 3, some isolations 2
#   90 min: all 3
#  120 min: all 3
_ISOLATION_SETS = {
    45: 2,    # all isolations get 2
    60: 3,    # all get 3
    75: 2,    # isolations get 2 (compounds stay 3)
    90: 3,    # all get 3
    120: 3,   # all get 3
}


def _enforce_sets(sessions: list[dict], max_session_minutes: int) -> list[dict]:
    """
    Enforce set counts based on session time budget.
    Compounds always get 3. Isolations get 2 or 3 depending on time.
    """
    iso_sets = _ISOLATION_SETS.get(max_session_minutes, 3)

    for sess in sessions:
        for ex in sess.get("exercises", []):
            role = ex.get("role", "")
            if role == "isolation":
                ex["sets"] = iso_sets
            else:
                ex["sets"] = 3
    return sessions


# Fields that can be overridden when generating a test plan from the
# Tjedni Plan page without modifying the user's saved IntakeProfile.
OVERRIDABLE_FIELDS = (
    "sex", "age", "days_per_week_available", "max_session_minutes",
    "body_part_priority", "primary_goal", "training_experience_level",
)


class _ProfileProxy:
    """Wraps an IntakeProfile, returning override values for selected fields."""

    def __init__(self, profile, overrides: dict | None):
        self._p = profile
        self._o = overrides or {}

    def __getattr__(self, name):
        if name in self._o and self._o[name] not in (None, ""):
            return self._o[name]
        return getattr(self._p, name)


def generate_plan_for(profile, overrides: dict | None = None) -> WeeklyPlan:
    proxy = _ProfileProxy(profile, overrides) if overrides else profile

    skeleton = build_skeleton(proxy)

    # --- AI #1: draft ----------------------------------------------------
    draft = draft_plan(skeleton)
    draft_sessions = draft.get("sessions", [])

    actual_draft = compute_actual_volume(draft_sessions)
    report = validate_volume(actual_draft, skeleton["volume_targets"])

    # --- AI #2: refine ---------------------------------------------------
    if report["needs_refinement"]:
        refined = refine_plan(skeleton, draft, report)
        refined_sessions = refined.get("sessions", draft_sessions)
        actual_refined = compute_actual_volume(refined_sessions)
        final_report = validate_volume(actual_refined, skeleton["volume_targets"])
    else:
        refined = None
        refined_sessions = draft_sessions
        actual_refined = actual_draft
        final_report = report

    # Sanitize: enforce slot constraints + pool membership (before sort)
    refined_sessions = _sanitize_sessions(
        refined_sessions,
        skeleton["filtered_pool"],
        skeleton_sessions=skeleton["sessions"],
    )

    # Hard constraint check BEFORE sort (slot positions still match skeleton)
    constraint_errors = validate_constraints(
        refined_sessions,
        skeleton["filtered_pool"],
        skeleton_sessions=skeleton["sessions"],
    )
    final_report["constraint_errors"] = constraint_errors

    # Sort exercises: RDL first, hip thrust second, then compounds, then isolations
    refined_sessions = _sort_exercises(refined_sessions)

    # Enforce set counts based on session time budget
    session_minutes = int(getattr(proxy, "max_session_minutes"))
    refined_sessions = _enforce_sets(refined_sessions, session_minutes)

    # --- Compute next week number for this user --------------------------
    last_plan = WeeklyPlan.objects.filter(user=profile.user).order_by("-week_number").first()
    next_week = (last_plan.week_number + 1) if last_plan else 1
    # Narrow rep ranges (reps_min, reps_min + 2) while no training has been
    # logged — user is in "establishment" phase, finding their working loads.
    # TODO: once TrainingLog model exists, check if any logs exist instead.
    is_first_plan = True

    # --- Persist ---------------------------------------------------------
    with transaction.atomic():
        gen_params = {
            "sex": getattr(proxy, "sex"),
            "days_per_week_available": int(getattr(proxy, "days_per_week_available")),
            "max_session_minutes": int(getattr(proxy, "max_session_minutes")),
            "body_part_priority": getattr(proxy, "body_part_priority"),
            "primary_goal": getattr(proxy, "primary_goal"),
            "training_experience_level": getattr(proxy, "training_experience_level"),
        }
        plan = WeeklyPlan.objects.create(
            user=profile.user,
            week_number=next_week,
            split_type=skeleton["split_id"],
            days_per_week=int(getattr(proxy, "days_per_week_available")),
            max_session_minutes=int(getattr(proxy, "max_session_minutes")),
            generation_params=gen_params,
            volume_targets=skeleton["volume_targets"],
            volume_actual=actual_refined,
            validation_report=final_report,
            ai_draft=draft,
            ai_refined=refined,
        )

        for sess in refined_sessions:
            psession = PlannedSession.objects.create(
                plan=plan,
                order=sess.get("order", 1),
                name=sess.get("name", "Session"),
                template_key=sess.get("template_key", ""),
            )
            for i, ex in enumerate(sess.get("exercises", []), start=1):
                role = ex.get("role", "secondary_compound")
                presc = get_prescription(
                    ex.get("name", ""), role, first_plan=is_first_plan
                )
                # Hard rule: min 2 sets, max 3 sets, regardless of AI output.
                sets_val = max(2, min(3, int(ex.get("sets", presc["sets"]) or presc["sets"])))
                PlannedExercise.objects.create(
                    session=psession,
                    order=i,
                    name=ex.get("name", ""),
                    role=role,
                    movement_category=ex.get("movement_category", ""),
                    sets=sets_val,
                    reps_min=presc["reps_min"],
                    reps_max=presc["reps_max"],
                    target_rpe=presc["rpe"],
                    rest=presc["rest"],
                    weight_kg=None,
                )

    return plan
