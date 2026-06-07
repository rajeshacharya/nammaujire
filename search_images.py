import urllib.request
import urllib.parse
import re
import json

def search_ddg_image(query):
    try:
        # First get the vqd token
        req = urllib.request.Request(
            f"https://duckduckgo.com/?q={urllib.parse.quote(query)}",
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            vqd_match = re.search(r'vqd=([\d-]+)', html)
            if not vqd_match:
                return None
            vqd = vqd_match.group(1)
            
        # Now search images
        img_url = f"https://duckduckgo.com/i.js?l=us-en&o=json&q={urllib.parse.quote(query)}&vqd={vqd}&f=,,,type:photo,,&p=1"
        req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            if 'results' in data and len(data['results']) > 0:
                for res in data['results']:
                    url = res['image']
                    if 'wikipedia' not in url.lower(): # Prefer non-wiki if possible, or just take first
                        return url
                return data['results'][0]['image']
    except Exception as e:
        print(f"Failed for {query}: {e}")
    return None

queries = [
    'SDM Institute of Technology Ujire campus building',
    'SDM College of Naturopathy and Yogic Sciences campus',
    'SDM Pre-University College Ujire',
    'Anugraha PU College Ujire campus',
    'SDM College of Education Ujire',
    'Prasanna First Grade College Belthangady',
    'Prasanna College of Nursing Ujire',
    'SDM English Medium School Ujire',
    'Anugraha English Medium School Ujire',
    'Government High School Ujire'
]

for q in queries:
    print(f"{q}: {search_ddg_image(q)}")
