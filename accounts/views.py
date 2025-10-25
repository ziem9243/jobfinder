from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q

from .forms import RegisterForm, JobPostForm, CandidateSearchForm, MessageForm, ConversationForm, SavedSearchForm
from .models import User, Conversation, Message, SavedSearch, SearchNotification
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
    
    def get(self, request, *args, **kwargs):
        # Allow GET requests for logout (less secure but more user-friendly)
        return self.post(request, *args, **kwargs)


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
    
    # Get notification count for the recruiter
    notification_count = SearchNotification.objects.filter(
        saved_search__recruiter=request.user,
        is_read=False
    ).count()
    
    return render(request, "accounts/recruiter_dashboard.html", {
        "my_jobs": my_jobs,
        "notification_count": notification_count
    })


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

        # Only seekers with visible profiles
        qs = qs.filter(user__role=User.SEEKER, profile_visible=True)

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


# ------------------------------
# Messaging views
# ------------------------------

@login_required
def conversation_list(request):
    """List all conversations for the current user"""
    if request.user.role == User.RECRUITER:
        conversations = Conversation.objects.filter(recruiter=request.user).select_related('candidate')
    else:
        conversations = Conversation.objects.filter(candidate=request.user).select_related('recruiter')
    
    # Add unread counts and latest message info
    for conversation in conversations:
        conversation.unread_count = conversation.get_unread_count_for_user(request.user)
        conversation.latest_message = conversation.get_latest_message()
    
    return render(request, "accounts/conversation_list.html", {
        "conversations": conversations
    })


@login_required
def conversation_detail(request, conversation_id):
    """View a specific conversation and its messages"""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Check if user is part of this conversation
    if request.user not in [conversation.recruiter, conversation.candidate]:
        messages.error(request, "You don't have permission to view this conversation.")
        return redirect("accounts:conversation_list")
    
    # Get all messages in this conversation
    message_list = conversation.messages.all()
    
    # Mark messages as read when viewing
    for message in message_list:
        if message.sender != request.user and not message.is_read:
            message.mark_as_read()
    
    # Handle new message form
    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
            messages.success(request, "Message sent successfully!")
            return redirect("accounts:conversation_detail", conversation_id=conversation.id)
    else:
        form = MessageForm()
    
    # Determine the other participant
    other_user = conversation.candidate if request.user == conversation.recruiter else conversation.recruiter
    
    return render(request, "accounts/conversation_detail.html", {
        "conversation": conversation,
        "message_list": message_list,
        "form": form,
        "other_user": other_user
    })


@login_required
@user_passes_test(is_recruiter)
def start_conversation(request, candidate_id):
    """Start a new conversation with a candidate (recruiter only)"""
    candidate = get_object_or_404(User, id=candidate_id, role=User.SEEKER)
    
    # Check if conversation already exists
    try:
        conversation = Conversation.objects.get(recruiter=request.user, candidate=candidate)
        return redirect("accounts:conversation_detail", conversation_id=conversation.id)
    except Conversation.DoesNotExist:
        pass
    
    if request.method == "POST":
        form = ConversationForm(request.POST)
        if form.is_valid():
            conversation = form.save(commit=False)
            conversation.recruiter = request.user
            conversation.candidate = candidate
            conversation.save()
            
            # If there's an initial message, create it
            initial_content = request.POST.get('initial_message', '')
            if initial_content.strip():
                Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    content=initial_content
                )
            
            messages.success(request, f"Conversation started with {candidate.username}")
            return redirect("accounts:conversation_detail", conversation_id=conversation.id)
    else:
        form = ConversationForm()
    
    return render(request, "accounts/start_conversation.html", {
        "form": form,
        "candidate": candidate
    })


# Saved Search Views
@login_required
@user_passes_test(is_recruiter)
def saved_searches(request):
    """Display all saved searches for the recruiter"""
    searches = SavedSearch.objects.filter(recruiter=request.user)
    
    return render(request, "accounts/saved_searches.html", {
        "searches": searches
    })


@login_required
@user_passes_test(is_recruiter)
def create_saved_search(request):
    """Create a new saved search"""
    if request.method == "POST":
        form = SavedSearchForm(request.POST)
        if form.is_valid():
            search = form.save(commit=False)
            search.recruiter = request.user
            search.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, f"Saved search '{search.name}' created successfully!")
            return redirect("accounts:saved_searches")
    else:
        form = SavedSearchForm()
    
    return render(request, "accounts/saved_search_form.html", {
        "form": form,
        "title": "Create Saved Search"
    })


@login_required
@user_passes_test(is_recruiter)
def edit_saved_search(request, search_id):
    """Edit an existing saved search"""
    search = get_object_or_404(SavedSearch, id=search_id, recruiter=request.user)
    
    if request.method == "POST":
        form = SavedSearchForm(request.POST, instance=search)
        if form.is_valid():
            form.save()
            messages.success(request, f"Saved search '{search.name}' updated successfully!")
            return redirect("accounts:saved_searches")
    else:
        form = SavedSearchForm(instance=search)
    
    return render(request, "accounts/saved_search_form.html", {
        "form": form,
        "title": "Edit Saved Search",
        "search": search
    })


@login_required
@user_passes_test(is_recruiter)
def delete_saved_search(request, search_id):
    """Delete a saved search"""
    search = get_object_or_404(SavedSearch, id=search_id, recruiter=request.user)
    
    if request.method == "POST":
        search_name = search.name
        search.delete()
        messages.success(request, f"Saved search '{search_name}' deleted successfully!")
        return redirect("accounts:saved_searches")
    
    return render(request, "accounts/delete_saved_search.html", {
        "search": search
    })


@login_required
@user_passes_test(is_recruiter)
def saved_search_results(request, search_id):
    """View results for a specific saved search"""
    search = get_object_or_404(SavedSearch, id=search_id, recruiter=request.user)
    candidates = search.get_matching_candidates()
    
    return render(request, "accounts/saved_search_results.html", {
        "search": search,
        "candidates": candidates
    })


@login_required
@user_passes_test(is_recruiter)
def notifications(request):
    """Display notifications for the recruiter"""
    notifications_list = SearchNotification.objects.filter(
        saved_search__recruiter=request.user
    ).order_by('-created_at')
    
    # Mark all notifications as read
    notifications_list.update(is_read=True)
    
    return render(request, "accounts/notifications.html", {
        "notifications": notifications_list
    })


@login_required
@user_passes_test(is_recruiter)
def job_candidate_recommendations(request, job_id):
    """Get candidate recommendations for a specific job posting"""
    job = get_object_or_404(JobPost, id=job_id, created_by=request.user)
    
    # Get job skills
    job_skills = set(job.skills.all())
    
    # Find candidates with matching skills
    candidates = Profile.objects.filter(profile_visible=True)
    
    if job_skills:
        # Filter candidates who have at least one matching skill
        for skill in job_skills:
            candidates = candidates.filter(skills=skill)
    
    # Calculate match scores for each candidate
    candidate_scores = []
    for candidate in candidates:
        candidate_skills = set(candidate.skills.all())
        common_skills = job_skills.intersection(candidate_skills)
        
        if job_skills:
            match_percentage = len(common_skills) / len(job_skills)
            skill_bonus = len(common_skills) * 0.1
            match_score = match_percentage + skill_bonus
        else:
            match_score = 0.5  # Default score if job has no skills
        
        candidate_scores.append({
            'candidate': candidate,
            'score': match_score,
            'common_skills': list(common_skills),
            'missing_skills': list(job_skills - candidate_skills)
        })
    
    # Sort by match score
    candidate_scores.sort(key=lambda x: x['score'], reverse=True)
    
    return render(request, "accounts/job_candidate_recommendations.html", {
        "job": job,
        "candidate_scores": candidate_scores,
        "job_skills": job_skills
    })
