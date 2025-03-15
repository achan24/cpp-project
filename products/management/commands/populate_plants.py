import os
import random
import requests
import tempfile
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File
from products.models import Category, Plant
from decimal import Decimal
from urllib.parse import urlparse
from io import BytesIO
import re
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont

class Command(BaseCommand):
    help = 'Populates the database with sample plant data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of plants even if they already exist',
        )

    def download_image(self, plant_name):
        """Download an image for a plant using multiple search methods"""
        image_sources = [
            self._try_bing_search,
            self._try_duckduckgo_search,
            self._try_simple_search,
        ]
        
        # Try each image source until we get a valid image
        for source_method in image_sources:
            try:
                img_temp, filename = source_method(plant_name)
                if img_temp and filename and self._is_valid_image(img_temp, filename):
                    return img_temp, filename
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Error with {source_method.__name__} for {plant_name}: {str(e)}"))
        
        # If all methods fail, create a placeholder
        self.stdout.write(self.style.WARNING(f"No valid images found for {plant_name}, using default placeholder"))
        return self._create_placeholder_image(plant_name)
    
    def _is_valid_image(self, img_temp, filename):
        """Verify that the downloaded content is a valid image"""
        try:
            # Store current position
            current_pos = img_temp.tell()
            
            # Check file size - reject if too small
            img_temp.seek(0, 2)  # Go to end
            size = img_temp.tell()
            if size < 5000:  # Less than 5KB is suspicious
                self.stdout.write(self.style.WARNING(f"Image too small ({size} bytes), likely invalid"))
                img_temp.seek(current_pos)  # Restore position
                return False
            
            # Try to open as an image
            img_temp.seek(0)  # Go back to start
            Image.open(img_temp)
            
            # Restore position and return success
            img_temp.seek(current_pos)
            return True
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Invalid image: {str(e)}"))
            return False
    
    def _try_bing_search(self, plant_name):
        """Try to download an image using Bing search"""
        # Construct search query
        search_query = f"{plant_name} plant"
        search_url = f"https://www.bing.com/images/search?q={search_query.replace(' ', '+')}&form=HDRSC2&first=1"
        
        # Set headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make the request
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find image URLs in the page
            image_urls = []
            
            # Look for image metadata in the page
            for img_element in soup.select('a.iusc'):
                m_attr = img_element.get('m')
                if m_attr:
                    try:
                        # The m attribute contains JSON with the image URL
                        import json
                        metadata = json.loads(m_attr)
                        if 'murl' in metadata:
                            image_urls.append(metadata['murl'])
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"Error parsing image metadata: {str(e)}"))
            
            # If we found image URLs, try downloading them until we get a valid one
            for img_url in image_urls[:5]:  # Try up to 5 images
                try:
                    self.stdout.write(f"Trying image URL from Bing: {img_url}")
                    
                    # Download the image
                    img_response = requests.get(img_url, stream=True, timeout=10)
                    if img_response.status_code == 200:
                        # Create a temporary file
                        img_temp = BytesIO()
                        img_temp.write(img_response.content)
                        img_temp.seek(0)
                        
                        # Get a filename from the URL or create one
                        parsed_url = urlparse(img_url)
                        filename = os.path.basename(parsed_url.path)
                        if not filename or '.' not in filename:
                            filename = f"{plant_name.lower().replace(' ', '_')}.jpg"
                        
                        return img_temp, filename
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Error downloading image from {img_url}: {str(e)}"))
                    continue
        
        # If we reach here, try a different approach - look for standard image tags
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for img in soup.find_all('img', src=True):
                src = img.get('src')
                if src and (src.endswith('.jpg') or src.endswith('.jpeg') or src.endswith('.png')):
                    try:
                        # Download the image
                        img_response = requests.get(src, stream=True, timeout=10)
                        if img_response.status_code == 200:
                            img_temp = BytesIO()
                            img_temp.write(img_response.content)
                            img_temp.seek(0)
                            
                            # Get a filename
                            filename = f"{plant_name.lower().replace(' ', '_')}.jpg"
                            return img_temp, filename
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"Error downloading image from {src}: {str(e)}"))
                        continue
        
        return None, None
    
    def _try_duckduckgo_search(self, plant_name):
        """Try to download an image using DuckDuckGo search"""
        # Construct search query
        search_query = f"{plant_name} plant"
        search_url = f"https://duckduckgo.com/?q={search_query.replace(' ', '+')}&t=h_&iax=images&ia=images"
        
        # Set headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make the request
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for image elements
            for img in soup.find_all('img'):
                src = img.get('src')
                if src and not src.startswith('data:'):
                    try:
                        # Make sure URL is absolute
                        if not src.startswith('http'):
                            if src.startswith('//'):
                                src = 'https:' + src
                            else:
                                continue
                                
                        self.stdout.write(f"Trying image URL from DuckDuckGo: {src}")
                        
                        # Download the image
                        img_response = requests.get(src, stream=True, timeout=10)
                        if img_response.status_code == 200:
                            img_temp = BytesIO()
                            img_temp.write(img_response.content)
                            img_temp.seek(0)
                            
                            # Get a filename
                            filename = f"{plant_name.lower().replace(' ', '_')}_ddg.jpg"
                            return img_temp, filename
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"Error downloading image from {src}: {str(e)}"))
                        continue
        
        return None, None
    
    def _try_simple_search(self, plant_name):
        """Try a simple direct search for plant images on popular sites"""
        sites = [
            "https://www.gardeningknowhow.com",
            "https://www.thespruce.com",
            "https://www.almanac.com",
            "https://www.bhg.com"
        ]
        
        for site in sites:
            try:
                search_url = f"https://www.google.com/search?q=site:{site}+{plant_name.replace(' ', '+')}+plant+image&tbm=isch"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                response = requests.get(search_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find image elements
                    for img in soup.find_all('img'):
                        src = img.get('src')
                        if src and not src.startswith('data:') and 'google' not in src:
                            try:
                                if not src.startswith('http'):
                                    continue
                                    
                                self.stdout.write(f"Trying image URL from simple search: {src}")
                                
                                # Download the image
                                img_response = requests.get(src, stream=True, timeout=10)
                                if img_response.status_code == 200:
                                    img_temp = BytesIO()
                                    img_temp.write(img_response.content)
                                    img_temp.seek(0)
                                    
                                    # Get a filename
                                    filename = f"{plant_name.lower().replace(' ', '_')}_simple.jpg"
                                    return img_temp, filename
                            except Exception as e:
                                self.stdout.write(self.style.WARNING(f"Error downloading image from {src}: {str(e)}"))
                                continue
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Error with simple search for {plant_name}: {str(e)}"))
        
        return None, None
    
    def _create_placeholder_image(self, plant_name):
        """Create a placeholder image when no real images can be found"""
        # Create a very simple colored rectangle as a placeholder
        color_seed = ord(plant_name[0].lower()) % 6
        colors = [
            (200, 230, 200),  # Light green
            (230, 200, 200),  # Light red
            (200, 200, 230),  # Light blue
            (230, 230, 200),  # Light yellow
            (230, 200, 230),  # Light purple
            (200, 230, 230),  # Light cyan
        ]
        bg_color = colors[color_seed]
        
        # Create a new image with a colored background
        img = Image.new('RGB', (800, 600), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        # Add the plant name to the center
        try:
            # Try to use a font if available
            font = ImageFont.truetype("Arial", 40)
            draw.text((400, 300), plant_name, fill=(0, 0, 0), font=font, anchor="mm")
        except Exception:
            # Fallback to default font
            draw.text((400, 300), plant_name, fill=(0, 0, 0))
        
        # Save to BytesIO
        img_temp = BytesIO()
        img.save(img_temp, format='JPEG')
        img_temp.seek(0)
        filename = f"{plant_name.lower().replace(' ', '_')}_placeholder.jpg"
        
        return img_temp, filename

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        # Create categories if they don't exist
        categories = {
            'Indoor Plants': 'Beautiful plants that thrive indoors with minimal sunlight. Perfect for brightening up your home or office space.',
            'Outdoor Plants': 'Hardy plants that flourish in garden settings and can withstand various weather conditions.',
            'Succulents': 'Water-retaining plants adapted to arid conditions with thick, fleshy leaves.',
            'Herbs': 'Aromatic plants used for cooking, medicine, and adding fragrance to your home.',
            'Flowering Plants': 'Plants known for their beautiful blooms that add color to any space.',
            'Ferns': 'Ancient plants with feathery or leafy fronds that thrive in humid, shaded environments.',
            'Cacti': 'Desert plants with unique shapes and low water requirements.',
            'Bonsai': 'Miniature trees grown in containers using cultivation techniques to produce small trees that mimic the shape of full-size trees.'
        }
        
        for name, description in categories.items():
            Category.objects.get_or_create(name=name, description=description)
            
        self.stdout.write(self.style.SUCCESS('Categories created successfully!'))
        
        # Sample plants data
        plants_data = [
            # Indoor Plants
            {
                'name': 'Peace Lily',
                'category': 'Indoor Plants',
                'price': Decimal('24.99'),
                'description': 'The Peace Lily is a popular indoor plant known for its beautiful white flowers and ability to purify air. It\'s perfect for adding a touch of elegance to any room.',
                'care_instructions': 'Water when the top inch of soil is dry. Keep in medium to low light conditions. Avoid direct sunlight. Prefers high humidity but adapts to normal room conditions.',
                'difficulty': 'easy',
                'stock': random.randint(5, 20),
            },
            {
                'name': 'Snake Plant',
                'category': 'Indoor Plants',
                'price': Decimal('19.99'),
                'description': 'The Snake Plant, also known as Mother-in-Law\'s Tongue, is a hardy indoor plant with stiff, upright leaves. It\'s one of the most tolerant houseplants you can find.',
                'care_instructions': 'Water sparingly, allowing soil to dry completely between waterings. Tolerates low light but grows faster in bright light. Can survive in dry environments.',
                'difficulty': 'easy',
                'stock': random.randint(5, 20),
            },
            {
                'name': 'Fiddle Leaf Fig',
                'category': 'Indoor Plants',
                'price': Decimal('49.99'),
                'description': 'The Fiddle Leaf Fig is a popular houseplant with large, violin-shaped leaves. It makes a striking addition to any room with its tall, dramatic presence.',
                'care_instructions': 'Water when the top inch of soil is dry. Place in bright, indirect light. Rotate occasionally for even growth. Sensitive to changes in environment.',
                'difficulty': 'hard',
                'stock': random.randint(3, 10),
            },
            {
                'name': 'Pothos',
                'category': 'Indoor Plants',
                'price': Decimal('15.99'),
                'description': 'Pothos is a versatile trailing plant with heart-shaped leaves. It\'s perfect for hanging baskets or climbing up a moss pole.',
                'care_instructions': 'Water when the top inch of soil is dry. Adaptable to various light conditions, from low to bright indirect light. Trim regularly to encourage bushier growth.',
                'difficulty': 'easy',
                'stock': random.randint(5, 20),
            },
            {
                'name': 'Monstera Deliciosa',
                'category': 'Indoor Plants',
                'price': Decimal('29.99'),
                'description': 'Monstera Deliciosa, also known as the Swiss Cheese Plant, has distinctive split leaves that create a tropical feel in any space.',
                'care_instructions': 'Water when the top 2 inches of soil are dry. Place in bright, indirect light. Mist occasionally to increase humidity. Support with a moss pole as it grows.',
                'difficulty': 'medium',
                'stock': random.randint(3, 15),
            },
            {
                'name': 'ZZ Plant',
                'category': 'Indoor Plants',
                'price': Decimal('22.99'),
                'description': 'The ZZ Plant (Zamioculcas zamiifolia) is known for its glossy, dark green leaves and ability to thrive with minimal care, making it perfect for beginners.',
                'care_instructions': 'Water sparingly, allowing soil to dry completely between waterings. Tolerates low light conditions and irregular watering. Avoid overwatering.',
                'difficulty': 'easy',
                'stock': random.randint(5, 20),
            },
            {
                'name': 'Chinese Money Plant',
                'category': 'Indoor Plants',
                'price': Decimal('18.99'),
                'description': 'The Chinese Money Plant (Pilea peperomioides) features round, coin-shaped leaves on arching stems, creating a playful and modern look.',
                'care_instructions': 'Water when the top inch of soil is dry. Place in bright, indirect light. Rotate regularly for even growth. Propagates easily from offshoots.',
                'difficulty': 'medium',
                'stock': random.randint(3, 15),
            },
            {
                'name': 'Rubber Plant',
                'category': 'Indoor Plants',
                'price': Decimal('27.99'),
                'description': 'The Rubber Plant (Ficus elastica) has thick, glossy leaves and is known for its air-purifying qualities and striking vertical growth.',
                'care_instructions': 'Water when the top inch of soil is dry. Place in bright, indirect light. Wipe leaves occasionally to remove dust. Can be pruned to control height.',
                'difficulty': 'medium',
                'stock': random.randint(3, 15),
            },
            {
                'name': 'Spider Plant',
                'category': 'Indoor Plants',
                'price': Decimal('16.99'),
                'description': 'The Spider Plant (Chlorophytum comosum) has arching variegated leaves and produces baby plantlets that dangle from long stems.',
                'care_instructions': 'Keep soil lightly moist. Thrives in bright, indirect light but tolerates lower light. Remove baby plantlets to propagate new plants.',
                'difficulty': 'easy',
                'stock': random.randint(5, 20),
            },
            # Outdoor Plants
            {
                'name': 'Hydrangea',
                'category': 'Outdoor Plants',
                'price': Decimal('34.99'),
                'description': 'Hydrangeas are known for their large, showy flower heads that bloom throughout summer. They add a classic charm to any garden.',
                'care_instructions': 'Water deeply once or twice weekly. Plant in partial shade. Soil pH affects flower color - acidic soil for blue flowers, alkaline for pink.',
                'difficulty': 'medium',
                'stock': random.randint(3, 15),
            },
            {
                'name': 'Lavender',
                'category': 'Outdoor Plants',
                'price': Decimal('12.99'),
                'description': 'Lavender is a fragrant herb with purple flowers that attracts pollinators and repels pests. It\'s perfect for borders and herb gardens.',
                'care_instructions': 'Water sparingly once established. Plant in full sun with well-draining soil. Prune after flowering to maintain shape and promote new growth.',
                'difficulty': 'medium',
                'stock': random.randint(5, 20),
            },
            {
                'name': 'Rosemary',
                'category': 'Herbs',
                'price': Decimal('9.99'),
                'description': 'Rosemary is an aromatic herb with needle-like leaves that can be used fresh or dried in cooking. It also has ornamental value.',
                'care_instructions': 'Water when the top inch of soil is dry. Plant in full sun with well-draining soil. Prune regularly to prevent woodiness.',
                'difficulty': 'medium',
                'stock': random.randint(5, 20),
            },
            {
                'name': 'Azalea',
                'category': 'Outdoor Plants',
                'price': Decimal('29.99'),
                'description': 'Azaleas produce vibrant clusters of flowers in spring, creating a stunning display of color in shaded garden areas.',
                'care_instructions': 'Keep soil consistently moist but not soggy. Plant in partial shade. Prefers acidic soil. Prune after flowering.',
                'difficulty': 'medium',
                'stock': random.randint(3, 15),
            },
            {
                'name': 'Japanese Maple',
                'category': 'Outdoor Plants',
                'price': Decimal('59.99'),
                'description': 'Japanese Maple trees are known for their delicate, lacy foliage that changes color throughout the seasons, from red to orange to gold.',
                'care_instructions': 'Water deeply once weekly. Plant in partial shade, protected from strong winds. Mulch to retain moisture and protect roots.',
                'difficulty': 'medium',
                'stock': random.randint(2, 10),
            },
            {
                'name': 'Hosta',
                'category': 'Outdoor Plants',
                'price': Decimal('14.99'),
                'description': 'Hostas are shade-loving perennials grown primarily for their attractive foliage, which comes in various shapes, sizes, and colors.',
                'care_instructions': 'Keep soil consistently moist. Plant in shade or partial shade. Divide every few years to maintain vigor.',
                'difficulty': 'easy',
                'stock': random.randint(5, 20),
            },
            {
                'name': 'Peony',
                'category': 'Outdoor Plants',
                'price': Decimal('24.99'),
                'description': 'Peonies produce large, fragrant blooms in late spring and early summer, and can live for decades with minimal care.',
                'care_instructions': 'Water deeply once weekly. Plant in full sun with well-draining soil. Avoid transplanting. Support heavy blooms with stakes.',
                'difficulty': 'medium',
                'stock': random.randint(3, 15),
            },
            # Succulents
            {
                'name': 'Echeveria',
                'category': 'Succulents',
                'price': Decimal('8.99'),
                'description': 'Echeveria is a rosette-forming succulent with thick, fleshy leaves that come in a variety of colors and textures.',
                'care_instructions': 'Water sparingly, allowing soil to dry completely between waterings. Place in bright light. Plant in well-draining soil.',
                'difficulty': 'easy',
                'stock': random.randint(5, 20),
            },
            {
                'name': 'Aloe Vera',
                'category': 'Succulents',
                'price': Decimal('11.99'),
                'description': 'Aloe Vera is a medicinal plant with thick, fleshy leaves containing a gel that can be used to soothe burns and skin irritations.',
                'care_instructions': 'Water deeply but infrequently. Place in bright, indirect light. Plant in well-draining soil. Protect from frost.',
                'difficulty': 'easy',
                'stock': random.randint(5, 20),
            },
            {
                'name': 'Jade Plant',
                'category': 'Succulents',
                'price': Decimal('14.99'),
                'description': 'The Jade Plant is a popular succulent with thick, woody stems and oval-shaped leaves. It\'s considered a symbol of good luck.',
                'care_instructions': 'Water when the top inch of soil is dry. Place in bright, indirect light. Can tolerate some direct sun. Prune to maintain shape.',
                'difficulty': 'easy',
                'stock': random.randint(5, 20),
            },
            {
                'name': 'Haworthia',
                'category': 'Succulents',
                'price': Decimal('9.99'),
                'description': 'Haworthia is a small, rosette-forming succulent with distinctive white stripes or patterns on its leaves. Perfect for small spaces.',
                'care_instructions': 'Water sparingly, allowing soil to dry between waterings. Prefers bright, indirect light. Protect from intense afternoon sun.',
                'difficulty': 'easy',
                'stock': random.randint(5, 20),
            },
            {
                'name': 'String of Pearls',
                'category': 'Succulents',
                'price': Decimal('12.99'),
                'description': 'String of Pearls (Senecio rowleyanus) has unique bead-like leaves that cascade down, making it perfect for hanging baskets.',
                'care_instructions': 'Water sparingly, allowing soil to dry between waterings. Place in bright, indirect light. Plant in well-draining soil.',
                'difficulty': 'medium',
                'stock': random.randint(3, 15),
            },
            {
                'name': 'Burro\'s Tail',
                'category': 'Succulents',
                'price': Decimal('13.99'),
                'description': 'Burro\'s Tail (Sedum morganianum) has trailing stems covered in plump, overlapping leaves that resemble a donkey\'s tail.',
                'care_instructions': 'Water when the soil is completely dry. Place in bright light with some direct sun. Handle carefully as leaves fall off easily.',
                'difficulty': 'medium',
                'stock': random.randint(3, 15),
            },
            # Herbs
            {
                'name': 'Basil',
                'category': 'Herbs',
                'price': Decimal('4.99'),
                'description': 'Basil is a culinary herb with aromatic leaves used in many cuisines, particularly Italian. It\'s easy to grow and harvest.',
                'care_instructions': 'Keep soil consistently moist. Place in full sun. Pinch off flower buds to encourage leaf production. Harvest regularly.',
                'difficulty': 'easy',
                'stock': random.randint(5, 20),
            },
            {
                'name': 'Mint',
                'category': 'Herbs',
                'price': Decimal('4.99'),
                'description': 'Mint is a vigorous herb with fragrant leaves used in teas, cocktails, and cooking. It spreads quickly and is best contained.',
                'care_instructions': 'Keep soil consistently moist. Can grow in full sun to partial shade. Plant in containers to control spreading.',
                'difficulty': 'easy',
                'stock': random.randint(5, 20),
            },
            {
                'name': 'Thyme',
                'category': 'Herbs',
                'price': Decimal('4.99'),
                'description': 'Thyme is a low-growing herb with tiny, aromatic leaves used in cooking. It also attracts beneficial insects to the garden.',
                'care_instructions': 'Water when the top inch of soil is dry. Plant in full sun with well-draining soil. Trim after flowering to maintain shape.',
                'difficulty': 'easy',
                'stock': random.randint(5, 20),
            },
            {
                'name': 'Cilantro',
                'category': 'Herbs',
                'price': Decimal('4.99'),
                'description': 'Cilantro is a versatile herb used in many cuisines. Its leaves have a fresh, citrusy flavor, and its seeds (coriander) are used as a spice.',
                'care_instructions': 'Keep soil consistently moist. Plant in partial shade in hot climates. Succession plant for continuous harvest.',
                'difficulty': 'medium',
                'stock': random.randint(5, 20),
            },
            {
                'name': 'Oregano',
                'category': 'Herbs',
                'price': Decimal('4.99'),
                'description': 'Oregano is a perennial herb with a strong, aromatic flavor that intensifies when dried. Essential for Mediterranean cooking.',
                'care_instructions': 'Water when the top inch of soil is dry. Plant in full sun with well-draining soil. Trim regularly to prevent woodiness.',
                'difficulty': 'easy',
                'stock': random.randint(5, 20),
            },
            {
                'name': 'Sage',
                'category': 'Herbs',
                'price': Decimal('4.99'),
                'description': 'Sage is a culinary and medicinal herb with soft, gray-green leaves and a savory, slightly peppery flavor.',
                'care_instructions': 'Water when the top inch of soil is dry. Plant in full sun with well-draining soil. Prune in spring to maintain shape.',
                'difficulty': 'medium',
                'stock': random.randint(5, 20),
            },
            # Flowering Plants
            {
                'name': 'Orchid',
                'category': 'Flowering Plants',
                'price': Decimal('29.99'),
                'description': 'Orchids are exotic flowering plants known for their intricate, long-lasting blooms that add elegance to any space.',
                'care_instructions': 'Water weekly, allowing the bark medium to dry between waterings. Place in bright, indirect light. High humidity preferred.',
                'difficulty': 'hard',
                'stock': random.randint(3, 10),
            },
            {
                'name': 'African Violet',
                'category': 'Flowering Plants',
                'price': Decimal('8.99'),
                'description': 'African Violets are compact plants with velvety leaves and delicate flowers that bloom year-round under proper conditions.',
                'care_instructions': 'Water from the bottom when the top of the soil feels dry. Place in bright, indirect light. Avoid getting water on the leaves.',
                'difficulty': 'medium',
                'stock': random.randint(3, 15),
            },
            {
                'name': 'Anthurium',
                'category': 'Flowering Plants',
                'price': Decimal('24.99'),
                'description': 'Anthuriums feature glossy, heart-shaped flowers in vibrant colors that can bloom year-round with proper care.',
                'care_instructions': 'Keep soil consistently moist but not soggy. Place in bright, indirect light. Prefers high humidity.',
                'difficulty': 'medium',
                'stock': random.randint(3, 15),
            },
            {
                'name': 'Peace Lily',
                'category': 'Flowering Plants',
                'price': Decimal('19.99'),
                'description': 'Peace Lilies produce elegant white spathes and are excellent air purifiers. They\'re also known for being forgiving plants.',
                'care_instructions': 'Water when the leaves start to droop slightly. Can tolerate low light but blooms best in medium, indirect light.',
                'difficulty': 'easy',
                'stock': random.randint(5, 20),
            },
            {
                'name': 'Begonia',
                'category': 'Flowering Plants',
                'price': Decimal('12.99'),
                'description': 'Begonias come in many varieties with colorful flowers and often interesting foliage patterns. They add color to shaded areas.',
                'care_instructions': 'Keep soil lightly moist. Place in bright, indirect light. Avoid wetting the leaves. Pinch back to encourage bushiness.',
                'difficulty': 'medium',
                'stock': random.randint(3, 15),
            },
            {
                'name': 'Gerbera Daisy',
                'category': 'Flowering Plants',
                'price': Decimal('9.99'),
                'description': 'Gerbera Daisies produce large, vibrant flowers on long stems, making them excellent as potted plants or cut flowers.',
                'care_instructions': 'Water at the base when the top inch of soil is dry. Place in bright light with some direct sun. Remove spent flowers.',
                'difficulty': 'medium',
                'stock': random.randint(3, 15),
            },
            # Ferns
            {
                'name': 'Boston Fern',
                'category': 'Ferns',
                'price': Decimal('15.99'),
                'description': 'Boston Ferns have arching fronds with small leaflets, creating a lush, feathery appearance. They\'re classic hanging plants.',
                'care_instructions': 'Keep soil consistently moist. Place in bright, indirect light. Mist regularly to increase humidity. Avoid drafts.',
                'difficulty': 'medium',
                'stock': random.randint(3, 15),
            },
            {
                'name': 'Maidenhair Fern',
                'category': 'Ferns',
                'price': Decimal('12.99'),
                'description': 'Maidenhair Ferns have delicate, fan-shaped fronds with thin, black stems, creating an elegant, airy appearance.',
                'care_instructions': 'Keep soil consistently moist. Place in bright, indirect light. High humidity required. Protect from drafts.',
                'difficulty': 'hard',
                'stock': random.randint(3, 10),
            },
            {
                'name': 'Bird\'s Nest Fern',
                'category': 'Ferns',
                'price': Decimal('17.99'),
                'description': 'Bird\'s Nest Ferns have wide, rippled fronds that emerge from a central rosette, resembling a bird\'s nest.',
                'care_instructions': 'Keep soil consistently moist. Place in medium to low light. Avoid getting water in the center rosette.',
                'difficulty': 'medium',
                'stock': random.randint(3, 15),
            },
            {
                'name': 'Staghorn Fern',
                'category': 'Ferns',
                'price': Decimal('22.99'),
                'description': 'Staghorn Ferns have unique, antler-like fronds and can be mounted on boards for display as living wall art.',
                'care_instructions': 'Soak in water weekly. Place in bright, indirect light. Mist regularly to increase humidity.',
                'difficulty': 'medium',
                'stock': random.randint(3, 10),
            },
            {
                'name': 'Rabbit\'s Foot Fern',
                'category': 'Ferns',
                'price': Decimal('19.99'),
                'description': 'Rabbit\'s Foot Ferns have fuzzy rhizomes that resemble rabbit\'s feet, which grow over the edge of the pot.',
                'care_instructions': 'Keep soil lightly moist. Place in bright, indirect light. Mist regularly to increase humidity.',
                'difficulty': 'medium',
                'stock': random.randint(3, 15),
            },
            # Cacti
            {
                'name': 'Barrel Cactus',
                'category': 'Cacti',
                'price': Decimal('16.99'),
                'description': 'Barrel Cacti are round, ribbed cacti with sharp spines. They can produce bright yellow or orange flowers at the top.',
                'care_instructions': 'Water sparingly, allowing soil to dry completely between waterings. Place in bright light with some direct sun.',
                'difficulty': 'easy',
                'stock': random.randint(3, 15),
            },
            {
                'name': 'Prickly Pear',
                'category': 'Cacti',
                'price': Decimal('14.99'),
                'description': 'Prickly Pear cacti have flat, paddle-shaped segments and produce colorful flowers followed by edible fruits.',
                'care_instructions': 'Water sparingly, allowing soil to dry completely between waterings. Place in full sun. Handle with care due to tiny spines.',
                'difficulty': 'easy',
                'stock': random.randint(3, 15),
            },
            {
                'name': 'Christmas Cactus',
                'category': 'Cacti',
                'price': Decimal('12.99'),
                'description': 'Christmas Cacti have flattened stems and bloom around the holiday season with tubular flowers in pink, red, or white.',
                'care_instructions': 'Water when the top inch of soil is dry. Place in bright, indirect light. Requires a period of darkness to initiate blooming.',
                'difficulty': 'medium',
                'stock': random.randint(3, 15),
            },
            {
                'name': 'Old Man Cactus',
                'category': 'Cacti',
                'price': Decimal('18.99'),
                'description': 'Old Man Cactus (Cephalocereus senilis) is covered in long, white hairs that resemble an old man\'s beard, protecting it from the sun.',
                'care_instructions': 'Water sparingly, allowing soil to dry completely between waterings. Place in bright light with some direct sun.',
                'difficulty': 'easy',
                'stock': random.randint(3, 15),
            },
            {
                'name': 'Star Cactus',
                'category': 'Cacti',
                'price': Decimal('9.99'),
                'description': 'Star Cactus (Astrophytum) has a distinctive ribbed, star-shaped form and is often covered in tiny white dots.',
                'care_instructions': 'Water sparingly, allowing soil to dry completely between waterings. Place in bright light with some direct sun.',
                'difficulty': 'easy',
                'stock': random.randint(3, 15),
            },
            # Bonsai
            {
                'name': 'Juniper Bonsai',
                'category': 'Bonsai',
                'price': Decimal('39.99'),
                'description': 'Juniper Bonsai trees have textured bark and needle-like foliage, creating a classic bonsai appearance.',
                'care_instructions': 'Water when the top half-inch of soil is dry. Place in bright light with some direct sun. Prune regularly to maintain shape.',
                'difficulty': 'medium',
                'stock': random.randint(2, 10),
            },
            {
                'name': 'Ficus Bonsai',
                'category': 'Bonsai',
                'price': Decimal('34.99'),
                'description': 'Ficus Bonsai trees have glossy leaves and develop interesting aerial roots and trunk formations over time.',
                'care_instructions': 'Water when the top inch of soil is dry. Place in bright, indirect light. Mist occasionally to increase humidity.',
                'difficulty': 'medium',
                'stock': random.randint(2, 10),
            },
            {
                'name': 'Japanese Maple Bonsai',
                'category': 'Bonsai',
                'price': Decimal('49.99'),
                'description': 'Japanese Maple Bonsai trees have delicate, star-shaped leaves that change color with the seasons, creating a miniature version of the full-sized tree.',
                'care_instructions': 'Keep soil consistently moist but not soggy. Place in bright, indirect light. Protect from strong winds and extreme temperatures.',
                'difficulty': 'hard',
                'stock': random.randint(2, 8),
            },
            {
                'name': 'Chinese Elm Bonsai',
                'category': 'Bonsai',
                'price': Decimal('44.99'),
                'description': 'Chinese Elm Bonsai trees have small leaves and develop beautiful trunk patterns, making them popular for beginners.',
                'care_instructions': 'Water when the top half-inch of soil is dry. Place in bright light with some direct sun. Can be grown indoors or outdoors.',
                'difficulty': 'medium',
                'stock': random.randint(2, 10),
            },
            {
                'name': 'Azalea Bonsai',
                'category': 'Bonsai',
                'price': Decimal('39.99'),
                'description': 'Azalea Bonsai trees produce vibrant flowers in spring, creating a stunning miniature flowering tree.',
                'care_instructions': 'Keep soil consistently moist but not soggy. Place in bright, indirect light. Prefers acidic soil. Prune after flowering.',
                'difficulty': 'hard',
                'stock': random.randint(2, 8),
            },
        ]
        
        # Create plants
        plants_created = 0
        plants_updated = 0
        
        for plant_data in plants_data:
            category_name = plant_data.pop('category')
            category = Category.objects.get(name=category_name)
            
            # Check if plant already exists
            plant_exists = Plant.objects.filter(name=plant_data['name']).exists()
            
            if force and plant_exists:
                # Update existing plant
                plant = Plant.objects.get(name=plant_data['name'])
                
                # Update fields
                for key, value in plant_data.items():
                    setattr(plant, key, value)
                
                plant.category = category
                plant.available = True
                
                # Download and attach image
                self.stdout.write(f"Downloading image for {plant_data['name']}...")
                img_temp, filename = self.download_image(plant_data['name'])
                if img_temp and filename:
                    # Delete old image if it exists
                    if plant.image:
                        plant.image.delete(save=False)
                    plant.image.save(filename, File(img_temp), save=False)
                
                # Save the plant
                plant.save()
                plants_updated += 1
                self.stdout.write(f"Updated plant: {plant_data['name']}")
                
            elif not plant_exists:
                # Create a new plant instance
                plant = Plant(category=category, available=True, **plant_data)
                
                # Download and attach image
                self.stdout.write(f"Downloading image for {plant_data['name']}...")
                img_temp, filename = self.download_image(plant_data['name'])
                if img_temp and filename:
                    plant.image.save(filename, File(img_temp), save=False)
                
                # Save the plant
                plant.save()
                plants_created += 1
                self.stdout.write(f"Created plant: {plant_data['name']}")
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {plants_created} plants and updated {plants_updated} plants!'))
