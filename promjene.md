# FitOS-AI — Context za nastavak razvoja

## Projekt

FitOS-AI je Django 6.0 fitness coaching aplikacija koja koristi GPT-4o-mini za generiranje personaliziranih tjednih planova treninga. Korisnik ispuni intake upitnik (4 koraka), AI generira plan, korisnik logira treninge, daje weekly feedback, i AI prilagođava sljedeći tjedan.

**Tech stack:** Django 6.0, Python 3.13, SQLite, GPT-4o-mini (OpenAI API), Tailwind CSS (CDN), vanilla JS. Nema npm/webpack/React — sve je server-rendered Django templates.

**Repo:** https://github.com/lux2324/FitOS-AI.git, branch: master

---

## Struktura (6 Django appova, ~7,000 LOC)

```
FitOS-AI/
├── fitos/              # Django config (settings.py, urls.py)
├── core/    230 LOC    # Dashboard view (KPIs, readiness, streak, volume trend)
├── users/   137 LOC    # Auth (custom User model, login/register/logout)
├── intake/  772 LOC    # Onboarding wizard (4 steps + AI injury analysis)
│   ├── models.py       # IntakeProfile (sex, age, goals, days/week, limitations)
│   ├── forms.py        # Step forms
│   ├── ai_service.py   # OpenAI call za analizu ozljeda
│   └── muscle_index.py # Exercise → muscle activation mapping (342 LOC static data)
├── plans/  1,935 LOC   # AI plan generation (BIGGEST MODULE)
│   ├── models.py       # WeeklyPlan, PlannedSession, PlannedExercise
│   ├── service.py      # Pipeline: skeleton → AI draft → refine → sanitize → sort → save
│   ├── plan_maker.py   # Split selection, volume targets, constraints
│   ├── plan_ai.py      # GPT-4o-mini prompts (sex-aware, template-based)
│   ├── exercise_pool.py # YAML loader + sex/limitation filtering
│   ├── rep_ranges.py   # Per-exercise rep prescriptions
│   ├── volume_targets.py # Weekly set targets per muscle group
│   ├── views.py        # weekly_plan, generate, batch_generate, substitute_exercise
│   └── data/exercise_pool.yaml  # 50+ exercises, Croatian names, 714 lines
├── logs/    576 LOC    # Workout logging + statistics
│   ├── models.py       # TrainingLog, LoggedExercise, LoggedSet
│   └── views.py        # session_picker, log_session, save_set (AJAX),
│                       # finish_session, summary, statistika
├── feedback/ 179 LOC   # Weekly feedback + AI coach
│   ├── models.py       # WeeklyFeedback (sleep 1-5, stress 1-5, DOMS 1-5, notes)
│   └── views.py        # feedback_form, generate_next_week
└── templates/          # Tailwind dark theme, all extend base_tw.html
    ├── base_tw.html    # Sidebar, header, shared CSS (glass-panel, etc.)
    ├── core/dashboard.html
    ├── plans/weekly_plan.html
    ├── logs/{session_picker,log_session,summary,statistika}.html
    └── feedback/weekly_feedback.html
```

---

## URL Routes (16 endpoints)

```
/                           core:home              Dashboard
/plan/                      plans:weekly_plan       Weekly plan view
/plan/generate/             plans:generate          POST: generate plan
/plan/batch/                plans:batch_generate    POST: batch compare
/plan/substitute/           plans:substitute_exercise POST: AI exercise swap
/log/                       logs:session_picker     Pick session to start
/log/start/<id>/            logs:start_session      POST: create TrainingLog
/log/<id>/                  logs:log_session        Live workout page
/log/<id>/save-set/         logs:save_set           POST AJAX: save one set
/log/<id>/save-note/        logs:save_note          POST AJAX: save notes
/log/<id>/finish/           logs:finish_session     POST: finish workout
/log/<id>/summary/          logs:summary            Post-workout summary
/log/statistika/            logs:statistika         Statistics page
/feedback/weekly/           feedback:weekly         Weekly feedback form
/feedback/                  feedback:feedback_form  Alias → weekly
/feedback/generate-next/    feedback:generate_next_week  POST: gen next plan
```

---

## Plan Generation Pipeline (plans/service.py)

```
IntakeProfile → build_skeleton() → draft_plan() [AI#1] → compute_actual_volume()
→ validate_volume() → refine_plan() [AI#2] → _sanitize_sessions() [2-pass]
→ validate_constraints() → _sort_exercises() → _enforce_sets() → save to DB
```

- Sex-aware: female plans use lower_f1/lower_f2/full_body_f templates, no chest/pullups
- Sort priority: RDL (tier 0) → Hip thrust (tier 1) → compounds → isolations
- Sanitization: slot constraint check + pool membership check
- AI prompts are template-based: shared base + sex-specific rules dict

---

## Workout Logging UX (templates/logs/log_session.html — 921 LOC)

- Ghost value UX: previous session values shown as faded teal overlays
- Single click on check button → accepts previous values, marks set complete
- Click on ghost overlay → fills inputs with prev values
- Double-click on ghost → focuses input for custom entry
- Right panel: RPE slider (1-10, step 0.5), notes textarea, mini stats
- Impression modal: on "Finish Workout" → asks "How was the workout?" → saves notes
- Exercise swap: ⇄ button → modal → AI picks substitute from same pool
- AJAX: save_set, save_note auto-save on blur
- Rest timer with progress bar, +15s/Skip buttons

---

## Modeli (9 tablica)

```python
# users
User (AbstractUser)

# intake
IntakeProfile (sex, age, height_cm, weight_kg, days_per_week_available,
               max_session_minutes, primary_goal, body_part_priority,
               training_experience_level, limitations JSON, completed bool)

# plans
WeeklyPlan (user, week_number, split_type, days_per_week, max_session_minutes,
            generation_params JSON, volume_targets JSON, volume_actual JSON,
            validation_report JSON, ai_draft JSON, ai_refined JSON)
PlannedSession (plan FK, order, name, template_key)
PlannedExercise (session FK, order, name, role, movement_category,
                 sets, reps_min, reps_max, target_rpe DecimalField(3,1),
                 rest, weight_kg nullable)

# logs
TrainingLog (user FK, planned_session FK, started_at, ended_at, notes, is_finished)
LoggedExercise (training_log FK, planned_exercise FK, order, name)
LoggedSet (logged_exercise FK, set_number, weight_kg, reps_done, rpe_done,
           completed bool, logged_at)

# feedback
WeeklyFeedback (user FK, week_start DateField, sleep_quality 1-5,
                stress_level 1-5, doms_level 1-5, training_notes, ai_summary)
```

---

## Što radi / Što je testirano

✅ Intake wizard (4 steps) → sprema IntakeProfile
✅ Plan generation (male/female, 3-6 days, 45-120 min, balanced/upper/lower priority)
✅ Plan display s volume report i body heatmap
✅ Test parameters panel (override intake za testnu generaciju)
✅ Batch compare (generira sve kombinacije paralelno)
✅ Exercise substitution via AI (⇄ button)
✅ Session picker → Start workout → Log sets → Finish → Summary
✅ Ghost value UX (previous set values as faded overlays)
✅ Weekly feedback form (sliders za sleep/stress/DOMS + notes)
✅ Weekly reset (plan_is_complete: 7 days OR all sessions done)
✅ Dashboard s KPIs (sessions, volume, streak, readiness, volume trend)
✅ Statistika (personal records, exercise filter, session type filter, SVG charts)
✅ Readiness score (computed from WeeklyFeedback)
✅ All templates extend base_tw.html (deduplicated sidebar, header, CSS)

---

## Poznati TODO-ovi / Što još treba

### Prioritet 1 — Core funkc. (nedovršeno)
1. **AI weekly summary**: Kad user submita feedback, pozvati OpenAI da generira `ai_summary` (analiza tjedna na temelju stats + feedback) — view je spreman, samo nedostaje OpenAI call
2. **Progression queue** na dashboardu je placeholder — treba prava logika: za svaku vježbu s 3+ logova, izračunaj avg RPE zadnja 3 treninga i preporuči LOAD +2.5 / REP +1 / HOLD
3. **Intake step2/step4 JS null-checks** — `getElementById` bez null guarda može crashati

### Prioritet 2 — UX/Polish
4. **English UI**: Većina UI je na engleskom ali ima ostataka hrvatskog teksta u nekim templateima (swap modal "Zamijeni vježbu", error poruke u views.py)
5. **Exercise pool data**: Nazivi vježbi su na hrvatskom (Bench press, Rumunjsko mrtvo dizanje, Hip thrust) — treba odlučiti: sve na EN ili HR
6. **Volume trend progress bar** na dashboardu koristi `consistency_pct` ali je fallback 50%
7. **Summary page** — total_volume_kg property radi in-memory loop, mogao bi biti annotation query

### Prioritet 3 — Production readiness
8. **SECRET_KEY** → .env (trenutno hardcoded u settings.py)
9. **ALLOWED_HOSTS** = [] → treba popuniti za production
10. **STATIC_ROOT** nedostaje → collectstatic ne radi
11. **users/views.py logout** nema @login_required
12. **OPENAI_API_KEY** null-check — crash ako .env nedostaje

### Prioritet 4 — Buduće feature
13. **AI feedback loop**: Training notes + weekly feedback → AI koristi za personalizaciju sljedećeg plana (prompt enhancement)
14. **Body weight tracking**: Dashboard ima "Masa" KPI ali nema model za praćenje težine
15. **Deload week logic**: Automatski deload nakon 4-6 tjedana visokog intenziteta
16. **Notification system**: Podsjetnici za trening, feedback
17. **Mobile responsive**: Trenutni UI je desktop-first

---

## Code Review — Popravljeno

- ✅ IDOR u save_set (exercise ownership validation)
- ✅ substitute_exercise ValueError catch
- ✅ start_session GET→POST (weekly_plan + dashboard)
- ✅ N+1 streak (loop → single query)
- ✅ N+1 volume trend (per-plan → batch)
- ✅ total_volume_kg .filter() breaking prefetch → .all() loop
- ✅ target_rpe PositiveIntegerField → DecimalField(3,1)
- ✅ Template deduplication (base_tw.html, shared CSS)
- ✅ Header bar centralized
- ✅ plan_ai.py 4 prompts → 2 templates

---

## Design System

- **Tailwind CSS via CDN** (no build step)
- **Dark theme**: bg #0a0e1a, surface #0f131f/#1b1f2c, primary #71ffe8
- **Fonts**: Space Grotesk (headlines), Inter (body)
- **Icons**: Material Symbols Outlined
- **Glass panels**: `backdrop-filter: blur(12px)`, subtle teal borders
- **Stitch mockups**: Reference designs at `stitch/` folder (Figma → HTML exports)
- **All pages extend `base_tw.html`** with blocks: title, sidebar_*, header_left, extra_css, body, extra_js

---

## Kako pokrenuti

```bash
cd C:\Users\Luka\Downloads\FitOS-AI
python manage.py runserver
# Login: http://127.0.0.1:8000/
# Treba OPENAI_API_KEY u environment za AI features
```

---

## Napomene za AI assistant

- Projekt koristi **Django template language** ({% %}, {{ }}), NE React/Vue
- **Nema npm/webpack** — Tailwind je CDN, JS je inline u templateima
- **OpenAI calls** su u `plans/plan_ai.py` (plan generation) i `intake/ai_service.py` (injury analysis)
- **Exercise pool** je YAML (`plans/data/exercise_pool.yaml`) — ne hardcoded Python
- **Croatian exercise names** u bazi (Bench press, Rumunjsko mrtvo dizanje, Hip thrust, Squat, Lat pulldown...) — mješavina EN/HR
- **Sex-aware filtering**: `exercise_pool.py` filtrira `sex: male` exercises za žene
- **Female templates**: lower_f1, lower_f2, full_body_f (no chest, glute priority)
- **Sort priority**: RDL → Hip thrust → compounds → isolations (hardcoded u service.py)
- Template `log_session.html` je najveći (921 LOC) — workout logging s puno JS-a
