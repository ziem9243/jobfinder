from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q

from .forms import RegisterForm, JobPostForm, CandidateSearchForm
from .models import User
from home.models import JobPost, Profile   # ✅ import Profile from home.models


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            # 🔑 ensure seekers always have a Profile
            if user.role == User.SEEKER:
                Profile.objects.get_or_create(user=user)

            return redirect("home:index") if user.role == User.SEEKER else redirect("accounts:recruiter_dashboard")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


class RoleLoginView(LoginView):
    template_name = "accounts/login.html"

    def get_success_url(self):
        user = self.request.user
        next_url = self.get_redirect_url()
        if next_url:
            return next_url
        return reverse_lazy("home:index") if user.role == User.SEEKER else reverse_lazy("accounts:recruiter_dashboard")


class RoleLogoutView(LogoutView):
    next_page = reverse_lazy("home:index")


def is_recruiter(user):
    return user.is_authenticated and user.role == User.RECRUITER


@user_passes_test(is_recruiter)
def recruiter_welcome(request):
    return render(request, "accounts/recruiter_welcome.html")


# ------------------------------
# Recruiter-only views
# ------------------------------

@login_required
@user_passes_test(is_recruiter)
def recruiter_dashboard(request):
    my_jobs = JobPost.objects.filter(created_by=request.user).order_by("-created_at")
    return render(request, "accounts/recruiter_dashboard.html", {"my_jobs": my_jobs})


@login_required
@user_passes_test(is_recruiter)
def job_create(request):
    if request.method == "POST":
        form = JobPostForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.created_by = request.user
            job.save()
            form.save_m2m()
            messages.success(request, "Job posted.")
            return redirect("accounts:recruiter_dashboard")
    else:
        form = JobPostForm()
    return render(request, "accounts/job_form.html", {"form": form, "mode": "create"})


@login_required
@user_passes_test(is_recruiter)
def job_edit(request, pk):
    job = get_object_or_404(JobPost, pk=pk, created_by=request.user)
    if request.method == "POST":
        form = JobPostForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated.")
            return redirect("accounts:recruiter_dashboard")
    else:
        form = JobPostForm(instance=job)
    return render(request, "accounts/job_form.html", {"form": form, "mode": "edit", "job": job})


@login_required
@user_passes_test(is_recruiter)
def candidate_search(request):
    form = CandidateSearchForm(request.GET or None)
    results = Profile.objects.none()

    if form.is_valid():
        qs = Profile.objects.select_related("user").prefetch_related("skills")

        # Only seekers
        qs = qs.filter(user__role=User.SEEKER)

        skills = form.cleaned_data.get("skills")
        location_contains = form.cleaned_data.get("location_contains") or ""
        projects_contains = form.cleaned_data.get("projects_contains") or ""

        if skills and skills.exists():
            qs = qs.filter(skills__in=skills).distinct()

        if location_contains:
            qs = qs.filter(location__icontains=location_contains)

        if projects_contains:
            qs = qs.filter(
                Q(work_experience__icontains=projects_contains) |  # ✅ changed from projects to work_experience
                Q(education__icontains=projects_contains) |
                Q(headline__icontains=projects_contains)
            )

        results = qs.order_by("user__username")

    return render(request, "accounts/candidate_search.html", {
        "form": form,
        "results": results
    })
