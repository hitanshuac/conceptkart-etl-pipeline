def validate_price_payload(payload: dict, target_price: int = None) -> tuple[bool, bool]:
    """
    Validates the payload and checks if the target price is hit.
    Returns: (is_valid, is_target_hit)
    """
    if 'price_current' not in payload:
        raise KeyError("FATAL: 'price_current' key is missing from the payload.")
        
    price = payload['price_current']
    
    # Strict type enforcement. No strings allowed.
    if not isinstance(price, (int, float)):
        raise TypeError(f"FATAL: Expected int or float for price, got {type(price).__name__}.")
        
    # Boundary constraints
    if price <= 100:
        raise ValueError(f"ANOMALY: Price ₹{price} is too low. Did we scrape a cable instead of the IEM?")
        
    if price >= 500000:
        raise ValueError(f"ANOMALY: Price ₹{price} is too high. Check extraction logic.")
        
    is_target_hit = False
    if target_price and price <= target_price:
        is_target_hit = True
        
    return True, is_target_hit

if __name__ == "__main__":
    test_data = {'price_current': 1500}
    try:
        valid, hit = validate_price_payload(test_data, 2000)
        print(f"Valid: {valid}, Target Hit: {hit}")
    except Exception as e:
        print(f"Error: {e}")
