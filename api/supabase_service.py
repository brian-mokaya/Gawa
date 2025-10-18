"""
Supabase service for authentication and database operations
"""
import os
from supabase import create_client, Client
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from .models import User


class SupabaseService:
    """Service for Supabase operations"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.jwt_secret = os.getenv('SUPABASE_JWT_SECRET', settings.SECRET_KEY)
        
        # Try to initialize Supabase client, but allow graceful failure
        try:
            if self.supabase_url and self.supabase_key:
                self.client: Client = create_client(self.supabase_url, self.supabase_key)
            else:
                self.client = None
        except Exception as e:
            print(f"Warning: Could not initialize Supabase client: {e}")
            self.client = None
    
    def generate_local_jwt(self, user: User) -> dict:
        """Generate JWT tokens for local development mode"""
        # Access token (expires in 1 hour)
        access_payload = {
            'user_id': user.id,
            'email': user.email,
            'name': user.name,
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        access_token = jwt.encode(access_payload, self.jwt_secret, algorithm='HS256')
        
        # Refresh token (expires in 7 days)
        refresh_payload = {
            'user_id': user.id,
            'email': user.email,
            'exp': datetime.utcnow() + timedelta(days=7),
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }
        refresh_token = jwt.encode(refresh_payload, self.jwt_secret, algorithm='HS256')
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }

    def sign_up(self, email: str, password: str, name: str, phone_number: str) -> dict:
        """Sign up a new user"""
        try:
            if not self.client:
                # Create local user for testing
                user, _ = User.objects.get_or_create(
                    email=email,
                    defaults={
                        'id': f'local_{email}',
                        'name': name,
                        'phone_number': phone_number,
                        'credit_score': 600,
                    }
                )
                # Generate JWT tokens
                tokens = self.generate_local_jwt(user)
                return {
                    'success': True,
                    'user': user,
                    'session': None,
                    'access_token': tokens['access_token'],
                    'refresh_token': tokens['refresh_token'],
                    'message': 'User created locally (Supabase not configured)'
                }
            
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
            if not self.client:
                # Allow local login for testing
                try:
                    user = User.objects.get(email=email)
                    # Generate JWT tokens
                    tokens = self.generate_local_jwt(user)
                    return {
                        'success': True,
                        'user': user,
                        'session': None,
                        'access_token': tokens['access_token'],
                        'refresh_token': tokens['refresh_token'],
                        'message': 'Logged in locally (Supabase not configured)'
                    }
                except User.DoesNotExist:
                    return {
                        'success': False,
                        'message': 'User not found. Please register first.'
                    }
            
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
            # Decode the JWT token (works for both local and Supabase tokens)
            decoded = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"]
            )
            # Support both 'user_id' (local) and 'sub' (Supabase) fields
            user_id = decoded.get('user_id') or decoded.get('sub')
            return {
                'valid': True,
                'user_id': user_id,
                'email': decoded.get('email'),
                'decoded': decoded
            }
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
            if self.client:
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
