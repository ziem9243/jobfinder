from django.contrib import admin
from django.http import HttpResponse
import csv

from home.models import Application, Profile  # already registered below
from .models import User, CandidateProfile, SavedSearch, SearchNotification


# ---------- Global CSV export action ----------
def export_as_csv(modeladmin, request, queryset):
    """
    Export the selected objects for *any* model as CSV.
    Includes concrete fields and many-to-many fields (as '; '-joined).
    """
    meta = modeladmin.model._meta
    # Concrete fields (FKs will render via __str__)
    field_names = [f.name for f in meta.fields]
    # Many-to-many field names
    m2m_field_names = [f.name for f in meta.many_to_many]

    # Prepare response
    filename = f"{meta.app_label}_{meta.model_name}_export.csv"
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)

    # Header
    writer.writerow(field_names + m2m_field_names)

    # Rows
    for obj in queryset:
        row = []
        # Concrete fields
        for f in meta.fields:
            val = getattr(obj, f.name)
            row.append("" if val is None else str(val))
        # Many-to-many (render as '; '-joined)
        for f in meta.many_to_many:
            try:
                m2m_vals = getattr(obj, f.name).all()
                row.append("; ".join(str(v) for v in m2m_vals))
            except Exception:
                row.append("")
        writer.writerow(row)

    return response


# Make the action available in *all* admin changelists
export_as_csv.short_description = "Export selected as CSV"
admin.site.add_action(export_as_csv)
# ----------------------------------------------


# Existing registrations (now automatically get the global CSV action)

admin.site.register(User)


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "location")
    search_fields = ("user__username", "location", "projects", "bio")
    filter_horizontal = ("skills",)
    # No need to add actions=[...] — the global action is already available


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "job", "applicant", "status", "applied_at", "status_updated_at")
    search_fields = ("job__title", "applicant__username", "note")
    list_filter = ("status", "applied_at", "status_updated_at")
    list_editable = ("status",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "headline", "location", "updated_at")


@admin.register(SavedSearch)
class SavedSearchAdmin(admin.ModelAdmin):
    list_display = ("name", "recruiter", "location", "is_active", "notify_on_new_matches", "created_at")
    list_filter = ("is_active", "notify_on_new_matches", "created_at")
    search_fields = ("name", "recruiter__username", "location", "headline_keywords")
    filter_horizontal = ("skills",)


@admin.register(SearchNotification)
class SearchNotificationAdmin(admin.ModelAdmin):
    list_display = ("saved_search", "message", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("saved_search__name", "message")
