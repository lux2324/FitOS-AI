from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


@login_required
def home(request):
    # If user hasn't completed intake, redirect to intake wizard
    if not hasattr(request.user, 'intake_profile') or not request.user.intake_profile.completed:
        return redirect('intake:step1')
    return render(request, 'core/dashboard.html')
