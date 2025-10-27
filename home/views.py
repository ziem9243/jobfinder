from math import radians, sin, cos, sqrt, atan2
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from accounts.forms import ProfileForm
from .models import JobPost, Skill, Application, Profile
from django.contrib.auth.decorators import login_required

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def index(request):
    jobs = JobPost.objects.all()
    all_skills = Skill.objects.all()

    selected_skills = request.GET.getlist("skills")
    title = request.GET.get("title")
    location = request.GET.get("location")
    min_salary = request.GET.get("min_salary")
    max_salary = request.GET.get("max_salary")
    remote = request.GET.get("remote")
    visa = request.GET.get("visa")
    distance_filter = request.GET.get("distance")
    user_lat = request.GET.get("lat")
    user_lon = request.GET.get("lon")
    view_mode = request.GET.get("view", "list")
    
    # Get user's commute radius and location if logged in
    user_commute_radius = None
    profile_lat = None
    profile_lon = None
    if request.user.is_authenticated:
        try:
            profile = Profile.objects.get(user=request.user)
            user_commute_radius = profile.commute_radius_miles
            profile_lat = profile.latitude
            profile_lon = profile.longitude
        except Profile.DoesNotExist:
            pass

    if title:
        jobs = jobs.filter(title__icontains=title)
    if selected_skills:
        for skill_id in selected_skills:
            jobs = jobs.filter(skills__id=skill_id)
    if location:
        jobs = jobs.filter(location__icontains=location)
    if min_salary:
        jobs = jobs.filter(min_salary__gte=min_salary)
    if max_salary:
        jobs = jobs.filter(max_salary__lte=max_salary)
    if remote:
        jobs = jobs.filter(remote=(remote == "remote"))
    if visa:
        jobs = jobs.filter(visa_sponsorship=(visa == "yes"))

    job_list = []
    try:
        # Use manual location if provided, otherwise use profile location
        effective_lat = None
        effective_lon = None
        
        if user_lat and user_lon:
            effective_lat = float(user_lat)
            effective_lon = float(user_lon)
        elif profile_lat and profile_lon:
            effective_lat = profile_lat
            effective_lon = profile_lon
            
        if effective_lat and effective_lon:
            for job in jobs:
                if job.latitude and job.longitude:
                    dist = haversine(effective_lat, effective_lon, job.latitude, job.longitude)
                    job.distance_km = round(dist, 2)
                    job.distance_miles = round(dist * 0.621371, 2)  # Convert km to miles
                else:
                    job.distance_km = None
                    job.distance_miles = None
                job_list.append(job)
            
            # Apply distance filtering (optional)
            max_distance_miles = None
            distance_filtering_active = False
            
            # Check if user explicitly set a distance filter
            if distance_filter and distance_filter.strip():
                try:
                    max_distance_miles = float(distance_filter)
                    distance_filtering_active = True
                except ValueError:
                    # If distance_filter is not a valid number, ignore it
                    pass
            
            # If no manual distance filter, check user's profile commute radius
            elif user_commute_radius is not None and user_commute_radius > 0:
                max_distance_miles = user_commute_radius
                distance_filtering_active = True
            
            # Apply distance filtering only if explicitly requested
            if distance_filtering_active and max_distance_miles is not None:
                # Filter jobs by distance (compare in miles), but always include remote jobs
                job_list = [job for job in job_list if 
                           (job.distance_miles and job.distance_miles <= max_distance_miles) or 
                           job.remote]
        else:
            for job in jobs:
                job.distance_km = None
                job.distance_miles = None
                job_list.append(job)
    except ValueError:
        for job in jobs:
            job.distance_km = None
            job.distance_miles = None
            job_list.append(job)

    # Use effective coordinates for template context
    template_lat = effective_lat if 'effective_lat' in locals() else (float(user_lat) if user_lat else None)
    template_lon = effective_lon if 'effective_lon' in locals() else (float(user_lon) if user_lon else None)
    
    # Determine if distance filtering is active for template context
    active_distance_filter = None
    if 'distance_filtering_active' in locals() and distance_filtering_active:
        active_distance_filter = max_distance_miles
    
    return render(request, "home/index.html", {
        "jobs": job_list,
        "all_skills": all_skills,
        "selected_skills": selected_skills,
        "distance": distance_filter,
        "view_mode": view_mode,
        "user_lat": template_lat,
        "user_lon": template_lon,
        "user_commute_radius": user_commute_radius,
        "active_distance_filter": active_distance_filter,
        "distance_filtering_active": locals().get('distance_filtering_active', False),
    })


def apply_job(request, job_id):
    job = get_object_or_404(JobPost, id=job_id)

    if request.method == "POST":
        note = request.POST.get("note", "")
        applicant = request.user if request.user.is_authenticated else None
        Application.objects.create(
            job=job,
            applicant=applicant,
            note=note
        )
        messages.success(request, f"Applied to {job.title} successfully!")
        return redirect("home:index")

    return redirect("home:index")


@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("home:profile")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "home/profile.html", {"form": form})


@login_required
def my_applications(request):
    """Display all applications for the current user with their status"""
    applications = Application.objects.filter(applicant=request.user).order_by('-applied_at')
    
    # Group applications by status for better organization
    status_groups = {
        'applied': applications.filter(status=Application.APPLIED),
        'review': applications.filter(status=Application.REVIEW),
        'interview': applications.filter(status=Application.INTERVIEW),
        'offer': applications.filter(status=Application.OFFER),
        'closed': applications.filter(status=Application.CLOSED),
    }
    
    return render(request, "home/my_applications.html", {
        "applications": applications,
        "status_groups": status_groups,
    })


@login_required
def job_recommendations(request):
    """Display job recommendations based on user's skills"""
    try:
        # Get user's profile and skills
        profile = Profile.objects.get(user=request.user)
        user_skills = set(profile.skills.all())
        
        if not user_skills:
            # If user has no skills, show all jobs
            recommended_jobs = JobPost.objects.filter(approved=True).order_by('-created_at')
            job_context = {}
        else:
            # Get all approved jobs
            all_jobs = JobPost.objects.filter(approved=True)
            
            # Calculate match scores for each job
            job_scores = []
            for job in all_jobs:
                job_skills = set(job.skills.all())
                
                if not job_skills:
                    # If job has no skills specified, give it a low score
                    match_score = 0.1
                    match_reason = "Job has no specific skills listed"
                else:
                    # Calculate skill match percentage
                    common_skills = user_skills.intersection(job_skills)
                    match_percentage = len(common_skills) / len(job_skills)
                    
                    # Bonus for having more matching skills
                    skill_bonus = len(common_skills) * 0.1
                    
                    # Calculate final score
                    match_score = match_percentage + skill_bonus
                    
                    if match_percentage == 1.0:
                        match_reason = f"Perfect match! You have all required skills: {', '.join([s.name for s in common_skills])}"
                    elif match_percentage >= 0.5:
                        match_reason = f"Good match! You have {len(common_skills)}/{len(job_skills)} skills: {', '.join([s.name for s in common_skills])}"
                    else:
                        match_reason = f"Partial match. You have {len(common_skills)}/{len(job_skills)} skills: {', '.join([s.name for s in common_skills])}"
                
                # Add job with score and reason
                job_scores.append({
                    'job': job,
                    'score': match_score,
                    'match_reason': match_reason,
                    'common_skills': list(common_skills) if 'common_skills' in locals() else [],
                    'missing_skills': list(job_skills - user_skills) if 'job_skills' in locals() and job_skills else []
                })
            
            # Sort by match score (highest first)
            job_scores.sort(key=lambda x: x['score'], reverse=True)
            
            # Get the recommended jobs
            recommended_jobs = [item['job'] for item in job_scores]
            
            # Pass additional context for the template
            job_context = {item['job'].id: {
                'score': item['score'],
                'match_reason': item['match_reason'],
                'common_skills': item['common_skills'],
                'missing_skills': item['missing_skills']
            } for item in job_scores}
    
    except Profile.DoesNotExist:
        # If user has no profile, show all jobs
        recommended_jobs = JobPost.objects.filter(approved=True).order_by('-created_at')
        job_context = {}
        user_skills = set()
    
    # Get user's applied job IDs to exclude them from recommendations
    applied_job_ids = Application.objects.filter(applicant=request.user).values_list('job_id', flat=True)
    
    # Filter out already applied jobs
    recommended_jobs = [job for job in recommended_jobs if job.id not in applied_job_ids]
    
    # Apply commute radius filtering if user has location and commute radius
    try:
        profile = Profile.objects.get(user=request.user)
        user_commute_radius = profile.commute_radius_miles
        
        if user_commute_radius and user_commute_radius > 0:
            # Get user's location from profile
            user_lat = profile.latitude
            user_lon = profile.longitude
            
            # Only apply distance filtering if user has set their location
            if user_lat and user_lon:
                # Calculate distances and filter
                filtered_jobs = []
                for job in recommended_jobs:
                    if job.remote:
                        # Always include remote jobs
                        filtered_jobs.append(job)
                    elif job.latitude and job.longitude:
                        # Calculate distance for non-remote jobs
                        distance_km = haversine(user_lat, user_lon, job.latitude, job.longitude)
                        distance_miles = distance_km * 0.621371
                        
                        if distance_miles <= user_commute_radius:
                            job.distance_miles = round(distance_miles, 2)
                            filtered_jobs.append(job)
                    else:
                        # Include jobs without coordinates (fallback)
                        filtered_jobs.append(job)
                
                recommended_jobs = filtered_jobs
    except Profile.DoesNotExist:
        pass
    
    return render(request, "home/job_recommendations.html", {
        "recommended_jobs": recommended_jobs,
        "job_context": job_context,
        "user_skills": user_skills,
        "applied_job_ids": applied_job_ids,
    })
