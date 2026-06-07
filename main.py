"""
Pipeline orchestrator — main entry point for the ETL pipeline.

Fetches tracked products from Supabase, groups them by domain
to enforce rate limits, runs the extraction cascade for each,
validates, loads, and notifies.

This replaces the original flat main.py with domain-aware
orchestration and full observability.
"""

import time
from urllib.parse import urlparse

import db_setup
import extractor
import price_check
import load_data
import notifier

from load_data import get_supabase_client
from src.stealth.fingerprints import get_random_delay
from src.sites.registry import get_site_config
from src.observability.logger import log_error, get_recent_errors


def get_tracked_products():
    """Fetch active tracked products from Supabase."""
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("tracked_products")
            .select("id, url, target_price")
            .eq("is_active", True)
            .execute()
        )
        return [(item["id"], item["url"], item["target_price"]) for item in response.data]
    except Exception as e:
        print(f"Error fetching from Supabase: {e}")
        log_error(e, component="main.get_tracked_products")
        return []

def retry_failed_uploads():
    """Store-and-Forward: Retry failed Supabase inserts from the DLQ."""
    import os
    import ast
    try:
        import pyarrow.parquet as pq
    except ImportError:
        return
        
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    if not os.path.exists(data_dir):
        return
        
    for filename in os.listdir(data_dir):
        if filename.startswith("quarantine_") and filename.endswith(".parquet"):
            filepath = os.path.join(data_dir, filename)
            try:
                table = pq.read_table(filepath)
                error_types = table.column("error_type").to_pylist()
                payloads = table.column("raw_payload").to_pylist()
                
                retried = 0
                for err, payload_str in zip(error_types, payloads):
                    if err == 'SupabaseUploadFailed':
                        try:
                            payload = ast.literal_eval(payload_str)
                            product_id = payload.get('tracked_product_id')
                            if product_id:
                                # Supabase client is idempotent now (upsert)
                                load_data.load_to_database(payload, product_id)
                                retried += 1
                        except Exception as e:
                            print(f"  [DLQ] Retry failed: {e}")
                
                if retried > 0:
                    print(f"  [DLQ] Successfully replayed {retried} uploads from {filename}")
                    # In a fully-fledged system, we would remove the replayed rows here.
                    
            except Exception as e:
                print(f"  [DLQ] Error reading {filename}: {e}")



def main():
    print("\n--- STARTING ETL PIPELINE ---")

    # Step 1: Pre-execution error log check (per error-observability.md)
    recent_errors = get_recent_errors(limit=5)
    if recent_errors:
        unresolved = [e for e in recent_errors if e.get("status") == "UNRESOLVED"]
        if unresolved:
            print(f"  [WARN] {len(unresolved)} unresolved errors in history. Review data/error_logs.json.")

    try:
        # Step 1.5: Retry failed DB uploads (Store-and-Forward)
        retry_failed_uploads()

        # Step 2: Infrastructure check
        db_setup.create_table()

        # Step 3: Get targets
        products = get_tracked_products()
        if not products:
            print("No active products to track. Exiting.")
            return

        # Step 4: Group products by domain for rate limiting
        domain_groups: dict[str, list[tuple]] = {}
        for prod_id, target_url, target_price in products:
            domain = urlparse(target_url).netloc.replace("www.", "")
            domain_groups.setdefault(domain, []).append((prod_id, target_url, target_price))

        print(f"  Tracking {len(products)} products across {len(domain_groups)} domains.\n")

        # Step 5: Process each domain group with rate limiting
        success_count = 0
        fail_count = 0

        for domain, group in domain_groups.items():
            site_config = get_site_config(domain)
            print(f"--- Domain: {domain} ({len(group)} products, rate limit: {site_config.rate_limit_seconds}s) ---")

            for i, (prod_id, target_url, target_price) in enumerate(group):
                print(f"\n  [{prod_id}] {target_url} (Target: Rs.{target_price})")

                try:
                    # Extract via cascade
                    raw_data = extractor.scrape_conceptkart(target_url)

                    # Validate
                    is_valid, is_target_hit = price_check.validate_price_payload(
                        raw_data, target_price
                    )

                    if is_valid:
                        print(f"  Validation passed. Rs.{raw_data['price_current']}. Loading...")

                        # Load to Supabase
                        load_data.load_to_database(raw_data, prod_id)
                        success_count += 1

                        # Notify if target price hit
                        if is_target_hit:
                            notifier.notify_price_drop(
                                raw_data["product_name"],
                                raw_data["price_current"],
                                raw_data["vendor_url"],
                            )
                        else:
                            print("  Target price not hit. No notification sent.")

                except Exception as e:
                    fail_count += 1
                    print(f"  ERROR processing product {prod_id}: {e}")
                    log_error(
                        e,
                        component="main.process_product",
                        domain=domain,
                        context={"product_id": prod_id, "url": target_url},
                    )

                # Rate limiting: delay between requests to the same domain
                if i < len(group) - 1:
                    delay = get_random_delay(site_config.rate_limit_seconds)
                    print(f"  (rate limit: sleeping {delay:.1f}s)")
                    time.sleep(delay)

        # Step 6: Pipeline summary
        print(f"\n--- PIPELINE COMPLETED ---")
        print(f"  [SUCCESS] Succeeded: {success_count}")
        print(f"  [FAIL] Failed: {fail_count}")
        print(f"  Total: {success_count + fail_count}")

    except Exception as e:
        print(f"PIPELINE FAILED: {e}")
        log_error(e, component="main.pipeline")


if __name__ == "__main__":
    main()