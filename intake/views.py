from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import IntakeStep1Form, IntakeStep2Form, IntakeStep3Form, IntakeStep4Form
from .models import IntakeProfile
from .ai_service import analyze_intake_text


def _get_or_create_profile(user):
    profile, _ = IntakeProfile.objects.get_or_create(
        user=user,
        defaults={
            'age': 0, 'sex': 'male', 'height_cm': 0, 'weight_kg': 0,
            'primary_goal': 'general_fitness', 'body_part_priority': 'balanced',
            'training_experience_level': 'complete_novice', 'years_of_training': '0',
            'currently_training': 'no', 'days_per_week_available': 3,
            'max_session_minutes': 60, 'current_activity_level': 'not_active',
            'job_activity_level': 'sedentary', 'average_sleep': '7_to_8h',
            'average_stress': 'medium', 'current_steps': '5k_to_8k',
            'injury_history': 'no', 'current_pain_flags': 'no',
        }
    )
    return profile


def _make_step_view(step_num, form_class, next_url):
    """Factory for simple intake steps that just save a form and redirect."""
    @login_required
    def view(request):
        profile = _get_or_create_profile(request.user)
        form = form_class(request.POST or None, instance=profile)
        if request.method == 'POST' and form.is_valid():
            form.save()
            return redirect(next_url)
        return render(request, f'intake/step{step_num}.html', {'form': form, 'step': step_num})
    view.__name__ = f'step{step_num}'
    return view


step1 = _make_step_view(1, IntakeStep1Form, 'intake:step2')
step2 = _make_step_view(2, IntakeStep2Form, 'intake:step3')
step3 = _make_step_view(3, IntakeStep3Form, 'intake:step4')


@login_required
def step4(request):
    profile = _get_or_create_profile(request.user)
    form = IntakeStep4Form(instance=profile)

    if request.method == 'POST':
        form = IntakeStep4Form(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.completed = True
            analysis = analyze_intake_text(
                training_story=profile.training_story,
                limitations_story=profile.limitations_story,
                extra_notes=profile.extra_notes,
            )
            profile.ai_analysis = analysis
            profile.save()
            return redirect('core:home')

    show_limitations = profile.injury_history != 'no' or profile.current_pain_flags != 'no'
    return render(request, 'intake/step4.html', {
        'form': form,
        'step': 4,
        'show_limitations': show_limitations,
    })
