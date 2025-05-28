from django.urls import path

from .views import SignInView, SignUpView, SignOutView


app_name = "api_auth"

urlpatterns = [
    path("sign-in", SignInView.as_view(), name="login"),
    path("sign-up", SignUpView.as_view(), name="register"),
    path("sign-out", SignOutView.as_view(), name='logout'),
]
