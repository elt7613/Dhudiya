from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import logging

logger = logging.getLogger('django')

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if response is None:
        logger.error(f"Unexpected error: {str(exc)}")
        return Response({
            'error': 'An unexpected error occurred',
            'detail': str(exc) if settings.DEBUG else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response 