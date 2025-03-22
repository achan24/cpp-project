import os
import sys
import django
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files import File
from django.core.management import call_command
from django.contrib.staticfiles.storage import staticfiles_storage

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'botanica.settings')
django.setup()

from products.models import Plant

# First-time S3 migration guide:
"""
1. First ensure your .env has the correct AWS credentials and bucket settings:
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_STORAGE_BUCKET_NAME=botanica-media-eu-west-1
   AWS_S3_REGION_NAME=eu-west-1

2. Run the complete migration in this order:
   
   # Download category images from Unsplash
   curl -L "image_url" -o static/images/categories/indoor.jpg
   curl -L "image_url" -o static/images/categories/outdoor.jpg
   ... (repeat for all category images)

   # Run the migration script with all functions
   if __name__ == '__main__':
       main()  # This will run:
       # - migrate_media_to_s3() for product images
       # - migrate_static_to_s3() for static files
       # - migrate_category_images() for category images

   # After migration, update templates to use S3 URLs:
   # Old: <img src="/static/images/categories/indoor.jpg">
   # New: <img src="https://botanica-media-eu-west-1.s3.eu-west-1.amazonaws.com/categories/indoor.jpg">

3. Verify all images are accessible through S3 URLs
4. Update settings.py to use S3 as default storage
5. Remove local media files (optional, keep as backup)
"""

def migrate_media_to_s3():
    """Migrate existing plant images from local storage to S3"""
    media_root = settings.MEDIA_ROOT
    plants = Plant.objects.exclude(image='')
    total = plants.count()
    
    print("\n=== Migrating Media Files ===")
    print(f"Found {total} plants with images to migrate")
    
    for i, plant in enumerate(plants, 1):
        # Get the full local path including media directory
        local_path = os.path.join(project_root, 'media', plant.image.name)
        if os.path.exists(local_path):
            print(f"[{i}/{total}] Migrating {plant.image.name}...")
            
            # Open local file and upload to S3
            with open(local_path, 'rb') as f:
                file_content = File(f)
                # Save will automatically use S3 storage due to our settings
                plant.image.save(plant.image.name, file_content, save=True)
            
            print(f"✓ Successfully migrated {plant.image.name}")
        else:
            print(f"✗ Local file not found: {local_path}")

def migrate_static_to_s3():
    """Upload static files to S3 manually"""
    print("\n=== Migrating Static Files ===")
    static_root = settings.STATIC_ROOT
    static_dir = os.path.join(project_root, 'static')
    
    def upload_static_dir(directory):
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.startswith('.'):  # Skip hidden files
                    continue
                    
                local_path = os.path.join(root, file)
                relative_path = os.path.relpath(local_path, static_dir)
                
                print(f"Uploading {relative_path}...")
                with open(local_path, 'rb') as f:
                    file_content = File(f)
                    # Use staticfiles_storage to maintain proper static file paths
                    staticfiles_storage.save(relative_path, file_content)
                print(f"✓ Successfully uploaded {relative_path}")
    
    print("Uploading static files to S3...")
    upload_static_dir(static_dir)

def migrate_category_images():
    """Upload category images to S3"""
    print("\n=== Migrating Category Images ===")
    categories_dir = os.path.join(project_root, 'static', 'images', 'categories')
    
    for file in os.listdir(categories_dir):
        if file.startswith('.'):  # Skip hidden files
            continue
            
        local_path = os.path.join(categories_dir, file)
        s3_path = f'images/categories/{file}'  # Fixed path to match S3 structure
        
        print(f"Uploading {file}...")
        with open(local_path, 'rb') as f:
            default_storage.save(s3_path, File(f))
        print(f"✓ Successfully uploaded {file}")

def main():
    print("Starting migration to S3...")
    
    # First migrate media files
    migrate_media_to_s3()
    
    # Then migrate static files
    migrate_static_to_s3()
    
    print("\n=== Migration Complete ===")
    print("✓ Media files migrated to S3")
    print("✓ Static files migrated to S3")
    print(f"\nS3 Bucket: {settings.AWS_STORAGE_BUCKET_NAME}")
    print(f"Media URL: {settings.MEDIA_URL}")
    print(f"Static URL: {settings.STATIC_URL}")

if __name__ == '__main__':
    migrate_category_images()
