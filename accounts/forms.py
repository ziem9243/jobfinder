from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from home.models import JobPost, Skill, Profile



class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["headline", "skills", "education", "work_experience", "links", "location"]  # ✅ added location
        widgets = {
            "headline": forms.TextInput(attrs={"class": "form-control"}),
            "skills": forms.SelectMultiple(attrs={"class": "form-select"}),
            "education": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "work_experience": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "links": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "location": forms.TextInput(attrs={"class": "form-control"}),  # ✅ location input
        }
class RegisterForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        widget=forms.RadioSelect,
        label="I am a"
    )

    class Meta:
        model = User
        fields = ("username", "email", "role", "password1", "password2")
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "username": forms.TextInput(attrs={"class": "form-control"}),
        }



class JobPostForm(forms.ModelForm):
    class Meta:
        model = JobPost
        fields = [
            "title", "description", "skills", "location",
            "latitude", "longitude", "min_salary", "max_salary",
            "remote", "visa_sponsorship", "approved"
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "skills": forms.SelectMultiple(attrs={"class": "form-select"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "latitude": forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
            "longitude": forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
            "min_salary": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "max_salary": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "remote": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "visa_sponsorship": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "approved": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

class CandidateSearchForm(forms.Form):
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select"})
    )
    location_contains = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    projects_contains = forms.CharField(   # still named projects_contains for compatibility
        required=False,
        label="Projects/Experience contains",  # ✅ updated label
        widget=forms.TextInput(attrs={"class": "form-control"})
    )