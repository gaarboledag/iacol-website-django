from rest_framework import authentication, exceptions
from django.db import models
from .models import APIKey


class APIKeyAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication class for API key authentication.
    Expects 'X-API-Key' header with the API key.
    """

    def authenticate(self, request):
        api_key = self.get_api_key(request)

        if not api_key:
            return None  # No authentication attempted

        try:
            hashed = APIKey._hash_key(api_key)
            key_obj = APIKey.objects.select_related('created_by').filter(
                is_active=True
            ).filter(
                models.Q(key=api_key) | models.Q(key=hashed)
            ).first()
            if not key_obj:
                raise APIKey.DoesNotExist
        except APIKey.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid API key')

        # Return (user, auth) tuple
        return (key_obj.created_by, key_obj)

    def get_api_key(self, request):
        """
        Get API key from request headers.
        """
        api_key = request.META.get('HTTP_X_API_KEY')
        if not api_key:
            # Also check for 'Authorization: Bearer <key>' format
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                api_key = auth_header[7:]  # Remove 'Bearer ' prefix

        return api_key

    def authenticate_header(self, request):
        """
        Return the authentication scheme to be used in the WWW-Authenticate header.
        """
        return 'X-API-Key'
