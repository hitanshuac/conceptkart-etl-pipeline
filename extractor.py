import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import json
import re

def scrape_conceptkart(url: str = None) -> dict:
    if not url:
        # Fallback URL for testing if none is provided
        url = 'https://conceptkart.com/products/shanling-eh1'
        
    print(f"SCRAPING: Fetching data from {url}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"WARNING: Failed to retrieve page (Status code: {response.status_code}). Using mock data for testing.")
        return {
            'product_name': 'Mock IEM (Fallback Data)',
            'vendor_name': 'ConceptKart',
            'vendor_url': url,
            'price_current': 1500,
            'scraped_at_utc': datetime.now(timezone.utc).isoformat()
        }
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Try to extract from Open Graph meta tags (common in Shopify)
    title_meta = soup.find('meta', property='og:title')
    price_meta = soup.find('meta', property='og:price:amount')
    
    product_name = title_meta['content'] if title_meta else 'Unknown Product'
    price_current = 0
    
    if price_meta and price_meta.get('content'):
        try:
            price_current = int(float(price_meta['content']))
        except ValueError:
            pass
            
    # Fallback if meta tags are missing: look for price in JSON-LD or standard classes
    if price_current == 0:
        # Search for Shopify product JSON
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if '@type' in data and data['@type'] == 'Product':
                    if 'offers' in data and 'price' in data['offers']:
                        price_current = int(float(data['offers']['price']))
                        product_name = data.get('name', product_name)
                        break
            except (json.JSONDecodeError, TypeError, KeyError):
                continue
                
    # Final fallback for Conceptkart specifically (class names)
    if price_current == 0:
        price_elem = soup.find(class_=re.compile(r'price-item--regular|price__regular'))
        if price_elem:
            price_text = price_elem.text.strip().replace('Rs.', '').replace(',', '').replace('₹', '')
            try:
                price_current = int(float(price_text))
            except ValueError:
                pass

    if price_current == 0:
        raise ValueError(f"FATAL: Could not extract price from {url}")

    return {
        'product_name': product_name,
        'vendor_name': 'ConceptKart',
        'vendor_url': url,
        'price_current': price_current,
        'scraped_at_utc': datetime.now(timezone.utc).isoformat()
    }