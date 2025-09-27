from django.shortcuts import render
from .models import JobPost, Skill

def index(request):
    jobs = JobPost.objects.all()
    all_skills = Skill.objects.all()

    # Store selected skills explicitly
    selected_skills = request.GET.getlist("skills")

    # Other filters
    title = request.GET.get("title")
    location = request.GET.get("location")
    min_salary = request.GET.get("min_salary")
    max_salary = request.GET.get("max_salary")
    remote = request.GET.get("remote")
    visa = request.GET.get("visa")

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

    return render(request, "home/index.html", {
        "jobs": jobs,
        "all_skills": all_skills,
        "selected_skills": selected_skills,  # ✅ new context
    })
