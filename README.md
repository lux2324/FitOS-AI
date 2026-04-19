# FitOS-AI

AI fitness coach: intake upitnik → GPT generira tjedni plan → korisnik logira treninge → weekly feedback → AI prilagođava idući tjedan.

**Tech stack:** Django 5.2, Python 3.13, SQLite, GPT-4o-mini (OpenAI), Tailwind CSS (CDN), vanilla JS.

---

## 🚦 Gdje sam stao

> Ovu sekciju ažuriram **nakon svake sesije** — tako uvijek znam na čemu sam stao, bez obzira na kojem računalu radim.

**Zadnje ažurirano:** 2026-04-20

### Trenutni fokus
- [x] ~~Plan generation fixes (60s → 13s, httpx umjesto OpenAI SDK)~~ (2026-04-19)
- [x] ~~Refactor: @intake_required, clamp_int, statistika split, intake factory~~ (2026-04-19)
- [x] ~~PLAN.md + README.md + requirements.txt + .env.example~~ (2026-04-20)
- [ ] **Management command `seed_user`** (factory_boy + Faker za test podatke)
- [ ] **Unit testovi** za `plans/plan_maker.py` (build_skeleton, compute_actual_volume, validate_volume)
- [ ] AI weekly summary (OpenAI call u feedback/ai_service.py)
- [ ] Progression queue (prava logika, ne placeholder)

### Idući tjedan
- [ ] Production hardening (SECRET_KEY, DEBUG, ALLOWED_HOSTS, STATIC_ROOT iz env)
- [ ] Mobile responsive (dashboard + weekly_plan prvo)
- [ ] PWA (manifest.json, service worker)

### Dalje
- [ ] Fancy visuals (progress ring, radar chart, PR toast, muscle map animation)
- [ ] Deploy (Railway / Render / Fly.io)
- [ ] Native wrapper (Capacitor, ako treba App Store)

👉 **Kompletan plan s detaljima:** vidi [`PLAN.md`](PLAN.md)
👉 **Kontekst projekta (za AI asistenta):** vidi [`promjene.md`](promjene.md)

---

## ⚡ Quick start

```bash
git clone https://github.com/lux2324/FitOS-AI.git
cd FitOS-AI
python -m venv venv
source venv/bin/activate          # Mac/Linux
# ili: venv\Scripts\activate      # Windows

pip install -r requirements.txt

cp .env.example .env              # popuni OPENAI_API_KEY
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Otvori http://127.0.0.1:8000/ → registriraj korisnika → ispuni intake → generiraj plan.

---

## 🗺️ Struktura projekta

```
FitOS-AI/
├── fitos/         # Django config
├── core/          # Dashboard, decorators, utils
├── users/         # Auth
├── intake/        # 4-koračni wizard + AI analiza ozljeda
├── plans/         # AI plan generation (najveći modul)
│   ├── plan_ai.py         # GPT prompts + httpx calls
│   ├── service.py         # Generation pipeline orkestrator
│   ├── plan_maker.py      # Skeleton, volume validation
│   └── data/
│       └── exercise_pool.yaml  # 40+ vježbi
├── logs/          # Workout logging, setovi, statistika
├── feedback/      # Weekly feedback form, AI coach
├── templates/     # Django templates (svi extend base_tw.html)
├── static/        # JS (api.js), CSS, images
└── stitch/        # Figma mockupi (reference)
```

---

## 🧪 Testiranje (WIP)

Testovi su trenutno **prazni stubovi** u `<app>/tests.py`. Plan:

```bash
# kad budu dodani
pytest                    # svi testovi
pytest plans/             # samo jedan modul
pytest -k "skeleton"      # filter po imenu
```

---

## 🔑 Environment variables

| Var | Opis | Default |
|-----|------|---------|
| `OPENAI_API_KEY` | OpenAI project key | (obavezno) |
| `SECRET_KEY` | Django secret | `dev-secret` |
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_HOSTS` | Comma-separated hosts | `127.0.0.1,localhost` |

---

## 📝 Workflow između računala

1. Prije gašenja: `git push` (čak i WIP commit)
2. Na novom računalu: `git pull` → ažuriraj README.md "Gdje sam stao" sekciju
3. Nakon sesije: update progress u README.md, commit, push

---

## 🏗️ Arhitektura generacije plana

```
IntakeProfile
    ↓
build_skeleton()           # koji split, koliko slotova, volume targets
    ↓
draft_plan() [AI #1]       # GPT bira vježbe za svaki slot
    ↓
validate_volume()          # jesu li mišićne grupe pokrivene?
    ↓
refine_plan() [AI #2]      # (skip ako payload > 5000 chars)
    ↓
_sanitize_sessions()       # pool/slot validacija
    ↓
_sort_exercises()          # RDL → Hip thrust → compounds → isolations
    ↓
WeeklyPlan + PlannedSession + PlannedExercise (DB)
```

Generacija traje ~13s.
