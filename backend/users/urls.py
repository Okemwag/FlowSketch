"""
URL patterns for user authentication and management.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

# Create router for viewsets
router = DefaultRouter()
router.register(r"teams", views.TeamViewSet, basename="team")

urlpatterns = [
    # Authentication endpoints
    path("auth/register/", views.register, name="register"),
    path("auth/login/", views.login_view, name="login"),
    path("auth/logout/", views.logout_view, name="logout"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Profile management
    path("auth/profile/", views.profile, name="profile"),
    path("auth/profile/update/", views.update_profile, name="update_profile"),
    # Password management
    path("auth/change-password/", views.change_password, name="change_password"),
    path(
        "auth/reset-password/request/",
        views.request_password_reset,
        name="request_password_reset",
    ),
    path(
        "auth/reset-password/confirm/",
        views.confirm_password_reset,
        name="confirm_password_reset",
    ),
    # Email verification
    path(
        "auth/verify-email/request/",
        views.request_email_verification,
        name="request_email_verification",
    ),
    path(
        "auth/verify-email/confirm/",
        views.confirm_email_verification,
        name="confirm_email_verification",
    ),
    # Session management
    path("auth/sessions/", views.user_sessions, name="user_sessions"),
    path(
        "auth/sessions/<int:session_id>/terminate/",
        views.terminate_session,
        name="terminate_session",
    ),
    # Team management (via router)
    path("", include(router.urls)),
]
