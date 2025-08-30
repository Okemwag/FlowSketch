"""
Management command to create test users for development.
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from users.models import UserProfile


class Command(BaseCommand):
    help = "Create test users for development"

    def add_arguments(self, parser):
        parser.add_argument(
            "--admin",
            action="store_true",
            help="Create admin user",
        )

    def handle(self, *args, **options):
        if options["admin"]:
            self.create_admin_user()
        else:
            self.create_test_users()

    def create_admin_user(self):
        """Create admin user."""
        if User.objects.filter(username="admin").exists():
            self.stdout.write(self.style.WARNING("Admin user already exists"))
            return

        admin = User.objects.create_superuser(
            username="admin",
            email="admin@flowsketch.com",
            password="admin123",
            first_name="Admin",
            last_name="User",
        )

        # Update profile
        profile = admin.profile
        profile.is_email_verified = True
        profile.company = "FlowSketch"
        profile.job_title = "Administrator"
        profile.save()

        self.stdout.write(self.style.SUCCESS(f"Admin user created: {admin.username}"))

    def create_test_users(self):
        """Create test users."""
        test_users = [
            {
                "username": "testuser1",
                "email": "test1@example.com",
                "password": "testpass123",
                "first_name": "Test",
                "last_name": "User One",
                "company": "Test Company",
                "job_title": "Developer",
            },
            {
                "username": "testuser2",
                "email": "test2@example.com",
                "password": "testpass123",
                "first_name": "Test",
                "last_name": "User Two",
                "company": "Another Company",
                "job_title": "Designer",
            },
        ]

        for user_data in test_users:
            if User.objects.filter(username=user_data["username"]).exists():
                self.stdout.write(
                    self.style.WARNING(f"User {user_data['username']} already exists")
                )
                continue

            user = User.objects.create_user(
                username=user_data["username"],
                email=user_data["email"],
                password=user_data["password"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
            )

            # Update profile
            profile = user.profile
            profile.is_email_verified = True
            profile.company = user_data["company"]
            profile.job_title = user_data["job_title"]
            profile.save()

            self.stdout.write(self.style.SUCCESS(f"Test user created: {user.username}"))
