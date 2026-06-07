import os
import django
import urllib.request
from django.core.files.base import ContentFile

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nammaujire.settings")
django.setup()

from locations.models import Category, Place

import time

def download_image(url):
    try:
        # Wikimedia requires a descriptive User-Agent
        headers = {
            'User-Agent': 'NammaUjireApp/1.0 (contact@nammaujire.local) python-urllib/3.x',
            'Accept': 'image/jpeg,image/png,*/*'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            time.sleep(2) # Prevent 429 Too Many Requests
            return response.read()
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return None

def populate():
    # Clear existing
    Place.objects.all().delete()
    Category.objects.all().delete()

    # Create Categories
    cat_edu = Category.objects.create(name="Education", slug="education", icon="fa-solid fa-graduation-cap")
    cat_temple = Category.objects.create(name="Temples & Spiritual", slug="temples", icon="fa-solid fa-om")
    cat_nature = Category.objects.create(name="Nature & Trekking", slug="nature", icon="fa-solid fa-mountain-sun")
    cat_history = Category.objects.create(name="Historical", slug="historical", icon="fa-brands fa-fort-awesome")

    places_data = [
        {
            "name": "SDM College (Siddavana Gurukula)",
            "category": cat_edu,
            "short_description": "Prominent educational campus in Ujire.",
            "description": "SDM College Ujire is a leading autonomous college. The Siddavana Gurukula on the campus provides a traditional yet modern educational environment.",
            "rating": 4.8,
            "reviews_count": 1250,
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/c/c8/Siddavana_gurukula.JPG"
        },
        {
            "name": "Sri Kshetra Dharmasthala",
            "category": cat_temple,
            "short_description": "Famous 800-year-old Manjunatha Temple.",
            "description": "Located just a few kilometers from Ujire, Dharmasthala is one of the most revered pilgrimage centers in South India, dedicated to Lord Shiva as Manjunatha.",
            "rating": 4.9,
            "reviews_count": 15400,
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/a/ad/Dharmasthala_1.jpg"
        },
        {
            "name": "Charmadi Ghat",
            "category": cat_nature,
            "short_description": "A spectacularly scenic mountain pass in the Western Ghats.",
            "description": "Charmadi Ghat is one of the most beautiful and thrilling mountain passes in Karnataka. It connects Dakshina Kannada with Chikmagalur. It is famous for its lush green hills, deep valleys, and misty weather.",
            "rating": 4.8,
            "reviews_count": 5200,
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/1/18/Charmadi_Ghat_Road.jpg"
        },
        {
            "name": "Jamalabad Fort (Gadaikallu)",
            "category": cat_history,
            "short_description": "A historic hill fort built by Tipu Sultan.",
            "description": "Also known as Narasimhagada, Jamalabad Fort is located on a steep granite hill. Built in 1794, the fort requires a challenging trek up nearly 1900 steps. The top offers breathtaking panoramic views.",
            "rating": 4.6,
            "reviews_count": 890,
            "image_url": "https://upload.wikimedia.org/wikipedia/en/f/fc/Jamalabad_Rock%28Gadaikallu%29.jpg"
        },
        {
            "name": "Netravati River",
            "category": cat_nature,
            "short_description": "The lifeline river of the Dakshina Kannada region.",
            "description": "Originating in the Western Ghats, the Netravati River flows near Ujire and Dharmasthala. The river barrage is a beautiful spot to witness the serene flow of water surrounded by lush greenery.",
            "rating": 4.7,
            "reviews_count": 2100,
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/5/55/The_Netravati_%E0%B4%A8%E0%B5%87%E0%B4%A4%E0%B5%8D%E0%B4%B0%E0%B4%BE%E0%B4%B5%E0%B4%A4%E0%B4%BF.JPG"
        }
    ]

    for data in places_data:
        place = Place(
            name=data["name"],
            category=data["category"],
            short_description=data["short_description"],
            description=data["description"],
            rating=data["rating"],
            reviews_count=data["reviews_count"]
        )
        
        print(f"Downloading image for {place.name}...")
        img_content = download_image(data["image_url"])
        if img_content:
            file_name = data["image_url"].split('/')[-1]
            # url encoding fix for the netravati river file name
            file_name = urllib.parse.unquote(file_name)
            place.image.save(file_name, ContentFile(img_content), save=True)
            print(f"Successfully created {place.name}")
        else:
            print(f"Warning: Image failed for {place.name}. Created without image.")
            place.save()

if __name__ == "__main__":
    populate()
    print("Database populated successfully with REAL Wikipedia images!")
