from django.contrib import admin
from .models import TrainingLog, LoggedExercise, LoggedSet


class LoggedSetInline(admin.TabularInline):
    model = LoggedSet
    extra = 0
    readonly_fields = ('logged_at',)


class LoggedExerciseInline(admin.TabularInline):
    model = LoggedExercise
    extra = 0
    show_change_link = True


@admin.register(TrainingLog)
class TrainingLogAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'started_at', 'ended_at', 'is_finished')
    list_filter = ('is_finished',)
    search_fields = ('user__email', 'planned_session__name')
    readonly_fields = ('started_at',)
    inlines = [LoggedExerciseInline]


@admin.register(LoggedExercise)
class LoggedExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'training_log', 'order')
    search_fields = ('name',)
    inlines = [LoggedSetInline]


@admin.register(LoggedSet)
class LoggedSetAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'set_number', 'weight_kg', 'reps_done', 'rpe_done', 'completed', 'logged_at')
    list_filter = ('completed',)
    readonly_fields = ('logged_at',)
