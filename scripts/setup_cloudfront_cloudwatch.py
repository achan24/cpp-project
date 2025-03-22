import boto3
import json
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_aws_client(service):
    """
    Get AWS client with proper credentials
    """
    return boto3.client(
        service,
        aws_access_key_id=os.getenv('AWS_S3_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_S3_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_S3_REGION_NAME')
    )

def create_cloudfront_distribution():
    """
    Create a CloudFront distribution for the S3 bucket
    Returns the distribution ID and domain name
    """
    cloudfront = get_aws_client('cloudfront')
    
    # Distribution configuration
    distribution_config = {
        'CallerReference': f'botanica-media-{int(time.time())}',
        'Comment': 'Botanica media distribution',
        'Enabled': True,
        'DefaultRootObject': 'index.html',
        'Origins': {
            'Quantity': 1,
            'Items': [{
                'Id': 'S3-botanica-media',
                'DomainName': 'botanica-media-eu-west-1.s3.eu-west-1.amazonaws.com',
                'S3OriginConfig': {
                    'OriginAccessIdentity': ''
                }
            }]
        },
        'DefaultCacheBehavior': {
            'TargetOriginId': 'S3-botanica-media',
            'ViewerProtocolPolicy': 'redirect-to-https',
            'AllowedMethods': {
                'Quantity': 2,
                'Items': ['GET', 'HEAD'],
                'CachedMethods': {
                    'Quantity': 2,
                    'Items': ['GET', 'HEAD']
                }
            },
            'ForwardedValues': {
                'QueryString': False,
                'Cookies': {'Forward': 'none'}
            },
            'MinTTL': 0,
            'DefaultTTL': 86400,    # 24 hours
            'MaxTTL': 31536000      # 1 year
        }
    }
    
    try:
        print("Creating CloudFront distribution...")
        response = cloudfront.create_distribution(
            DistributionConfig=distribution_config
        )
        
        distribution_id = response['Distribution']['Id']
        domain_name = response['Distribution']['DomainName']
        
        print(f" Distribution created successfully!")
        print(f"Distribution ID: {distribution_id}")
        print(f"Domain Name: {domain_name}")
        
        # Save distribution info to .env file
        with open('.env', 'a') as f:
            f.write(f"\n# CloudFront Settings\n")
            f.write(f"CLOUDFRONT_DISTRIBUTION_ID={distribution_id}\n")
            f.write(f"CLOUDFRONT_DOMAIN={domain_name}\n")
        
        return distribution_id, domain_name
        
    except ClientError as e:
        print(f" Error creating distribution: {e}")
        return None, None

def create_cloudwatch_alarms(distribution_id):
    """
    Create CloudWatch alarms for monitoring
    """
    cloudwatch = get_aws_client('cloudwatch')
    
    try:
        print("\nSetting up CloudWatch alarms...")
        
        # 1. RDS CPU Usage Alarm
        cloudwatch.put_metric_alarm(
            AlarmName='Botanica-RDS-CPUUtilization',
            MetricName='CPUUtilization',
            Namespace='AWS/RDS',
            Dimensions=[
                {'Name': 'DBInstanceIdentifier', 'Value': 'botanica-db'}
            ],
            Period=300,  # 5 minutes
            EvaluationPeriods=1,
            Threshold=80.0,  # 80% CPU usage
            ComparisonOperator='GreaterThanThreshold',
            Statistic='Average',
            AlarmDescription='RDS CPU usage exceeds 80%'
        )
        print(" RDS CPU Usage alarm created")
        
        # 2. CloudFront 5xx Error Rate Alarm
        cloudwatch.put_metric_alarm(
            AlarmName='Botanica-CloudFront-5xxErrors',
            MetricName='5xxErrorRate',
            Namespace='AWS/CloudFront',
            Dimensions=[
                {'Name': 'DistributionId', 'Value': distribution_id},
                {'Name': 'Region', 'Value': 'Global'}
            ],
            Period=300,  # 5 minutes
            EvaluationPeriods=1,
            Threshold=5.0,  # 5% error rate
            ComparisonOperator='GreaterThanThreshold',
            Statistic='Average',
            AlarmDescription='CloudFront 5xx error rate exceeds 5%'
        )
        print(" CloudFront 5xx Error Rate alarm created")
        
        # 3. Daily Active Users Alarm
        cloudwatch.put_metric_alarm(
            AlarmName='Botanica-DailyActiveUsers',
            MetricName='UniqueVisitors',
            Namespace='Botanica/UserMetrics',
            Period=86400,  # 24 hours
            EvaluationPeriods=1,
            Threshold=10.0,  # Alert if less than 10 daily users
            ComparisonOperator='LessThanThreshold',
            Statistic='Sum',
            AlarmDescription='Daily active users below threshold'
        )
        print(" Daily Active Users alarm created")
        
        print("\n All CloudWatch alarms created successfully!")
        
    except ClientError as e:
        print(f" Error creating CloudWatch alarms: {e}")

if __name__ == '__main__':
    import time
    
    print("Setting up CloudFront CDN for Botanica...")
    distribution_id, domain_name = create_cloudfront_distribution()
    
    if distribution_id:
        create_cloudwatch_alarms(distribution_id)
        print("\n Setup complete! Your CDN is being deployed.")
        print("Note: It may take 15-20 minutes for the distribution to be fully deployed.")
