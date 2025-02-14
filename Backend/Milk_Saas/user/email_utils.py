from django.core.mail import send_mail
from django.conf import settings
import logging
from smtplib import SMTPException

logger = logging.getLogger('django')

def send_reset_password_email(user_email, otp):
    """Send reset password OTP email"""
    try:
        subject = 'Reset Your Password'
        message = f'''
Hello!

You have requested to reset your password. Your OTP is:

{otp}

This OTP is valid for 10 minutes. If you didn't request this, please ignore this email.

Best regards,
Your App Team
'''
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [user_email]
        
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
        )
        return True
    except SMTPException as e:
        logger.error(f"SMTP Error sending reset password email: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending reset password email: {str(e)}")
        return False 