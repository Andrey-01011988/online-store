from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.conf import settings

from common_mode.models import SoftDeleteModel, SoftDeleteManager


class SoftDeleteUserManager(SoftDeleteManager, UserManager):
    pass


class User(AbstractUser, SoftDeleteModel):
    """Модель пользователя"""

    objects = SoftDeleteUserManager()

    class Meta(AbstractUser.Meta):
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        db_table = 'api_auth_user'  # Сохраняем совместимость с оригинальной таблицей
        swappable = 'AUTH_USER_MODEL'
        app_label = 'api_auth'  # Явно указываем app_label

    def __str__(self):
        return self.username

    def delete(self, *args, **kwargs):
        if hasattr(self, "profile") and hasattr(self.profile, "avatar"):
            self.profile.delete()
            self.profile.avatar.delete()
        elif hasattr(self, "profile"):
            self.profile.delete()
        super().delete(*args, **kwargs)

    def restore(self, *args, **kwargs):
        if hasattr(self, "profile") and hasattr(self.profile, "avatar"):
            self.profile.restore()
            self.profile.avatar.restore()
        elif hasattr(self, "profile"):
            self.profile.restore()
        super().restore(*args, **kwargs)


def user_avatar_directory_path(instance: "Avatar", filename: str) -> str:
    return f"profile_{instance.profile.pk}/avatar/{filename}"


class Avatar(SoftDeleteModel):
    """Модель для хранения аватара пользователя"""

    profile = models.OneToOneField("Profile", on_delete=models.CASCADE, related_name="avatar")

    src = models.ImageField(
        upload_to=user_avatar_directory_path,
        default="app_users/avatars/default.png",
        verbose_name="Ссылка",
    )
    alt = models.CharField(max_length=128, verbose_name="Описание")

    class Meta:
        verbose_name = "Аватар"
        verbose_name_plural = "Аватары"

    def __str__(self):
        return self.alt


class Profile(SoftDeleteModel):
    """Модель профиля пользователя"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    fullName = models.CharField(max_length=128, verbose_name="Полное имя")
    phone = models.PositiveIntegerField(
        blank=True, null=True, unique=True, verbose_name="Номер телефона"
    )
    balance = models.DecimalField(decimal_places=2, max_digits=10, default=0, verbose_name="Баланс")

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        return f"pk={self.pk} name={self.fullName!r}"
