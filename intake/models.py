from django.db import models
from django.conf import settings


class IntakeProfile(models.Model):
    """All intake data from the 4-step wizard. One per user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='intake_profile',
    )

    # ---- Step 1: Basic + Goal ----
    age = models.PositiveIntegerField()
    SEX_CHOICES = [('male', 'Male'), ('female', 'Female')]
    sex = models.CharField(max_length=6, choices=SEX_CHOICES)
    height_cm = models.PositiveIntegerField()
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1)

    GOAL_CHOICES = [
        ('general_fitness', 'General Fitness'),
        ('muscle_gain', 'Muscle Gain'),
        ('fat_loss', 'Fat Loss'),
        ('recomposition', 'Recomposition'),
    ]
    primary_goal = models.CharField(max_length=20, choices=GOAL_CHOICES)

    BODY_PRIORITY_CHOICES = [
        ('upper_priority', 'Upper Body Priority'),
        ('lower_priority', 'Lower Body Priority'),
        ('balanced', 'Balanced'),
        ('chest_back_legs', 'Chest + Back + Legs'),
        ('legs_glutes_focus', 'Legs & Glutes Focus'),
        ('custom', 'Custom'),
    ]
    body_part_priority = models.CharField(max_length=20, choices=BODY_PRIORITY_CHOICES)

    # ---- Step 2: Experience ----
    EXPERIENCE_CHOICES = [
        ('complete_novice', 'Complete Novice'),
        ('novice', 'Novice'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    training_experience_level = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES)

    YEARS_CHOICES = [
        ('0', 'None'),
        ('0_to_1', 'Less than 1 year'),
        ('1_to_2', '1-2 years'),
        ('2_to_5', '2-5 years'),
        ('5_plus', '5+ years'),
    ]
    years_of_training = models.CharField(max_length=10, choices=YEARS_CHOICES)

    CURRENTLY_TRAINING_CHOICES = [
        ('no', 'No'),
        ('yes_irregularly', 'Yes, irregularly'),
        ('yes_regularly', 'Yes, regularly'),
    ]
    currently_training = models.CharField(max_length=20, choices=CURRENTLY_TRAINING_CHOICES)

    previous_sports = models.CharField(max_length=200, blank=True)  # comma-separated

    pushups_to_failure = models.PositiveIntegerField(null=True, blank=True)
    pullups_to_failure = models.PositiveIntegerField(null=True, blank=True)
    bodyweight_squats_to_failure = models.PositiveIntegerField(null=True, blank=True)

    # ---- Step 3: Recovery + Logistics ----
    DAYS_CHOICES = [(i, f'{i} days') for i in range(2, 7)]
    days_per_week_available = models.PositiveIntegerField(choices=DAYS_CHOICES)

    SESSION_MINUTES_CHOICES = [
        (45, '45 min'), (60, '60 min'), (75, '75 min'),
        (90, '90 min'), (120, '120 min'),
    ]
    max_session_minutes = models.PositiveIntegerField(choices=SESSION_MINUTES_CHOICES)

    ACTIVITY_CHOICES = [
        ('not_active', 'Not Active'),
        ('lightly_active', 'Lightly Active'),
        ('moderately_active', 'Moderately Active'),
        ('active', 'Active'),
        ('very_active', 'Very Active'),
    ]
    current_activity_level = models.CharField(max_length=20, choices=ACTIVITY_CHOICES)

    JOB_CHOICES = [
        ('sedentary', 'Sedentary'),
        ('mixed', 'Mixed'),
        ('physically_active', 'Physically Active'),
        ('physically_demanding', 'Physically Demanding'),
    ]
    job_activity_level = models.CharField(max_length=25, choices=JOB_CHOICES)

    SLEEP_CHOICES = [
        ('less_than_5h', 'Less than 5h'),
        ('5_to_6h', '5-6h'),
        ('6_to_7h', '6-7h'),
        ('7_to_8h', '7-8h'),
        ('8_plus_h', '8+ h'),
    ]
    average_sleep = models.CharField(max_length=15, choices=SLEEP_CHOICES)

    STRESS_CHOICES = [
        ('low', 'Low'), ('medium', 'Medium'),
        ('high', 'High'), ('very_high', 'Very High'),
    ]
    average_stress = models.CharField(max_length=10, choices=STRESS_CHOICES)

    STEPS_CHOICES = [
        ('less_than_3k', 'Less than 3k'),
        ('3k_to_5k', '3-5k'),
        ('5k_to_8k', '5-8k'),
        ('8k_to_12k', '8-12k'),
        ('12k_plus', '12k+'),
    ]
    current_steps = models.CharField(max_length=15, choices=STEPS_CHOICES)

    # ---- Step 4: Safety + Preferences ----
    INJURY_CHOICES = [
        ('no', 'No'), ('yes_minor', 'Yes, minor'), ('yes_major', 'Yes, major'),
    ]
    injury_history = models.CharField(max_length=10, choices=INJURY_CHOICES)
    body_part_affected = models.CharField(max_length=200, blank=True)

    PAIN_CHOICES = [
        ('no', 'No'), ('yes_mild', 'Yes, mild'), ('yes_significant', 'Yes, significant'),
    ]
    current_pain_flags = models.CharField(max_length=20, choices=PAIN_CHOICES)

    preferred_exercises = models.TextField(blank=True)
    disliked_exercises = models.TextField(blank=True)
    training_story = models.TextField(blank=True)
    limitations_story = models.TextField(blank=True)
    extra_notes = models.TextField(blank=True)

    # Meta
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Intake: {self.user.first_name} ({self.user.email})"
