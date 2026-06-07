from unittest.mock import patch, MagicMock
from load_data import load_to_database

@patch("load_data.get_supabase_client")
def test_db_idempotent_upsert(mock_get_client):
    """
    Test that successful DB operations use upsert for idempotency.
    """
    mock_supabase = MagicMock()
    mock_get_client.return_value = mock_supabase
    
    payload = {"price_current": 15000}
    product_id = 1
    
    load_to_database(payload, product_id)
    
    # Verify upsert is called on raw_daily_prices
    mock_supabase.table.assert_any_call("raw_daily_prices")
    mock_supabase.table().upsert.assert_called_once()
    
    # Verify the payload structure passed to upsert
    call_args = mock_supabase.table().upsert.call_args[0][0]
    assert call_args["tracked_product_id"] == 1
    assert call_args["price_current"] == 15000

@patch("load_data.get_supabase_client")
@patch("load_data._quarantine_record")
def test_dlq_store_and_forward(mock_quarantine, mock_get_client):
    """
    Test that network failures trigger the Parquet DLQ store-and-forward.
    """
    mock_supabase = MagicMock()
    # Simulate a network error during upsert
    mock_supabase.table().upsert().execute.side_effect = Exception("Supabase connection refused")
    mock_get_client.return_value = mock_supabase
    
    payload = {"price_current": 15000}
    product_id = 1
    
    load_to_database(payload, product_id)
    
    # Verify that the fallback DLQ was invoked instead of crashing
    mock_quarantine.assert_called_once()
    args, _ = mock_quarantine.call_args
    assert args[0]["price_current"] == 15000
    assert args[1] == "SupabaseUploadFailed"
