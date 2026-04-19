"""
Weekly volume targets per muscle group, in EFFECTIVE SETS.

Baseline: Schoenfeld / Helms hypertrophy guidance — 10-20 effective sets/week
per muscle group is the productive range. We pick a starting point inside that
range, then scale by:
  - body_part_priority (which groups get a boost)
  - sex (men → upper bias by default, women → lower bias by default)
  - days_per_week (fewer days → slightly lower totals because budget is tight)

The output is a dict {muscle: target_effective_sets} that the plan maker
later compares against actually-prescribed volume from muscle_index.
"""
from intake.muscle_index import MUSCLE_GROUPS


# Baseline (men, balanced, 4 days/week, intermediate). All in EFFECTIVE SETS / week.
# Numbers picked inside the 10-20 productive range, biased low so first plan
# is conservative and easy to scale up rather than rescue.
BASELINE_M_BALANCED = {
    "prsa":          12,
    "gornja_leda":   12,
    "latovi":        10,
    "prednje_rame":  10,   # heavy indirect from all pressing — naturally high
    "srednje_rame":   8,
    "straznje_rame":  6,
    "triceps":        8,
    "biceps":        12,   # heavy indirect from all pulling — naturally high
    "kvadovi":       12,
    "zadnja_loza":   10,
    "gluteus":        8,
    "donja_leda":     6,   # mostly indirect from compounds
    "listovi":        6,
    "trbuh":         10,   # heavy indirect from compounds as stabilizer
}

# Female balanced — lower body bias (~55-60 / 40-45)
BASELINE_F_BALANCED = {
    "prsa":           8,
    "gornja_leda":   10,
    "latovi":         8,
    "prednje_rame":   8,   # heavy indirect from pressing
    "srednje_rame":   6,
    "straznje_rame":  6,
    "triceps":        6,
    "biceps":        10,   # heavy indirect from pulling
    "kvadovi":       14,
    "zadnja_loza":   12,
    "gluteus":       14,
    "donja_leda":     6,
    "listovi":        6,
    "trbuh":         10,   # heavy indirect from compounds as stabilizer
}


# Body-part priority modifiers — multiplicative on baseline.
# Lists are which groups get boosted; everything else stays at 1.0.
PRIORITY_BOOSTS = {
    "upper_priority": {
        "boost": ["prsa", "gornja_leda", "latovi", "srednje_rame", "triceps", "biceps"],
        "boost_factor": 1.20,
        "cut": ["kvadovi", "zadnja_loza", "gluteus"],
        "cut_factor": 0.85,
    },
    "lower_priority": {
        "boost": ["kvadovi", "zadnja_loza", "gluteus", "listovi"],
        "boost_factor": 1.20,
        "cut": ["prsa", "gornja_leda", "latovi", "biceps", "triceps"],
        "cut_factor": 0.85,
    },
    "balanced": {
        "boost": [], "boost_factor": 1.0,
        "cut": [],   "cut_factor": 1.0,
    },
}


def _days_factor(days_per_week: int) -> float:
    """
    Fewer training days → less weekly volume budget. Capped so 2-day plans
    still hit ~75% of normal totals (otherwise we'd undertrain).
    """
    if days_per_week <= 2:
        return 0.75
    if days_per_week == 3:
        return 0.85
    if days_per_week == 4:
        return 1.00
    if days_per_week == 5:
        return 1.10
    return 1.15  # 6+


def get_volume_targets(sex: str,
                        body_part_priority: str,
                        days_per_week: int) -> dict[str, float]:
    """
    Return {muscle: target_effective_sets_per_week} after applying sex,
    priority and days-per-week modifiers.
    """
    base = (BASELINE_F_BALANCED if sex == "female" else BASELINE_M_BALANCED).copy()

    rule = PRIORITY_BOOSTS.get(body_part_priority, PRIORITY_BOOSTS["balanced"])
    boost_set = set(rule["boost"])
    cut_set = set(rule["cut"])

    days_mult = _days_factor(days_per_week)

    out = {}
    for m in MUSCLE_GROUPS:
        v = base.get(m, 6)
        if m in boost_set:
            v *= rule["boost_factor"]
        if m in cut_set:
            v *= rule["cut_factor"]
        v *= days_mult
        out[m] = round(v, 1)
    return out
