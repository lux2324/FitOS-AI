from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib import messages
from .forms import LoginForm, RegisterForm

User = get_user_model()


def user_login(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                u = User.objects.get(email=email)
                user = authenticate(request, username=u.username, password=password)
            except User.DoesNotExist:
                user = None
            if user:
                login(request, user)
                return redirect('core:home')
            else:
                messages.error(request, 'Invalid email or password.')

    return render(request, 'users/login.html', {'form': form})


def user_register(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    form = RegisterForm()
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('intake:step1')

    return render(request, 'users/register.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('users:login')
