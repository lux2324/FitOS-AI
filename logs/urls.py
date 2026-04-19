from django.urls import path
from . import views

app_name = 'logs'

urlpatterns = [
    path('', views.session_picker, name='session_picker'),
    path('statistika/', views.statistika, name='statistika'),
    path('<int:session_id>/start/', views.start_session, name='start_session'),
    path('<int:log_id>/', views.log_session, name='log_session'),
    path('<int:log_id>/set/', views.save_set, name='save_set'),
    path('<int:log_id>/note/', views.save_note, name='save_note'),
    path('<int:log_id>/finish/', views.finish_session, name='finish_session'),
    path('<int:log_id>/summary/', views.summary, name='summary'),
]
