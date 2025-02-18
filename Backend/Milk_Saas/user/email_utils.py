from django.core.mail import send_mail
from django.conf import settings
import logging
from time import sleep

logger = logging.getLogger('user')

def send_reset_password_email(email, otp):
    """Send reset password email with OTP"""
    max_retries = 3
    retry_delay = 1  # seconds
    
    subject = 'Reset Your Password - Milk Saas'
    message = f'''Hello,

You have requested to reset your password. Here is your OTP:

{otp}

This OTP will expire in 10 minutes.
Please DO NOT share this OTP with anyone.

If you did not request this password reset, please ignore this email.

Best regards,
Milk Saas Team'''

    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]

    for attempt in range(max_retries):
        try:
            # Validate email configuration
            if not all([settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD, 
                       settings.EMAIL_HOST, settings.EMAIL_PORT]):
                logger.error("Email configuration is incomplete")
                return False

            # Send email
            send_mail(
                subject,
                message,
                from_email,
                recipient_list,
                fail_silently=False
            )
            
            logger.info(f"Reset password email sent successfully to {email} on attempt {attempt + 1}")
            return True
            
        except Exception as e:
            logger.error(f"Attempt {attempt + 1}/{max_retries} failed to send reset password email to {email}. Error: {str(e)}")
            
            if attempt < max_retries - 1:
                sleep(retry_delay)
                continue
            else:
                logger.error(f"All {max_retries} attempts to send reset password email failed")
                return False

    return False 