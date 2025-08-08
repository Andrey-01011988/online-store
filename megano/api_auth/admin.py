from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone

from .models import Profile, Avatar, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ("is_deleted", "deleted_at")
    list_filter = UserAdmin.list_filter + ("is_deleted",)
    actions = ["soft_delete", "hard_delete", "restore"]

    def get_queryset(self, request):
        return User.objects.all_with_deleted()

    def soft_delete(self, request, queryset):
        # queryset.update(is_deleted=True, deleted_at=timezone.now())
        for user in queryset:
            user.delete()

    soft_delete.short_description = "Пометить как удаленные"

    def hard_delete(self, request, queryset):
        queryset.delete()

    hard_delete.short_description = "Удалить навсегда"

    def restore(self, request, queryset):
        for user in queryset:
            user.restore()

    restore.short_description = "Восстановить"


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "fullName",
        "phone",
        "balance",
        "avatar_link",
        "user_verbose",
        "is_deleted",
        "deleted_at",
    )
    list_display_links = (
        "id",
        "fullName",
    )
    ordering = ("id",)
    search_fields = (
        "fullName",
        "phone",
        "balance",
    )
    actions = ["soft_delete", "hard_delete", "restore"]

    def get_queryset(self, request):
        return Profile.objects.all_with_deleted().select_related("user", "avatar")

    def user_verbose(self, obj: Profile):
        return obj.user.first_name or obj.user.username

    def avatar_link(self, obj):
        if obj.avatar:
            url = reverse("admin:api_auth_avatar_change", args=[obj.avatar.id])
            return format_html('<a href="{}">Редактировать аватар</a>', url)
        return "-"

    avatar_link.short_description = "Аватар"

    def soft_delete(self, request, queryset):
        queryset.update(is_deleted=True, deleted_at=timezone.now())

    soft_delete.short_description = "Пометить как удаленные"

    def restore(self, request, queryset):
        queryset.update(is_deleted=False, deleted_at=None)

    restore.short_description = "Восстановить"

    def hard_delete(self, request, queryset):
        queryset.delete()

    hard_delete.short_description = "Удалить навсегда"


@admin.register(Avatar)
class AvatarAdmin(admin.ModelAdmin):
    list_display = "id", "src", "alt", "profile", "is_deleted", "deleted_at"
    list_display_links = "id", "src"
    ordering = ("id",)
    search_fields = (
        "alt",
        "profile__fullName",
    )
    actions = ["soft_delete", "hard_delete", "restore"]

    def get_queryset(self, request):
        return Avatar.objects.all_with_deleted().select_related("profile")

    def soft_delete(self, request, queryset):
        queryset.update(is_deleted=True, deleted_at=timezone.now())

    soft_delete.short_description = "Пометить как удаленные"

    def restore(self, request, queryset):
        queryset.update(is_deleted=False, deleted_at=None)

    restore.short_description = "Восстановить"

    def hard_delete(self, request, queryset):
        queryset.delete()

    hard_delete.short_description = "Удалить навсегда"
