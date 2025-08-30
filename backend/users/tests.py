"""
Tests for user authentication and management.
"""

from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import (
    EmailVerificationToken,
    PasswordResetToken,
    Team,
    TeamMembership,
    UserProfile,
    UserSession,
)
from .services.email_service import EmailService


class UserModelTests(TestCase):
    """Test user-related models."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_user_profile_created_automatically(self):
        """Test that user profile is created automatically via signals."""
        self.assertTrue(hasattr(self.user, "profile"))
        self.assertIsInstance(self.user.profile, UserProfile)

    def test_email_verification_token_generation(self):
        """Test email verification token generation."""
        token = EmailVerificationToken.objects.create(user=self.user)

        self.assertEqual(len(token.token), 64)
        self.assertEqual(len(token.code), 6)
        self.assertFalse(token.is_used)
        self.assertFalse(token.is_expired())

    def test_password_reset_token_generation(self):
        """Test password reset token generation."""
        token = PasswordResetToken.objects.create(user=self.user)

        self.assertEqual(len(token.token), 64)
        self.assertEqual(len(token.code), 6)
        self.assertFalse(token.is_used)
        self.assertFalse(token.is_expired())

    def test_team_creation(self):
        """Test team creation and membership."""
        team = Team.objects.create(
            name="Test Team", description="A test team", owner=self.user
        )

        # Create membership
        membership = TeamMembership.objects.create(
            user=self.user, team=team, role="owner"
        )

        self.assertEqual(team.owner, self.user)
        self.assertEqual(membership.role, "owner")
        self.assertIn(self.user, team.members.all())


class AuthenticationAPITests(APITestCase):
    """Test authentication API endpoints."""

    def setUp(self):
        self.register_url = reverse("register")
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.profile_url = reverse("profile")

        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "first_name": "Test",
            "last_name": "User",
        }

    @patch("users.services.email_service.EmailService.send_email_verification")
    def test_user_registration_success(self, mock_send_email):
        """Test successful user registration."""
        mock_send_email.return_value = True

        response = self.client.post(self.register_url, self.user_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("tokens", response.data)
        self.assertIn("user", response.data)
        self.assertTrue(response.data["verification_required"])

        # Check user was created
        user = User.objects.get(username="testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpass123"))

        # Check email verification token was created
        self.assertTrue(EmailVerificationToken.objects.filter(user=user).exists())

        # Check email was sent
        mock_send_email.assert_called_once()

    def test_user_registration_password_mismatch(self):
        """Test registration with password mismatch."""
        data = self.user_data.copy()
        data["password_confirm"] = "differentpass"

        response = self.client.post(self.register_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

    def test_user_registration_duplicate_email(self):
        """Test registration with duplicate email."""
        # Create existing user
        User.objects.create_user(
            username="existing", email="test@example.com", password="pass123"
        )

        response = self.client.post(self.register_url, self.user_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_user_login_success(self):
        """Test successful user login."""
        # Create user
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        login_data = {"username_or_email": "testuser", "password": "testpass123"}

        response = self.client.post(self.login_url, login_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tokens", response.data)
        self.assertIn("user", response.data)
        self.assertIn("session_id", response.data)

        # Check session was created
        self.assertTrue(UserSession.objects.filter(user=user).exists())

    def test_user_login_with_email(self):
        """Test login using email instead of username."""
        # Create user
        User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        login_data = {
            "username_or_email": "test@example.com",
            "password": "testpass123",
        }

        response = self.client.post(self.login_url, login_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        login_data = {"username_or_email": "nonexistent", "password": "wrongpass"}

        response = self.client.post(self.login_url, login_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

    def test_user_logout(self):
        """Test user logout."""
        # Create and login user
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=user)

        # Create session
        session = UserSession.objects.create(
            user=user,
            session_key="test-session",
            ip_address="127.0.0.1",
            user_agent="test-agent",
        )

        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check session was deactivated
        session.refresh_from_db()
        self.assertFalse(session.is_active)

    def test_get_profile(self):
        """Test getting user profile."""
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "testuser")
        self.assertEqual(response.data["email"], "test@example.com")
        self.assertIn("profile", response.data)


class PasswordManagementTests(APITestCase):
    """Test password management functionality."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="oldpass123"
        )
        self.change_password_url = reverse("change_password")
        self.request_reset_url = reverse("request_password_reset")
        self.confirm_reset_url = reverse("confirm_password_reset")

    def test_change_password_success(self):
        """Test successful password change."""
        self.client.force_authenticate(user=self.user)

        data = {
            "current_password": "oldpass123",
            "new_password": "newpass123",
            "new_password_confirm": "newpass123",
        }

        with patch(
            "users.services.email_service.EmailService.send_password_changed_notification"
        ) as mock_email:
            mock_email.return_value = True
            response = self.client.post(self.change_password_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass123"))

        # Check notification email was sent
        mock_email.assert_called_once_with(self.user)

    def test_change_password_wrong_current(self):
        """Test password change with wrong current password."""
        self.client.force_authenticate(user=self.user)

        data = {
            "current_password": "wrongpass",
            "new_password": "newpass123",
            "new_password_confirm": "newpass123",
        }

        response = self.client.post(self.change_password_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("current_password", response.data)

    @patch("users.services.email_service.EmailService.send_password_reset")
    def test_request_password_reset(self, mock_send_email):
        """Test password reset request."""
        mock_send_email.return_value = True

        data = {"email": "test@example.com"}
        response = self.client.post(self.request_reset_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check reset token was created
        self.assertTrue(PasswordResetToken.objects.filter(user=self.user).exists())

        # Check email was sent
        mock_send_email.assert_called_once()

    def test_request_password_reset_invalid_email(self):
        """Test password reset request with invalid email."""
        data = {"email": "nonexistent@example.com"}
        response = self.client.post(self.request_reset_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_confirm_password_reset(self):
        """Test password reset confirmation."""
        # Create reset token
        reset_token = PasswordResetToken.objects.create(user=self.user)

        data = {
            "token": reset_token.token,
            "code": reset_token.code,
            "new_password": "newpass123",
            "new_password_confirm": "newpass123",
        }

        with patch(
            "users.services.email_service.EmailService.send_password_changed_notification"
        ) as mock_email:
            mock_email.return_value = True
            response = self.client.post(self.confirm_reset_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass123"))

        # Check token was marked as used
        reset_token.refresh_from_db()
        self.assertTrue(reset_token.is_used)


class EmailVerificationTests(APITestCase):
    """Test email verification functionality."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.request_verification_url = reverse("request_email_verification")
        self.confirm_verification_url = reverse("confirm_email_verification")

    @patch("users.services.email_service.EmailService.send_email_verification")
    def test_request_email_verification(self, mock_send_email):
        """Test email verification request."""
        mock_send_email.return_value = True
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.request_verification_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check verification token was created
        self.assertTrue(EmailVerificationToken.objects.filter(user=self.user).exists())

        # Check email was sent
        mock_send_email.assert_called_once()

    def test_confirm_email_verification(self):
        """Test email verification confirmation."""
        # Create verification token
        verification_token = EmailVerificationToken.objects.create(user=self.user)

        data = {"token": verification_token.token, "code": verification_token.code}

        with patch(
            "users.services.email_service.EmailService.send_welcome_email"
        ) as mock_email:
            mock_email.return_value = True
            response = self.client.post(self.confirm_verification_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check email was marked as verified
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.is_email_verified)

        # Check token was marked as used
        verification_token.refresh_from_db()
        self.assertTrue(verification_token.is_used)


class EmailServiceTests(TestCase):
    """Test email service functionality."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    @patch("users.services.email_service.send_mail")
    def test_send_email_verification(self, mock_send_mail):
        """Test sending email verification."""
        mock_send_mail.return_value = 1

        result = EmailService.send_email_verification(
            user=self.user, token="test-token", code="123456"
        )

        self.assertTrue(result)
        mock_send_mail.assert_called_once()

        # Check email content
        call_args = mock_send_mail.call_args
        self.assertIn("Verify Your Email", call_args[1]["subject"])
        self.assertEqual(call_args[1]["recipient_list"], [self.user.email])

    @patch("users.services.email_service.send_mail")
    def test_send_password_reset(self, mock_send_mail):
        """Test sending password reset email."""
        mock_send_mail.return_value = 1

        result = EmailService.send_password_reset(
            user=self.user, token="test-token", code="123456"
        )

        self.assertTrue(result)
        mock_send_mail.assert_called_once()

        # Check email content
        call_args = mock_send_mail.call_args
        self.assertIn("Reset Your Password", call_args[1]["subject"])
        self.assertEqual(call_args[1]["recipient_list"], [self.user.email])
