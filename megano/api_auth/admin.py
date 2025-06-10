from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Profile, Avatar


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = "id", "fullName", "phone", "balance", "avatar_link", "user_verbose"
    list_display_links = "id", "fullName",
    ordering = "id",
    search_fields = "fullName", "phone", "balance",

    def get_queryset(self, request):
        return Profile.objects.select_related("user", "avatar")

    def user_verbose(self, obj: Profile):
        return obj.user.first_name or obj.user.username

    def avatar_link(self, obj):
        if obj.avatar:
            url = reverse("admin:api_auth_avatar_change", args=[obj.avatar.id])
            return format_html('<a href="{}">Редактировать аватар</a>', url)
        return "-"

    avatar_link.short_description = "Аватар"


@admin.register(Avatar)
class AvatarAdmin(admin.ModelAdmin):
    list_display = "id", "src", "alt", "profile"
    list_display_links = "id", "src"
    ordering = "id",
    search_fields = "alt", "profile__fullName",

    def get_queryset(self, request):
        return Avatar.objects.select_related("profile")
