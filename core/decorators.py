from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


def intake_required(view_func):
    """Combines @login_required with a completed intake profile check."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        profile = getattr(request.user, 'intake_profile', None)
        if not profile or not profile.completed:
            return redirect('intake:step1')
        return view_func(request, *args, **kwargs)
    return wrapper
