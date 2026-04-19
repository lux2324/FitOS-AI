from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count

from plans.models import WeeklyPlan
from logs.models import TrainingLog, LoggedExercise
from logs.views import plan_is_complete

try:
    from feedback.models import WeeklyFeedback
    _HAS_FEEDBACK = True
except ImportError:
    _HAS_FEEDBACK = False


def _compute_readiness(user):
    """Return int 0-100. Derived from latest WeeklyFeedback if available."""
    if not _HAS_FEEDBACK:
        return None
    try:
        fb = WeeklyFeedback.objects.filter(user=user).first()
    except Exception:
        return None
    if not fb:
        return None

    # sleep_quality 1-5 → contributes 50 pts
    sleep_score = ((fb.sleep_quality - 1) / 4.0) * 50

    # stress_level 1-5 → inverted (5=worst) → contributes 30 pts
    stress_score = ((5 - fb.stress_level) / 4.0) * 30

    # doms_level 1-5 (integer) → contributes 20 pts (1=no doms, 5=severe)
    doms_map = {1: 20, 2: 15, 3: 10, 4: 5, 5: 2}
    doms_score = doms_map.get(int(fb.doms_level), 10)

    return int(min(100, sleep_score + stress_score + doms_score))


def _readiness_label(score):
    if score is None:
        return None
    if score >= 85:
        return 'ODLICNO'
    elif score >= 70:
        return 'DOBRO'
    elif score >= 50:
        return 'SREDNJE'
    else:
        return 'ODMORI SE'


@login_required
def home(request):
    if not hasattr(request.user, 'intake_profile') or not request.user.intake_profile.completed:
        return redirect('intake:step1')

    # ------------------------------------------------------------------ #
    # Active plan (latest for user)
    # ------------------------------------------------------------------ #
    current_plan = (
        WeeklyPlan.objects
        .filter(user=request.user)
        .prefetch_related('sessions__exercises')
        .first()
    )

    # Active (unfinished) training log
    active_log = TrainingLog.objects.filter(user=request.user, is_finished=False).first()

    # ------------------------------------------------------------------ #
    # Weekly window (Mon 00:00 → now)
    # ------------------------------------------------------------------ #
    now = timezone.now()
    week_start = (now - timezone.timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    weekly_logs = (
        TrainingLog.objects
        .filter(user=request.user, is_finished=True, started_at__gte=week_start)
        .prefetch_related('logged_exercises__sets')
        .order_by('started_at')
    )

    kpi_sessions = weekly_logs.count()

    # Weekly volume
    weekly_volume = 0
    logged_session_ids = set()
    for log in weekly_logs:
        weekly_volume += log.total_volume_kg
        if log.planned_session_id:
            logged_session_ids.add(log.planned_session_id)

    # ------------------------------------------------------------------ #
    # Streak — consecutive days with at least one finished training
    # ------------------------------------------------------------------ #
    streak = 0
    check_date = now.date()
    while True:
        has_log = TrainingLog.objects.filter(
            user=request.user,
            is_finished=True,
            started_at__date=check_date,
        ).exists()
        if has_log:
            streak += 1
            check_date -= timezone.timedelta(days=1)
        else:
            break
        if streak > 365:  # safety
            break

    # ------------------------------------------------------------------ #
    # Progression queue — exercises with 3+ completed logs
    # ------------------------------------------------------------------ #
    exercise_counts = (
        LoggedExercise.objects
        .filter(training_log__user=request.user, training_log__is_finished=True)
        .values('name')
        .annotate(log_count=Count('id'))
        .filter(log_count__gte=3)
        .order_by('-log_count')[:8]
    )
    progression_queue = list(exercise_counts)

    # ------------------------------------------------------------------ #
    # Volume by day — current week (0=Mon … 6=Sun)
    # ------------------------------------------------------------------ #
    volume_by_day = {i: 0 for i in range(7)}
    for log in weekly_logs:
        day_idx = log.started_at.weekday()
        volume_by_day[day_idx] += log.total_volume_kg

    # ------------------------------------------------------------------ #
    # Today's session — first planned session not yet logged this week
    # ------------------------------------------------------------------ #
    todays_session = None
    if current_plan:
        for session in current_plan.sessions.all():
            if session.id not in logged_session_ids:
                todays_session = session
                break

    # ------------------------------------------------------------------ #
    # Readiness score
    # ------------------------------------------------------------------ #
    readiness_score = _compute_readiness(request.user)

    # ------------------------------------------------------------------ #
    # Volume trend — only weeks where training actually happened
    # Skip any plan week with zero completed logs (no fake 0s)
    # ------------------------------------------------------------------ #
    recent_plans = list(
        WeeklyPlan.objects
        .filter(user=request.user)
        .prefetch_related('sessions')
        .order_by('-created_at')[:8]
    )
    recent_plans = list(reversed(recent_plans))  # oldest → newest

    volume_trend = []
    for p in recent_plans:
        plan_session_ids = list(p.sessions.values_list('id', flat=True))
        logs_for_plan = (
            TrainingLog.objects
            .filter(
                user=request.user,
                is_finished=True,
                planned_session_id__in=plan_session_ids,
            )
            .prefetch_related('logged_exercises__sets')
        )
        plan_vol = sum(lg.total_volume_kg for lg in logs_for_plan)
        # Only include weeks where at least one session was completed
        if plan_vol > 0:
            volume_trend.append({
                'label': f"T{p.week_number}",
                'volume': plan_vol,
            })

    max_vol = max((t['volume'] for t in volume_trend), default=1) or 1
    for t in volume_trend:
        t['pct'] = round((t['volume'] / max_vol) * 100)

    # ------------------------------------------------------------------ #
    # Consistency metric — sessions completed vs planned this week
    # ------------------------------------------------------------------ #
    sessions_planned_this_week = current_plan.days_per_week if current_plan else 0
    if sessions_planned_this_week > 0:
        consistency_pct = round((kpi_sessions / sessions_planned_this_week) * 100)
    else:
        consistency_pct = None

    plan_complete = plan_is_complete(current_plan, request.user)

    ctx = {
        'current_plan': current_plan,
        'plan': current_plan,          # backward-compat alias
        'active_log': active_log,
        'weekly_logs': weekly_logs,
        'weekly_volume': round(weekly_volume, 1),
        'kpi_sessions': kpi_sessions,
        'sessions_done': kpi_sessions,                           # alias
        'sessions_total': current_plan.days_per_week if current_plan else 0,
        'streak': streak,
        'progression_queue': progression_queue,
        'volume_by_day': volume_by_day,
        'todays_session': todays_session,
        'today_session': todays_session,                         # alias
        'readiness_score': readiness_score,
        'readiness_label': _readiness_label(readiness_score),
        'volume_trend': volume_trend,
        'consistency_pct': consistency_pct,
        'plan_complete': plan_complete,
    }
    return render(request, 'core/dashboard.html', ctx)
