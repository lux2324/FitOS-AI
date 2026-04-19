import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from core.decorators import intake_required
from intake.models import IntakeProfile
from intake.muscle_index import EXERCISE_MUSCLE_INDEX, MUSCLE_GROUPS
from .models import WeeklyPlan, PlannedExercise
from .service import generate_plan_for, OVERRIDABLE_FIELDS
from .plan_maker import UNDER_TOL, OVER_TOL, _LENIENT_OVER
from .plan_ai import _call_openai
from .exercise_pool import filter_pool
from .rep_ranges import get_prescription


def _volume_rows(plan):
    if not plan or not plan.volume_targets:
        return []
    actual = plan.volume_actual or {}
    rows = []
    for muscle, target in plan.volume_targets.items():
        a = actual.get(muscle, 0)
        if not target:
            status = "ok"
        else:
            ratio = a / target
            over_tol = _LENIENT_OVER.get(muscle, OVER_TOL)
            if ratio < UNDER_TOL:
                status = "under"
            elif ratio > over_tol:
                status = "over"
            else:
                status = "ok"
        rows.append({"muscle": muscle, "target": target, "actual": a, "status": status})
    return rows


def _session_muscle_maps(plan):
    """
    For each session in the plan, compute a normalized 0-100 muscle heatmap.
    Returns {session_id: {muscle_name: intensity_0_100}}.
    """
    result = {}
    for session in plan.sessions.all():
        volume = {m: 0.0 for m in MUSCLE_GROUPS}
        for ex in session.exercises.all():
            scores = EXERCISE_MUSCLE_INDEX.get(ex.name)
            if not scores:
                continue
            for muscle, score in scores.items():
                volume[muscle] += ex.sets * (score / 100)
        max_val = max(volume.values()) or 1
        result[session.id] = {
            m: round((v / max_val) * 100) for m, v in volume.items()
        }
    return result


def _param_context(profile, plan=None):
    """Current values to pre-fill the parameter editor form.
    If a plan exists, use its values (which may include overrides from
    the generation that created it) so the form stays consistent."""

    def cur(field):
        # If there's a plan with generation_params, use those values
        # so the form stays consistent with what was last generated.
        if plan and plan.generation_params:
            v = plan.generation_params.get(field)
            if v is not None:
                return v
        return getattr(profile, field)

    return {
        "param_values": {
            "sex": cur("sex"),
            "days_per_week_available": cur("days_per_week_available"),
            "max_session_minutes": cur("max_session_minutes"),
            "body_part_priority": cur("body_part_priority"),
            "primary_goal": cur("primary_goal"),
            "training_experience_level": cur("training_experience_level"),
        },
        "param_choices": {
            "sex": IntakeProfile.SEX_CHOICES,
            "days_per_week_available": IntakeProfile.DAYS_CHOICES,
            "max_session_minutes": IntakeProfile.SESSION_MINUTES_CHOICES,
            "body_part_priority": IntakeProfile.BODY_PRIORITY_CHOICES,
            "primary_goal": IntakeProfile.GOAL_CHOICES,
            "training_experience_level": IntakeProfile.EXPERIENCE_CHOICES,
        },
    }


@intake_required
@never_cache
def weekly_plan(request):
    """Show the user's most recent weekly plan + parameter editor."""
    profile = request.user.intake_profile
    plan = (
        WeeklyPlan.objects.filter(user=request.user)
        .prefetch_related("sessions__exercises")
        .first()
    )

    session_muscles = _session_muscle_maps(plan) if plan else {}

    ctx = {
        "plan": plan,
        "volume_rows": _volume_rows(plan),
        "session_muscles": session_muscles,
    }
    ctx.update(_param_context(profile, plan=plan))
    return render(request, "plans/weekly_plan.html", ctx)


def _collect_overrides(request) -> dict:
    out = {}
    for f in OVERRIDABLE_FIELDS:
        v = request.POST.get(f)
        if v not in (None, ""):
            # cast numerics
            if f in ("days_per_week_available", "max_session_minutes", "age"):
                try:
                    v = int(v)
                except (TypeError, ValueError):
                    continue
            out[f] = v
    return out


@intake_required
@require_POST
def generate(request):
    profile = request.user.intake_profile
    overrides = _collect_overrides(request)

    try:
        plan = generate_plan_for(profile, overrides=overrides)
        msg = f"Plan #{plan.pk} generated."
        if overrides:
            msg += f" (overrides: {', '.join(overrides.keys())})"
        messages.success(request, msg)
    except Exception as e:
        messages.error(request, f"Plan generation failed: {e}")

    return redirect("plans:weekly_plan")


@intake_required
@require_POST
def batch_generate(request):
    """Generate plans for all combinations of selected parameters in parallel."""
    profile = request.user.intake_profile

    # Collect which params to vary — checkboxes name="vary_<field>"
    # and the values to try for each
    vary_days = request.POST.getlist("vary_days")
    vary_minutes = request.POST.getlist("vary_minutes")
    vary_priority = request.POST.getlist("vary_priority")
    vary_sex = request.POST.getlist("vary_sex")

    # Defaults if nothing checked
    days_list = [int(d) for d in vary_days] if vary_days else [profile.days_per_week_available]
    minutes_list = [int(m) for m in vary_minutes] if vary_minutes else [profile.max_session_minutes]
    priority_list = vary_priority if vary_priority else [profile.body_part_priority]
    sex_list = vary_sex if vary_sex else [profile.sex]

    combos = list(itertools.product(sex_list, days_list, minutes_list, priority_list))

    def _gen(combo):
        sex, days, mins, prio = combo
        overrides = {
            "sex": sex,
            "days_per_week_available": days,
            "max_session_minutes": mins,
            "body_part_priority": prio,
        }
        label = f"{sex[0].upper()}/{days}d/{mins}min/{prio}"
        try:
            plan = generate_plan_for(profile, overrides=overrides)
            return label, plan.pk, None
        except Exception as e:
            return label, None, str(e)

    results = []
    with ThreadPoolExecutor(max_workers=min(6, len(combos))) as pool:
        futures = {pool.submit(_gen, c): c for c in combos}
        for f in as_completed(futures):
            label, plan_id, error = f.result()
            results.append({"label": label, "plan_id": plan_id, "error": error})

    results.sort(key=lambda r: r["label"])

    # Load all generated plans for comparison
    plan_ids = [r["plan_id"] for r in results if r["plan_id"]]
    plans = (
        WeeklyPlan.objects.filter(pk__in=plan_ids)
        .prefetch_related("sessions__exercises")
        .order_by("pk")
    )
    plans_by_id = {p.pk: p for p in plans}

    male_plans = []
    female_plans = []
    for r in results:
        plan = plans_by_id.get(r["plan_id"])
        entry = {
            "label": r["label"],
            "plan": plan,
            "error": r["error"],
            "session_muscles": _session_muscle_maps(plan) if plan else {},
        }
        if r["label"].startswith("M/"):
            male_plans.append(entry)
        else:
            female_plans.append(entry)

    return render(request, "plans/compare.html", {
        "male_plans": male_plans,
        "female_plans": female_plans,
        "total": len(combos),
        "success": sum(1 for r in results if r["plan_id"]),
    })


@login_required
def plan_detail(request, plan_id: int):
    profile = getattr(request.user, "intake_profile", None)
    plan = get_object_or_404(
        WeeklyPlan.objects.prefetch_related("sessions__exercises"),
        pk=plan_id,
        user=request.user,
    )
    ctx = {
        "plan": plan,
        "volume_rows": _volume_rows(plan),
    }
    if profile:
        ctx.update(_param_context(profile))
    return render(request, "plans/weekly_plan.html", ctx)


@login_required
@require_POST
def substitute_exercise(request):
    """
    AJAX endpoint — replace a PlannedExercise with an AI-chosen substitute.

    POST params:
        exercise_id  — PlannedExercise pk
        reason       — user's description of why the exercise doesn't suit them

    Returns JSON: {ok: true, new_name, new_role, new_category}
                  {ok: false, error: "..."}
    """
    exercise_id = request.POST.get("exercise_id")
    reason = request.POST.get("reason", "").strip()

    if not exercise_id:
        return JsonResponse({"ok": False, "error": "Missing exercise_id."}, status=400)

    # Fetch the PlannedExercise and verify ownership
    try:
        pe = PlannedExercise.objects.select_related(
            "session__plan__user"
        ).get(pk=exercise_id)
    except (PlannedExercise.DoesNotExist, ValueError, TypeError):
        return JsonResponse({"ok": False, "error": "Exercise not found."}, status=404)

    if pe.session.plan.user != request.user:
        return JsonResponse({"ok": False, "error": "Nema pristupa."}, status=403)

    # Get the user's intake profile for sex-aware pool filtering
    try:
        profile = IntakeProfile.objects.get(user=request.user)
    except IntakeProfile.DoesNotExist:
        return JsonResponse(
            {"ok": False, "error": "Intake profil nije pronađen. Ispuni intake anketu."},
            status=400,
        )

    # Build a pool filtered by sex, role, and category — excluding current exercise
    pool = filter_pool(sex=profile.sex)
    candidates = [
        ex for ex in pool
        if ex.get("role") == pe.role
        and ex.get("movement_category") == pe.movement_category
        and ex["name"] != pe.name
    ]

    if not candidates:
        return JsonResponse(
            {"ok": False, "error": "Nema dostupnih zamjena za tu kategoriju."},
            status=400,
        )

    candidate_names = ", ".join(ex["name"] for ex in candidates)

    system_prompt = (
        "You are a personal trainer. Given a list of exercises, pick the best substitute "
        "based on the user's feedback. Return ONLY a JSON object: {\"name\": \"exact exercise name from the list\"}"
    )
    user_prompt = (
        f"Exercise to replace: {pe.name} (role: {pe.role}, category: {pe.movement_category}). "
        f"User reason: {reason or 'no specific reason given'}. "
        f"Available alternatives: {candidate_names}. "
        f"Pick the best one."
    )

    try:
        ai_response = _call_openai(system_prompt, user_prompt, max_tokens=100)
    except Exception as exc:
        return JsonResponse(
            {"ok": False, "error": f"AI greška: {exc}"},
            status=502,
        )

    chosen_name = (ai_response.get("name") or "").strip()

    # Validate the AI returned an exercise actually in the candidate list
    chosen_ex = next((ex for ex in candidates if ex["name"] == chosen_name), None)
    if chosen_ex is None:
        # Fallback: pick the first candidate if AI hallucinated
        chosen_ex = candidates[0]
        chosen_name = chosen_ex["name"]

    # Update the PlannedExercise
    prescription = get_prescription(chosen_name, pe.role)

    pe.name = chosen_name
    pe.movement_category = chosen_ex.get("movement_category", pe.movement_category)
    pe.reps_min = prescription["reps_min"]
    pe.reps_max = prescription["reps_max"]
    pe.target_rpe = prescription.get("rpe", pe.target_rpe)
    pe.rest = prescription.get("rest", pe.rest)
    pe.save(update_fields=["name", "movement_category", "reps_min", "reps_max", "target_rpe", "rest"])

    return JsonResponse({
        "ok": True,
        "new_name": pe.name,
        "new_role": pe.role,
        "new_category": pe.movement_category,
    })
