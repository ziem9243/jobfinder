from django.contrib import admin
from .models import User, CandidateProfile

admin.site.register(User)

@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "location")
    search_fields = ("user__username", "location", "projects", "bio")
    filter_horizontal = ("skills",)
