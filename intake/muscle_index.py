"""
Muscle activation index for all exercises in the FitOS pool.

Each exercise has a score 0-100 per muscle group:
  85-100 = primary mover
  40-70  = strong secondary
  15-30  = stabilizer/tertiary
  5-10   = minimal
  0      = not involved

Sources: Escamilla 2000/2001, Contreras 2012/2016, Lehman 2005,
         Fenwick 2009, Boehler 2011, Barnett 1995, Maeo 2021,
         NSCA Essentials 4th ed.

Muscle groups (14):
  prsa, gornja_leda, latovi, prednje_rame, srednje_rame, straznje_rame,
  triceps, biceps, kvadovi, zadnja_loza, gluteus, donja_leda, listovi, trbuh
"""

MUSCLE_GROUPS = [
    'prsa', 'gornja_leda', 'latovi', 'prednje_rame', 'srednje_rame',
    'straznje_rame', 'triceps', 'biceps', 'kvadovi', 'zadnja_loza',
    'gluteus', 'donja_leda', 'listovi', 'trbuh',
]

# fmt: off
EXERCISE_MUSCLE_INDEX = {

    # ============ HORIZONTAL PUSH ============

    "Bench press": {
        "prsa": 90, "gornja_leda": 20, "latovi": 10, "prednje_rame": 70,
        "srednje_rame": 15, "straznje_rame": 0, "triceps": 65, "biceps": 5,
        "kvadovi": 0, "zadnja_loza": 0, "gluteus": 10, "donja_leda": 15,
        "listovi": 0, "trbuh": 20,
    },
    "Kosi potisak bucicama": {
        "prsa": 85, "gornja_leda": 20, "latovi": 10, "prednje_rame": 75,
        "srednje_rame": 15, "straznje_rame": 0, "triceps": 60, "biceps": 5,
        "kvadovi": 0, "zadnja_loza": 0, "gluteus": 5, "donja_leda": 10,
        "listovi": 0, "trbuh": 20,
    },
    "Kosi bench press": {
        "prsa": 85, "gornja_leda": 20, "latovi": 10, "prednje_rame": 75,
        "srednje_rame": 15, "straznje_rame": 0, "triceps": 60, "biceps": 5,
        "kvadovi": 0, "zadnja_loza": 0, "gluteus": 5, "donja_leda": 10,
        "listovi": 0, "trbuh": 20,
    },
    "Chest press": {
        "prsa": 88, "gornja_leda": 10, "latovi": 5, "prednje_rame": 60,
        "srednje_rame": 10, "straznje_rame": 0, "triceps": 60, "biceps": 0,
        "kvadovi": 0, "zadnja_loza": 0, "gluteus": 0, "donja_leda": 5,
        "listovi": 0, "trbuh": 10,
    },
    "Propadanja": {
        "prsa": 85, "gornja_leda": 20, "latovi": 20, "prednje_rame": 65,
        "srednje_rame": 15, "straznje_rame": 5, "triceps": 70, "biceps": 10,
        "kvadovi": 0, "zadnja_loza": 0, "gluteus": 5, "donja_leda": 15,
        "listovi": 0, "trbuh": 25,
    },

    # ============ VERTICAL PULL ============

    "Lat pulldown": {
        "prsa": 0, "gornja_leda": 55, "latovi": 90, "prednje_rame": 10,
        "srednje_rame": 5, "straznje_rame": 30, "triceps": 0, "biceps": 65,
        "kvadovi": 0, "zadnja_loza": 0, "gluteus": 0, "donja_leda": 15,
        "listovi": 0, "trbuh": 15,
    },
    "Lat pulldown uski hvat": {
        "prsa": 0, "gornja_leda": 55, "latovi": 88, "prednje_rame": 10,
        "srednje_rame": 5, "straznje_rame": 25, "triceps": 0, "biceps": 70,
        "kvadovi": 0, "zadnja_loza": 0, "gluteus": 0, "donja_leda": 15,
        "listovi": 0, "trbuh": 15,
    },
    "Pullups": {
        "prsa": 5, "gornja_leda": 60, "latovi": 90, "prednje_rame": 10,
        "srednje_rame": 5, "straznje_rame": 30, "triceps": 0, "biceps": 70,
        "kvadovi": 0, "zadnja_loza": 0, "gluteus": 15, "donja_leda": 20,
        "listovi": 0, "trbuh": 25,
    },

    # ============ HORIZONTAL PULL ============

    "Veslanje u pretklonu sa sipkom": {
        "prsa": 0, "gornja_leda": 85, "latovi": 75, "prednje_rame": 0,
        "srednje_rame": 5, "straznje_rame": 65, "triceps": 0, "biceps": 60,
        "kvadovi": 20, "zadnja_loza": 30, "gluteus": 20, "donja_leda": 55,
        "listovi": 10, "trbuh": 30,
    },
    "Veslanje na sajli": {
        "prsa": 0, "gornja_leda": 85, "latovi": 70, "prednje_rame": 0,
        "srednje_rame": 5, "straznje_rame": 60, "triceps": 0, "biceps": 65,
        "kvadovi": 5, "zadnja_loza": 10, "gluteus": 5, "donja_leda": 30,
        "listovi": 0, "trbuh": 20,
    },
    "Veslanje bucicom": {
        "prsa": 0, "gornja_leda": 80, "latovi": 85, "prednje_rame": 0,
        "srednje_rame": 0, "straznje_rame": 55, "triceps": 0, "biceps": 65,
        "kvadovi": 10, "zadnja_loza": 15, "gluteus": 10, "donja_leda": 20,
        "listovi": 0, "trbuh": 20,
    },
    "Veslanje sprava": {
        "prsa": 0, "gornja_leda": 85, "latovi": 70, "prednje_rame": 0,
        "srednje_rame": 5, "straznje_rame": 55, "triceps": 0, "biceps": 60,
        "kvadovi": 0, "zadnja_loza": 0, "gluteus": 0, "donja_leda": 10,
        "listovi": 0, "trbuh": 10,
    },
    "T-bar": {
        "prsa": 0, "gornja_leda": 85, "latovi": 80, "prednje_rame": 0,
        "srednje_rame": 5, "straznje_rame": 60, "triceps": 0, "biceps": 65,
        "kvadovi": 20, "zadnja_loza": 25, "gluteus": 20, "donja_leda": 50,
        "listovi": 10, "trbuh": 25,
    },
    "Cable row siroki": {
        "prsa": 0, "gornja_leda": 85, "latovi": 65, "prednje_rame": 0,
        "srednje_rame": 5, "straznje_rame": 65, "triceps": 0, "biceps": 60,
        "kvadovi": 5, "zadnja_loza": 10, "gluteus": 5, "donja_leda": 25,
        "listovi": 0, "trbuh": 20,
    },

    # ============ SQUAT / KNEE-DOMINANT ============

    "Leg press": {
        "prsa": 0, "gornja_leda": 0, "latovi": 0, "prednje_rame": 0,
        "srednje_rame": 0, "straznje_rame": 0, "triceps": 0, "biceps": 0,
        "kvadovi": 90, "zadnja_loza": 30, "gluteus": 35, "donja_leda": 10,
        "listovi": 15, "trbuh": 15,
    },
    "Hack squat": {
        "prsa": 0, "gornja_leda": 10, "latovi": 0, "prednje_rame": 0,
        "srednje_rame": 0, "straznje_rame": 0, "triceps": 0, "biceps": 0,
        "kvadovi": 92, "zadnja_loza": 20, "gluteus": 25, "donja_leda": 10,
        "listovi": 20, "trbuh": 20,
    },
    "Bugarski cucanj": {
        "prsa": 0, "gornja_leda": 15, "latovi": 5, "prednje_rame": 5,
        "srednje_rame": 5, "straznje_rame": 0, "triceps": 0, "biceps": 0,
        "kvadovi": 85, "zadnja_loza": 40, "gluteus": 70, "donja_leda": 25,
        "listovi": 20, "trbuh": 30,
    },
    "Step-ups": {
        "prsa": 0, "gornja_leda": 5, "latovi": 0, "prednje_rame": 0,
        "srednje_rame": 0, "straznje_rame": 0, "triceps": 0, "biceps": 0,
        "kvadovi": 75, "zadnja_loza": 20, "gluteus": 65, "donja_leda": 10,
        "listovi": 15, "trbuh": 15,
    },

    # ============ HIP HINGE ============

    "Rumunjsko mrtvo dizanje": {
        "prsa": 0, "gornja_leda": 30, "latovi": 25, "prednje_rame": 0,
        "srednje_rame": 0, "straznje_rame": 10, "triceps": 0, "biceps": 15,
        "kvadovi": 20, "zadnja_loza": 90, "gluteus": 75, "donja_leda": 60,
        "listovi": 10, "trbuh": 25,
    },
    "Stiff leg deadlift": {
        "prsa": 0, "gornja_leda": 30, "latovi": 25, "prednje_rame": 0,
        "srednje_rame": 0, "straznje_rame": 10, "triceps": 0, "biceps": 15,
        "kvadovi": 15, "zadnja_loza": 92, "gluteus": 75, "donja_leda": 65,
        "listovi": 10, "trbuh": 25,
    },

    # ============ CHEST ISOLATION ============

    "Razvlacenje za prsa na sajli": {
        "prsa": 88, "gornja_leda": 10, "latovi": 10, "prednje_rame": 45,
        "srednje_rame": 10, "straznje_rame": 5, "triceps": 5, "biceps": 10,
        "kvadovi": 0, "zadnja_loza": 0, "gluteus": 10, "donja_leda": 10,
        "listovi": 10, "trbuh": 20,
    },
    "Razvlacenje za prsa sprava": {
        "prsa": 88, "gornja_leda": 5, "latovi": 5, "prednje_rame": 40,
        "srednje_rame": 10, "straznje_rame": 0, "triceps": 5, "biceps": 5,
        "kvadovi": 0, "zadnja_loza": 0, "gluteus": 0, "donja_leda": 5,
        "listovi": 0, "trbuh": 10,
    },
    "Letenje bucicama": {
        "prsa": 85, "gornja_leda": 15, "latovi": 10, "prednje_rame": 50,
        "srednje_rame": 10, "straznje_rame": 0, "triceps": 10, "biceps": 5,
        "kvadovi": 0, "zadnja_loza": 0, "gluteus": 5, "donja_leda": 10,
        "listovi": 0, "trbuh": 15,
    },

    # ============ SHOULDER ISOLATION ============

    "Lateral raises": {
        "prsa": 0, "gornja_leda": 15, "latovi": 0, "prednje_rame": 25,
        "srednje_rame": 90, "straznje_rame": 15, "triceps": 0, "biceps": 0,
        "kvadovi": 0, "zadnja_loza": 0, "gluteus": 0, "donja_leda": 10,
        "listovi": 0, "trbuh": 15,
    },

    # ============ TRICEPS ISOLATION ============

    "Triceps ekstenzija iznad glave": {
        "prsa": 0, "gornja_leda": 10, "latovi": 20, "prednje_rame": 15,
        "srednje_rame": 5, "straznje_rame": 0, "triceps": 92, "biceps": 0,
        "kvadovi": 0, "zadnja_loza": 0, "gluteus": 0, "donja_leda": 15,
        "listovi": 0, "trbuh": 20,
    },
    "Triceps ekstenzija sajla": {
        "prsa": 0, "gornja_leda": 10, "latovi": 15, "prednje_rame": 10,
        "srednje_rame": 0, "straznje_rame": 0, "triceps": 90, "biceps": 0,
        "kvadovi": 0, "zadnja_loza": 0, "gluteus": 0, "donja_leda": 10,
        "listovi": 0, "trbuh": 15,
    },
    "Skullcrushers": {
        "prsa": 5, "gornja_leda": 10, "latovi": 10, "prednje_rame": 10,
        "srednje_rame": 0, "straznje_rame": 0, "triceps": 90, "biceps": 5,
        "kvadovi": 0, "zadnja_loza": 0, "gluteus": 0, "donja_leda": 10,
        "listovi": 0, "trbuh": 10,
    },

    # ============ BICEPS ISOLATION ============

    "Biceps pregib s bucicama": {
        "prsa": 0, "gornja_leda": 10, "latovi": 0, "prednje_rame": 20,
        "srednje_rame": 0, "straznje_rame": 0, "triceps": 0, "biceps": 90,
        "kvadovi": 0, "zadnja_loza": 0, "gluteus": 0, "donja_leda": 10,
        "listovi": 0, "trbuh": 15,
    },
    "Biceps pregib sa sipkom": {
        "prsa": 0, "gornja_leda": 10, "latovi": 0, "prednje_rame": 20,
        "srednje_rame": 0, "straznje_rame": 0, "triceps": 0, "biceps": 90,
        "kvadovi": 0, "zadnja_loza": 0, "gluteus": 0, "donja_leda": 10,
        "listovi": 0, "trbuh": 15,
    },
    "Jednoručni preacher curl": {
        "prsa": 0, "gornja_leda": 0, "latovi": 0, "prednje_rame": 0,
        "srednje_rame": 0, "straznje_rame": 0, "triceps": 0, "biceps": 92,
        "kvadovi": 0, "zadnja_loza": 0, "gluteus": 0, "donja_leda": 0,
        "listovi": 0, "trbuh": 0,
    },

    # ============ QUAD ISOLATION ============

    "Nozna ekstenzija": {
        "prsa": 0, "gornja_leda": 0, "latovi": 0, "prednje_rame": 0,
        "srednje_rame": 0, "straznje_rame": 0, "triceps": 0, "biceps": 0,
        "kvadovi": 95, "zadnja_loza": 0, "gluteus": 0, "donja_leda": 0,
        "listovi": 0, "trbuh": 5,
    },

    # ============ HAMSTRING ISOLATION ============

    "Lezeca fleksija": {
        "prsa": 0, "gornja_leda": 0, "latovi": 0, "prednje_rame": 0,
        "srednje_rame": 0, "straznje_rame": 0, "triceps": 0, "biceps": 0,
        "kvadovi": 0, "zadnja_loza": 92, "gluteus": 15, "donja_leda": 10,
        "listovi": 20, "trbuh": 0,
    },
    "Sjedeca fleksija": {
        "prsa": 0, "gornja_leda": 0, "latovi": 0, "prednje_rame": 0,
        "srednje_rame": 0, "straznje_rame": 0, "triceps": 0, "biceps": 0,
        "kvadovi": 0, "zadnja_loza": 92, "gluteus": 5, "donja_leda": 0,
        "listovi": 10, "trbuh": 5,
    },

    # ============ CALVES ============

    "Podizanje na prste": {
        "prsa": 0, "gornja_leda": 0, "latovi": 0, "prednje_rame": 0,
        "srednje_rame": 0, "straznje_rame": 0, "triceps": 0, "biceps": 0,
        "kvadovi": 0, "zadnja_loza": 5, "gluteus": 5, "donja_leda": 10,
        "listovi": 95, "trbuh": 10,
    },

    # ============ GLUTE / HIP ============

    "Hip thrust": {
        "prsa": 0, "gornja_leda": 5, "latovi": 0, "prednje_rame": 0,
        "srednje_rame": 0, "straznje_rame": 0, "triceps": 0, "biceps": 0,
        "kvadovi": 20, "zadnja_loza": 40, "gluteus": 95, "donja_leda": 15,
        "listovi": 5, "trbuh": 20,
    },
    "Hip abduction sprava": {
        "prsa": 0, "gornja_leda": 0, "latovi": 0, "prednje_rame": 0,
        "srednje_rame": 0, "straznje_rame": 0, "triceps": 0, "biceps": 0,
        "kvadovi": 0, "zadnja_loza": 0, "gluteus": 85, "donja_leda": 0,
        "listovi": 0, "trbuh": 5,
    },
    "Hip adduction sprava": {
        "prsa": 0, "gornja_leda": 0, "latovi": 0, "prednje_rame": 0,
        "srednje_rame": 0, "straznje_rame": 0, "triceps": 0, "biceps": 0,
        "kvadovi": 30, "zadnja_loza": 0, "gluteus": 15, "donja_leda": 0,
        "listovi": 0, "trbuh": 5,
    },
    "Cable kickback": {
        "prsa": 0, "gornja_leda": 0, "latovi": 0, "prednje_rame": 0,
        "srednje_rame": 0, "straznje_rame": 0, "triceps": 0, "biceps": 0,
        "kvadovi": 0, "zadnja_loza": 15, "gluteus": 90, "donja_leda": 5,
        "listovi": 0, "trbuh": 10,
    },

    # ============ ABS ============

    "Plank": {
        "prsa": 5, "gornja_leda": 30, "latovi": 20, "prednje_rame": 25,
        "srednje_rame": 20, "straznje_rame": 15, "triceps": 20, "biceps": 10,
        "kvadovi": 30, "zadnja_loza": 20, "gluteus": 35, "donja_leda": 40,
        "listovi": 15, "trbuh": 85,
    },
    "Podizanje nogu": {
        "prsa": 0, "gornja_leda": 20, "latovi": 25, "prednje_rame": 15,
        "srednje_rame": 10, "straznje_rame": 5, "triceps": 0, "biceps": 10,
        "kvadovi": 30, "zadnja_loza": 0, "gluteus": 10, "donja_leda": 15,
        "listovi": 0, "trbuh": 90,
    },
}
# fmt: on


def get_weekly_muscle_volume(plan_exercises: list[dict]) -> dict:
    """
    Calculate weekly muscle volume scores from a list of exercises.

    Each exercise dict needs: {"name": str, "sets": int}
    Returns: {"prsa": 270, "triceps": 195, ...}

    Score = sum of (sets * muscle_score) for each exercise.
    Higher = more volume on that muscle group.
    """
    volume = {m: 0 for m in MUSCLE_GROUPS}
    for ex in plan_exercises:
        name = ex["name"]
        sets = ex.get("sets", 3)
        if name in EXERCISE_MUSCLE_INDEX:
            for muscle, score in EXERCISE_MUSCLE_INDEX[name].items():
                volume[muscle] += sets * score
    return volume


def get_muscle_heatmap(volume: dict) -> dict:
    """
    Normalize volume dict to 0-100 scale for heatmap display.
    100 = most trained muscle group, 0 = least.
    """
    if not volume:
        return {m: 0 for m in MUSCLE_GROUPS}
    max_val = max(volume.values()) or 1
    return {m: round((v / max_val) * 100) for m, v in volume.items()}
