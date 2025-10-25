from django.urls import path
from .views import (
    register, RoleLoginView, RoleLogoutView,
    recruiter_welcome, recruiter_dashboard, job_create, job_edit, candidate_search,
    conversation_list, conversation_detail, start_conversation,
    saved_searches, create_saved_search, edit_saved_search, delete_saved_search,
    saved_search_results, notifications, job_candidate_recommendations
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
    
    # Messaging URLs
    path("messages/", conversation_list, name="conversation_list"),
    path("messages/<int:conversation_id>/", conversation_detail, name="conversation_detail"),
    path("messages/start/<int:candidate_id>/", start_conversation, name="start_conversation"),
    
    # Saved Search URLs
    path("saved-searches/", saved_searches, name="saved_searches"),
    path("saved-searches/create/", create_saved_search, name="create_saved_search"),
    path("saved-searches/<int:search_id>/edit/", edit_saved_search, name="edit_saved_search"),
    path("saved-searches/<int:search_id>/delete/", delete_saved_search, name="delete_saved_search"),
    path("saved-searches/<int:search_id>/results/", saved_search_results, name="saved_search_results"),
    
    # Notification URLs
    path("notifications/", notifications, name="notifications"),
    
    # Candidate Recommendation URLs
    path("jobs/<int:job_id>/candidates/", job_candidate_recommendations, name="job_candidate_recommendations"),
]


