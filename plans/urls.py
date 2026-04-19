from django.urls import path
from . import views

app_name = "plans"

urlpatterns = [
    path("", views.weekly_plan, name="weekly_plan"),
    path("generate/", views.generate, name="generate"),
    path("batch/", views.batch_generate, name="batch_generate"),
    path("substitute/", views.substitute_exercise, name="substitute_exercise"),
    path("<int:plan_id>/", views.plan_detail, name="plan_detail"),
]
