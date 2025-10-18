"""
Custom authentication for Supabase JWT
"""
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import AnonymousUser
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from .supabase_service import get_supabase_service
from .models import User


class SupabaseJWTAuthentication(BaseAuthentication):
    """Custom authentication using Supabase JWT"""
    
    keyword = 'Bearer'
    
    def authenticate(self, request):
        """Authenticate request using Supabase JWT token"""
        # Get the authorization header
        auth_header = self.get_authorization_header(request)
        
        if not auth_header:
            return None  # No auth header, let other auth methods handle it
        
        try:
            auth = auth_header.split()
        except Exception:
            raise AuthenticationFailed('Invalid authorization header.')
        
        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None  # Not a Bearer token
        
        if len(auth) == 1:
            msg = 'Invalid token header. No credentials provided.'
            raise AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = 'Invalid token header. Token string should not contain spaces.'
            raise AuthenticationFailed(msg)
        
        try:
            token = auth[1].decode()
        except UnicodeDecodeError:
            msg = 'Invalid token header. Token string should not contain invalid characters.'
            raise AuthenticationFailed(msg)
        
        return self.authenticate_credentials(token)
    
    def get_authorization_header(self, request):
        """Get the authorization header from request"""
        auth = request.META.get('HTTP_AUTHORIZATION', b'')
        if isinstance(auth, str):
            auth = auth.encode('iso-8859-1')
        return auth
    
    def authenticate_credentials(self, token):
        """Authenticate JWT token with Supabase"""
        try:
            supabase_service = get_supabase_service()
        except ValueError:
            # Supabase not configured, allow anonymous access for docs
            return (AnonymousUser(), None)
        
        # Verify JWT
        result = supabase_service.verify_jwt(token)
        
        if not result.get('valid'):
            raise AuthenticationFailed('Invalid authentication token.')
        
        user_id = result.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found.')
        
        return (user, token)


class SupabaseJWTAuthenticationExtension(OpenApiAuthenticationExtension):
    """Extension for drf-spectacular to handle Supabase JWT authentication"""
    target_class = 'api.auth.SupabaseJWTAuthentication'
    name = 'Bearer'
    
    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
            'description': 'Supabase JWT token. Get this from /api/auth/login/',
        }


def get_current_user(request) -> User:
    """Get current authenticated user from request"""
    if not request.user or not request.user.is_authenticated:
        return None
    return request.user
