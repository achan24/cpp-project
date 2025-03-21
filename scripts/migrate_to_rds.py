import os
import sys
import django
import psycopg2
from django.core.management import call_command
from django.db import connections

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'botanica.settings')
django.setup()

def backup_sqlite():
    """Create a backup of the SQLite database"""
    from django.conf import settings
    import shutil
    from datetime import datetime
    
    sqlite_path = str(settings.BASE_DIR / 'db.sqlite3')  # Get the full path to SQLite file
    backup_path = f"{sqlite_path}.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    print(f"\n=== Backing up SQLite database ===")
    print(f"Source: {sqlite_path}")
    print(f"Backup: {backup_path}")
    
    shutil.copy2(sqlite_path, backup_path)
    print("✓ Backup completed")
    return backup_path

def test_postgres_connection():
    """Test connection to PostgreSQL"""
    print("\n=== Testing PostgreSQL connection ===")
    try:
        # Use connection details directly
        from django.db import connections
        connections.databases['default'] = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'botanica',
            'USER': 'botanica_admin',
            'PASSWORD': 'BotanicaDB2025!Secure',
            'HOST': 'botanica-db.clc0i260czqp.eu-west-1.rds.amazonaws.com',
            'PORT': '5432',
        }
        
        print(f"Attempting to connect with:")
        print(f"Host: {connections.databases['default']['HOST']}")
        print(f"Port: {connections.databases['default']['PORT']}")
        print(f"Database: {connections.databases['default']['NAME']}")
        print(f"User: {connections.databases['default']['USER']}")
        
        connection = connections['default']
        connection.ensure_connection()
        print("✓ Successfully connected to PostgreSQL")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def migrate_database():
    """Run Django migrations on PostgreSQL"""
    print("\n=== Running migrations ===")
    try:
        call_command('migrate', verbosity=1)
        print("✓ Migrations completed")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def migrate_data():
    """Migrate data from SQLite to PostgreSQL"""
    from products.models import Plant
    from django.contrib.auth.models import User
    
    print("\n=== Migrating Data ===")
    
    # Migrate plants
    print("\nMigrating plants...")
    plants = Plant.objects.all()
    total_plants = plants.count()
    print(f"Found {total_plants} plants to migrate")
    
    for i, plant in enumerate(plants, 1):
        print(f"[{i}/{total_plants}] Migrating {plant.name}...")
        try:
            plant.save()
            print(f"✓ Successfully migrated {plant.name}")
        except Exception as e:
            print(f"❌ Failed to migrate {plant.name}: {e}")
    
    # Migrate users (if any)
    print("\nMigrating users...")
    users = User.objects.all()
    total_users = users.count()
    print(f"Found {total_users} users to migrate")
    
    for i, user in enumerate(users, 1):
        print(f"[{i}/{total_users}] Migrating {user.username}...")
        try:
            user.save()
            print(f"✓ Successfully migrated {user.username}")
        except Exception as e:
            print(f"❌ Failed to migrate {user.username}: {e}")

def verify_migration():
    """Verify that all data was migrated correctly"""
    from products.models import Plant
    from django.contrib.auth.models import User
    
    print("\n=== Verifying Migration ===")
    
    # Verify plants
    plant_count = Plant.objects.count()
    print(f"Plants in database: {plant_count}")
    
    # Verify users
    user_count = User.objects.count()
    print(f"Users in database: {user_count}")
    
    # Verify a sample plant's data
    if plant_count > 0:
        sample_plant = Plant.objects.first()
        print(f"\nSample plant verification:")
        print(f"Name: {sample_plant.name}")
        print(f"Price: ${sample_plant.price}")
        print(f"Image: {sample_plant.image.url if sample_plant.image else 'No image'}")

def main():
    print("=== Starting RDS Migration ===")
    
    # Force reload environment variables
    from dotenv import load_dotenv
    load_dotenv(override=True)  # Add override=True to force reload
    
    # Backup SQLite database
    backup_path = backup_sqlite()
    
    # Test PostgreSQL connection
    if not test_postgres_connection():
        print("\n❌ Migration aborted: Could not connect to PostgreSQL")
        return False
    
    # Run migrations
    if not migrate_database():
        print("\n❌ Migration aborted: Could not run migrations")
        return False
    
    # Migrate data
    migrate_data()
    
    # Verify migration
    verify_migration()
    
    print("\n=== Migration Complete ===")
    print(f"SQLite backup: {backup_path}")
    print("\nNext steps:")
    print("1. Verify the application works with PostgreSQL")
    print("2. Update settings.py to remove SQLite configuration")
    print("3. Deploy updated configuration to EC2")
    
    return True

if __name__ == '__main__':
    main()
