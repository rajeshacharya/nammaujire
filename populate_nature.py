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

DEFAULT_NATURE_IMG = r"C:\Users\Rajesh Acharya\.gemini\antigravity\brain\37c075d0-26e7-49fd-a0b0-dd125b8b105a\default_school_1778348259362.png" # I will just rely on web scraping

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
                    if 'lookaside' not in url.lower() and 'facebook' not in url.lower() and 'tripadvisor' not in url.lower():
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
    cat_nature, _ = Category.objects.get_or_create(
        slug="nature", 
        defaults={"name": "Nature & Trekking", "icon": "fa-solid fa-mountain-sun"}
    )
    
    nature_data = [
        {
            "name": "Jamalabad Fort / Gadaikallu",
            "search_query": "Jamalabad Fort Gadaikallu",
            "desc": "One of the closest strong trekking options from Ujire: steep rock-cut steps, hill-fort ruins, and wide Western Ghats views.",
            "notes": "Moderate but steep. Best October–May. Rocks become slippery and dangerous in the rainy season."
        },
        {
            "name": "Bandaje Arbi Falls + Ballalarayana Durga Fort",
            "search_query": "Bandaje Arbi Falls Ballalarayana Durga Fort",
            "desc": "Probably the most famous serious trek near Ujire. It combines forest trail, open grasslands, the Ballalarayana Durga fort area, and a high 200-ft plunge waterfall.",
            "notes": "Moderate to hard. Permission from Belthangady Wildlife Range Office required. Post-monsoon to winter is best."
        },
        {
            "name": "Didupe Falls / Kadamagundi Falls",
            "search_query": "Didupe Falls Kadamagundi",
            "desc": "A beautiful waterfall at the base of Charmadi Ghat, surrounded by rocky terrain and dense forest. Short trek through forest, streams, and private farmland.",
            "notes": "Short trek but slippery. Forest-department permission required at Didupe village. Best November–March."
        },
        {
            "name": "Ermai / Ermayi Falls",
            "search_query": "Ermayi Falls Ujire",
            "desc": "A multi-layered seasonal waterfall on the slopes of the Ballalarayana Durga range. Good for a half-day nature visit.",
            "notes": "Sources warn about poor roads, slippery moss-covered rocks, rising water in rain. Recommend local help."
        },
        {
            "name": "Dondole Falls",
            "search_query": "Dondole Falls Kakkinje",
            "desc": "A lesser-known waterfall option in the Charmadi belt, useful for offbeat travelers.",
            "notes": "Verify access locally before going. Local access, road condition, and water flow may vary."
        },
        {
            "name": "Charmadi Ghat",
            "search_query": "Charmadi Ghat scenic view",
            "desc": "Excellent for nature views without committing to a long trek. The ghat has hairpin bends, forested slopes, streams, and monsoon waterfalls.",
            "notes": "Great in/after monsoon, but driving can be risky in heavy rain. Avoid night driving."
        },
        {
            "name": "Rani Jhari Edge Point",
            "search_query": "Rani Jhari Edge Point viewpoint",
            "desc": "One of the best cliff-edge viewpoints in the region, with views toward Kudremukh National Park, Ballalarayana Durga, valleys, and grasslands.",
            "notes": "Short but exposed 1.5 km trek (30–45 minutes). Go in a group and avoid foggy or rainy conditions."
        },
        {
            "name": "Devaramane Betta",
            "search_query": "Devaramane Betta Viewpoint",
            "desc": "A scenic Western Ghats hill area with rolling hillocks, mist, grasslands, and beginner-friendly climbs. Good for sunrise/sunset views.",
            "notes": "Easier than Bandaje. Best after monsoon and in winter."
        },
        {
            "name": "Ettina Bhuja",
            "search_query": "Ettina Bhuja trek peak",
            "desc": "A very rewarding peak trek with views of the Charmadi range, nearby peaks, forests, and grasslands.",
            "notes": "Moderate. Byrapura route is straightforward, Shishila route needs a guide. Best post-monsoon to winter."
        },
        {
            "name": "Amedikallu Peak",
            "search_query": "Amedikallu Peak Shishila",
            "desc": "A more serious Charmadi-range trek, usually treated as a long or two-day plan by trekking groups. Best for experienced trekkers.",
            "notes": "Moderate to difficult. 6–8 hour one-way effort. Take a guide and verify permission."
        },
        {
            "name": "Netravathi Peak",
            "search_query": "Netravati Peak trek Samse",
            "desc": "A major Western Ghats trek with rolling shola grasslands and views toward Belthangady. A popular alternative to Kudremukh Peak.",
            "notes": "Moderate. Needs stamina and permission. Go in the official season."
        },
        {
            "name": "Kudremukh National Park Treks",
            "search_query": "Kudremukh Peak trek landscape",
            "desc": "Best for serious trekkers who want bigger Western Ghats landscapes. Includes Kudremukha, Kurinjal, Gangadikal, Narasimha Parvatha, and Valikunja.",
            "notes": "Requires official booking/permission. Treks range from moderate to challenging (6–21 km). Best October–March."
        },
        {
            "name": "Hanumangundi Falls",
            "search_query": "Hanumangundi Falls Kudremukh",
            "desc": "Beautiful waterfalls inside the Kudremukh region. Good add-ons if you are already going toward Kudremukh National Park.",
            "notes": "Check opening status and forest rules before visiting."
        }
    ]

    for data in nature_data:
        existing = Place.objects.filter(name__icontains=data['name'].split('/')[0].strip()).first()
        
        full_desc = f"{data['desc']}\n\nNotes & Difficulty:\n{data['notes']}"
        
        if existing:
            # We skip Jamalabad and Charmadi Ghat because they might already exist
            # Wait, if they exist we should ensure their category is updated or we just append
            print(f"Updating existing place: {existing.name}")
            if "Notes & Difficulty" not in existing.description:
                existing.description = existing.description + "\n\n" + full_desc
                existing.save()
            continue

        print(f"Processing NEW place: {data['name']}...")
        place = Place(
            name=data["name"],
            category=cat_nature,
            short_description=data["desc"][:190] + "..." if len(data["desc"]) > 190 else data["desc"],
            description=full_desc,
            rating=4.8,
            reviews_count=700
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
    print("Nature places populated successfully!")
