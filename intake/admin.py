from django.contrib import admin
from .models import IntakeProfile


@admin.register(IntakeProfile)
class IntakeProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'primary_goal', 'training_experience_level', 'completed', 'created_at']
    list_filter = ['completed', 'primary_goal', 'sex']
    search_fields = ['user__email', 'user__first_name']
