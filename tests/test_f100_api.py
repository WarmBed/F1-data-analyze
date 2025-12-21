import requests
import json

print("=" * 60)
print("Testing API Function 100 - Historical Flags Analysis")
print("=" * 60)

try:
    response = requests.post(
        "http://localhost:8000/analyze",
        json={"function_id": "100", "race": "Bahrain Grand Prix"},
        timeout=120
    )
    
    print(f"Status Code: {response.status_code}")
    result = response.json()
    
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message')}")
    
    if result.get("data"):
        print("\n=== DATA STRUCTURE ===")
        data = result["data"]
        print(f"Top-level keys: {list(data.keys())}")
        
        if "metadata" in data:
            print("\n--- Metadata ---")
            metadata = data["metadata"]
            print(f"  years_analyzed: {metadata.get('years_analyzed')}")
            print(f"  total_years: {metadata.get('total_years')}")
        
        if "yearly_summary" in data:
            print("\n--- Yearly Summary ---")
            years = list(data["yearly_summary"].keys())
            print(f"  Years: {years}")
        
        if "trends" in data:
            print("\n--- Trends ---")
            trends = data["trends"]
            print(f"  Keys: {list(trends.keys())}")
            if "average_flags_per_year" in trends:
                print("  WARNING: average_flags_per_year still exists!")
            else:
                print("  OK: average_flags_per_year removed")
    else:
        print("\nNo data in response")
        
except requests.exceptions.ConnectionError:
    print("ERROR: Cannot connect to API at http://localhost:8000")
except Exception as e:
    print(f"ERROR: {e}")
