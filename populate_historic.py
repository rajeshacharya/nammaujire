import os
import django
import urllib.request
import urllib.parse
import json
import time
import re
from django.core.files.base import ContentFile

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nammaujire.settings")
django.setup()

from locations.models import Category, Place

DEFAULT_HISTORIC_IMG = r"C:\Users\Rajesh Acharya\.gemini\antigravity\brain\37c075d0-26e7-49fd-a0b0-dd125b8b105a\default_school_1778348259362.png" # Need a historic default maybe? I will just use web scraping

def search_ddg_image(query):
    try:
        req = urllib.request.Request(
            f"https://duckduckgo.com/?q={urllib.parse.quote(query)}",
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            vqd_match = re.search(r'vqd=([\d-]+)', html)
            if not vqd_match: return None
            vqd = vqd_match.group(1)
            
        img_url = f"https://duckduckgo.com/i.js?l=us-en&o=json&q={urllib.parse.quote(query)}&vqd={vqd}&f=,,,type:photo,,&p=1"
        req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            if 'results' in data and len(data['results']) > 0:
                for res in data['results']:
                    url = res['image']
                    if 'lookaside' not in url.lower() and 'facebook' not in url.lower():
                        return url
                return data['results'][0]['image']
    except Exception as e:
        print(f"DDG search failed for {query}: {e}")
    return None

def download_image(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'image/jpeg,image/png,*/*'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            time.sleep(1)
            return response.read()
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return None

def populate():
    cat_historic, _ = Category.objects.get_or_create(
        slug="historical", 
        defaults={"name": "Historical", "icon": "fa-brands fa-fort-awesome"}
    )
    
    historic_data = [
        {
            "name": "Sri Janardhana Swamy Temple",
            "search_query": "Sri Janardhana Swamy Temple Ujire",
            "desc": "A major old Vishnu/Janardhana temple in Ujire. A Kannada historical article notes evidence linked to CE 1060 and a CE 1469 inscription, and describes the shrine’s old gajaprishta / elephant-back style sanctum.",
            "source": "Upayuktha local history article"
        },
        {
            "name": "Sri Sadashiva Rudra Temple (Surya Temple)",
            "search_query": "Sri Sadashiva Rudra Temple Ujire",
            "desc": "A Shiva temple famous for clay-offering traditions (mannina harake). The source says it is about 4 km from Ujire and that inscriptions indicate history dating to the 13th century.",
            "source": "Mangalore Heritage"
        },
        {
            "name": "Jamalabad Fort / Gadaikallu",
            "search_query": "Jamalabad Fort Gadaikallu",
            "desc": "An 18th-century hill fort. Built by Tipu Sultan on the ruins of an older Hoysala fort, with rock-cut steps and panoramic hill views.",
            "source": "Karnataka Tourism"
        },
        {
            "name": "Old Jain Basadi near Permannu",
            "search_query": "Old Jain Basadi near Permannu Belthangady",
            "desc": "A lesser-known Jain heritage stop mentioned by Karnataka Tourism as being on the route to Jamalabad Fort.",
            "source": "Karnataka Tourism"
        },
        {
            "name": "Dharmasthala Manjunatha Temple",
            "search_query": "Dharmasthala Manjunatha Temple",
            "desc": "A major religious-heritage center known for a distinctive blend of traditions: a Shaivite temple served by Madhwa Vaishnavite priests and administered by the Jain Heggade family.",
            "source": "Dakshina Kannada District Administration"
        },
        {
            "name": "Manjusha Museum",
            "search_query": "Manjusha Museum Dharmasthala",
            "desc": "A useful historical stop near the temple; houses ancient palm-leaf scripts, silver jewellery, religious statuary, and other heritage objects.",
            "source": "Dakshina Kannada District Administration"
        },
        {
            "name": "Sri Chandranatha Swamy Basadi",
            "search_query": "Sri Chandranatha Swamy Basadi Dharmasthala",
            "desc": "A Jain basadi listed by Karnataka Tourism as an important Jain center in the Dharmasthala heritage complex.",
            "source": "Karnataka Tourism"
        },
        {
            "name": "Bahubali Statue, Dharmasthala",
            "search_query": "Bahubali Statue Dharmasthala",
            "desc": "A 39-ft Bahubali statue representing Jain influence in the area; it was erected in 1980.",
            "source": "Dakshina Kannada District Administration"
        },
        {
            "name": "Venur Gomateshwara",
            "search_query": "Venur Gomateshwara Bahubali Statue",
            "desc": "Venur was once the capital of the Ajilas. Known for its 35-ft monolithic Gomateshwara statue and palace remains; Timmanna Ajila IV consecrated the statue in 1604.",
            "source": "Karnataka Tourism"
        }
    ]

    for data in historic_data:
        # Check if we already have it by a similar name
        existing = Place.objects.filter(name__icontains=data['name'].split('/')[0].strip()).first()
        
        full_desc = f"{data['desc']} (Source: {data['source']})"
        
        if existing:
            print(f"Updating existing place: {existing.name}")
            existing.description = existing.description + "\n\nHistorical Context:\n" + full_desc
            existing.save()
            continue

        print(f"Processing NEW place: {data['name']}...")
        place = Place(
            name=data["name"],
            category=cat_historic,
            short_description=data["desc"][:190] + "..." if len(data["desc"]) > 190 else data["desc"],
            description=full_desc,
            rating=4.7,
            reviews_count=450
        )
        
        print(f"  -> Searching DDG for image: {data['search_query']}")
        img_url = search_ddg_image(data['search_query'])
        img_content = None
        
        if img_url:
            print(f"  -> Found DDG image: {img_url}")
            img_content = download_image(img_url)

        if img_content and img_url:
            file_name = img_url.split('/')[-1].split('?')[0]
            file_name = urllib.parse.unquote(file_name)
            if not file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                file_name += '.jpg'
            place.image.save(file_name, ContentFile(img_content), save=True)
            print(f"  -> Saved real image.")
        else:
            print(f"  -> No image found. Saving without image for now.")
            place.save()

if __name__ == "__main__":
    populate()
    print("Historic places populated successfully!")
