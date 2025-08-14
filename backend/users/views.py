"""
Authentication and user management views.
"""
import logging

from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiExample, extend_schema,
                                   extend_schema_view)
from rest_framework import permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (EmailVerificationToken, PasswordResetToken, Team,
                     TeamMembership, UserProfile, UserSession)
from .serializers import (EmailVerificationConfirmSerializer,
                          EmailVerificationRequestSerializer,
                          PasswordChangeSerializer,
                          PasswordResetConfirmSerializer,
                          PasswordResetRequestSerializer, TeamInviteSerializer,
                          TeamMembershipSerializer, TeamSerializer,
                          UserLoginSerializer, UserProfileUpdateSerializer,
                          UserRegistrationSerializer, UserSerializer,
                          UserSessionSerializer)
from .services.email_service import EmailService

logger = logging.getLogger(__name__)


@extend_schema(
    summary="Register new user",
    description="Register a new user account and send email verification.",
    request=UserRegistrationSerializer,
    responses={
        201: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT,
        500: OpenApiTypes.OBJECT
    },
    examples=[
        OpenApiExample(
            'User registration',
            summary='Register a new user',
            description='Example of user registration with email verification',
            value={
                'username': 'johndoe',
                'email': 'john@example.com',
                'password': 'securepassword123',
                'first_name': 'John',
                'last_name': 'Doe'
            },
            request_only=True,
        ),
    ],
    tags=["Authentication"]
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    """Register a new user."""
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            with transaction.atomic():
                user = serializer.save()
                
                # Create email verification token
                verification_token = EmailVerificationToken.objects.create(user=user)
                
                # Send verification email
                EmailService.send_email_verification(
                    user=user,
                    token=verification_token.token,
                    code=verification_token.code,
                    request=request
                )
                
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'message': 'Registration successful. Please check your email to verify your account.',
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    },
                    'verification_required': True
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}")
            return Response(
                {'error': 'Registration failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="User login",
    description="Authenticate user and return JWT tokens.",
    request=UserLoginSerializer,
    responses={
        200: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT
    },
    examples=[
        OpenApiExample(
            'User login',
            summary='Login with username/email and password',
            description='Example of user authentication',
            value={
                'username': 'johndoe',
                'password': 'securepassword123'
            },
            request_only=True,
        ),
    ],
    tags=["Authentication"]
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """Authenticate user and return JWT tokens."""
    serializer = UserLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Create user session
        session = UserSession.objects.create(
            user=user,
            session_key=request.session.session_key or 'api-session',
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Update last login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        return Response({
            'message': 'Login successful',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'session_id': session.id
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="User logout",
    description="Logout user and invalidate session and tokens.",
    responses={
        200: OpenApiTypes.OBJECT,
        500: OpenApiTypes.OBJECT
    },
    tags=["Authentication"]
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """Logout user and invalidate session."""
    try:
        # Deactivate user sessions
        UserSession.objects.filter(
            user=request.user,
            is_active=True
        ).update(is_active=False)
        
        # Blacklist refresh token if provided
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass  # Token might already be invalid
        
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        return Response(
            {'error': 'Logout failed'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    summary="Get user profile",
    description="Retrieve the current authenticated user's profile information.",
    responses={200: UserSerializer},
    tags=["User Profile"]
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def profile(request):
    """Get current user profile."""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_profile(request):
    """Update current user profile."""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    serializer = UserProfileUpdateSerializer(
        profile, 
        data=request.data, 
        partial=request.method == 'PATCH'
    )
    
    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': 'Profile updated successfully',
            'user': UserSerializer(request.user).data
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """Change user password."""
    serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        user = request.user
        new_password = serializer.validated_data['new_password']
        
        # Change password
        user.set_password(new_password)
        user.save()
        
        # Send notification email
        EmailService.send_password_changed_notification(user)
        
        # Invalidate all user sessions except current
        UserSession.objects.filter(user=user).exclude(
            session_key=request.session.session_key
        ).update(is_active=False)
        
        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def request_password_reset(request):
    """Request password reset."""
    serializer = PasswordResetRequestSerializer(data=request.data)
    
    if serializer.is_valid():
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Invalidate existing reset tokens
        PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Create new reset token
        reset_token = PasswordResetToken.objects.create(user=user)
        
        # Send reset email
        EmailService.send_password_reset(
            user=user,
            token=reset_token.token,
            code=reset_token.code,
            request=request
        )
        
        return Response({
            'message': 'Password reset email sent. Please check your email.'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def confirm_password_reset(request):
    """Confirm password reset with token and code."""
    serializer = PasswordResetConfirmSerializer(data=request.data)
    
    if serializer.is_valid():
        reset_token = serializer.validated_data['reset_token']
        new_password = serializer.validated_data['new_password']
        
        # Reset password
        user = reset_token.user
        user.set_password(new_password)
        user.save()
        
        # Mark token as used
        reset_token.is_used = True
        reset_token.save()
        
        # Send notification email
        EmailService.send_password_changed_notification(user)
        
        # Invalidate all user sessions
        UserSession.objects.filter(user=user).update(is_active=False)
        
        return Response({
            'message': 'Password reset successful. Please login with your new password.'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def request_email_verification(request):
    """Request email verification."""
    user = request.user
    
    if user.profile.is_email_verified:
        return Response({
            'message': 'Email is already verified'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Invalidate existing verification tokens
    EmailVerificationToken.objects.filter(user=user, is_used=False).update(is_used=True)
    
    # Create new verification token
    verification_token = EmailVerificationToken.objects.create(user=user)
    
    # Send verification email
    EmailService.send_email_verification(
        user=user,
        token=verification_token.token,
        code=verification_token.code,
        request=request
    )
    
    return Response({
        'message': 'Verification email sent. Please check your email.'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def confirm_email_verification(request):
    """Confirm email verification with token and code."""
    serializer = EmailVerificationConfirmSerializer(data=request.data)
    
    if serializer.is_valid():
        verification_token = serializer.validated_data['verification_token']
        
        # Mark email as verified
        user = verification_token.user
        user.profile.is_email_verified = True
        user.profile.save()
        
        # Mark token as used
        verification_token.is_used = True
        verification_token.save()
        
        # Send welcome email
        EmailService.send_welcome_email(user, request)
        
        return Response({
            'message': 'Email verified successfully'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_sessions(request):
    """Get user's active sessions."""
    sessions = UserSession.objects.filter(user=request.user, is_active=True)
    serializer = UserSessionSerializer(sessions, many=True)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def terminate_session(request, session_id):
    """Terminate a specific user session."""
    try:
        session = UserSession.objects.get(
            id=session_id,
            user=request.user,
            is_active=True
        )
        session.is_active = False
        session.save()
        
        return Response({
            'message': 'Session terminated successfully'
        }, status=status.HTTP_200_OK)
        
    except UserSession.DoesNotExist:
        return Response({
            'error': 'Session not found'
        }, status=status.HTTP_404_NOT_FOUND)


@extend_schema_view(
    list=extend_schema(
        summary="List teams",
        description="Retrieve teams where the authenticated user is a member.",
        tags=["Teams"]
    ),
    create=extend_schema(
        summary="Create team",
        description="Create a new team with the authenticated user as owner.",
        tags=["Teams"]
    ),
    retrieve=extend_schema(
        summary="Get team",
        description="Retrieve a specific team by ID.",
        tags=["Teams"]
    ),
    update=extend_schema(
        summary="Update team",
        description="Update team details (owner/admin only).",
        tags=["Teams"]
    ),
    partial_update=extend_schema(
        summary="Partially update team",
        description="Partially update team details (owner/admin only).",
        tags=["Teams"]
    ),
    destroy=extend_schema(
        summary="Delete team",
        description="Delete a team (owner only).",
        tags=["Teams"]
    ),
)
class TeamViewSet(ModelViewSet):
    """ViewSet for team management."""
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get teams where user is a member."""
        return Team.objects.filter(members=self.request.user).distinct()
    
    @action(detail=True, methods=['post'])
    def invite_member(self, request, pk=None):
        """Invite a user to join the team."""
        team = self.get_object()
        
        # Check if user has permission to invite
        membership = TeamMembership.objects.get(user=request.user, team=team)
        if membership.role not in ['owner', 'admin']:
            return Response(
                {'error': 'You do not have permission to invite members'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = TeamInviteSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            role = serializer.validated_data['role']
            
            try:
                user_to_invite = User.objects.get(email=email)
                
                # Check if user is already a member
                if TeamMembership.objects.filter(user=user_to_invite, team=team).exists():
                    return Response(
                        {'error': 'User is already a member of this team'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Create membership
                TeamMembership.objects.create(
                    user=user_to_invite,
                    team=team,
                    role=role
                )
                
                return Response({
                    'message': f'User {user_to_invite.username} added to team successfully'
                }, status=status.HTTP_201_CREATED)
                
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Get team members."""
        team = self.get_object()
        memberships = TeamMembership.objects.filter(team=team)
        serializer = TeamMembershipSerializer(memberships, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['delete'])
    def remove_member(self, request, pk=None):
        """Remove a member from the team."""
        team = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check permissions
        requester_membership = TeamMembership.objects.get(user=request.user, team=team)
        if requester_membership.role not in ['owner', 'admin']:
            return Response(
                {'error': 'You do not have permission to remove members'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            membership = TeamMembership.objects.get(user_id=user_id, team=team)
            
            # Prevent removing the owner
            if membership.role == 'owner':
                return Response(
                    {'error': 'Cannot remove team owner'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            membership.delete()
            
            return Response({
                'message': 'Member removed successfully'
            }, status=status.HTTP_200_OK)
            
        except TeamMembership.DoesNotExist:
            return Response(
                {'error': 'Member not found'},
                status=status.HTTP_404_NOT_FOUND
            )
