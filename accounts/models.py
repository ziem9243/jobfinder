from django.contrib.auth.models import AbstractUser
from django.db import models
from home.models import Skill
from django.conf import settings
from django.utils import timezone

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


class Conversation(models.Model):
    """Represents a conversation between a recruiter and a candidate"""
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recruiter_conversations",
        limit_choices_to={'role': User.RECRUITER}
    )
    candidate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="candidate_conversations",
        limit_choices_to={'role': User.SEEKER}
    )
    subject = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['recruiter', 'candidate']
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Conversation: {self.recruiter.username} <-> {self.candidate.username}"
    
    def get_latest_message(self):
        """Get the most recent message in this conversation"""
        return self.messages.order_by('-created_at').first()
    
    def get_unread_count_for_user(self, user):
        """Get the number of unread messages for a specific user"""
        return self.messages.exclude(
            sender=user
        ).filter(
            read_at__isnull=True
        ).count()


class Message(models.Model):
    """Represents a message within a conversation"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message from {self.sender.username} in {self.conversation}"
    
    def mark_as_read(self):
        """Mark this message as read"""
        if not self.read_at:
            self.read_at = timezone.now()
            self.save()
    
    @property
    def is_read(self):
        """Check if this message has been read"""
        return self.read_at is not None


class SavedSearch(models.Model):
    """Represents a saved candidate search by a recruiter"""
    recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_searches",
        limit_choices_to={'role': User.RECRUITER}
    )
    name = models.CharField(max_length=200, help_text="Name for this saved search")
    description = models.TextField(blank=True, help_text="Optional description")
    
    # Search criteria
    skills = models.ManyToManyField('home.Skill', blank=True, related_name="saved_searches")
    location = models.CharField(max_length=200, blank=True)
    headline_keywords = models.CharField(max_length=500, blank=True, help_text="Keywords to search in headlines")
    education_keywords = models.CharField(max_length=500, blank=True, help_text="Keywords to search in education")
    experience_keywords = models.CharField(max_length=500, blank=True, help_text="Keywords to search in work experience")
    
    # Notification settings
    notify_on_new_matches = models.BooleanField(default=True, help_text="Get notified when new candidates match this search")
    last_notified_at = models.DateTimeField(null=True, blank=True, help_text="Last time notifications were sent")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, help_text="Whether this search is active")
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Saved Search"
        verbose_name_plural = "Saved Searches"
    
    def __str__(self):
        return f"{self.name} by {self.recruiter.username}"
    
    def get_matching_candidates(self):
        """Get candidates that match this search criteria"""
        from home.models import Profile
        
        # Start with all visible profiles
        candidates = Profile.objects.filter(profile_visible=True)
        
        # Filter by skills
        if self.skills.exists():
            for skill in self.skills.all():
                candidates = candidates.filter(skills=skill)
        
        # Filter by location
        if self.location:
            candidates = candidates.filter(location__icontains=self.location)
        
        # Filter by headline keywords
        if self.headline_keywords:
            keywords = self.headline_keywords.split(',')
            for keyword in keywords:
                candidates = candidates.filter(headline__icontains=keyword.strip())
        
        # Filter by education keywords
        if self.education_keywords:
            keywords = self.education_keywords.split(',')
            for keyword in keywords:
                candidates = candidates.filter(education__icontains=keyword.strip())
        
        # Filter by experience keywords
        if self.experience_keywords:
            keywords = self.experience_keywords.split(',')
            for keyword in keywords:
                candidates = candidates.filter(work_experience__icontains=keyword.strip())
        
        return candidates.distinct()
    
    def get_new_matches_since(self, since_datetime):
        """Get new candidate matches since a specific datetime"""
        candidates = self.get_matching_candidates()
        return candidates.filter(updated_at__gt=since_datetime)


class SearchNotification(models.Model):
    """Represents a notification about new candidate matches for a saved search"""
    saved_search = models.ForeignKey(SavedSearch, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.saved_search.name}"
