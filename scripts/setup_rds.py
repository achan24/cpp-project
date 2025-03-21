import os
import sys
import boto3
import psycopg2
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Load environment variables
load_dotenv()

def create_db_instance(rds_client, db_instance_identifier, master_username, master_password):
    """Create a new RDS instance"""
    try:
        response = rds_client.create_db_instance(
            DBInstanceIdentifier=db_instance_identifier,
            DBInstanceClass='db.t3.micro',  # t3.micro is available in both regions
            Engine='postgres',
            EngineVersion='11.22',  # Stable version that works with t3.micro
            MasterUsername=master_username,
            MasterUserPassword=master_password,
            AllocatedStorage=5,  # Minimum allowed storage (5GB)
            PubliclyAccessible=True,
            AutoMinorVersionUpgrade=True,
            BackupRetentionPeriod=3,  # 3 days for order history safety
            MultiAZ=False,
            VpcSecurityGroupIds=[],  # We'll add this later
            DBName='botanica',
            Port=5432
        )
        print("✅ RDS instance creation initiated")
        return True
    except ClientError as e:
        print(f"❌ Error creating RDS instance: {e}")
        return False

def wait_for_db_available(rds_client, db_instance_identifier):
    """Wait for the RDS instance to be available"""
    print("Waiting for RDS instance to be available...")
    waiter = rds_client.get_waiter('db_instance_available')
    try:
        waiter.wait(
            DBInstanceIdentifier=db_instance_identifier,
            WaiterConfig={'Delay': 30, 'MaxAttempts': 60}
        )
        print("RDS instance is now available!")
        return True
    except Exception as e:
        print(f"Error waiting for RDS instance: {e}")
        return False

def get_db_endpoint(rds_client, db_instance_identifier):
    """Get the endpoint of the RDS instance"""
    try:
        response = rds_client.describe_db_instances(
            DBInstanceIdentifier=db_instance_identifier
        )
        endpoint = response['DBInstances'][0]['Endpoint']
        return endpoint['Address'], endpoint['Port']
    except ClientError as e:
        print(f"Error getting RDS endpoint: {e}")
        return None, None

def test_connection(host, port, dbname, user, password):
    """Test the connection to the RDS instance"""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        conn.close()
        print("Successfully connected to RDS!")
        return True
    except Exception as e:
        print(f"Error connecting to RDS: {e}")
        return False

def main():
    print("=== Setting up RDS for Botanica ===")
    
    # Initialize AWS RDS client with S3 credentials
    rds_client = boto3.client(
        'rds',
        region_name=os.getenv('AWS_S3_REGION_NAME'),
        aws_access_key_id=os.getenv('AWS_S3_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_S3_SECRET_ACCESS_KEY')
    )
    
    # Get configuration from environment
    DB_INSTANCE_ID = 'botanica-db'
    DB_USERNAME = os.getenv('RDS_USERNAME')
    DB_PASSWORD = os.getenv('RDS_PASSWORD')
    
    # Create RDS instance
    if create_db_instance(rds_client, DB_INSTANCE_ID, DB_USERNAME, DB_PASSWORD):
        print("\n=== RDS Setup Started ===")
        print("The RDS instance creation has been initiated.")
        print("\nThis will take 5-10 minutes to complete.")
        print("\nNext steps:")
        print("1. Wait for the instance to be available")
        print("2. Update .env with the endpoint (will be provided)")
        print("3. Run migration script to transfer data")
        return True
    
    print("\n❌ RDS setup failed")
    return False

if __name__ == '__main__':
    main()
