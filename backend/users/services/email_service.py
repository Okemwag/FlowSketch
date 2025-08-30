"""
Email service for sending authentication-related emails.
"""

import logging
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending authentication emails."""

    @staticmethod
    def send_email_verification(
        user: User, token: str, code: str, request=None
    ) -> bool:
        """
        Send email verification email to user.

        Args:
            user: User instance
            token: Verification token
            code: 6-digit verification code
            request: HTTP request object for building absolute URLs

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Build verification URL
            verification_url = EmailService._build_verification_url(
                token, code, request
            )

            # Prepare email context
            context = {
                "user": user,
                "code": code,
                "token": token,
                "verification_url": verification_url,
            }

            # Render email templates
            html_message = render_to_string(
                "users/emails/email_verification.html", context
            )
            text_message = render_to_string(
                "users/emails/email_verification.txt", context
            )

            # Send email
            success = send_mail(
                subject="Verify Your Email - FlowSketch",
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            logger.info(f"Email verification sent to {user.email}")
            return success == 1

        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
            return False

    @staticmethod
    def send_password_reset(user: User, token: str, code: str, request=None) -> bool:
        """
        Send password reset email to user.

        Args:
            user: User instance
            token: Reset token
            code: 6-digit reset code
            request: HTTP request object for building absolute URLs

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Build reset URL
            reset_url = EmailService._build_password_reset_url(token, code, request)

            # Prepare email context
            context = {
                "user": user,
                "code": code,
                "token": token,
                "reset_url": reset_url,
            }

            # Render email templates
            html_message = render_to_string("users/emails/password_reset.html", context)
            text_message = render_to_string("users/emails/password_reset.txt", context)

            # Send email
            success = send_mail(
                subject="Reset Your Password - FlowSketch",
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            logger.info(f"Password reset email sent to {user.email}")
            return success == 1

        except Exception as e:
            logger.error(
                f"Failed to send password reset email to {user.email}: {str(e)}"
            )
            return False

    @staticmethod
    def send_welcome_email(user: User, request=None) -> bool:
        """
        Send welcome email to newly registered user.

        Args:
            user: User instance
            request: HTTP request object

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Prepare email context
            context = {
                "user": user,
                "login_url": EmailService._build_login_url(request),
            }

            # Simple welcome message (you can create templates for this too)
            subject = "Welcome to FlowSketch!"
            message = f"""
Hi {user.first_name or user.username},

Welcome to FlowSketch! Your account has been successfully created.

You can now start creating amazing diagrams and specifications from your unstructured text.

Get started: {context['login_url']}

Best regards,
The FlowSketch Team
            """.strip()

            # Send email
            success = send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            logger.info(f"Welcome email sent to {user.email}")
            return success == 1

        except Exception as e:
            logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
            return False

    @staticmethod
    def send_password_changed_notification(user: User) -> bool:
        """
        Send notification email when password is changed.

        Args:
            user: User instance

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            subject = "Password Changed - FlowSketch"
            message = f"""
Hi {user.first_name or user.username},

Your FlowSketch account password has been successfully changed.

If you didn't make this change, please contact our support team immediately.

Best regards,
The FlowSketch Team
            """.strip()

            # Send email
            success = send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            logger.info(f"Password change notification sent to {user.email}")
            return success == 1

        except Exception as e:
            logger.error(
                f"Failed to send password change notification to {user.email}: {str(e)}"
            )
            return False

    @staticmethod
    def _build_verification_url(token: str, code: str, request=None) -> str:
        """Build email verification URL."""
        if request:
            base_url = request.build_absolute_uri("/")[:-1]  # Remove trailing slash
        else:
            base_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")

        return f"{base_url}/verify-email?token={token}&code={code}"

    @staticmethod
    def _build_password_reset_url(token: str, code: str, request=None) -> str:
        """Build password reset URL."""
        if request:
            base_url = request.build_absolute_uri("/")[:-1]  # Remove trailing slash
        else:
            base_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")

        return f"{base_url}/reset-password?token={token}&code={code}"

    @staticmethod
    def _build_login_url(request=None) -> str:
        """Build login URL."""
        if request:
            base_url = request.build_absolute_uri("/")[:-1]  # Remove trailing slash
        else:
            base_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")

        return f"{base_url}/login"
