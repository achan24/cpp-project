import psycopg2
from psycopg2 import OperationalError
import socket

# Connection parameters
params = {
    'dbname': 'botanica',
    'user': 'botanica_admin',
    'password': 'BotanicaDB2025!Secure',
    'host': 'botanica-db.clc0i260czqp.eu-west-1.rds.amazonaws.com',
    'port': '5432',
    'connect_timeout': 15  # 15 seconds timeout
}

print("Trying to connect to PostgreSQL...")
print(f"Resolving hostname {params['host']}...")
try:
    # Try to resolve the hostname first
    ip_info = socket.gethostbyname_ex(params['host'])
    print(f"Resolved IPs: {ip_info[2]}")
    
    print("\nAttempting database connection (15s timeout)...")
    conn = psycopg2.connect(**params)
    print("✓ Successfully connected to PostgreSQL!")
    
    # Test query
    cur = conn.cursor()
    cur.execute('SELECT version();')
    version = cur.fetchone()
    print(f"\nPostgreSQL version: {version[0]}")
    
    cur.close()
    conn.close()
except socket.gaierror as e:
    print(f"❌ DNS resolution failed: {e}")
except OperationalError as e:
    print(f"❌ Connection failed: {e}")
    print("\nMake sure:")
    print("1. Security group allows access from 80.233.59.27/32 on port 5432")
    print("2. RDS instance is available and public access is enabled")
    print("3. Database name and credentials are correct")
