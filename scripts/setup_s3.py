import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AWS credentials from environment (using S3-specific credentials)
AWS_ACCESS_KEY_ID = os.environ.get('AWS_S3_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_S3_SECRET_ACCESS_KEY')
AWS_REGION = os.environ.get('AWS_S3_REGION_NAME', 'eu-west-1')  # Ireland region

# Bucket configuration
BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'botanica-media')
ALLOWED_ORIGINS = ['http://localhost:8000']  # Add your domains here

def create_bucket(s3_client, bucket_name, region):
    """Create an S3 bucket in a specified region"""
    try:
        location = {'LocationConstraint': region}
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration=location
        )
        print(f"Created bucket {bucket_name} in {region}")
        return True
    except ClientError as e:
        print(f"Error creating bucket: {e}")
        return False

def set_bucket_cors(s3_client, bucket_name):
    """Set CORS configuration for the bucket"""
    cors_configuration = {
        'CORSRules': [{
            'AllowedHeaders': ['*'],
            'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE'],
            'AllowedOrigins': ALLOWED_ORIGINS,
            'ExposeHeaders': ['ETag'],
            'MaxAgeSeconds': 3000
        }]
    }
    try:
        s3_client.put_bucket_cors(
            Bucket=bucket_name,
            CORSConfiguration=cors_configuration
        )
        print(f"Set CORS configuration for {bucket_name}")
        return True
    except ClientError as e:
        print(f"Error setting CORS: {e}")
        return False

def set_bucket_policy(s3_client, bucket_name):
    """Set public read access for the bucket"""
    bucket_policy = {
        'Version': '2012-10-17',
        'Statement': [{
            'Sid': 'PublicReadGetObject',
            'Effect': 'Allow',
            'Principal': '*',
            'Action': ['s3:GetObject'],
            'Resource': [f'arn:aws:s3:::{bucket_name}/*']
        }]
    }
    try:
        s3_client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=str(bucket_policy).replace("'", '"')
        )
        print(f"Set public read policy for {bucket_name}")
        return True
    except ClientError as e:
        print(f"Error setting bucket policy: {e}")
        return False

def enable_bucket_versioning(s3_client, bucket_name):
    """Enable versioning for the bucket"""
    try:
        s3_client.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        print(f"Enabled versioning for {bucket_name}")
        return True
    except ClientError as e:
        print(f"Error enabling versioning: {e}")
        return False

def main():
    # Initialize S3 client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )

    # Create bucket with unique name
    bucket_name = f"{BUCKET_NAME}-{AWS_REGION}"
    if create_bucket(s3_client, bucket_name, AWS_REGION):
        # Configure bucket
        set_bucket_cors(s3_client, bucket_name)
        set_bucket_policy(s3_client, bucket_name)
        enable_bucket_versioning(s3_client, bucket_name)
        
        # Print success message with bucket details
        print("\nS3 Bucket Setup Complete!")
        print(f"Bucket Name: {bucket_name}")
        print(f"Bucket Region: {AWS_REGION}")
        print(f"Bucket URL: https://{bucket_name}.s3.{AWS_REGION}.amazonaws.com/")
        
        # Update settings instructions
        print("\nNext Steps:")
        print("1. Add these settings to your .env file:")
        print(f"AWS_STORAGE_BUCKET_NAME={bucket_name}")
        print("2. Add django-storages to requirements.txt")
        print("3. Update INSTALLED_APPS in settings.py to include 'storages'")
    else:
        print("Failed to create bucket. Check your AWS credentials and permissions.")

if __name__ == '__main__':
    main()
