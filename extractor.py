import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import json
import re
import os
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

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
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key and genai:
            print("WARNING: Standard extractors failed. Falling back to AI Self-Healing scraper...")
            try:
                client = genai.Client(api_key=api_key)
                
                # Strip excessive whitespace and truncate to save tokens
                body_text = soup.body.get_text(separator=' ', strip=True) if soup.body else response.text
                prompt = "Extract the current selling price (as an integer in INR, without currency symbols) and the product name from the following webpage text."
                
                res = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[prompt, body_text[:30000]],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema={
                            "type": "OBJECT",
                            "properties": {
                                "product_name": {"type": "STRING", "description": "The name of the product"},
                                "price_current": {"type": "INTEGER", "description": "The current selling price as an integer"}
                            },
                            "required": ["product_name", "price_current"]
                        },
                        temperature=0.0
                    )
                )
                
                extracted = json.loads(res.text)
                price_current = extracted.get('price_current', 0)
                product_name = extracted.get('product_name', product_name)
                
                if price_current > 0:
                    print(f"SUCCESS: AI successfully recovered data. Product: {product_name}, Price: Rs.{price_current}")
            except Exception as ai_e:
                print(f"AI Scraper Fallback failed: {ai_e}")

    if price_current == 0:
        raise ValueError(f"FATAL: Could not extract price from {url} even with AI fallback.")

    return {
        'product_name': product_name,
        'vendor_name': 'ConceptKart',
        'vendor_url': url,
        'price_current': price_current,
        'scraped_at_utc': datetime.now(timezone.utc).isoformat()
    }