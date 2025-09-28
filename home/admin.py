from django.contrib import admin
from .models import JobPost, Skill

@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    list_display = ("title", "location", "min_salary", "max_salary", "remote", "visa_sponsorship")
    search_fields = ("title", "location", "description")
    list_filter = ("remote", "visa_sponsorship", "skills")

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ("name",)
