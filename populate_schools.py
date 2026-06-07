import os
import django
import urllib.request
import urllib.parse
import json
import time
from django.core.files.base import ContentFile

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nammaujire.settings")
django.setup()

from locations.models import Category, Place

DEFAULT_SCHOOL_IMG = r"C:\Users\Rajesh Acharya\.gemini\antigravity\brain\37c075d0-26e7-49fd-a0b0-dd125b8b105a\default_school_1778348259362.png"

def search_wiki_image(query):
    # Try to find a Wikipedia image for the given query
    url = f'https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=original&titles={urllib.parse.quote(query)}'
    try:
        headers = {'User-Agent': 'NammaUjireApp/1.0 (contact@nammaujire.local) python-urllib/3.x'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            time.sleep(1) # Prevent rate limits
            data = json.loads(response.read().decode('utf-8'))
            pages = data['query']['pages']
            for page_id, page_info in pages.items():
                if 'original' in page_info:
                    return page_info['original']['source']
    except Exception as e:
        print(f"Wiki search failed for {query}: {e}")
    return None

import re

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
                    # skip facebook/lookaside which often block python downloads
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
    # Make sure we have the category
    cat_edu, created = Category.objects.get_or_create(
        slug="education", 
        defaults={"name": "Schools & Colleges", "icon": "fa-solid fa-graduation-cap"}
    )
    # Update name if it already existed
    cat_edu.name = "Schools & Colleges"
    cat_edu.save()

    places_data = [
        # Colleges
        {"name": "SDM College (Autonomous)", "query": "Sri Dharmasthala Manjunatheshwara College, Ujire", "desc": "The flagship institution affiliated with Mangalore University, offering a vast range of Undergraduate, Postgraduate, Vocational, and Doctoral programs across arts, science, commerce, and management."},
        {"name": "SDM Institute of Technology (SDMIT)", "query": "Sri Dharmasthala Manjunatheshwara Institute of Technology", "desc": "A prominent engineering college offering various technical and engineering degree programs."},
        {"name": "SDM College of Naturopathy and Yogic Sciences", "query": "SDM College of Naturopathy and Yogic Sciences", "desc": "A specialized institution offering medical degrees and training in naturopathy and yoga."},
        {"name": "SDM Pre-University (PU) College", "query": "SDM Pre-University College, Ujire", "desc": "Offers standard PU courses across Science, Commerce, and Arts streams."},
        {"name": "SDM Residential Pre-University College", "query": "SDM Residential PU College", "desc": "A dedicated residential PU college offering focused academic programs for students staying on campus."},
        {"name": "Anugraha Pre-University (PU) College", "query": "Anugraha PU College Ujire", "desc": "Offers higher secondary courses, including well-regarded Commerce and Science streams, managed by the Catholic Board of Education."},
        {"name": "SDM College of Education (B.Ed / D.Ed)", "query": "SDM College of Education", "desc": "An institution dedicated to teacher training and educational methodologies."},
        {"name": "Sri Dharmasthala Manjunatheshwara (SDM) Polytechnic", "query": "SDM Polytechnic Ujire", "desc": "Provides various technical diploma courses in engineering and technology fields."},
        {"name": "Prasanna First Grade College", "query": "Prasanna First Grade College", "desc": "A private college offering undergraduate degree programs."},
        {"name": "Prasanna College of Nursing", "query": "Prasanna College of Nursing", "desc": "Offers specialized education and training in nursing and healthcare."},
        
        # Schools
        {"name": "SDM English Medium School", "query": "SDM English Medium School", "desc": "A major school offering primary, upper primary, and secondary education with both CBSE and Karnataka State Board curriculum options."},
        {"name": "Anugraha English Medium School", "query": "Anugraha English Medium School", "desc": "A highly regarded educational pillar situated near St. Antony's Church, offering strong primary and high school education with a focus on discipline and academic foundation."},
        {"name": "SDM Aided Higher Primary School", "query": "SDM Aided Higher Primary School", "desc": "Provides foundational and primary education to the local community."},
        {"name": "Government High School, Ujire", "query": "Government High School Ujire", "desc": "A prominent state-run high school serving the area."},
        {"name": "DKZP Government Lower Primary School", "query": "DKZP Government Lower Primary School Ujire", "desc": "A state-run primary education facility."},
        {"name": "DKZP Government Higher Primary School, Guripalla", "query": "DKZP Guripalla", "desc": "A state-run higher primary school catering to the Guripalla locality."},
        {"name": "DKZP Government Higher Primary School, Badanaje", "query": "DKZP Badanaje", "desc": "An RMSA-upgraded government school."},
        {"name": "Government High School, Kalmanja", "query": "Government High School Kalmanja", "desc": "Located just on the outskirts of Ujire, serving the students of the Kalmanja area."}
    ]

    for data in places_data:
        # Check if already exists so we don't duplicate
        if Place.objects.filter(name=data["name"]).exists():
            print(f"Skipping {data['name']}, already exists.")
            continue
            
        print(f"Processing {data['name']}...")
        place = Place(
            name=data["name"],
            category=cat_edu,
            short_description=data["desc"][:190] + "..." if len(data["desc"]) > 190 else data["desc"],
            description=data["desc"],
            rating=4.5,
            reviews_count=120
        )
        
        # 1. Try to find Wikipedia image
        img_url = search_wiki_image(data["query"])
        img_content = None
        
        if img_url:
            print(f"  -> Found Wikipedia image: {img_url}")
            img_content = download_image(img_url)
            
        # 2. Try DuckDuckGo image search
        if not img_content:
            print(f"  -> No Wikipedia image, trying DDG for: {data['name']} campus building")
            img_url = search_ddg_image(f"{data['name']} campus building")
            if img_url:
                print(f"  -> Found DDG image: {img_url}")
                img_content = download_image(img_url)

        # 3. Save image
        if img_content and img_url:
            file_name = img_url.split('/')[-1].split('?')[0] # remove query params
            file_name = urllib.parse.unquote(file_name)
            if not file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                file_name += '.jpg'
            place.image.save(file_name, ContentFile(img_content), save=True)
            print(f"  -> Saved real image.")
        else:
            # Fallback to default
            print(f"  -> No real image found/downloaded. Using default school image.")
            with open(DEFAULT_SCHOOL_IMG, 'rb') as f:
                place.image.save(f"default_school_{int(time.time())}.png", ContentFile(f.read()), save=True)

if __name__ == "__main__":
    populate()
    print("Schools populated successfully!")
