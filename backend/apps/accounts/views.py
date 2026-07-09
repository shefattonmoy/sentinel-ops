# apps/accounts/views.py
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .two_factor import TwoFactorService
from django.contrib.auth import get_user_model
from apps.audit.models import log_action

from .models import Organization
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    OrganizationSerializer,
    CustomTokenObtainPairSerializer,
    ChangePasswordSerializer,
    UserProfileUpdateSerializer,
    UserProfileSerializer,
    ProfileUpdateSerializer,
    AvatarUploadSerializer,
    TwoFactorSetupSerializer,
    TwoFactorVerifySerializer,
    TwoFactorDisableSerializer,
    ChangePasswordSerializer,
)

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view that returns user data with tokens"""

    serializer_class = CustomTokenObtainPairSerializer


class UserRegistrationView(generics.CreateAPIView):
    """Register a new user"""

    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "status": "success",
                "message": "User registered successfully",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get or update current user profile"""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return UserProfileUpdateSerializer
        return UserSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            {
                "status": "success",
                "message": "Profile updated successfully",
                "user": UserSerializer(instance).data,
            }
        )


class ChangePasswordView(APIView):
    """Change user password"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        data = serializer.validated_data

        # Check old password
        if not user.check_password(data["old_password"]):
            return Response(
                {"error": "Current password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Set new password
        user.set_password(data["new_password"])
        user.save()

        return Response(
            {"status": "success", "message": "Password changed successfully"}
        )


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for managing users (admin only)"""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            if user.organization:
                return User.objects.filter(organization=user.organization)
            return User.objects.all()
        return User.objects.filter(id=user.id)

    @action(detail=True, methods=["post"])
    def change_role(self, request, pk=None):
        """Change user role (admin only)"""
        if request.user.role != "admin":
            return Response(
                {"error": "Only admins can change roles"},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = self.get_object()
        new_role = request.data.get("role")

        if new_role not in ["admin", "analyst", "viewer"]:
            return Response(
                {"error": "Invalid role"}, status=status.HTTP_400_BAD_REQUEST
            )

        user.role = new_role
        user.save()

        return Response(
            {
                "status": "success",
                "message": f"Role changed to {new_role}",
                "user": UserSerializer(user).data,
            }
        )

    @action(detail=True, methods=["post"])
    def toggle_active(self, request, pk=None):
        """Activate/deactivate user (admin only)"""
        if request.user.role != "admin":
            return Response(
                {"error": "Only admins can manage users"},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = self.get_object()
        user.is_active = not user.is_active
        user.save()

        return Response(
            {
                "status": "success",
                "message": f'User {"activated" if user.is_active else "deactivated"}',
                "user": UserSerializer(user).data,
            }
        )


class OrganizationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing organizations (admin only)"""

    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == "admin":
            return Organization.objects.all()
        return Organization.objects.filter(id=self.request.user.organization_id)

    def perform_create(self, serializer):
        serializer.save()


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def current_user(request):
    """Get current authenticated user"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def check_username(request):
    """Check if username is available"""
    username = request.data.get("username")
    if not username:
        return Response({"error": "Username required"}, status=400)

    exists = User.objects.filter(username=username).exists()
    return Response({"available": not exists})


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def check_email(request):
    """Check if email is available"""
    email = request.data.get("email")
    if not email:
        return Response({"error": "Email required"}, status=400)

    exists = User.objects.filter(email=email).exists()
    return Response({"available": not exists})


class ProfileViewSet(viewsets.ViewSet):
    """Complete profile management"""
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Update profile information"""
        old_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'bio': request.user.bio,
        }
        
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Track changes for audit log
        changes = {}
        for field in old_data:
            new_val = getattr(request.user, field)
            if str(old_data[field] or '') != str(new_val or ''):
                changes[field] = {'old': old_data[field], 'new': new_val}
        
        if changes:
            log_action(
                user=request.user,
                action='UPDATE',
                description=f'Updated profile fields: {", ".join(changes.keys())}',
                obj=request.user,
                changes=changes,
                request=request,
            )
        
        return Response({
            'status': 'success',
            'message': 'Profile updated successfully',
            'user': UserProfileSerializer(request.user).data,
        })
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_avatar(self, request):
        """Upload profile avatar"""
        if 'avatar' not in request.FILES:
            return Response({'error': 'No avatar file provided'}, status=400)
        
        user = request.user
        user.avatar = request.FILES['avatar']
        user.save(update_fields=['avatar'])
        
        log_action(
            user=request.user,
            action='UPDATE',
            description='Updated profile avatar',
            obj=request.user,
            request=request,
        )
        
        return Response({
            'status': 'success',
            'message': 'Avatar uploaded',
            'avatar_url': request.build_absolute_uri(user.avatar.url) if user.avatar else None,
        })
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change password"""
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        data = serializer.validated_data
        
        if not user.check_password(data['old_password']):
            log_action(
                user=user,
                action='PASSWORD_CHANGE_FAILED',
                description='Failed password change attempt - incorrect current password',
                severity='warning',
                request=request,
            )
            return Response({'error': 'Current password is incorrect'}, status=400)
        
        user.set_password(data['new_password'])
        user.save()
        
        log_action(
            user=user,
            action='PASSWORD_CHANGE',
            description='Password changed successfully',
            severity='warning',
            request=request,
        )
        
        return Response({'status': 'success', 'message': 'Password changed successfully'})
    
    # ===== TWO-FACTOR AUTHENTICATION =====
    
    @action(detail=False, methods=['post'])
    def setup_2fa(self, request):
        """Setup 2FA - generates QR code and backup codes"""
        service = TwoFactorService(request.user)
        data = service.setup_2fa()
        
        log_action(
            user=request.user,
            action='2FA_SETUP',
            description='User initiated 2FA setup',
            severity='warning',
            request=request,
        )
        
        return Response({
            'status': 'success',
            'qr_code': data['qr_code'],
            'secret': data['secret'],
            'backup_codes': data['backup_codes'],
            'message': 'Scan QR code with Google Authenticator and verify with token',
        })
    
    @action(detail=False, methods=['post'])
    def verify_2fa(self, request):
        """Verify 2FA token and enable 2FA"""
        serializer = TwoFactorVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service = TwoFactorService(request.user)
        token = serializer.validated_data['token']
        
        if service.verify_token(token):
            service.enable_2fa()
            
            log_action(
                user=request.user,
                action='2FA_ENABLE',
                description='2FA enabled successfully',
                severity='warning',
                request=request,
            )
            
            return Response({
                'status': 'success',
                'message': '2FA enabled successfully',
                'backup_codes': request.user.two_factor_backup_codes,
            })
        
        if service.verify_backup_code(token):
            log_action(
                user=request.user,
                action='2FA_BACKUP_CODE_USED',
                description='Backup code used for verification',
                severity='warning',
                request=request,
            )
            return Response({
                'status': 'success',
                'message': 'Backup code used. 2FA remains enabled.',
            })
        
        log_action(
            user=request.user,
            action='2FA_VERIFY_FAILED',
            description='Failed 2FA verification attempt',
            severity='warning',
            request=request,
        )
        
        return Response({'error': 'Invalid token'}, status=400)
    
    @action(detail=False, methods=['post'])
    def disable_2fa(self, request):
        """Disable 2FA"""
        serializer = TwoFactorDisableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        if not user.check_password(serializer.validated_data['password']):
            return Response({'error': 'Incorrect password'}, status=400)
        
        service = TwoFactorService(user)
        service.disable_2fa()
        
        log_action(
            user=request.user,
            action='2FA_DISABLE',
            description='2FA disabled',
            severity='critical',
            request=request,
        )
        
        return Response({'status': 'success', 'message': '2FA disabled'})
    
    @action(detail=False, methods=['get'])
    def backup_codes(self, request):
        """Get backup codes (only if 2FA is enabled)"""
        if not request.user.two_factor_enabled:
            return Response({'error': '2FA not enabled'}, status=400)
        
        return Response({
            'backup_codes': request.user.two_factor_backup_codes,
            'remaining': len(request.user.two_factor_backup_codes),
        })
    
    @action(detail=False, methods=['post'])
    def regenerate_backup_codes(self, request):
        """Regenerate backup codes"""
        if not request.user.two_factor_enabled:
            return Response({'error': '2FA not enabled'}, status=400)
        
        service = TwoFactorService(request.user)
        codes = service.generate_backup_codes()
        request.user.two_factor_backup_codes = codes
        request.user.save(update_fields=['two_factor_backup_codes'])
        
        log_action(
            user=request.user,
            action='2FA_BACKUP_CODES_REGENERATED',
            description='Backup codes regenerated',
            severity='warning',
            request=request,
        )
        
        return Response({
            'status': 'success',
            'backup_codes': codes,
        })