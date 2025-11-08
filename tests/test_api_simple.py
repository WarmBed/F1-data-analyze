#!/usr/bin/env python3
"""Simple API test for Season Progress"""
import json
import requests
import sys

def test_api():
    url = "https://api.f1telemetrystationpro.org/api/v2/analysis/execute"
    params = {"function_id": 97, "year": 2025}
    
    print("Testing Season Progress API...")
    print(f"URL: {url}")
    print(f"Params: {params}\n")
    
    try:
        response = requests.post(url, params=params, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"ERROR: HTTP {response.status_code}")
            return False
        
        data = response.json()
        
        # Save response
        with open("api_response_raw.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("Raw response saved to: api_response_raw.json")
        
        # Check structure
        print(f"\nSuccess: {data.get('success')}")
        print(f"Message: {data.get('message')}")
        
        api_data = data.get("data", {})
        print(f"\nAPI data keys: {list(api_data.keys())}")
        
        # Detect nesting
        if "data" in api_data:
            inner_data = api_data["data"]
            drivers = inner_data.get("drivers", [])
            constructors = inner_data.get("constructors", [])
            metadata = api_data.get("metadata", {})
            print(f"Structure: Double-nested (data.data)")
        else:
            drivers = api_data.get("drivers", [])
            constructors = api_data.get("constructors", [])
            metadata = api_data.get("metadata", {})
            print(f"Structure: Single-layer")
        
        print(f"\nDrivers: {len(drivers)}")
        print(f"Constructors: {len(constructors)}")
        print(f"Season year: {metadata.get('season_year')}")
        print(f"Round: {metadata.get('resolved_round')}")
        
        if drivers:
            first = drivers[0]
            print(f"\nFirst driver:")
            print(f"  Name: {first.get('driver', {}).get('full_name')}")
            print(f"  Points: {first.get('points')}")
            print(f"  Team: {first.get('constructors', [{}])[0].get('name')}")
        
        # Test transform
        print("\n--- Testing DataLoader Transform ---")
        from modules.gui.season_progress.season_progress_data_loader import SeasonProgressDataLoader
        
        loader = SeasonProgressDataLoader('2025')
        raw_for_transform = {
            "success": True,
            "data": {
                "drivers": drivers,
                "constructors": constructors,
                "metadata": metadata
            }
        }
        
        display_data = loader._transform_data_for_display(raw_for_transform)
        
        # Save transformed data
        with open("api_response_transformed.json", "w", encoding="utf-8") as f:
            json.dump(display_data, f, indent=2, ensure_ascii=False)
        print("Transformed data saved to: api_response_transformed.json")
        
        print(f"\nTransformed keys: {list(display_data.keys())}")
        print(f"Season year: {display_data.get('season_year')}")
        print(f"Round: {display_data.get('round')}")
        
        leaders = display_data.get('leaders', {})
        print(f"\nLeaders:")
        print(f"  Driver: {leaders.get('driver')}")
        print(f"  Constructor: {leaders.get('constructor')}")
        
        calendar = display_data.get('calendar', {})
        print(f"\nCalendar:")
        print(f"  Completed: {calendar.get('completed')}")
        print(f"  Remaining: {calendar.get('remaining')}")
        print(f"  Next race: {calendar.get('next_race')}")
        
        print("\n[SUCCESS] API is compatible with Season Progress GUI!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)
