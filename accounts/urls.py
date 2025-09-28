from django.urls import path
from .views import (
    register, RoleLoginView, RoleLogoutView,
    recruiter_welcome, recruiter_dashboard, job_create, job_edit, candidate_search
)
app_name = "accounts"

urlpatterns = [
    path("register/", register, name="register"),
    path("login/", RoleLoginView.as_view(), name="login"),
    path("logout/", RoleLogoutView.as_view(), name="logout"),

     path("recruiter/", recruiter_dashboard, name="recruiter_dashboard"),
    path("recruiter/welcome/", recruiter_welcome, name="recruiter_welcome"),  # you can keep or remove
    path("recruiter/jobs/new/", job_create, name="job_create"),
    path("recruiter/jobs/<int:pk>/edit/", job_edit, name="job_edit"),
    path("recruiter/candidates/", candidate_search, name="candidate_search"),
]


