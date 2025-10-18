"""
Custom authentication for Supabase JWT
"""
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .supabase_service import get_supabase_service
from .models import User


class SupabaseJWTAuthentication(TokenAuthentication):
    """Custom authentication using Supabase JWT"""
    
    keyword = 'Bearer'
    
    def authenticate(self, request):
        auth = self.get_authorization_header(request).split()
        
        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None
        
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
    
    def authenticate_credentials(self, key):
        """Authenticate JWT token with Supabase"""
        supabase_service = get_supabase_service()
        
        # Verify JWT
        result = supabase_service.verify_jwt(key)
        
        if not result.get('valid'):
            raise AuthenticationFailed('Invalid authentication token.')
        
        user_id = result.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found.')
        
        return (user, key)


def get_current_user(request) -> User:
    """Get current authenticated user from request"""
    if not request.user or not request.user.is_authenticated:
        return None
    return request.user
