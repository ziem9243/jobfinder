from django.contrib import admin

from home.models import Application, Profile
from .models import User, CandidateProfile

admin.site.register(User)

@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "location")
    search_fields = ("user__username", "location", "projects", "bio")
    filter_horizontal = ("skills",)

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "job", "applicant", "applied_at")
    search_fields = ("job__title", "applicant__username", "note")
    list_filter = ("applied_at",)



@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "headline", "updated_at")
    search_fields = ("user__username", "headline")