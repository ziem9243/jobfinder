from django.contrib import admin
from .models import JobPost
# Register your models here.
@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin) :
    list_display = ("title", "created_by", "approved", "created_at")
    list_filter = ("approved", "created_at")
    search_fields = ("title", "description")

    actions = ["approve_posts", "reject_posts"]

    def approve_posts(self, request, queryset):
        queryset.update(approved=True)
    approve_posts.short_description = "Approve selected job posts"

    def reject_posts(self, request, queryset):
        queryset.update(approved=False)
    reject_posts.short_description = "Reject selected job posts"