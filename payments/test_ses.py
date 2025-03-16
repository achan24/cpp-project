import boto3
import sys
import os
from django.conf import settings
from botocore.exceptions import ClientError, NoCredentialsError
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'botanica.settings')
django.setup()

def test_ses_connection():
    """
    Test the AWS SES connection and credentials.
    This function will check if the AWS credentials are valid and if SES is accessible.
    """
    print("Testing AWS SES Connection...")
    print(f"AWS Region: {settings.AWS_REGION}")
    print(f"AWS Access Key ID: {settings.AWS_ACCESS_KEY_ID[:4]}...{settings.AWS_ACCESS_KEY_ID[-4:]}")
    print(f"SES Sender Email: {settings.AWS_SES_SENDER_EMAIL}")
    
    try:
        # Initialize SES client
        ses = boto3.client(
            'ses',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        
        # Test connection by listing verified email addresses
        response = ses.list_verified_email_addresses()
        
        print("\n✅ Successfully connected to AWS SES!")
        print("\nVerified Email Addresses:")
        if not response.get('VerifiedEmailAddresses'):
            print("  - No verified email addresses found")
        else:
            for email in response.get('VerifiedEmailAddresses', []):
                print(f"  - {email}")
        
        # Check if sender email is verified
        if settings.AWS_SES_SENDER_EMAIL in response.get('VerifiedEmailAddresses', []):
            print(f"\n✅ Sender email {settings.AWS_SES_SENDER_EMAIL} is verified!")
        else:
            print(f"\n❌ Sender email {settings.AWS_SES_SENDER_EMAIL} is NOT verified!")
            print("   You need to verify this email before you can send from it.")
            
        # Get sending limits
        account_info = ses.get_send_quota()
        print("\nSES Account Limits:")
        print(f"  - Max 24 Hour Send: {account_info['Max24HourSend']}")
        print(f"  - Max Send Rate: {account_info['MaxSendRate']} emails/second")
        print(f"  - Sent Last 24 Hours: {account_info['SentLast24Hours']}")
        
        # Check if in sandbox mode
        account_status = ses.get_account_sending_enabled()
        if account_status.get('Enabled', False):
            print("\n✅ Your SES account is in production mode!")
        else:
            print("\n⚠️ Your SES account is in SANDBOX mode!")
            print("   In sandbox mode, you can only send to verified email addresses.")
            print("   To move out of sandbox mode, submit a request to AWS Support.")
        
        return True
        
    except NoCredentialsError:
        print("\n❌ AWS credentials not found or invalid!")
        print("   Please check your AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in your .env file.")
        return False
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        
        print(f"\n❌ AWS SES Error: {error_code}")
        print(f"   {error_message}")
        
        if error_code == 'AccessDenied':
            print("\n   Possible causes:")
            print("   - Your IAM user doesn't have SES permissions")
            print("   - Your AWS credentials are incorrect")
        elif error_code == 'InvalidClientTokenId':
            print("\n   Your AWS Access Key ID is invalid or doesn't exist.")
        
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    test_ses_connection()
