"""
Serializers for user authentication and management.
"""

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers

from .models import (
    EmailVerificationToken,
    PasswordResetToken,
    Team,
    TeamMembership,
    UserProfile,
    UserSession,
)


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile."""

    class Meta:
        model = UserProfile
        fields = [
            "avatar",
            "bio",
            "phone_number",
            "company",
            "job_title",
            "timezone",
            "is_email_verified",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["is_email_verified", "created_at", "updated_at"]


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user with profile information."""

    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_joined",
            "last_login",
            "is_active",
            "profile",
        ]
        read_only_fields = ["id", "date_joined", "last_login", "is_active"]


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
        ]

    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        """Validate username uniqueness."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )
        return value

    def validate(self, attrs):
        """Validate password confirmation and strength."""
        password = attrs.get("password")
        password_confirm = attrs.get("password_confirm")

        if password != password_confirm:
            raise serializers.ValidationError("Passwords do not match.")

        # Validate password strength
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError({"password": e.messages})

        return attrs

    def create(self, validated_data):
        """Create user and profile."""
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")

        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        # Create user profile
        UserProfile.objects.create(user=user)

        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login."""

    username_or_email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Validate login credentials."""
        username_or_email = attrs.get("username_or_email")
        password = attrs.get("password")

        if not username_or_email or not password:
            raise serializers.ValidationError(
                "Both username/email and password are required."
            )

        # Try to find user by username or email
        user = None
        if "@" in username_or_email:
            try:
                user = User.objects.get(email=username_or_email)
                username = user.username
            except User.DoesNotExist:
                pass
        else:
            username = username_or_email

        if user or User.objects.filter(username=username).exists():
            user = authenticate(
                username=username if user is None else user.username, password=password
            )

            if user:
                if not user.is_active:
                    raise serializers.ValidationError("User account is disabled.")
                attrs["user"] = user
                return attrs

        raise serializers.ValidationError("Invalid credentials.")


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""

    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        """Validate current password."""
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        """Validate new password confirmation and strength."""
        new_password = attrs.get("new_password")
        new_password_confirm = attrs.get("new_password_confirm")

        if new_password != new_password_confirm:
            raise serializers.ValidationError("New passwords do not match.")

        # Validate password strength
        try:
            validate_password(new_password)
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": e.messages})

        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request."""

    email = serializers.EmailField()

    def validate_email(self, value):
        """Validate email exists."""
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation."""

    token = serializers.CharField()
    code = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Validate token, code, and new password."""
        token = attrs.get("token")
        code = attrs.get("code")
        new_password = attrs.get("new_password")
        new_password_confirm = attrs.get("new_password_confirm")

        # Validate token and code
        try:
            reset_token = PasswordResetToken.objects.get(
                token=token, code=code, is_used=False
            )
            if reset_token.is_expired():
                raise serializers.ValidationError("Reset token has expired.")
            attrs["reset_token"] = reset_token
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid token or code.")

        # Validate password confirmation and strength
        if new_password != new_password_confirm:
            raise serializers.ValidationError("Passwords do not match.")

        try:
            validate_password(new_password)
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": e.messages})

        return attrs


class EmailVerificationRequestSerializer(serializers.Serializer):
    """Serializer for email verification request."""

    pass  # No fields needed, uses authenticated user


class EmailVerificationConfirmSerializer(serializers.Serializer):
    """Serializer for email verification confirmation."""

    token = serializers.CharField()
    code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        """Validate token and code."""
        token = attrs.get("token")
        code = attrs.get("code")

        try:
            verification_token = EmailVerificationToken.objects.get(
                token=token, code=code, is_used=False
            )
            if verification_token.is_expired():
                raise serializers.ValidationError("Verification token has expired.")
            attrs["verification_token"] = verification_token
        except EmailVerificationToken.DoesNotExist:
            raise serializers.ValidationError("Invalid token or code.")

        return attrs


class TeamSerializer(serializers.ModelSerializer):
    """Serializer for team."""

    owner = UserSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = [
            "id",
            "name",
            "description",
            "owner",
            "member_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_member_count(self, obj):
        """Get number of team members."""
        return obj.members.count()

    def create(self, validated_data):
        """Create team with current user as owner."""
        validated_data["owner"] = self.context["request"].user
        team = super().create(validated_data)

        # Add owner as team member with owner role
        TeamMembership.objects.create(user=team.owner, team=team, role="owner")

        return team


class TeamMembershipSerializer(serializers.ModelSerializer):
    """Serializer for team membership."""

    user = UserSerializer(read_only=True)
    team = TeamSerializer(read_only=True)

    class Meta:
        model = TeamMembership
        fields = ["user", "team", "role", "joined_at"]
        read_only_fields = ["joined_at"]


class TeamInviteSerializer(serializers.Serializer):
    """Serializer for team invitation."""

    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=TeamMembership.ROLE_CHOICES, default="member"
    )

    def validate_email(self, value):
        """Validate email exists."""
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value


class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer for user session."""

    class Meta:
        model = UserSession
        fields = [
            "id",
            "session_key",
            "ip_address",
            "user_agent",
            "created_at",
            "last_activity",
            "is_active",
        ]
        read_only_fields = ["id", "created_at", "last_activity"]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    first_name = serializers.CharField(source="user.first_name", required=False)
    last_name = serializers.CharField(source="user.last_name", required=False)

    class Meta:
        model = UserProfile
        fields = [
            "first_name",
            "last_name",
            "avatar",
            "bio",
            "phone_number",
            "company",
            "job_title",
            "timezone",
        ]

    def update(self, instance, validated_data):
        """Update user and profile."""
        user_data = validated_data.pop("user", {})

        # Update user fields
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        instance.user.save()

        # Update profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance
