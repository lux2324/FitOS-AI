# FitOS-AI — Razvojni plan

> Zadnje ažurirano: 2026-04-19
> Projekt je prošao **prvi prolaz** — svi moduli rade end-to-end. Sada slijedi **testiranje, refinement i nadogradnja**.

---

## 📊 Trenutno stanje

### ✅ Što je gotovo (prvi prolaz)

| Modul | Status | LOC | Što radi |
|-------|--------|-----|----------|
| **Auth** (`users/`) | ✅ | 137 | Custom User, login/register/logout |
| **Intake wizard** (`intake/`) | ✅ | 772 | 4 koraka + AI analiza ozljeda (GPT-4o-mini) |
| **Plan generation** (`plans/`) | ✅ | 3,558 | Sex-aware, limitation-aware pipeline (draft → validate → refine → sanitize → save) |
| **Exercise pool** (`plans/data/exercise_pool.yaml`) | ✅ | 714 | 40+ vježbi, filtrirano po spolu/ozljedama |
| **Workout logging** (`logs/`) | ✅ | 576 | Ghost values, AJAX save, rest timer, exercise swap |
| **Weekly feedback** (`feedback/`) | ✅ | 179 | Sleep/stress/DOMS slideri, recovery gauge |
| **Dashboard** (`core/`) | ✅ | 230 | KPIs, streak, readiness, volume trend |
| **Statistika** (`logs/views.statistika`) | ✅ | — | PR tracking, 1RM evolution, muscle volume |
| **Design system** (Tailwind + glassmorphism) | ✅ | — | 12 stitch mockupa (Figma exports) kao referenca |

### 🛠️ Nedavni fixevi (refactor session)

- Zamijenjen `openai` SDK direktnim `httpx` pozivima (SDK se zaglavljivao na Windowsu)
- Plan generation: 60s → **13s** (smanjen payload, skip refine kad je prevelik)
- `@intake_required` decorator (uklonio 7+ boilerplate checks)
- `clamp_int()` helper (uklonio try/except repetitiju)
- `statistika()` 260 LOC → split u 6 helpera
- Intake step views → factory pattern
- Shared `api.js` (FitAPI.postForm/postJSON)

---

## 🎯 Do kraja tjedna — "close the loop"

Cilj: **moći pokrenuti potpuni ciklus** (intake → plan → log trening → feedback → novi plan) bez ručnog podešavanja.

### Priority 1 — Test data generation (P1)

**Zašto:** Bez fake podataka ne možemo testirati readiness score, streak, volume trend, PR detection, weekly feedback loop. Trenutno sve to vidimo samo kao prazne KPIs.

**Što treba:**

- [ ] **Management command** `python manage.py seed_user <username>` — kreira:
  - IntakeProfile (dummy podaci)
  - 4 WeeklyPlana (prošla 4 tjedna)
  - 12-16 TrainingLog-ova s realnim setovima (progresivni overload)
  - 3-4 WeeklyFeedback-a (varirani sleep/stress/DOMS)
- [ ] **Management command** `python manage.py seed_plan_variations` — generira planove za sve kombinacije (već postoji `batch_generate` view, ali iz CLI-a)
- [ ] **Factory klase** u `<app>/factories.py` koristeći `factory_boy`:
  - `UserFactory`, `IntakeProfileFactory`, `WeeklyPlanFactory`, `TrainingLogFactory`
- [ ] **Fixture** `fixtures/demo.json` — brz restore demo usera za prezentacije

### Priority 2 — Unit testovi za kritične komponente (P1)

**Zašto:** Kad sustav krene rasti, bez testova ne znamo što se razbilo kad. Fokus na **business logic**, ne na Django framework.

**Kritične komponente koje moraju imati testove:**

- [ ] **`plans/plan_maker.py`**
  - `build_skeleton()` — razni `days_per_week`, `sex`, `body_part_priority`
  - `compute_actual_volume()` — brojanje setova po mišićnoj grupi
  - `validate_volume()` — under/ok/over klasifikacija
  - `validate_constraints()` — session time limits
- [ ] **`plans/service.py`**
  - `generate_plan_for()` — mock OpenAI odgovor, provjeri da pipeline ne pada
  - `_sanitize_sessions()` — slot constraint + pool membership
  - `_sort_exercises()` — RDL first, compounds before isolations
- [ ] **`plans/rep_ranges.py`**
  - `get_prescription()` — ispravan rep range po vježbi + role
- [ ] **`logs/views.py`**
  - `plan_is_complete()` — 7-day rule, all-sessions-done rule
  - `save_set` — IDOR validacija (drugi user ne može mijenjati moj set)
  - `_compute_personal_records` — Epley formula, top-8 sortiranje
- [ ] **`core/views.py`**
  - `_compute_readiness` — formula sleep/stress/DOMS
  - Streak calculation
  - Volume trend aggregation
- [ ] **`intake/ai_service.py`**
  - Mock AI response, provjeri da ispravan JSON parsing radi
  - Handle AI error (API fail → fallback)

**Test setup:**
- [ ] Dodaj `pytest` + `pytest-django` u requirements
- [ ] `pytest.ini` s `DJANGO_SETTINGS_MODULE`
- [ ] `conftest.py` s zajedničkim fixturesom (user, profile, plan)
- [ ] CI hook — `pytest` u `.github/workflows/ci.yml` (kasnije)

### Priority 3 — AI Weekly Summary (P2)

**Status:** View endpoint postoji (`feedback/generate_next_week`), samo nedostaje OpenAI call koji analizira tjedan.

**Što treba:**
- [ ] Nova funkcija u `feedback/ai_service.py`:
  ```python
  def generate_weekly_summary(user, week_start):
      # Agreguj: completed sessions, total volume, avg RPE, PRs, 
      #         feedback (sleep/stress/DOMS), notes
      # → OpenAI call → vraća 3-4 rečenice + preporuke za idući tjedan
  ```
- [ ] Kad user klikne "Submit feedback", pozovi i spremi `ai_summary` u `WeeklyFeedback`
- [ ] Prikaži summary na dashboardu i u weekly_feedback view-u

### Priority 4 — Progression Queue (P2)

**Status:** Dashboard prikazuje vježbe s 3+ logova, ali bez pravih preporuka (placeholder).

**Što treba:**
- [ ] Za svaku vježbu s 3+ completed logova izračunaj:
  - Avg RPE zadnja 3 treninga
  - Trend težine (raste / stagnira / pada)
- [ ] Preporuka:
  - Avg RPE < 7 → `LOAD +2.5kg`
  - RPE 7-8 + reps pun range → `REP +1`
  - RPE > 8.5 → `HOLD` / `DELOAD`

---

## 🎨 Visual enhancements

**Inspiracija:** stitch/aether_flux/DESIGN.md — "Tactical Biometric Interface"

### Postojeći fancy vizuali
- Body heatmap (SVG) na weekly_plan.html — muscle activation per session
- Recovery gauge (SVG circle) u weekly_feedback
- Volume trend bar chart
- Progress bar za loading (plan generation — 13s animation)

### Ideje za dodati

- [ ] **Session heatmap 3D-ish** — trenutna 2D silueta može imati subtle gradient/glow po intenzitetu
- [ ] **Weekly progress ring** na dashboardu — circular chart tipa Apple Watch (sessions done / planned)
- [ ] **RPE distribution chart** — histogram RPE vrijednosti po tjednu
- [ ] **Muscle group balance radar chart** — 6 mišićnih grupa kao radar
- [ ] **Streak flame icon** — animirani plamen koji raste s duljinom streak-a
- [ ] **PR notification toast** — kad user logira novi PR, animirani "NEW PR 💪" banner
- [ ] **Volume evolution sparkline** — mini SVG grafovi uz svaku vježbu u statistici
- [ ] **Animated muscle map tijekom log session-a** — kako korisnik radi setove, mišići se "pale"

### Chart library
- Trenutno: inline SVG (OK za jednostavne stvari)
- Razmotriti: **Chart.js** (CDN, bez build stepa) ili **D3.js** za kompleksnije vizualizacije

---

## 📱 Mobile app (Django-based)

**Pristup:** Progressive Web App (PWA) — jedan codebase, radi na mobitelu, offline support.

**Zašto ne native (React Native / Flutter)?**
- Django templating + Tailwind već postoje
- PWA = 0 novog koda ako je UI responsive
- Install-to-homescreen experience identičan nativnoj app

### Što treba za PWA

- [ ] **Mobile-responsive CSS** — trenutni UI je desktop-first (1280px+). Treba:
  - Mobile-first breakpoints (Tailwind `sm:`, `md:`, `lg:`)
  - Sidebar → bottom tab bar na mobile
  - Dashboard stack umjesto grid
  - Log session — jedan exercise full screen, swipe između setova
- [ ] **`manifest.json`** — app name, icons, theme colors, display mode standalone
- [ ] **Service Worker** — cache static assets, offline fallback za dashboard
- [ ] **`<link rel="manifest">`** + apple-touch-icon tags u `base_tw.html`
- [ ] **Viewport meta** — već imamo `width=device-width`

### Mobile-specific feature-i

- [ ] **Rest timer** — trenutno radi, ali treba push notifikaciju kad timer istekne
- [ ] **Quick-log mode** — minimalni UI za logiranje bez distractiona
- [ ] **Camera integration** za unos body weight fotografija (opcionalno)
- [ ] **Geolocation** — auto-detect "u teretani" vs "doma" za različite planove (opcionalno)

### Alternativa: Native wrapper
- [ ] **Capacitor.js** može wrap PWA u native iOS/Android app (kasnije, ako treba App Store distribution)

---

## 🧹 Organization & housekeeping

### Stvari koje treba commitat ili obrisati

```
?? .claude/                    # Ignoriraj (dodaj u .gitignore)
?? _back_paths.txt             # Obrisati (debug dump)
?? _front_paths.txt            # Obrisati (debug dump)
?? _paths_output.txt           # Obrisati (debug dump)
?? CONTEXT.md                  # Stari, zamijenjen s promjene.md — obrisati
?? promjene.md                 # Commit (važan kontekst)
?? PLAN.md                     # Commit (ovaj fajl)
?? core/decorators.py          # Commit (refactor artifact)
?? core/utils.py               # Commit
?? static/js/api.js            # Commit
?? static/images/              # Commit (body diagrams)
?? stitch/                     # Commit (design reference)
```

### Dodati u .gitignore
```
.claude/
_back_paths.txt
_front_paths.txt
_paths_output.txt
.vscode/
.idea/
```

### Dependencies management

**Trenutno:** Nema `requirements.txt` ni `pyproject.toml` — instalirano direktno u venv.

- [ ] **Generiraj `requirements.txt`**:
  ```bash
  pip freeze > requirements.txt
  ```
  Key paketi: `Django>=6.0`, `openai>=2.0`, `httpx>=0.25`, `PyYAML`, `python-dotenv` (ako koristimo)
- [ ] **Opcionalno: pyproject.toml s Poetry** za bolju dependency resolution

### Production hardening

**Trenutno (od promjene.md TODO-ova):**
- [ ] `SECRET_KEY` → `os.environ.get('SECRET_KEY')` + default za dev
- [ ] `DEBUG` → `os.environ.get('DEBUG', 'False') == 'True'`
- [ ] `ALLOWED_HOSTS` → iz env var (comma-separated)
- [ ] `STATIC_ROOT = BASE_DIR / 'staticfiles'` — za `collectstatic`
- [ ] `logout` view → `@login_required`
- [ ] OPENAI_API_KEY null check (graceful fallback umjesto crash)
- [ ] `DATABASES` — opcija za PostgreSQL (`DATABASE_URL` env var)

### README.md

- [ ] Dodati **README.md** u root s:
  - Kratak opis projekta
  - Screenshot ili GIF
  - Setup instrukcije (`.env`, `pip install`, `migrate`, `runserver`)
  - Tech stack
  - Link na PLAN.md i promjene.md

---

## 💻 Multi-device workflow (MacBook)

Za rad na Macbooku:

### Setup na novom računalu

```bash
git clone https://github.com/lux2324/FitOS-AI.git
cd FitOS-AI
python -m venv venv
source venv/bin/activate          # Mac/Linux
# ili: venv\Scripts\activate      # Windows
pip install -r requirements.txt

# .env (kopiraj ručno — NIJE u gitu)
echo "OPENAI_API_KEY=sk-proj-..." > .env
echo "SECRET_KEY=dev-secret" >> .env

python manage.py migrate
python manage.py createsuperuser  # ili seed command kad bude
python manage.py runserver
```

### Git workflow između računala

- `main` branch — stable, always working
- `feature/<ime>` — sve nove stvari (testovi, visuals, mobile)
- Prije gašenja računala: **uvijek `git push`** (čak i WIP commit)
- Prije rada na drugom: **uvijek `git pull`**

### Datoteke koje MORAJU biti sinhronizirane

| Fajl | Git? | Zašto |
|------|------|-------|
| `PLAN.md` | ✅ | Plan razvoja |
| `promjene.md` | ✅ | Kontekst za AI asistenta (Claude) |
| `requirements.txt` | ✅ | Dependency lock |
| `.env.example` | ✅ | Template (bez tajni) |
| `.env` | ❌ | Samo lokalno (tajne) |
| `db.sqlite3` | ❌ | Lokalni dev DB, razlikuje se |
| `venv/` | ❌ | Virtual env — recreate po potrebi |

### Napomena za AI asistenta (Claude Code)

Kad radiš na drugom računalu, prvi prompt u sesiji:
```
Otvori PLAN.md i promjene.md i reci mi što je zadnje stanje.
Iduće radim na: [što god]
```

---

## 📋 Konkretni checklist za iduću sesiju (po prioritetu)

### Ovaj tjedan
- [ ] `requirements.txt` + `.env.example` + README.md
- [ ] `.gitignore` update (`.claude/`, debug fajlovi)
- [ ] Commit svega što je sad untracked (osim junk fajlova)
- [ ] Management command `seed_user` (factory_boy + Faker)
- [ ] Prvi unit testovi — `plans/plan_maker.py` (`build_skeleton`, `compute_actual_volume`)

### Idući tjedan
- [ ] AI weekly summary (real OpenAI call)
- [ ] Progression queue (prava logika umjesto placeholder-a)
- [ ] Production hardening (SECRET_KEY, DEBUG, ALLOWED_HOSTS, STATIC_ROOT)
- [ ] Mobile responsive — dashboard + weekly_plan (najvažnije za demo)

### Pa onda
- [ ] PWA (manifest.json, service worker)
- [ ] Fancy visuals (progress ring, radar chart, muscle map animation)
- [ ] Deploy (Railway / Render / Fly.io)

---

## 🔥 Potencijalni problemi do kojih može doći

| Problem | Kad će se pojaviti | Mitigation |
|---------|-------------------|------------|
| OpenAI API quota / rate limit | Kad testiramo često | Cache rezultate, mock u testovima |
| `exercise_pool.yaml` neusklađen s `rep_ranges.py` | Kad dodamo novu vježbu u pool | Test koji provjerava da svaka vježba ima prescription |
| Volume targets previsoki za female planove | Već sad — draftu faila validate | Tweak u `volume_targets.py` + testiranje |
| Hrvatski vs engleski nazivi vježbi | Kad širimo na veći pool | Odlučiti — sve na EN ili sve na HR, migrirati |
| SQLite locking na multi-user | Kad (ako) ide u prod | Prijeći na PostgreSQL |
| AI hallucination u exercise substitution | Već sad rijetko | Fallback na first-candidate postoji, test da se hvata |

---

## 📞 Napomene za mene osobno

- **Plan je žive stvar** — dopuni ga kako god treba, pomakni checkbox-ove, dodaj nove TODOs
- **Uvijek commitaj PLAN.md kad ga mijenjaš** — tako je sinkronizacija između računala automatska
- Kad dodaš novi feature, update i `promjene.md` da AI asistent zna novi kontekst
- **Radi malo-pomalo** — ne sve odjednom. Jedna stvar po sesiji, commit, push, sljedeća.
