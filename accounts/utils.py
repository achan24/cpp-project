import boto3
import logging
from botocore.exceptions import ClientError
from django.conf import settings

logger = logging.getLogger(__name__)

def verify_email_with_ses(email):
    """
    Verify an email address with Amazon SES.
    
    This function sends a verification email to the specified address
    when a user registers on the site. The user must click the link in
    the verification email to confirm their address before they can
    receive order confirmations.
    
    Args:
        email (str): The email address to verify
        
    Returns:
        bool: True if the verification email was sent successfully, False otherwise
        str: Error message if any
    """
    try:
        # Initialize SES client
        ses = boto3.client(
            'ses',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        
        # Send verification email
        response = ses.verify_email_identity(
            EmailAddress=email
        )
        
        logger.info(f"Verification email sent to {email}")
        return True, None
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        
        if error_code == 'InvalidParameterValue':
            logger.error(f"Invalid email format for {email}: {error_message}")
            return False, "The email address format is invalid."
        elif error_code == 'LimitExceeded':
            logger.error(f"Verification limit exceeded for {email}: {error_message}")
            return False, "Verification limit exceeded. Please try again later."
        elif error_code == 'MessageRejected':
            logger.error(f"Email rejected for {email}: {error_message}")
            return False, "The email address was rejected. Please use a different email."
        elif error_code == 'AccessDenied':
            logger.error(f"Access denied for SES: {error_message}")
            return False, "Access denied to email service. Please contact support."
        else:
            logger.error(f"Error verifying email {email} with SES: {error_code} - {error_message}")
            return False, f"Error: {error_message}"
            
    except Exception as e:
        logger.error(f"Unexpected error verifying email {email}: {e}")
        return False, f"Unexpected error: {str(e)}"
