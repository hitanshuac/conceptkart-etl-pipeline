import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import json
import re
import os

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

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
        
    if response.url.rstrip('/') == 'https://conceptkart.com':
        raise ValueError(f"FATAL: Product URL redirected to homepage. Product likely removed or URL is invalid: {url}")
        
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
        api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("GROQ_API_KEY")
        if api_key and OpenAI:
            print("WARNING: Standard extractors failed. Falling back to AI Self-Healing scraper...")
            try:
                # Detect if the user provided a Groq key (usually starts with gsk_) to auto-configure
                is_groq = api_key.startswith("gsk_") or os.environ.get("GROQ_API_KEY") == api_key
                base_url = "https://api.groq.com/openai/v1" if is_groq else "https://openrouter.ai/api/v1"
                model_name = "llama3-8b-8192" if is_groq else "meta-llama/llama-3-8b-instruct:free"

                client = OpenAI(
                    base_url=base_url,
                    api_key=api_key,
                )
                
                # Strip excessive whitespace and truncate to save tokens/context limits
                body_text = soup.body.get_text(separator=' ', strip=True) if soup.body else response.text
                truncated_text = body_text[:15000]
                
                system_prompt = "You are a specialized data extractor. Output ONLY valid JSON containing EXACTLY two keys: 'product_name' (string) and 'price_current' (integer). Do not include any markdown formatting or code blocks, just raw JSON."
                
                res = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Extract the product name and current selling price in INR from this webpage text:\n\n{truncated_text}"}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0
                )
                
                content = res.choices[0].message.content
                extracted = json.loads(content)
                
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