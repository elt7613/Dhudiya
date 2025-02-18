import logging
import time
import uuid
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('django')

class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware to log all requests and responses."""

    def process_request(self, request):
        """Process the request before it reaches the view."""
        # Generate unique request ID
        request.id = str(uuid.uuid4())
        request.start_time = time.time()

        # Log the request
        logger.info(
            f"Request {request.id}: {request.method} {request.path} "
            f"from {request.META.get('REMOTE_ADDR')}"
        )

    def process_response(self, request, response):
        """Process the response after the view is called."""
        # Calculate request duration
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log the response
            logger.info(
                f"Response {getattr(request, 'id', 'unknown')}: "
                f"Status {response.status_code} "
                f"Duration {duration:.2f}s"
            )

        return response

class SecurityMiddleware(MiddlewareMixin):
    """Middleware to add security headers."""

    def process_response(self, request, response):
        """Add security headers to response."""
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=()'
        
        return response

class MaintenanceModeMiddleware(MiddlewareMixin):
    """Middleware to handle maintenance mode."""
    
    def process_request(self, request):
        """Check if site is in maintenance mode."""
        from django.conf import settings
        from django.http import HttpResponse
        
        if getattr(settings, 'MAINTENANCE_MODE', False):
            if not request.path.startswith('/admin'):  # Allow admin access
                return HttpResponse(
                    'Site is under maintenance. Please try again later.',
                    status=503
                ) 