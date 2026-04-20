# FitOS-AI — Kontekst za novi AI razgovor

## Tech stack
- Django 5.2, Python 3.13, SQLite
- GPT-4o-mini via **httpx direktni POST** (ne OpenAI SDK — SDK hanga na Windowsu)
- Tailwind CSS CDN (no build step — razvoj), vanilla JS
- Working dir: `C:\Users\Luka\Downloads\FitOS-AI`
- Pokreće se: `python manage.py runserver`

---

## Arhitektura — kako radi plan generation

```
IntakeProfile
    ↓
build_skeleton()           # plans/plan_maker.py — koji split, koliko slotova, volume targets
    ↓
draft_plan() [AI #1]       # plans/plan_ai.py — GPT bira vježbe za svaki slot
    ↓
validate_volume()          # jesu li mišićne grupe pokrivene?
    ↓
refine_plan() [AI #2]      # (skip ako payload > 5000 chars)
    ↓
_sanitize_sessions()
    ↓
_sort_exercises()
    ↓
WeeklyPlan + PlannedSession + PlannedExercise (DB)
```

Generacija traje ~13s. Entry point: `plans/service.py → generate_plan_for(profile)`.

---

## Ključni modeli

### `plans/models.py`
```python
WeeklyPlan      # user, week_number, split_type, days_per_week, max_session_minutes
PlannedSession  # plan FK, order, name ("Push"), template_key ("push")
PlannedExercise # session FK, order, name, role, sets, reps_min, reps_max, target_rpe, weight_kg (null=establish)
```

### `logs/models.py`
```python
TrainingLog     # user FK, planned_session FK, started_at, ended_at, notes, fatigue (1-5), is_finished
LoggedExercise  # training_log FK, planned_exercise FK, order, name
LoggedSet       # logged_exercise FK, set_number, weight_kg, reps_done, rpe_done, completed
```

### `feedback/models.py`
```python
WeeklyFeedback  # user, week_of, sleep_quality (1-5), stress_level (1-5), doms_level (1-5), training_notes, ai_summary
```

### `intake/models.py`
```python
IntakeProfile   # user, sex, age, days_per_week_available, max_session_minutes,
                # body_part_priority, primary_goal, training_experience_level,
                # injuries (JSONField), disliked_exercises (JSONField)
```

---

## Tijek korisnika

1. **Intake wizard** (4 koraka) → sprema `IntakeProfile`
2. **Generate Plan** → `plans/service.py → generate_plan_for()` → AI kreira `WeeklyPlan`
3. **Log workout** → session picker → `log_session.html` (per-exercise RPE slider, ghost values za previous)
4. **Weekly Feedback** → `feedback/views.py` → submit Sleep/Stress/DOMS → klikni "Accept plan for next week"
5. **Generate next week** → `feedback/views.py → generate_next_week()` → opet `generate_plan_for()` → redirect na weekly plan

---

## Što je napravljeno u zadnjoj sesiji

### `templates/logs/log_session.html` (najveće izmjene)
- **Target RPE** i **sets×reps** premješteni u desni kut exercise card headera, istaknuti (veliki broj)
- **Rest timer**: main_compound → 4 min, ostalo → 2:30 min (čita `data-role` s check buttona)
- **Add Set gumb** uklonjen (setovi su fiksirani planom)
- **Fatigue picker** (1–5) dodan u "Workout complete" modal — plain CSS hover (bez Tailwind CDN) za brzu animaciju
- **Volume na page load** se sad izračunava iz DOM-a (`calcInitialVolume()`) umjesto hardkodiranog 0
- `transition-all` → `transition-colors` svugdje (performance fix)

### `logs/models.py`
- Dodano `fatigue = PositiveSmallIntegerField(null=True)` na `TrainingLog`
- Migration: `logs/migrations/0002_traininglog_fatigue.py`

### `logs/views.py`
- `finish_session()` sad sprema `fatigue` field
- `log_session()` — **"Previous" lookup sad traži po `ex.name`** (ne po `planned_exercise FK`!) → radi između tjedana
- `session_picker()` — `done_this_week` flag (last_log unutar 7 dana)

### `templates/logs/session_picker.html`
- Završena sesija: `opacity-70`, "Done" badge (teal, top-right), gumb postaje "Repeat Workout"

### `core/views.py`
- Progression queue threshold: `log_count__gte=3` → `log_count__gte=1`

### `feedback/views.py`
- Error logging: sad prikazuje konkretnu grešku umjesto generičke poruke

### `templates/feedback/weekly_feedback.html`
- "Accept plan for next week" sad prikazuje isti full-screen loading overlay kao generate plan (progress bar 0→90% za 13s)

---

## Poznati bugovi / TODO

### 🔴 HITNO — Progression logic ne radi
**Problem:** `generate_plan_for()` ne gleda prošlotjedne logove. Novi plan ima identične rep rangove i nema `weight_kg` popunjen na temelju stvarne izvedbe.

**Što treba implementirati u `plans/service.py`:**

```python
def _get_last_week_actuals(user):
    """Vraća {exercise_name: {avg_rpe, avg_weight, sets_done, avg_reps}} iz zadnjih logova."""
    result = {}
    logs = TrainingLog.objects.filter(user=user, is_finished=True).order_by('-started_at')[:10]
    for tlog in logs:
        for lex in tlog.logged_exercises.prefetch_related('sets').all():
            if lex.name in result:
                continue
            completed = [s for s in lex.sets.all() if s.completed and s.weight_kg and s.reps_done]
            if not completed:
                continue
            result[lex.name] = {
                'avg_rpe': round(sum(float(s.rpe_done or 0) for s in completed) / len(completed), 1),
                'avg_weight': round(sum(float(s.weight_kg) for s in completed) / len(completed), 1),
                'sets_done': len(completed),
                'avg_reps': round(sum(s.reps_done for s in completed) / len(completed), 1),
            }
    return result
```

Proslijedi `actuals` u `draft_plan()` i dodaj u system prompt:
```
LAST WEEK PERFORMANCE:
- Bench press: 3 sets, avg 60kg, avg 7.5 reps, avg RPE 7.5
  → Within range, moderate RPE → same prescription or +2.5kg
```

**Progression rules:**
- `avg_rpe <= 7.0` AND `avg_reps >= reps_max` → progress (+2.5kg compounds, +1kg iso)
- `avg_rpe 7.5–8.5` AND reps within range → isti prescription
- `avg_rpe >= 9.0` → deload (smanji reps_max ili težinu)

AI treba popuniti `weight_kg` na `PlannedExercise` (field već postoji, sad je `null`).

### 🟡 Kosmetičko — Week number
`week_number` je trenutno 132 (jer su generirani batch test planovi). Ako treba resetirati, filter `WeeklyPlan.objects.filter(user=user)` i ručno podesiti ili ignorirati.

### 🟡 Tjedan u session pickeru
`done_this_week` koristi `timedelta(days=7)` — radi OK za tjedni ciklus, ali nije vezano za kalendarski tjedan.

---

## Kako pokrenuti lokalno

```bash
cd C:\Users\Luka\Downloads\FitOS-AI
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
# .env file treba OPENAI_API_KEY=sk-proj-...
python manage.py migrate
python manage.py runserver
```

---

## Napomene za AI asistenta

- **NIKAD ne koristi OpenAI SDK** — koristi `httpx.post()` direktno (vidi `plans/plan_ai.py` za primjer)
- Tailwind CDN je spor — ne dodavaj `transition-all` (koristi `transition-colors`)
- Hover animacije za interaktivne elemente stavljaj u `<style>` block kao plain CSS (izbjegava Tailwind CDN re-scan)
- Git user: `luka2`, branch: `master`
- Previous set lookup u `logs/views.py` radi po `ex.name` (ne po FK) — važno za međutjedni continuity
