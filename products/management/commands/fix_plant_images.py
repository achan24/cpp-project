import os
import django
from django.core.management.base import BaseCommand
from products.models import Plant

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'botanica.settings')
django.setup()

class Command(BaseCommand):
    help = 'Fix broken plant images for specific plants'

    def handle(self, *args, **options):
        # Plants with broken images
        plants_to_fix = [
            'African Violet',
            'Anthurium',
            'Juniper Bonsai',
            'Monstera Deliciosa'
        ]
        
        # Get the populate_plants command to use its download_image method
        from products.management.commands.populate_plants import Command as PopulateCommand
        populate_cmd = PopulateCommand()
        
        fixed_count = 0
        
        for plant_name in plants_to_fix:
            try:
                # Find the plant in the database
                plant = Plant.objects.get(name=plant_name)
                
                # Remove the old image if it exists
                if plant.image:
                    old_path = plant.image.path
                    if os.path.exists(old_path):
                        os.remove(old_path)
                        self.stdout.write(f"Removed old image for {plant_name}")
                
                # Download a new image
                self.stdout.write(f"Downloading new image for {plant_name}...")
                img_temp, filename = populate_cmd.download_image(plant_name)
                
                if img_temp and filename:
                    # Save the new image
                    plant.image.save(filename, img_temp)
                    plant.save()
                    self.stdout.write(self.style.SUCCESS(f"Fixed image for {plant_name}"))
                    fixed_count += 1
                else:
                    self.stdout.write(self.style.ERROR(f"Failed to download image for {plant_name}"))
            
            except Plant.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Plant not found: {plant_name}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error fixing image for {plant_name}: {str(e)}"))
        
        self.stdout.write(self.style.SUCCESS(f"Fixed {fixed_count} out of {len(plants_to_fix)} plant images"))

if __name__ == '__main__':
    cmd = Command()
    cmd.handle()
