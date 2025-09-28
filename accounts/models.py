from django.contrib.auth.models import AbstractUser
from django.db import models
from home.models import Skill
from django.conf import settings

class User(AbstractUser):
    SEEKER = "seeker"
    RECRUITER = "recruiter"
    ROLE_CHOICES = [
        (SEEKER, "Job Seeker"),
        (RECRUITER, "Recruiter"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=SEEKER)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class CandidateProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="candidate_profile")
    location = models.CharField(max_length=200, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    headline = models.CharField(max_length=255, blank=True)   # new
    education = models.TextField(blank=True)                  # new
    work_experience = models.TextField(blank=True)            # new
    links = models.TextField(blank=True)                      # new

    bio = models.TextField(blank=True)
    projects = models.TextField(blank=True)
    skills = models.ManyToManyField(Skill, blank=True, related_name="candidates")

    def __str__(self):
        return f"CandidateProfile({self.user.username})"
