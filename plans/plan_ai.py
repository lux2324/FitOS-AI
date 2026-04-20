"""
AI step of the plan maker.

Two calls:
  1) draft_plan(skeleton)             — pick exercises and sets for each slot
  2) refine_plan(skeleton, draft, validation_report)
                                       — fix volume issues from python validator

Both use gpt-4o-mini with JSON-only output.
Sex-aware prompts: male and female get separate system prompts so the AI
isn't confused by rules that don't apply to the plan it's building.
"""
import json
import httpx
from django.conf import settings


# ---------------------------------------------------------------------------
# System prompt — shared base + sex-specific rules
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT_BASE = """You are a strength coach assembling a weekly training plan for a {sex_upper} athlete.

You receive a SKELETON describing:
- the chosen split (sessions and their roles/categories per slot)
- a filtered exercise pool (exercises the user is allowed to do)
- weekly volume targets per muscle group (in EFFECTIVE SETS — sets * activation)
- the user's profile (sex, age, days/week, time per session, goal, priority)
- limitations (avoid_movements, avoid_body_parts, severity)

{sex_split_intro}Your job: for EVERY slot in EVERY session, pick exactly one exercise from the
filtered pool and assign sets. Respect these rules:

1. The exercise's `role` and `category` MUST EXACTLY match the slot's role
   and category. Prefer exercises with higher `freq` and `preferred: true`.
2. NEVER pick an exercise that is not in the filtered_pool list.
3. No duplicate exercises within one session. Across the week, light
   duplication is fine if the split repeats a session type.{sex_duplication_note}
{sex_angle_variation}4. EQUIPMENT VARIATION for paired isolation slots. When the same session
   has two slots in the same isolation category (e.g. two biceps_isolation
   slots), use DIFFERENT equipment:
     - if one is dumbbell, the other should be barbell or cable/preacher
     - if one is barbell, the other should be dumbbell or preacher
   {sex_equip_detail}
5. Sets per exercise:
     - main_compound:      3 sets (NEVER 4)
     - secondary_compound: 3 sets (NEVER 4)
     - isolation:          2 or 3 sets
   HARD MINIMUM: 2 sets. HARD MAXIMUM: 3 sets.
5a. SET ALLOCATION by session time:
      - 45 min: 5 exercises, compounds 3 sets, isolations 2 sets
      - 60 min: 5 exercises, ALL 3 sets
      - 75 min: 6 exercises, compounds 3, some isolations 2
      - 90 min: 6 exercises, ALL 3 sets
      {sex_120min_line}
6. {sex_volume_aim}
7. Keep the first plan conservative — prefer {sex_conservative_pref} variants for
   low-experience users; prefer higher log_frequency exercises overall.
{sex_time_budget}8. {sex_order_rules}

Output STRICT JSON (no markdown, no commentary):

{{
  "sessions": [
    {{
      "order": 1,
      "name": "{sex_example_name}",
      "template_key": "{sex_example_key}",
      "exercises": [
        {{"name": "{sex_example_exercise}", "role": "main_compound",
         "movement_category": "{sex_example_category}", "sets": 3}},
        ...
      ]
    }},
    ...
  ]
}}

The number of sessions and their order/name/template_key MUST match the
skeleton. The number of exercises per session must equal the number of slots.

If the input includes a "last_week_performance" field, use it for CONTEXT ONLY.
It shows what the user actually did last week (avg weight, reps, RPE per exercise).
Use this to prefer exercises the user is already doing well — but do NOT change
the JSON output format or the slot/role/category rules."""


_SYSTEM_SEX_RULES = {
    "male": {
        "sex_upper": "MALE",
        "sex_split_intro": "",
        "sex_duplication_note": """
3a. AVOID REDUNDANT ANGLES inside one session. If a session has two
    horizontal_push slots, the second should be a DIFFERENT angle or grip
    (e.g. incline after flat, or dips after bench). Same for horizontal_pull.""",
        "sex_angle_variation": """3b. """,
        "sex_equip_detail": (
            'Specific biceps rule: if "Jednoručni preacher curl" is picked, the OTHER\n'
            '   biceps slot MUST be "Biceps pregib sa sipkom" (barbell), NOT dumbbell.\n'
            "   Never pair two dumbbell biceps variants. Same logic for triceps (don't\n"
            "   pair two cable variants — mix cable with overhead or skullcrushers)."
        ),
        "sex_120min_line": "- 120 min: 7 exercises, ALL 3 sets",
        "sex_volume_aim": (
            "Aim for weekly volume targets per muscle group. Prefer to slightly\n"
            "   under-shoot rather than over-shoot for the first plan."
        ),
        "sex_conservative_pref": "stable/machine",
        "sex_time_budget": (
            "7. The session time budget (max_slots) is a SOFT CAP. Going ~10-15 min\n"
            "   over is acceptable rather than dropping any exercise below 2 sets.\n"
        ),
        "sex_order_rules": (
            'EXERCISE ORDER RULE: "Rumunjsko mrtvo dizanje" (RDL) must ALWAYS be the\n'
            "   FIRST exercise in any session that includes it. If RDL is in the session,\n"
            "   it goes in slot 1 regardless of what the template says."
        ),
        "sex_example_name": "Push",
        "sex_example_key": "push",
        "sex_example_exercise": "Bench press",
        "sex_example_category": "horizontal_push",
    },
    "female": {
        "sex_upper": "FEMALE",
        "sex_split_intro": (
            "The female split uses two session types:\n"
            "  LOWER (lower_f1 / lower_f2) — heavy leg and glute compounds + isolations\n"
            "  FULL BODY (full_body_f)     — 2 leg/glute compounds first, then back, then arms\n\n"
        ),
        "sex_duplication_note": (
            " Across the week you may repeat\n"
            "   an exercise if the split repeats the same session type — but try to vary\n"
            "   where possible (e.g. use Step-ups in Full Body 2 if Bugarski was in Full Body 1)."
        ),
        "sex_angle_variation": "",
        "sex_equip_detail": (
            "Do not pair two dumbbell biceps variants; mix dumbbell with barbell or cable."
        ),
        "sex_120min_line": "",
        "sex_volume_aim": (
            "Aim for weekly volume targets per muscle group — especially gluteus,\n"
            "   kvadovi, zadnja_loza. Prefer to slightly under-shoot rather than over-shoot."
        ),
        "sex_conservative_pref": "machine/cable",
        "sex_time_budget": "",
        "sex_order_rules": (
            'EXERCISE ORDER RULES (apply in this priority):\n'
            '   a) "Rumunjsko mrtvo dizanje" — ALWAYS slot 1 if in the session.\n'
            '   b) "Hip thrust" — ALWAYS directly after RDL (slot 2 if RDL present,\n'
            '      slot 1 if RDL is absent). Hip thrust requires the most hip-hinge\n'
            '      energy and must come before knee-dominant or single-leg work.\n'
            '   c) Single-leg exercises (Bugarski cucanj, Step-ups) — after hip thrust.\n'
            '   d) Back exercises (lat pulldown, cable row) — after all leg compounds.\n'
            '   e) Isolations — always last.'
        ),
        "sex_example_name": "Lower 1",
        "sex_example_key": "lower_f1",
        "sex_example_exercise": "Rumunjsko mrtvo dizanje",
        "sex_example_category": "hip_hinge",
    },
}


# ---------------------------------------------------------------------------
# Refinement prompt — shared base + sex-specific rules
# ---------------------------------------------------------------------------

_REFINEMENT_PROMPT_BASE = """You are refining a weekly training plan ({sex_upper} athlete) you previously drafted.
A python validator computed the actual effective-set volume per muscle group
from your draft and compared it to the target. You will receive:
- the original SKELETON
- your previous DRAFT plan
- a VALIDATION report listing muscles UNDER target, OVER target, or OK

Your job: produce a REFINED plan that fixes under/over issues while respecting
all original rules (slot role/category match, only exercises from filtered pool,
no duplicates within a session, conservative sets).

{sex_priority_note}Strategies:
- Swap an exercise for another in the SAME slot category{sex_swap_detail}.
- Adjust sets up or down by 1 (within 2-3 for isolation, exactly 3 for compounds).
- Pick variants with higher activation on the under-target muscle.

Do NOT change the split, number of sessions, or slot structure.
Output the SAME JSON shape — strict JSON only, no commentary."""


_REFINEMENT_SEX_RULES = {
    "male": {
        "sex_upper": "MALE",
        "sex_priority_note": "",
        "sex_swap_detail": " that better hits\n  the under-target muscle",
    },
    "female": {
        "sex_upper": "FEMALE",
        "sex_priority_note": (
            "Priority muscles for female plans: gluteus, kvadovi, zadnja_loza.\n"
            "If these are under target, swap isolation or secondary compound exercises\n"
            "for ones with higher activation scores on these muscles.\n\n"
        ),
        "sex_swap_detail": "",
    },
}


# ---------------------------------------------------------------------------
# JSON fix helper
# ---------------------------------------------------------------------------

def _fix_json(raw: str) -> str:
    import re
    raw = re.sub(r'(?<=[{,])\s*(\w+)\s*:', r' "\1":', raw)
    raw = re.sub(r',\s*([}\]])', r'\1', raw)
    return raw


# ---------------------------------------------------------------------------
# OpenAI call
# ---------------------------------------------------------------------------

def _call_openai(system: str, user: str, max_tokens: int = 2000,
                 retries: int = 2) -> dict:
    for attempt in range(retries + 1):
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.4,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"].strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            try:
                return json.loads(_fix_json(raw))
            except json.JSONDecodeError:
                if attempt < retries:
                    continue
                raise


# ---------------------------------------------------------------------------
# Skeleton compactor — strip the pool down so the prompt stays small
# ---------------------------------------------------------------------------

def _compact_pool(pool: list[dict]) -> list[dict]:
    return [
        {"n": ex["name"], "r": ex["role"], "c": ex["movement_category"]}
        for ex in pool
    ]


def _compact_skeleton(skeleton: dict) -> dict:
    return {
        "split_id": skeleton["split_id"],
        "max_slots": skeleton["max_slots"],
        "profile": skeleton["profile_summary"],
        "limitations": skeleton["limitations"],
        "volume_targets": skeleton["volume_targets"],
        "sessions": [
            {
                "order": s["order"],
                "name": s["name"],
                "template_key": s["template_key"],
                "slots": s["slots"],
            }
            for s in skeleton["sessions"]
        ],
        "filtered_pool": _compact_pool(skeleton["filtered_pool"]),
    }


# ---------------------------------------------------------------------------
# Public calls
# ---------------------------------------------------------------------------

def _pick_prompts(skeleton: dict) -> tuple[str, str]:
    """Return (draft_system_prompt, refinement_prompt) based on sex."""
    sex = skeleton.get("profile_summary", {}).get("sex", "male")
    key = sex if sex in ("male", "female") else "male"
    system = _SYSTEM_PROMPT_BASE.format(**_SYSTEM_SEX_RULES[key])
    refine = _REFINEMENT_PROMPT_BASE.format(**_REFINEMENT_SEX_RULES[key])
    return system, refine


def draft_plan(skeleton: dict, actuals: dict | None = None) -> dict:
    system_prompt, _ = _pick_prompts(skeleton)
    payload = _compact_skeleton(skeleton)
    if actuals:
        payload["last_week_performance"] = actuals
    user_payload = json.dumps(payload, ensure_ascii=False)
    return _call_openai(system_prompt, user_payload, max_tokens=1200, retries=1)


def _compact_skeleton_for_refine(skeleton: dict, validation_report: dict) -> dict:
    """
    Smaller skeleton for the refinement call: drop pool exercises that can't
    help fix under-target muscles — keeps payload well under token limit.
    """
    under_muscles: set[str] = {
        r["muscle"] for r in validation_report.get("issues", {}).get("under", [])
    }

    # Keep exercises that hit at least one under-target muscle, plus all
    # exercises already used in the draft (so the AI knows what it picked).
    used_names: set[str] = set()
    for sess in skeleton.get("sessions", []):
        for ex in sess.get("exercises", []):
            used_names.add(ex.get("name", ""))

    filtered = []
    for ex in skeleton["filtered_pool"]:
        primary = set(ex.get("primary_muscles", []))
        secondary = set(ex.get("secondary_muscles", []))
        if (primary | secondary) & under_muscles or ex["name"] in used_names:
            filtered.append(ex)

    slim = _compact_skeleton(skeleton)
    slim["filtered_pool"] = _compact_pool(filtered)
    return slim


def refine_plan(skeleton: dict, draft: dict, validation_report: dict,
                actuals: dict | None = None) -> dict:
    """
    Refine the draft plan based on the validation report.
    Returns refined plan dict, or the original draft if payload is too large
    or refinement fails.
    """
    _, refinement_prompt = _pick_prompts(skeleton)
    slim_skeleton = _compact_skeleton_for_refine(skeleton, validation_report)
    payload = {
        "skeleton": slim_skeleton,
        "draft": draft,
        "validation": {
            "under": validation_report["issues"]["under"],
            "over": validation_report["issues"]["over"],
        },
    }
    if actuals:
        payload["last_week_performance"] = actuals
    user_payload = json.dumps(payload, ensure_ascii=False)

    # Skip if payload too large — refine would truncate and waste ~30s
    if len(user_payload) > 5000:
        import logging
        logging.getLogger(__name__).info(
            "refine_plan skipped (payload %d chars) — using draft.", len(user_payload)
        )
        return draft

    try:
        return _call_openai(refinement_prompt, user_payload, max_tokens=1500, retries=0)
    except (json.JSONDecodeError, Exception):
        import logging
        logging.getLogger(__name__).warning(
            "refine_plan failed — using draft as final plan."
        )
        return draft
