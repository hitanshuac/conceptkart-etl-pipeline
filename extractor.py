from datetime import datetime, timezone

def scrape_conceptkart():
    print("MOCK SCRAPER: Simulating web extraction...")
    
    # We are faking the web scrape for right now to test the pipes
    mock_data = {
        'product_name': 'Shanling EH1',
        'vendor_name': 'ConceptKart',
        'vendor_url': 'https://conceptkart.com/products/shanling-eh1',
        'price_current': 16990,
        'scraped_at_utc': datetime.now(timezone.utc).isoformat()
    }
    
    return mock_data