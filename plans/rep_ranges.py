"""
Rep ranges per exercise (from MVP/EXCERSISES/rep_ranges.md).

Each entry: (reps_min, reps_max). Used to assign prescribed reps after AI
selects exercises. If exercise not in table, fall back to ROLE_DEFAULTS.
"""

# Full rep ranges. reps_min here is the FLOOR — the lowest we'd ever go.
# For heavy compounds, the true floor (5 reps) is locked behind a strength
# threshold (see LOWER_REP_UNLOCK below). Until then, the effective minimum
# is raised to 6 via get_prescription().
REP_RANGES: dict[str, tuple[int, int]] = {
    # Horizontal Push
    "Bench press": (5, 12),
    "Kosi potisak bucicama": (6, 15),
    "Kosi bench press": (8, 12),
    "Propadanja": (6, 13),
    "Chest press": (8, 12),

    # Vertical Pull
    "Lat pulldown": (6, 15),
    "Lat pulldown uski hvat": (8, 12),
    "Pullups": (5, 10),

    # Horizontal Pull
    "Veslanje u pretklonu sa sipkom": (6, 12),
    "Veslanje na sajli": (6, 15),
    "Veslanje bucicom": (8, 15),
    "Veslanje sprava": (6, 12),
    "T-bar": (10, 15),
    "Cable row siroki": (8, 12),

    # Squat / Knee-Dominant
    "Leg press": (5, 12),
    "Hack squat": (5, 13),
    "Bugarski cucanj": (8, 13),
    "Step-ups": (8, 14),

    # Hip Hinge
    "Rumunjsko mrtvo dizanje": (5, 12),
    "Stiff leg deadlift": (8, 10),

    # Chest isolation
    "Razvlacenje za prsa na sajli": (8, 15),
    "Razvlacenje za prsa sprava": (8, 15),
    "Letenje bucicama": (6, 15),

    # Shoulder isolation
    "Lateral raises": (9, 15),

    # Triceps isolation
    "Triceps ekstenzija iznad glave": (6, 14),
    "Triceps ekstenzija sajla": (8, 15),
    "Skullcrushers": (8, 15),

    # Biceps isolation
    "Biceps pregib s bucicama": (6, 15),
    "Biceps pregib sa sipkom": (6, 15),
    "Jednoručni preacher curl": (9, 15),

    # Quad isolation
    "Nozna ekstenzija": (8, 15),

    # Hamstring isolation
    "Lezeca fleksija": (8, 15),
    "Sjedeca fleksija": (8, 15),

    # Calves
    "Podizanje na prste": (8, 15),

    # Glute / Hip
    "Hip thrust": (5, 12),
    "Hip abduction sprava": (8, 15),
    "Hip adduction sprava": (8, 15),
    "Cable kickback": (8, 15),

    # Abs
    "Plank": (0, 0),  # time-based: 0 = establish_needed (user sets first value)
    "Podizanje nogu": (7, 12),
}


# Default by role if exercise not found in REP_RANGES.
ROLE_DEFAULTS = {
    "main_compound":      {"sets": 3, "reps_min": 6,  "reps_max": 10, "rpe": 8,  "rest": "3-5min"},
    "secondary_compound": {"sets": 3, "reps_min": 8,  "reps_max": 12, "rpe": 8,  "rest": "1-3min"},
    "isolation":          {"sets": 3, "reps_min": 10, "reps_max": 15, "rpe": 9,  "rest": "1-3min"},
}


def get_prescription(exercise_name: str, role: str,
                      first_plan: bool = False) -> dict:
    """
    Return {sets, reps_min, reps_max, rpe, rest} for an exercise.
    Pulls reps from REP_RANGES if available, otherwise uses role defaults.

    first_plan=True narrows the rep window to (reps_min, reps_min + 2) so
    the user establishes loads at the bottom of the range and has clear
    room to grow. Used for week 1 of every fresh plan.
    """
    base = ROLE_DEFAULTS.get(role, ROLE_DEFAULTS["secondary_compound"]).copy()
    if exercise_name in REP_RANGES:
        rmin, rmax = REP_RANGES[exercise_name]
        base["reps_min"] = rmin
        base["reps_max"] = rmax

    # Lock lower reps (5) for heavy compounds until strength threshold met.
    # Effective minimum becomes 6 until unlocked.
    if exercise_name in LOWER_REP_LOCKED and not _LOWER_REPS_UNLOCKED:
        base["reps_min"] = max(base["reps_min"], 6)

    if first_plan and exercise_name != "Plank":
        base["reps_max"] = base["reps_min"] + 2

    return base


# Exercises that use time (seconds) instead of reps.
TIME_BASED_EXERCISES = {"Plank"}

# Heavy compounds where the true reps_min (5) is locked until the user
# reaches a strength threshold. Until unlocked, effective reps_min = 6.
#
# Unlock conditions (checked when TrainingLog exists):
#   - Barbell/machine compounds: working weight >= 2/3 * bodyweight
#   - Pullups: added weight >= 5kg
#   - Until then, we clamp reps_min to max(reps_min, 6).
#
# TODO: implement unlock check once TrainingLog model is in place.
LOWER_REP_LOCKED = {
    "Bench press",
    "Pullups",
    "Leg press",
    "Hack squat",
    "Rumunjsko mrtvo dizanje",
    "Hip thrust",
}

# Per-exercise unlock thresholds. Once working weight exceeds this,
# reps_min drops to the true floor (5).
# Format: exercise_name -> (threshold_kg, condition_description)
UNLOCK_THRESHOLDS = {
    "Bench press":             ("2/3_bodyweight", "working weight >= 2/3 bodyweight"),
    "Pullups":                 (5,               "added weight >= 5kg"),
    "Leg press":               ("2/3_bodyweight", "working weight >= 2/3 bodyweight"),
    "Hack squat":              (30,              "working weight >= 30kg"),
    "Rumunjsko mrtvo dizanje": ("2/3_bodyweight", "working weight >= 2/3 bodyweight"),
}

# Currently always True — no training logs exist yet.
# Once TrainingLog is implemented, this becomes a per-exercise check.
_LOWER_REPS_UNLOCKED = False
