#test_data = {'price': 400}

def validate_price_payload(payload: dict) -> bool:
    if 'price' not in payload:
        raise KeyError("FATAL: 'price' key is missing from the payload.")
        
    price = payload['price']
    
    # Strict type enforcement. No strings allowed.
    if not isinstance(price, (int, float)):
        raise TypeError(f"FATAL: Expected int or float for price, got {type(price).__name__}.")
        
    # Boundary constraints
    if price <= 500:
        raise ValueError(f"ANOMALY: Price ₹{price} is too low. Did we scrape a cable instead of the DAC?")
        
    if price >= 25000:
        raise ValueError(f"ANOMALY: Price ₹{price} is too high. Check extraction logic.")
        
    return True

try:
    if validate_price_payload(test_data):
        print("Data is clean, proceeding to BigQuery.")
except (KeyError, TypeError, ValueError) as e:
    print(f"Triggering Webhook -> Slack Alert: {e}")
