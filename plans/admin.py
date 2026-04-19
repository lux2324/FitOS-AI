from django.contrib import admin
from .models import WeeklyPlan, PlannedSession, PlannedExercise


class PlannedExerciseInline(admin.TabularInline):
    model = PlannedExercise
    extra = 0


class PlannedSessionInline(admin.TabularInline):
    model = PlannedSession
    extra = 0


@admin.register(WeeklyPlan)
class WeeklyPlanAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "week_number", "split_type", "created_at")
    list_filter = ("split_type", "created_at")
    readonly_fields = ("volume_targets", "volume_actual", "validation_report",
                       "ai_draft", "ai_refined", "created_at")
    inlines = [PlannedSessionInline]


@admin.register(PlannedSession)
class PlannedSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "plan", "order", "name", "template_key")
    inlines = [PlannedExerciseInline]


@admin.register(PlannedExercise)
class PlannedExerciseAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "order", "name", "role", "sets",
                    "reps_min", "reps_max", "target_rpe")
