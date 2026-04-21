#!/usr/bin/env python3
"""Test updated API with calendar support"""
import json
import requests

def test_updated_api():
    url = "http://localhost:8000/api/v2/analysis/execute"
    params = {
        "function_id": 97,
        "year": 2025,
        "force_refresh": True  # 強制重新生成
    }
    
    print("Testing updated Season Progress API with calendar...")
    print(f"URL: {url}")
    print(f"Params: {params}\n")
    
    try:
        response = requests.post(url, params=params, timeout=60)
        print(f"Status: {response.status_code}\n")
        
        if response.status_code != 200:
            print(f"ERROR: HTTP {response.status_code}")
            print(response.text[:500])
            return False
        
        data = response.json()
        
        # Save full response
        with open("api_response_with_calendar.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("Full response saved to: api_response_with_calendar.json\n")
        
        # Check calendar in response
        api_data = data.get("data", {})
        
        # Handle double-nesting
        if "data" in api_data:
            inner_data = api_data["data"]
        else:
            inner_data = api_data
        
        calendar = inner_data.get("calendar")
        
        print("=== Calendar Check ===")
        if calendar:
            print("[SUCCESS] Calendar found in API response!")
            print(f"Calendar data: {json.dumps(calendar, indent=2, ensure_ascii=False)}")
            
            # Validate structure
            required_keys = ["completed", "remaining", "total", "next_race"]
            missing = [k for k in required_keys if k not in calendar]
            
            if missing:
                print(f"\n[WARNING] Missing keys: {missing}")
            else:
                print("\n[OK] Calendar structure is complete")
                print(f"  Completed: {calendar['completed']}")
                print(f"  Remaining: {calendar['remaining']}")
                print(f"  Total: {calendar['total']}")
                print(f"  Next race: {calendar['next_race']}")
        else:
            print("[ERROR] Calendar NOT found in API response")
            print(f"Available keys in data: {list(inner_data.keys())}")
            return False
        
        # Test with GUI DataLoader
        print("\n=== GUI Compatibility Test ===")
        from modules.gui.season_progress.season_progress_data_loader import SeasonProgressDataLoader
        
        loader = SeasonProgressDataLoader('2025')
        
        # Simulate MDI processing
        drivers = inner_data.get("drivers", [])
        constructors = inner_data.get("constructors", [])
        metadata = api_data.get("metadata", {})
        
        raw_data = {
            "success": True,
            "data": {
                "drivers": drivers,
                "constructors": constructors,
                "metadata": metadata,
                "calendar": calendar  # Include calendar
            }
        }
        
        display_data = loader._transform_data_for_display(raw_data)
        
        # Save transformed data
        with open("api_transformed_with_calendar.json", "w", encoding="utf-8") as f:
            json.dump(display_data, f, indent=2, ensure_ascii=False)
        print("Transformed data saved to: api_transformed_with_calendar.json")
        
        # Check final calendar
        final_calendar = display_data.get("calendar", {})
        print(f"\nFinal calendar in display data:")
        print(f"  Completed: {final_calendar.get('completed')}")
        print(f"  Remaining: {final_calendar.get('remaining')}")
        print(f"  Total: {final_calendar.get('total')}")
        print(f"  Next race: {final_calendar.get('next_race')}")
        
        if final_calendar.get("total", 0) > 0:
            print("\n[SUCCESS] Calendar data is now available in GUI!")
            return True
        else:
            print("\n[WARNING] Calendar total is still 0")
            return False
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_updated_api()
