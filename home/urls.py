from django.urls import path
from . import views

app_name = "home"

urlpatterns = [
    path("", views.index, name="index"),
    path("apply/<int:job_id>/", views.apply_job, name="apply_job"),
    path("profile/", views.profile_view, name="profile"),
]
