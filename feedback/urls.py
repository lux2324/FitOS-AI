from django.urls import path
from . import views

app_name = 'feedback'

urlpatterns = [
    path('weekly/', views.weekly_feedback, name='weekly'),
    path('generate-next/', views.generate_next_week, name='generate_next_week'),
    # Legacy alias kept so any cached/bookmarked URLs still work
    path('', views.feedback_form, name='feedback_form'),
]
