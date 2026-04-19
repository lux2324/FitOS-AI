from datetime import timedelta
from collections import defaultdict

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone

from plans.models import WeeklyPlan, PlannedSession, PlannedExercise
from .models import TrainingLog, LoggedExercise, LoggedSet


def plan_is_complete(plan, user):
    """
    Return True if the weekly plan should be considered finished:
    - The plan was created more than 7 days ago, OR
    - Every session in the plan has at least one completed TrainingLog for this user.
    """
    if plan is None:
        return False

    age = timezone.now() - plan.created_at
    if age > timedelta(days=7):
        return True

    sessions = list(plan.sessions.all())
    if not sessions:
        return False

    for session in sessions:
        has_log = TrainingLog.objects.filter(
            user=user,
            planned_session=session,
            is_finished=True,
        ).exists()
        if not has_log:
            return False

    return True


@login_required
def session_picker(request):
    unfinished = (
        TrainingLog.objects
        .filter(user=request.user, is_finished=False)
        .first()
    )
    if unfinished:
        return redirect('logs:log_session', log_id=unfinished.pk)

    plan = (
        WeeklyPlan.objects
        .filter(user=request.user)
        .prefetch_related('sessions__exercises')
        .first()
    )

    complete = plan_is_complete(plan, request.user)

    sessions = []
    if plan and not complete:
        for session in plan.sessions.all().order_by('order'):
            session.last_log = (
                TrainingLog.objects
                .filter(
                    user=request.user,
                    planned_session=session,
                    is_finished=True,
                )
                .order_by('-started_at')
                .first()
            )
            sessions.append(session)

    return render(request, 'logs/session_picker.html', {
        'plan': plan,
        'sessions': sessions,
        'plan_complete': complete,
    })


@login_required
@require_POST
def start_session(request, session_id):
    session = get_object_or_404(PlannedSession, pk=session_id, plan__user=request.user)

    log = TrainingLog.objects.create(user=request.user, planned_session=session)

    for ex in session.exercises.all().order_by('order'):
        logged_ex = LoggedExercise.objects.create(
            training_log=log,
            planned_exercise=ex,
            order=ex.order,
            name=ex.name,
        )
        for set_num in range(1, ex.sets + 1):
            LoggedSet.objects.create(
                logged_exercise=logged_ex,
                set_number=set_num,
                weight_kg=None,
                reps_done=None,
                completed=False,
            )

    return redirect('logs:log_session', log_id=log.pk)


@login_required
def log_session(request, log_id):
    log = get_object_or_404(
        TrainingLog.objects.prefetch_related(
            'logged_exercises__sets',
            'logged_exercises__planned_exercise',
        ),
        pk=log_id,
        user=request.user,
    )

    if log.is_finished:
        return redirect('logs:summary', log_id=log_id)

    exercises = []
    for ex in log.logged_exercises.all():
        pe = ex.planned_exercise

        if pe:
            ex.target = {
                'sets': pe.sets,
                'reps_min': pe.reps_min,
                'reps_max': pe.reps_max,
                'rpe': pe.target_rpe,
            }
        else:
            ex.target = {'sets': 3, 'reps_min': 8, 'reps_max': 12, 'rpe': None}

        prev_lookup = {}
        if pe:
            prev_log = (
                TrainingLog.objects
                .filter(
                    user=request.user,
                    is_finished=True,
                    logged_exercises__planned_exercise=pe,
                )
                .exclude(pk=log.pk)
                .order_by('-started_at')
                .first()
            )
            if prev_log:
                prev_logged_ex = prev_log.logged_exercises.filter(planned_exercise=pe).first()
                if prev_logged_ex:
                    for ps in prev_logged_ex.sets.order_by('set_number'):
                        prev_lookup[ps.set_number] = ps

        ex.prev_sets = list(prev_lookup.values())
        for s in ex.sets.all():
            s.prev = prev_lookup.get(s.set_number)

        exercises.append(ex)

    return render(request, 'logs/log_session.html', {
        'log': log,
        'exercises': exercises,
        'session_name': log.planned_session.name if log.planned_session else '',
    })


@login_required
@require_POST
def save_set(request, log_id):
    log = get_object_or_404(TrainingLog, pk=log_id, user=request.user, is_finished=False)

    exercise_id = request.POST.get('exercise_id')
    set_number = request.POST.get('set_number')
    weight_kg = request.POST.get('weight_kg') or None
    reps_done = request.POST.get('reps_done') or None
    rpe_done = request.POST.get('rpe_done') or None
    completed = request.POST.get('completed', 'false').lower() == 'true'

    logged_set, _ = LoggedSet.objects.get_or_create(
        logged_exercise_id=exercise_id,
        logged_exercise__training_log=log,
        set_number=set_number,
    )

    logged_set.weight_kg = weight_kg
    logged_set.reps_done = reps_done
    logged_set.rpe_done = rpe_done
    logged_set.completed = completed
    logged_set.save()

    return JsonResponse({'ok': True, 'volume': log.total_volume_kg})


@login_required
@require_POST
def save_note(request, log_id):
    log = get_object_or_404(TrainingLog, pk=log_id, user=request.user)
    log.notes = request.POST.get('notes', '')
    log.save(update_fields=['notes'])
    return JsonResponse({'ok': True})


@login_required
@require_POST
def finish_session(request, log_id):
    log = get_object_or_404(TrainingLog, pk=log_id, user=request.user)

    notes = request.POST.get('notes', '').strip()
    if notes:
        log.notes = notes

    log.ended_at = timezone.now()
    log.is_finished = True
    log.save(update_fields=['ended_at', 'is_finished', 'notes'])

    return redirect('logs:summary', log_id=log.pk)


@login_required
def summary(request, log_id):
    log = get_object_or_404(
        TrainingLog.objects.prefetch_related(
            'logged_exercises__sets',
            'logged_exercises__planned_exercise',
        ),
        pk=log_id,
        user=request.user,
    )

    return render(request, 'logs/summary.html', {
        'log': log,
        'exercises': list(log.logged_exercises.all()),
        'duration_seconds': log.duration_seconds,
        'total_volume': log.total_volume_kg,
    })


# ---------------------------------------------------------------------------
# STATISTIKA
# ---------------------------------------------------------------------------

def _epley_1rm(weight_kg, reps):
    if not weight_kg or not reps:
        return 0
    return float(weight_kg) * (1 + reps / 30)


COMPOUND_EXERCISES = [
    'Squat', 'Back Squat', 'Front Squat',
    'Deadlift', 'Romanian Deadlift',
    'Bench Press', 'Incline Bench Press',
    'Overhead Press', 'Military Press',
    'Pull-Up', 'Chin-Up',
    'Barbell Row',
]

MUSCLE_KEYWORDS = {
    'Noge / Stražnjica': ['squat', 'leg', 'lunge', 'deadlift', 'glute', 'hip thrust', 'romanian'],
    'Leđa / Pulling':    ['row', 'pull', 'lat', 'chin', 'back', 'shrug'],
    'Prsa / Pushing':    ['bench', 'press', 'chest', 'push', 'fly', 'dip'],
    'Ramena / Deltoids': ['shoulder', 'lateral', 'front raise', 'overhead', 'military', 'delt'],
    'Ruke':              ['curl', 'tricep', 'bicep', 'arm', 'extension'],
    'Core':              ['crunch', 'plank', 'ab', 'core', 'oblique'],
}


def _classify_muscle(exercise_name: str) -> str:
    name_lower = exercise_name.lower()
    for group, keywords in MUSCLE_KEYWORDS.items():
        if any(kw in name_lower for kw in keywords):
            return group
    return 'Ostalo'


def _compute_personal_records(user):
    """Returns (personal_records_top8, exercise_list)."""
    all_sets = (
        LoggedSet.objects
        .filter(logged_exercise__training_log__user=user, completed=True, weight_kg__isnull=False)
        .select_related('logged_exercise')
    )
    pr_by_exercise = {}
    for s in all_sets:
        name = s.logged_exercise.name
        w = float(s.weight_kg)
        reps = s.reps_done or 1
        existing = pr_by_exercise.get(name)
        if existing is None or w > existing['weight_kg']:
            pr_by_exercise[name] = {
                'name': name, 'weight_kg': w, 'reps': reps,
                'est_1rm': round(_epley_1rm(w, reps), 1), 'logged_at': s.logged_at,
            }
    personal_records = sorted(pr_by_exercise.values(), key=lambda x: x['weight_kg'], reverse=True)[:8]
    return personal_records, sorted(pr_by_exercise.keys())


def _compute_strength_evolution(user, eight_weeks_ago, selected_session_type):
    """Returns (strength_chart, week_labels)."""
    current_week = timezone.now().isocalendar()[1]
    week_labels = [(current_week - 7 + i) % 53 or 53 for i in range(8)]

    compound_data = defaultdict(lambda: defaultdict(float))
    compound_sets = (
        LoggedSet.objects
        .filter(
            logged_exercise__training_log__user=user,
            logged_exercise__training_log__started_at__gte=eight_weeks_ago,
            completed=True, weight_kg__isnull=False,
        )
        .select_related('logged_exercise__training_log')
    )
    if selected_session_type:
        compound_sets = compound_sets.filter(
            logged_exercise__training_log__planned_session__name=selected_session_type
        )

    for s in compound_sets:
        name = s.logged_exercise.name
        is_compound = any(
            comp.lower() in name.lower() or name.lower() in comp.lower()
            for comp in COMPOUND_EXERCISES
        )
        if not is_compound:
            continue
        week = s.logged_exercise.training_log.started_at.isocalendar()[1]
        est = _epley_1rm(float(s.weight_kg), s.reps_done or 1)
        if est > compound_data[name][week]:
            compound_data[name][week] = round(est, 1)

    strength_chart = []
    for name, weekly in list(compound_data.items())[:3]:
        points = [weekly.get(w, None) for w in week_labels]
        filled, last_val = [], None
        for p in points:
            if p is not None:
                last_val = p
            filled.append(last_val)
        strength_chart.append({'name': name, 'points': filled, 'max': max((v for v in filled if v), default=0)})

    return strength_chart, week_labels


def _build_svg_paths(strength_chart):
    """Returns SVG polyline path data for the strength chart."""
    svg_paths = []
    colors = ['#71ffe8', '#d3fbff', '#00eefc']
    for idx, ex_data in enumerate(strength_chart):
        vals = ex_data['points']
        valid_vals = [v for v in vals if v is not None]
        if not valid_vals:
            continue
        chart_max = max(valid_vals) * 1.1 or 1
        chart_min = min(valid_vals) * 0.9
        pts = []
        for i, v in enumerate(vals):
            if v is None:
                continue
            x = round((i / 7) * 760 + 20)
            y = round(180 - ((v - chart_min) / (chart_max - chart_min + 0.01)) * 160)
            pts.append(f"{x},{y}")
        if pts:
            svg_paths.append({
                'name': ex_data['name'],
                'color': colors[idx % len(colors)],
                'points': ' '.join(pts),
                'max_1rm': ex_data['max'],
            })
    return svg_paths


def _compute_volume_by_muscle(user, four_weeks_ago, selected_session_type):
    """Returns (recent_logs queryset, volume_bars, total_volume)."""
    qs = TrainingLog.objects.filter(user=user, is_finished=True, started_at__gte=four_weeks_ago)
    if selected_session_type:
        qs = qs.filter(planned_session__name=selected_session_type)
    recent_logs = qs.prefetch_related('logged_exercises__sets')

    muscle_volume = defaultdict(float)
    for log in recent_logs:
        for ex in log.logged_exercises.all():
            group = _classify_muscle(ex.name)
            for s in ex.sets.filter(completed=True):
                if s.weight_kg and s.reps_done:
                    muscle_volume[group] += float(s.weight_kg) * s.reps_done

    max_vol = max(muscle_volume.values()) if muscle_volume else 1
    volume_bars = [
        {'group': g, 'volume': round(v, 1), 'pct': round((v / max_vol) * 100)}
        for g, v in sorted(muscle_volume.items(), key=lambda x: x[1], reverse=True)
    ]
    return recent_logs, volume_bars, round(sum(muscle_volume.values()))


def _compute_weekly_stats(recent_logs):
    """Returns (avg_sessions, avg_sets, avg_volume, week_vol_bars)."""
    weekly_sessions = defaultdict(int)
    weekly_volume   = defaultdict(float)
    weekly_sets     = defaultdict(int)

    for log in recent_logs:
        week = log.started_at.isocalendar()[1]
        weekly_sessions[week] += 1
        weekly_volume[week]   += log.total_volume_kg
        for ex in log.logged_exercises.all():
            weekly_sets[week] += ex.sets.filter(completed=True).count()

    active_weeks = [w for w, vol in weekly_volume.items() if vol > 0]
    n = len(active_weeks) or 1
    avg_sessions = round(sum(weekly_sessions[w] for w in active_weeks) / n, 1)
    avg_sets     = round(sum(weekly_sets[w]     for w in active_weeks) / n)
    avg_volume   = round(sum(weekly_volume[w]   for w in active_weeks) / n, 1)

    max_wv = max(weekly_volume.values()) if weekly_volume else 1
    week_vol_bars = [
        {'label': f'Tj {wk}', 'volume': round(vol, 1), 'pct': round((vol / max_wv) * 100)}
        for wk, vol in sorted(weekly_volume.items()) if vol > 0
    ]
    return avg_sessions, avg_sets, avg_volume, week_vol_bars


def _compute_exercise_history(user, selected_exercise):
    """Returns exercise_history list (last 12 weeks, with pct)."""
    if not selected_exercise:
        return []
    ex_sets = (
        LoggedSet.objects
        .filter(
            logged_exercise__training_log__user=user,
            logged_exercise__name=selected_exercise,
            completed=True, weight_kg__isnull=False,
        )
        .select_related('logged_exercise__training_log')
        .order_by('logged_exercise__training_log__started_at')
    )
    weekly_best = {}
    for s in ex_sets:
        log_dt = s.logged_exercise.training_log.started_at
        iso = log_dt.isocalendar()
        week_key = (iso[0], iso[1])
        w = float(s.weight_kg)
        reps = s.reps_done or 1
        est = _epley_1rm(w, reps)
        existing = weekly_best.get(week_key)
        if existing is None or est > existing['best_1rm']:
            weekly_best[week_key] = {
                'week_key': week_key, 'week_label': f"T{iso[1]}",
                'best_1rm': round(est, 1), 'best_weight': w, 'best_reps': reps,
            }
    history = [v for _, v in sorted(weekly_best.items())][-12:]
    if history:
        max_1rm = max(p['best_1rm'] for p in history) or 1
        for p in history:
            p['pct'] = round((p['best_1rm'] / max_1rm) * 100)
    return history


@login_required
def statistika(request):
    selected_exercise    = request.GET.get('exercise', '').strip()
    selected_session_type = request.GET.get('session_type', '').strip()

    personal_records, exercise_list = _compute_personal_records(request.user)

    session_types = list(
        PlannedSession.objects
        .filter(plan__user=request.user)
        .values_list('name', flat=True)
        .distinct()
        .order_by('name')
    )

    eight_weeks_ago = timezone.now() - timedelta(weeks=8)
    strength_chart, week_labels = _compute_strength_evolution(
        request.user, eight_weeks_ago, selected_session_type
    )
    svg_paths = _build_svg_paths(strength_chart)

    four_weeks_ago = timezone.now() - timedelta(weeks=4)
    recent_logs, volume_bars, total_volume = _compute_volume_by_muscle(
        request.user, four_weeks_ago, selected_session_type
    )
    avg_sessions, avg_sets, avg_volume, week_vol_bars = _compute_weekly_stats(recent_logs)

    exercise_history = _compute_exercise_history(request.user, selected_exercise)

    ctx = {
        'personal_records':    personal_records,
        'strength_chart':      strength_chart,
        'svg_paths':           svg_paths,
        'volume_bars':         volume_bars,
        'total_volume_kg':     total_volume,
        'week_vol_bars':       week_vol_bars,
        'avg_sessions':        avg_sessions,
        'avg_sets':            avg_sets,
        'avg_volume':          avg_volume,
        'week_labels':         [f'Tj {w}' for w in week_labels],
        'exercise_list':       exercise_list,
        'selected_exercise':   selected_exercise,
        'exercise_history':    exercise_history,
        'session_types':       session_types,
        'selected_session_type': selected_session_type,
    }
    return render(request, 'logs/statistika.html', ctx)
