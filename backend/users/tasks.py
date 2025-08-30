from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import EmailVerificationToken, PasswordResetToken


@shared_task
def send_verification_email(user_id, token_id):
    """Send email verification email with 6-digit code."""
    try:
        user = User.objects.get(id=user_id)
        token = EmailVerificationToken.objects.get(id=token_id)

        subject = "Verify your FlowSketch account"

        # Render HTML email template
        html_message = render_to_string(
            "users/emails/verification_email.html",
            {
                "user": user,
                "verification_code": token.code,
                "verification_url": f"{settings.FRONTEND_URL}/verify-email/{token.token}",
            },
        )

        # Create plain text version
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        return f"Verification email sent to {user.email}"

    except (User.DoesNotExist, EmailVerificationToken.DoesNotExist) as e:
        return f"Error sending verification email: {str(e)}"


@shared_task
def send_password_reset_email(user_id, token_id):
    """Send password reset email with 6-digit code."""
    try:
        user = User.objects.get(id=user_id)
        token = PasswordResetToken.objects.get(id=token_id)

        subject = "Reset your FlowSketch password"

        # Render HTML email template
        html_message = render_to_string(
            "users/emails/password_reset_email.html",
            {
                "user": user,
                "reset_code": token.code,
                "reset_url": f"{settings.FRONTEND_URL}/reset-password/{token.token}",
            },
        )

        # Create plain text version
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        return f"Password reset email sent to {user.email}"

    except (User.DoesNotExist, PasswordResetToken.DoesNotExist) as e:
        return f"Error sending password reset email: {str(e)}"


@shared_task
def send_welcome_email(user_id):
    """Send welcome email to new users."""
    try:
        user = User.objects.get(id=user_id)

        subject = "Welcome to FlowSketch!"

        # Render HTML email template
        html_message = render_to_string(
            "users/emails/welcome_email.html",
            {
                "user": user,
            },
        )

        # Create plain text version
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        return f"Welcome email sent to {user.email}"

    except User.DoesNotExist as e:
        return f"Error sending welcome email: {str(e)}"


@shared_task
def send_team_invitation_email(user_id, team_id, inviter_id):
    """Send team invitation email."""
    try:
        from .models import Team

        user = User.objects.get(id=user_id)
        team = Team.objects.get(id=team_id)
        inviter = User.objects.get(id=inviter_id)

        subject = f"You've been invited to join {team.name} on FlowSketch"

        # Render HTML email template
        html_message = render_to_string(
            "users/emails/team_invitation_email.html",
            {
                "user": user,
                "team": team,
                "inviter": inviter,
                "invitation_url": f"{settings.FRONTEND_URL}/teams/join/{team.id}",
            },
        )

        # Create plain text version
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        return f"Team invitation email sent to {user.email}"

    except (User.DoesNotExist, Team.DoesNotExist) as e:
        return f"Error sending team invitation email: {str(e)}"
