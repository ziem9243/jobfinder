from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from home.models import Profile
from .models import SavedSearch, SearchNotification


@receiver(post_save, sender=Profile)
def check_saved_searches_for_new_matches(sender, instance, created, **kwargs):
    """
    Automatically check if updated profile matches any saved searches
    and create notifications for recruiters
    """
    if not instance.profile_visible:
        return  # Don't notify for invisible profiles
    
    # Get all active saved searches
    active_searches = SavedSearch.objects.filter(
        is_active=True,
        notify_on_new_matches=True
    )
    
    for search in active_searches:
        # Check if this profile matches the search criteria
        matches = search.get_matching_candidates().filter(id=instance.id)
        
        if matches.exists():
            # Check if we should notify (avoid duplicate notifications)
            recent_notification = SearchNotification.objects.filter(
                saved_search=search,
                created_at__gte=timezone.now() - timezone.timedelta(hours=1)
            ).exists()
            
            if not recent_notification:
                # Create notification
                message = f"New candidate {instance.user.username} matches your '{search.name}' search"
                
                SearchNotification.objects.create(
                    saved_search=search,
                    message=message
                )
                
                # Update last notified timestamp
                search.last_notified_at = timezone.now()
                search.save()

