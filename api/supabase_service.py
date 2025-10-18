"""
Supabase service for authentication and database operations
"""
import os
from supabase import create_client, Client
import jwt
from django.conf import settings
from .models import User


class SupabaseService:
    """Service for Supabase operations"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.jwt_secret = os.getenv('SUPABASE_JWT_SECRET', '')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)

    def sign_up(self, email: str, password: str, name: str, phone_number: str) -> dict:
        """Sign up a new user"""
        try:
            # Create auth user in Supabase
            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
            })
            
            if response.user:
                # Create user record in our database
                user, _ = User.objects.get_or_create(
                    id=response.user.id,
                    defaults={
                        'name': name,
                        'email': email,
                        'phone_number': phone_number,
                        'credit_score': 600,
                    }
                )
                return {
                    'success': True,
                    'user': user,
                    'session': response.session
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to create user'
                }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }

    def sign_in(self, email: str, password: str) -> dict:
        """Sign in a user"""
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password,
            })
            
            if response.session:
                # Get or create user record
                user, _ = User.objects.get_or_create(
                    id=response.user.id,
                    defaults={
                        'name': response.user.user_metadata.get('name', email),
                        'email': email,
                        'phone_number': response.user.user_metadata.get('phone_number', ''),
                    }
                )
                return {
                    'success': True,
                    'user': user,
                    'session': response.session,
                    'access_token': response.session.access_token,
                    'refresh_token': response.session.refresh_token
                }
            else:
                return {
                    'success': False,
                    'message': 'Invalid credentials'
                }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }

    def verify_jwt(self, token: str) -> dict:
        """Verify JWT token from Supabase"""
        try:
            # Decode the JWT token
            if self.jwt_secret:
                decoded = jwt.decode(
                    token,
                    self.jwt_secret,
                    algorithms=["HS256"]
                )
                return {
                    'valid': True,
                    'user_id': decoded.get('sub'),
                    'email': decoded.get('email'),
                    'decoded': decoded
                }
            else:
                # Fallback: try to verify with Supabase
                user = self.client.auth.get_user(token)
                if user:
                    return {
                        'valid': True,
                        'user_id': user.id,
                        'email': user.email,
                    }
                return {'valid': False}
        except Exception as e:
            return {
                'valid': False,
                'message': str(e)
            }

    def get_user_by_phone(self, phone_number: str) -> User:
        """Get user by phone number"""
        try:
            return User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            return None

    def update_user_profile(self, user_id: str, data: dict) -> dict:
        """Update user profile"""
        try:
            user = User.objects.get(id=user_id)
            
            if 'name' in data:
                user.name = data['name']
            if 'phone_number' in data:
                user.phone_number = data['phone_number']
            
            user.save()
            return {'success': True, 'user': user}
        except User.DoesNotExist:
            return {'success': False, 'message': 'User not found'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def sign_out(self, token: str) -> dict:
        """Sign out a user"""
        try:
            self.client.auth.sign_out()
            return {'success': True, 'message': 'Signed out successfully'}
        except Exception as e:
            return {'success': False, 'message': str(e)}


# Singleton instance
_supabase_service = None


def get_supabase_service() -> SupabaseService:
    """Get Supabase service singleton"""
    global _supabase_service
    if _supabase_service is None:
        _supabase_service = SupabaseService()
    return _supabase_service
