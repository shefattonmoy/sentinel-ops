# apps/accounts/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'organizations', views.OrganizationViewSet, basename='organization')

app_name = 'accounts'

urlpatterns = [
    # Authentication endpoints
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Registration
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    
    # Profile endpoints - USE ProfileViewSet ONLY (remove duplicate UserProfileView)
    path('profile/', views.ProfileViewSet.as_view({'get': 'me'}), name='profile'),
    path('profile/update/', views.ProfileViewSet.as_view({'put': 'update_profile', 'patch': 'update_profile'}), name='profile-update'),
    path('profile/avatar/', views.ProfileViewSet.as_view({'post': 'upload_avatar'}), name='profile-avatar'),
    path('profile/change-password/', views.ProfileViewSet.as_view({'post': 'change_password'}), name='change-password'),
    
    # 2FA endpoints
    path('profile/2fa/setup/', views.ProfileViewSet.as_view({'post': 'setup_2fa'}), name='2fa-setup'),
    path('profile/2fa/verify/', views.ProfileViewSet.as_view({'post': 'verify_2fa'}), name='2fa-verify'),
    path('profile/2fa/disable/', views.ProfileViewSet.as_view({'post': 'disable_2fa'}), name='2fa-disable'),
    path('profile/2fa/backup-codes/', views.ProfileViewSet.as_view({'get': 'backup_codes'}), name='2fa-backup-codes'),
    path('profile/2fa/regenerate-codes/', views.ProfileViewSet.as_view({'post': 'regenerate_backup_codes'}), name='2fa-regenerate-codes'),
    
    # Validation endpoints
    path('check-username/', views.check_username, name='check_username'),
    path('check-email/', views.check_email, name='check_email'),
    
    # Router endpoints (users, organizations)
    path('', include(router.urls)),
]