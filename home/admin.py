from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Count
import csv
import datetime

from .models import JobPost, Skill

def export_jobs_with_applications(modeladmin, request, queryset):
    """Export jobs with detailed application metrics"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="jobs_with_applications_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Job ID', 'Title', 'Creator', 'Location', 'Remote', 'Posted Date', 
        'Total Applications', 'Applied Status', 'Under Review', 'Interview', 
        'Offer', 'Closed', 'Skills Required', 'Salary Range', 'Days Active'
    ])
    
    for job in queryset:
        applications = job.applications.all()
        
        # Count by status
        status_counts = {
            'applied': applications.filter(status='applied').count(),
            'review': applications.filter(status='review').count(),
            'interview': applications.filter(status='interview').count(),
            'offer': applications.filter(status='offer').count(),
            'closed': applications.filter(status='closed').count(),
        }
        
        skills = ', '.join([skill.name for skill in job.skills.all()])
        salary_range = 'N/A'
        if job.min_salary or job.max_salary:
            min_sal = f"${job.min_salary:,.0f}" if job.min_salary else "N/A"
            max_sal = f"${job.max_salary:,.0f}" if job.max_salary else "N/A"
            salary_range = f"{min_sal} - {max_sal}"
        
        days_active = (timezone.now().date() - job.created_at.date()).days
        
        writer.writerow([
            job.id,
            job.title,
            job.created_by.username,
            job.location or 'Not specified',
            'Yes' if job.remote else 'No',
            job.created_at.strftime('%Y-%m-%d'),
            applications.count(),
            status_counts['applied'],
            status_counts['review'],
            status_counts['interview'],
            status_counts['offer'],
            status_counts['closed'],
            skills or 'None specified',
            salary_range,
            days_active
        ])
    
    return response

export_jobs_with_applications.short_description = "Export Jobs with Application Metrics"

def export_skills_demand_analysis(modeladmin, request, queryset):
    """Export skills demand analysis based on selected skills"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="skills_demand_analysis_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Skill Name', 'Jobs Requiring Skill', 'Total Applications to These Jobs',
        'Users with This Skill', 'Supply vs Demand Ratio', 'Average Salary Range'
    ])
    
    for skill in queryset:
        jobs_with_skill = JobPost.objects.filter(skills=skill)
        total_applications = sum(job.applications.count() for job in jobs_with_skill)
        users_with_skill = skill.profile_set.count()
        
        # Calculate supply vs demand ratio
        if jobs_with_skill.count() > 0:
            ratio = users_with_skill / jobs_with_skill.count()
        else:
            ratio = 0
        
        # Calculate average salary range
        salaries = []
        for job in jobs_with_skill:
            if job.min_salary:
                salaries.append(float(job.min_salary))
            if job.max_salary:
                salaries.append(float(job.max_salary))
        
        avg_salary = f"${sum(salaries)/len(salaries):,.0f}" if salaries else "N/A"
        
        writer.writerow([
            skill.name,
            jobs_with_skill.count(),
            total_applications,
            users_with_skill,
            f"{ratio:.2f}",
            avg_salary
        ])
    
    return response

export_skills_demand_analysis.short_description = "Export Skills Demand Analysis"

@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    list_display = ("title", "location", "min_salary", "max_salary", "remote", "visa_sponsorship", "created_at")
    search_fields = ("title", "location", "description")
    list_filter = ("remote", "visa_sponsorship", "skills", "approved", "created_at")
    filter_horizontal = ("skills",)
    actions = [export_jobs_with_applications]

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "job_count", "user_count")
    search_fields = ("name",)
    actions = [export_skills_demand_analysis]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            job_count=Count('jobs', distinct=True),
            user_count=Count('profile', distinct=True)
        )
    
    def job_count(self, obj):
        return obj.job_count
    job_count.short_description = 'Jobs Requiring'
    job_count.admin_order_field = 'job_count'
    
    def user_count(self, obj):
        return obj.user_count
    user_count.short_description = 'Users with Skill'
    user_count.admin_order_field = 'user_count'
