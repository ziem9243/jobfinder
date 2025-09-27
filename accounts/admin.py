from django.contrib import admin
from .models import JobPost, Skill

admin.site.register(Skill)
admin.site.register(JobPost)
