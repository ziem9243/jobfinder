from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import SavedSearch, SearchNotification
from home.models import Profile


class Command(BaseCommand):
    help = 'Check for new candidate matches and send notifications to recruiters'

    def handle(self, *args, **options):
        """Check all active saved searches for new matches"""
        
        # Get all active saved searches with notifications enabled
        active_searches = SavedSearch.objects.filter(
            is_active=True,
            notify_on_new_matches=True
        )
        
        total_notifications = 0
        
        for search in active_searches:
            # Get new matches since last notification
            if search.last_notified_at:
                new_matches = search.get_new_matches_since(search.last_notified_at)
            else:
                # First time - get all matches
                new_matches = search.get_matching_candidates()
            
            if new_matches.exists():
                # Create notification
                match_count = new_matches.count()
                message = f"{match_count} new candidate{'s' if match_count > 1 else ''} match your '{search.name}' search"
                
                SearchNotification.objects.create(
                    saved_search=search,
                    message=message
                )
                
                # Update last notified timestamp
                search.last_notified_at = timezone.now()
                search.save()
                
                total_notifications += 1
                
                self.stdout.write(
                    self.style.SUCCESS(f'Created notification for "{search.name}": {match_count} new matches')
                )
        
        if total_notifications == 0:
            self.stdout.write(self.style.WARNING('No new matches found for any saved searches'))
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {total_notifications} notifications')
            )
