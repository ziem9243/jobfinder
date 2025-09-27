from math import radians, sin, cos, sqrt, atan2
from django.shortcuts import render
from .models import JobPost, Skill

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c  # km
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

    # Apply normal filters
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
    print(user_lat, user_lon, "asdf")
    try:
        if user_lat and user_lon:
            user_lat = float(user_lat)
            user_lon = float(user_lon)

            for job in jobs:
                if job.latitude and job.longitude:
                    dist = haversine(user_lat, user_lon, job.latitude, job.longitude)
                    job.distance_km = round(dist, 2)
                else:
                    job.distance_km = None
                job_list.append(job)

            # Apply distance filter
            if distance_filter:
                max_dist = float(distance_filter)
                job_list = [job for job in job_list if job.distance_km and job.distance_km <= max_dist]
        else:
            # No user location → just set distance None
            for job in jobs:
                job.distance_km = None
                job_list.append(job)
    except ValueError:
        # Bad inputs → just return jobs without distance
        for job in jobs:
            job.distance_km = None
            job_list.append(job)

    for job in job_list:
        print(job.longitude, job.latitude, job.distance_km)

    return render(request, "home/index.html", {
        "jobs": job_list,
        "all_skills": all_skills,
        "selected_skills": selected_skills,
        "distance": distance_filter,
        "view_mode": view_mode,
        "user_lat": user_lat,
        "user_lon": user_lon,
    })
