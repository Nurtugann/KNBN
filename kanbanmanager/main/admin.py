# main/admin.py

from django.contrib import admin
from .models import Company, Status, CompanyStatusHistory, Comment, Profile, Region


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "status",
        "region",
        "position",
    )
    list_filter = (
        "status",
        "region",
    )
    search_fields = ("name",)
    ordering = ("position",)


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "duration_days")
    list_editable = ("order", "duration_days")
    ordering = ("order",)


@admin.register(CompanyStatusHistory)
class CompanyStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("company", "status", "changed_at")
    list_filter = ("status", "changed_at")
    date_hierarchy = "changed_at"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("company", "author", "created_at")
    list_filter = ("created_at",)
    search_fields = ("text",)


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "get_regions")
    list_filter = ("regions",)
    search_fields = ("user__username",)
    filter_horizontal = ("regions",)

    def get_regions(self, obj):
        return ", ".join([r.get_code_display() for r in obj.regions.all()])
    get_regions.short_description = "Регионы"
