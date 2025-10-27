from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Count, Avg
import csv
import datetime

from home.models import Application, Profile, JobPost, Skill  # already registered below
from .models import User, CandidateProfile, SavedSearch, SearchNotification


# ---------- Global CSV export action ----------
def export_as_csv(modeladmin, request, queryset):
    """
    Export the selected objects for *any* model as CSV.
    Includes concrete fields and many-to-many fields (as '; '-joined).
    """
    meta = modeladmin.model._meta
    # Concrete fields (FKs will render via __str__)
    field_names = [f.name for f in meta.fields]
    # Many-to-many field names
    m2m_field_names = [f.name for f in meta.many_to_many]

    # Prepare response
    filename = f"{meta.app_label}_{meta.model_name}_export.csv"
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)

    # Header
    writer.writerow(field_names + m2m_field_names)

    # Rows
    for obj in queryset:
        row = []
        # Concrete fields
        for f in meta.fields:
            val = getattr(obj, f.name)
            row.append("" if val is None else str(val))
        # Many-to-many (render as '; '-joined)
        for f in meta.many_to_many:
            try:
                m2m_vals = getattr(obj, f.name).all()
                row.append("; ".join(str(v) for v in m2m_vals))
            except Exception:
                row.append("")
        writer.writerow(row)

    return response


# Make the action available in *all* admin changelists
export_as_csv.short_description = "Export selected as CSV"
admin.site.add_action(export_as_csv)

# ---------- Enhanced Reporting Actions ----------

def export_user_activity_report(modeladmin, request, queryset):
    """Export detailed user activity report with application statistics"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="user_activity_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Username', 'Email', 'Role', 'Date Joined', 'Last Login', 'Is Active',
        'Total Applications', 'Applications This Month', 'Profile Complete',
        'Skills Count', 'Location Set', 'Commute Radius'
    ])
    
    for user in queryset:
        try:
            profile = Profile.objects.get(user=user)
            skills_count = profile.skills.count()
            location_set = bool(profile.latitude and profile.longitude)
            commute_radius = profile.commute_radius_miles
            profile_complete = bool(profile.headline and profile.skills.exists())
        except Profile.DoesNotExist:
            skills_count = 0
            location_set = False
            commute_radius = 'N/A'
            profile_complete = False
        
        total_applications = Application.objects.filter(applicant=user).count()
        
        # Applications this month
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_applications = Application.objects.filter(
            applicant=user,
            applied_at__gte=current_month
        ).count()
        
        writer.writerow([
            user.username,
            user.email,
            user.get_role_display(),
            user.date_joined.strftime('%Y-%m-%d'),
            user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never',
            'Yes' if user.is_active else 'No',
            total_applications,
            monthly_applications,
            'Yes' if profile_complete else 'No',
            skills_count,
            'Yes' if location_set else 'No',
            commute_radius
        ])
    
    return response

export_user_activity_report.short_description = "Export User Activity Report"

def export_job_analytics_report(modeladmin, request, queryset):
    """Export job posting analytics with application statistics"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="job_analytics_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Job ID', 'Title', 'Company/Creator', 'Location', 'Remote', 'Salary Range',
        'Posted Date', 'Total Applications', 'Applications This Week', 
        'Skills Required', 'Visa Sponsorship', 'Approved', 'Days Since Posted'
    ])
    
    for job in queryset:
        applications_count = job.applications.count()
        
        # Applications this week
        week_ago = timezone.now() - datetime.timedelta(days=7)
        weekly_applications = job.applications.filter(applied_at__gte=week_ago).count()
        
        # Skills
        skills = ', '.join([skill.name for skill in job.skills.all()])
        
        # Salary range
        salary_range = 'N/A'
        if job.min_salary or job.max_salary:
            min_sal = f"${job.min_salary:,.0f}" if job.min_salary else "N/A"
            max_sal = f"${job.max_salary:,.0f}" if job.max_salary else "N/A"
            salary_range = f"{min_sal} - {max_sal}"
        
        # Days since posted
        days_posted = (timezone.now().date() - job.created_at.date()).days
        
        writer.writerow([
            job.id,
            job.title,
            job.created_by.username,
            job.location or 'Not specified',
            'Yes' if job.remote else 'No',
            salary_range,
            job.created_at.strftime('%Y-%m-%d'),
            applications_count,
            weekly_applications,
            skills or 'None specified',
            'Yes' if job.visa_sponsorship else 'No',
            'Yes' if job.approved else 'No',
            days_posted
        ])
    
    return response

export_job_analytics_report.short_description = "Export Job Analytics Report"

def export_application_tracking_report(modeladmin, request, queryset):
    """Export detailed application tracking report"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="application_tracking_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Application ID', 'Job Title', 'Company', 'Applicant Username', 'Applicant Email',
        'Application Date', 'Status', 'Status Updated', 'Days in Current Status',
        'Has Note', 'Job Location', 'Job Remote', 'Job Salary Range'
    ])
    
    for app in queryset:
        # Days in current status
        days_in_status = (timezone.now().date() - app.status_updated_at.date()).days
        
        # Job salary info
        job = app.job
        salary_range = 'N/A'
        if job.min_salary or job.max_salary:
            min_sal = f"${job.min_salary:,.0f}" if job.min_salary else "N/A"
            max_sal = f"${job.max_salary:,.0f}" if job.max_salary else "N/A"
            salary_range = f"{min_sal} - {max_sal}"
        
        writer.writerow([
            app.id,
            job.title,
            job.created_by.username,
            app.applicant.username if app.applicant else 'Anonymous',
            app.applicant.email if app.applicant else 'N/A',
            app.applied_at.strftime('%Y-%m-%d %H:%M'),
            app.get_status_display(),
            app.status_updated_at.strftime('%Y-%m-%d %H:%M'),
            days_in_status,
            'Yes' if app.note.strip() else 'No',
            job.location or 'Not specified',
            'Yes' if job.remote else 'No',
            salary_range
        ])
    
    return response

export_application_tracking_report.short_description = "Export Application Tracking Report"

def export_platform_usage_summary(modeladmin, request, queryset):
    """Export platform usage summary with key metrics"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="platform_usage_summary_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Overall platform metrics
    total_users = User.objects.count()
    seekers = User.objects.filter(role='seeker').count()
    recruiters = User.objects.filter(role='recruiter').count()
    active_users = User.objects.filter(is_active=True).count()
    
    total_jobs = JobPost.objects.count()
    active_jobs = JobPost.objects.filter(approved=True).count()
    remote_jobs = JobPost.objects.filter(remote=True).count()
    
    total_applications = Application.objects.count()
    
    # Write summary metrics
    writer.writerow(['Platform Usage Summary', f'Generated: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'])
    writer.writerow([])
    writer.writerow(['Metric', 'Value'])
    writer.writerow(['Total Users', total_users])
    writer.writerow(['Job Seekers', seekers])
    writer.writerow(['Recruiters', recruiters])
    writer.writerow(['Active Users', active_users])
    writer.writerow(['Total Job Posts', total_jobs])
    writer.writerow(['Active Job Posts', active_jobs])
    writer.writerow(['Remote Jobs', remote_jobs])
    writer.writerow(['Total Applications', total_applications])
    
    # Skills demand analysis
    writer.writerow([])
    writer.writerow(['Top Skills in Demand'])
    writer.writerow(['Skill', 'Job Posts Requiring', 'Users with Skill'])
    
    skills_data = Skill.objects.annotate(
        job_count=Count('jobs'),
        user_count=Count('profile')
    ).order_by('-job_count')[:10]
    
    for skill in skills_data:
        writer.writerow([skill.name, skill.job_count, skill.user_count])
    
    return response

export_platform_usage_summary.short_description = "Export Platform Usage Summary"

# Add these actions to relevant admin classes
admin.site.add_action(export_user_activity_report)
admin.site.add_action(export_job_analytics_report) 
admin.site.add_action(export_application_tracking_report)
admin.site.add_action(export_platform_usage_summary)

# ----------------------------------------------


# Existing registrations (now automatically get the global CSV action)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "role", "is_active", "date_joined", "last_login", "application_count")
    search_fields = ("username", "email", "first_name", "last_name")
    list_filter = ("role", "is_active", "is_staff", "is_superuser", "date_joined")
    actions = [export_user_activity_report]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('applications')
    
    def application_count(self, obj):
        return obj.applications.count()
    application_count.short_description = 'Applications'


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "location")
    search_fields = ("user__username", "location", "projects", "bio")
    filter_horizontal = ("skills",)
    # No need to add actions=[...] — the global action is already available


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "job", "applicant", "status", "applied_at", "status_updated_at", "days_in_status")
    search_fields = ("job__title", "applicant__username", "note")
    list_filter = ("status", "applied_at", "status_updated_at", "job__remote", "job__visa_sponsorship")
    list_editable = ("status",)
    actions = [export_application_tracking_report]
    
    def days_in_status(self, obj):
        return (timezone.now().date() - obj.status_updated_at.date()).days
    days_in_status.short_description = 'Days in Status'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "headline", "location", "skills_count", "location_set", "commute_radius_miles", "updated_at")
    search_fields = ("user__username", "headline", "location")
    list_filter = ("profile_visible", "show_headline", "show_skills", "updated_at")
    filter_horizontal = ("skills",)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('skills')
    
    def skills_count(self, obj):
        return obj.skills.count()
    skills_count.short_description = 'Skills'
    
    def location_set(self, obj):
        return bool(obj.latitude and obj.longitude)
    location_set.short_description = 'Location Set'
    location_set.boolean = True


@admin.register(SavedSearch)
class SavedSearchAdmin(admin.ModelAdmin):
    list_display = ("name", "recruiter", "location", "is_active", "notify_on_new_matches", "created_at")
    list_filter = ("is_active", "notify_on_new_matches", "created_at")
    search_fields = ("name", "recruiter__username", "location", "headline_keywords")
    filter_horizontal = ("skills",)


@admin.register(SearchNotification)
class SearchNotificationAdmin(admin.ModelAdmin):
    list_display = ("saved_search", "message", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("saved_search__name", "message")
