from django.conf import settings
from django.db import models



class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    headline = models.CharField(max_length=255, blank=True)
    skills = models.ManyToManyField("Skill", blank=True)
    education = models.TextField(blank=True)
    work_experience = models.TextField(blank=True)
    links = models.TextField(blank=True)  # e.g. LinkedIn, GitHub, Portfolio
    location = models.CharField(max_length=200, blank=True)
    
    # Commute preferences
    commute_radius_miles = models.PositiveIntegerField(
        default=25, 
        help_text="Preferred commute radius in miles (0 = no limit, remote only)"
    )

    # Privacy settings
    show_headline = models.BooleanField(default=True, help_text="Show headline to recruiters")
    show_skills = models.BooleanField(default=True, help_text="Show skills to recruiters")
    show_education = models.BooleanField(default=True, help_text="Show education to recruiters")
    show_work_experience = models.BooleanField(default=True, help_text="Show work experience to recruiters")
    show_links = models.BooleanField(default=True, help_text="Show links to recruiters")
    show_location = models.BooleanField(default=True, help_text="Show location to recruiters")
    profile_visible = models.BooleanField(default=True, help_text="Make profile visible to recruiters in search")

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class JobPost(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    skills = models.ManyToManyField(Skill, blank=True, related_name="jobs")
    location = models.CharField(max_length=200, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    min_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    remote = models.BooleanField(default=False)
    visa_sponsorship = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_posts",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Application(models.Model):
    APPLIED = "applied"
    REVIEW = "review"
    INTERVIEW = "interview"
    OFFER = "offer"
    CLOSED = "closed"
    
    STATUS_CHOICES = [
        (APPLIED, "Applied"),
        (REVIEW, "Under Review"),
        (INTERVIEW, "Interview"),
        (OFFER, "Offer"),
        (CLOSED, "Closed"),
    ]
    
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applications",
    )
    note = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=APPLIED)
    status_updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        who = self.applicant.username if self.applicant else "Anonymous"
        return f"{who} -> {self.job.title} ({self.get_status_display()})"
