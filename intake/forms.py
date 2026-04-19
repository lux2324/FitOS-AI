from django import forms
from .models import IntakeProfile


class IntakeStep1Form(forms.ModelForm):
    """Basic + Goal"""

    class Meta:
        model = IntakeProfile
        fields = ['age', 'sex', 'height_cm', 'weight_kg', 'primary_goal', 'body_part_priority']
        widgets = {
            'age': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '25', 'min': 16, 'max': 100}),
            'height_cm': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '180', 'min': 140, 'max': 230}),
            'weight_kg': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '80', 'step': '0.1', 'min': 40, 'max': 240}),
            'sex': forms.HiddenInput(),
            'primary_goal': forms.HiddenInput(),
            'body_part_priority': forms.Select(attrs={'class': 'form-input'}),
        }

    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age and (age < 16 or age > 100):
            raise forms.ValidationError('Age must be between 16 and 100.')
        return age

    def clean_height_cm(self):
        h = self.cleaned_data.get('height_cm')
        if h and (h < 140 or h > 230):
            raise forms.ValidationError('Height must be between 140 and 230 cm.')
        return h

    def clean_weight_kg(self):
        w = self.cleaned_data.get('weight_kg')
        if w and (w < 40 or w > 240):
            raise forms.ValidationError('Weight must be between 40 and 240 kg.')
        return w


class IntakeStep2Form(forms.ModelForm):
    """Experience"""

    class Meta:
        model = IntakeProfile
        fields = [
            'training_experience_level', 'years_of_training', 'currently_training',
            'previous_sports',
            'pushups_to_failure', 'pullups_to_failure', 'bodyweight_squats_to_failure',
        ]
        widgets = {
            'training_experience_level': forms.HiddenInput(),
            'years_of_training': forms.Select(attrs={'class': 'form-input'}),
            'currently_training': forms.Select(attrs={'class': 'form-input'}),
            'previous_sports': forms.HiddenInput(),
            'pushups_to_failure': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '15'}),
            'pullups_to_failure': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '5'}),
            'bodyweight_squats_to_failure': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '30'}),
        }


class IntakeStep3Form(forms.ModelForm):
    """Recovery + Logistics"""

    class Meta:
        model = IntakeProfile
        fields = [
            'days_per_week_available', 'max_session_minutes',
            'current_activity_level', 'job_activity_level',
            'average_sleep', 'average_stress', 'current_steps',
        ]
        widgets = {
            'days_per_week_available': forms.HiddenInput(),
            'max_session_minutes': forms.HiddenInput(),
            'current_activity_level': forms.Select(attrs={'class': 'form-input'}),
            'job_activity_level': forms.Select(attrs={'class': 'form-input'}),
            'average_sleep': forms.Select(attrs={'class': 'form-input'}),
            'average_stress': forms.Select(attrs={'class': 'form-input'}),
            'current_steps': forms.Select(attrs={'class': 'form-input'}),
        }


class IntakeStep4Form(forms.ModelForm):
    """Safety + Preferences"""

    class Meta:
        model = IntakeProfile
        fields = [
            'injury_history', 'body_part_affected', 'current_pain_flags',
            'training_story', 'limitations_story', 'extra_notes',
        ]
        widgets = {
            'injury_history': forms.HiddenInput(),
            'current_pain_flags': forms.HiddenInput(),
            'body_part_affected': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. left shoulder, lower back'}),
            'training_story': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Briefly describe your training history...'}),
            'limitations_story': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Describe any injuries or limitations...'}),
            'extra_notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Anything else we should know?'}),
        }
