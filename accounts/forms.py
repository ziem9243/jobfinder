from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Conversation, Message, SavedSearch
from home.models import JobPost, Skill, Profile



class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            "headline", "skills", "education", "work_experience", "links", "location",
            "commute_radius_miles",
            "show_headline", "show_skills", "show_education", "show_work_experience", 
            "show_links", "show_location", "profile_visible"
        ]
        widgets = {
            "headline": forms.TextInput(attrs={"class": "form-control"}),
            "skills": forms.SelectMultiple(attrs={"class": "form-select"}),
            "education": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "work_experience": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "links": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "commute_radius_miles": forms.NumberInput(attrs={"class": "form-control", "min": 0, "max": 100}),
            # Privacy settings widgets
            "show_headline": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "show_skills": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "show_education": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "show_work_experience": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "show_links": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "show_location": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "profile_visible": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "show_headline": "Show headline to recruiters",
            "show_skills": "Show skills to recruiters", 
            "show_education": "Show education to recruiters",
            "show_work_experience": "Show work experience to recruiters",
            "show_links": "Show links to recruiters",
            "show_location": "Show location to recruiters",
            "profile_visible": "Make profile visible to recruiters in search",
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


class MessageForm(forms.ModelForm):
    """Form for sending messages"""
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Type your message here...'
            })
        }
        labels = {
            'content': 'Message'
        }


class ConversationForm(forms.ModelForm):
    """Form for creating new conversations"""
    class Meta:
        model = Conversation
        fields = ['subject']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter conversation subject...'
            })
        }
        labels = {
            'subject': 'Subject'
        }


class SavedSearchForm(forms.ModelForm):
    """Form for creating and editing saved candidate searches"""
    class Meta:
        model = SavedSearch
        fields = [
            'name', 'description', 'skills', 'location', 
            'headline_keywords', 'education_keywords', 'experience_keywords',
            'notify_on_new_matches', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'skills': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'headline_keywords': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., senior developer, team lead'}),
            'education_keywords': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., computer science, engineering'}),
            'experience_keywords': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., startup, fintech, management'}),
            'notify_on_new_matches': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'headline_keywords': 'Comma-separated keywords to search in candidate headlines',
            'education_keywords': 'Comma-separated keywords to search in education fields',
            'experience_keywords': 'Comma-separated keywords to search in work experience',
        }