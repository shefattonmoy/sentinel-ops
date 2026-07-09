from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from .models import log_action

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    log_action(
        user=user,
        action='LOGIN',
        description=f'User {user.username} logged in successfully',
        severity='info',
        request=request,
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        log_action(
            user=user,
            action='LOGOUT',
            description=f'User {user.username} logged out',
            severity='info',
            request=request,
        )

@receiver(user_login_failed)
def log_login_failed(sender, credentials, request, **kwargs):
    username = credentials.get('username', 'unknown')
    log_action(
        user=None,
        action='LOGIN_FAILED',
        description=f'Failed login attempt for username: {username}',
        severity='warning',
        request=request,
        metadata={'username': username},
    )