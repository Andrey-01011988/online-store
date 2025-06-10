from django.db import models
from django.contrib.auth.models import User


def user_avatar_directory_path(instance: "Avatar", filename: str) -> str:
    return f"profile_{instance.profile.pk}/avatar/{filename}"


class Avatar(models.Model):
    """Модель для хранения аватара пользователя"""

    profile = models.OneToOneField(
        "Profile", on_delete=models.CASCADE, related_name="avatar"
    )

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


class Profile(models.Model):
    """Модель профиля пользователя"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    fullName = models.CharField(max_length=128, verbose_name="Полное имя")
    phone = models.PositiveIntegerField(
        blank=True, null=True, unique=True, verbose_name="Номер телефона"
    )
    balance = models.DecimalField(
        decimal_places=2, max_digits=10, default=0, verbose_name="Баланс"
    )

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        return f"pk={self.pk} name={self.fullName!r}"
