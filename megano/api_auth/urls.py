from django.urls import path

from .views import SignInView, SignUpView, SignOutView, ProfileView, ChangePasswordView

app_name = "api_auth"

urlpatterns = [
    path("sign-in", SignInView.as_view(), name="login"),
    path("sign-up", SignUpView.as_view(), name="register"),
    path("sign-out", SignOutView.as_view(), name='logout'),
    path("profile", ProfileView.as_view(), name="profile"),
    path("profile/password", ChangePasswordView.as_view(), name="password"),
]
