from datetime import date, timedelta

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone

from core.utils import clamp_int
from logs.models import TrainingLog
from plans.models import WeeklyPlan
from .models import WeeklyFeedback


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _current_week_start() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())


def _last_week_stats(user):
    cutoff = timezone.now() - timedelta(days=7)
    logs = TrainingLog.objects.filter(
        user=user,
        is_finished=True,
        ended_at__gte=cutoff,
    ).prefetch_related('logged_exercises__sets')

    sessions_completed = logs.count()
    total_volume = 0.0
    total_duration_sec = 0
    rpe_values = []

    for log in logs:
        total_volume += log.total_volume_kg
        if log.duration_seconds:
            total_duration_sec += log.duration_seconds
        for ex in log.logged_exercises.all():
            for s in ex.sets.filter(completed=True):
                if s.rpe_done is not None:
                    rpe_values.append(float(s.rpe_done))

    avg_rpe = round(sum(rpe_values) / len(rpe_values), 1) if rpe_values else None
    total_duration_min = round(total_duration_sec / 60) if total_duration_sec else 0

    if total_volume >= 1000:
        volume_display = f"+{round(total_volume / 1000, 1)}t"
    else:
        volume_display = f"{round(total_volume)} kg"

    return {
        'sessions_completed': sessions_completed,
        'total_volume': total_volume,
        'volume_display': volume_display,
        'total_duration_min': total_duration_min,
        'avg_rpe': avg_rpe,
    }


def _build_feedback_context(request, existing, week_start):
    last_week = _last_week_stats(request.user)

    recovery_pct = int(((existing.sleep_quality - 1) / 4) * 100) if existing else 75
    recovery_offset = round(364.4 * (1 - recovery_pct / 100))

    latest_plan = WeeklyPlan.objects.filter(user=request.user).first()

    return {
        'week_start': week_start,
        'existing': existing,
        'last_week': last_week,
        'recovery_pct': recovery_pct,
        'recovery_offset': recovery_offset,
        'latest_plan': latest_plan,
        'rating_range': range(1, 6),
    }


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@login_required
def weekly_feedback(request):
    week_start = _current_week_start()
    existing = WeeklyFeedback.objects.filter(user=request.user, week_start=week_start).first()

    if request.method == 'POST':
        sleep_quality = clamp_int(request.POST.get('sleep_quality', 3), 1, 5, 3)
        stress_level  = clamp_int(request.POST.get('stress_level',  3), 1, 5, 3)
        doms_level    = clamp_int(request.POST.get('doms_level',    1), 1, 5, 1)
        training_notes = request.POST.get('training_notes', '').strip()

        if existing:
            existing.sleep_quality = sleep_quality
            existing.stress_level  = stress_level
            existing.doms_level    = doms_level
            existing.training_notes = training_notes
            existing.save(update_fields=['sleep_quality', 'stress_level', 'doms_level', 'training_notes'])
            messages.success(request, 'Feedback uspješno ažuriran!')
        else:
            WeeklyFeedback.objects.create(
                user=request.user,
                week_start=week_start,
                sleep_quality=sleep_quality,
                stress_level=stress_level,
                doms_level=doms_level,
                training_notes=training_notes,
                ai_summary='',
            )
            messages.success(request, 'Feedback uspješno spremljen!')

        return redirect('feedback:weekly')

    ctx = _build_feedback_context(request, existing, week_start)
    return render(request, 'feedback/weekly_feedback.html', ctx)


@login_required
def feedback_form(request):
    return weekly_feedback(request)


@login_required
@require_POST
def generate_next_week(request):
    from django.http import JsonResponse

    try:
        from intake.models import IntakeProfile
        from plans.service import generate_plan_for
        profile = IntakeProfile.objects.get(user=request.user)
        generate_plan_for(profile)
        msg = 'Novi tjedni plan je uspješno generiran!'
    except IntakeProfile.DoesNotExist:
        msg = 'Nema intake profila. Popuni upitnik prvo.'
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("generate_next_week failed: %s", e)
        msg = 'Greška pri generiranju plana. Pokušaj ručno iz Tjedni Plan sekcije.'

    is_ajax = (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or 'application/json' in request.headers.get('Content-Type', '')
    )

    if is_ajax:
        return JsonResponse({'status': 'ok', 'message': msg})

    messages.success(request, msg)
    return redirect('plans:weekly_plan')
