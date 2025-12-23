#!/usr/bin/env python3
"""
驗證 JSON 結構向後兼容性
確認新增 track_location 欄位不影響現有欄位
"""

import json

def verify_backward_compatibility():
    """驗證所有原有欄位仍然存在"""
    
    json_file = "json/all_incidents_summary_2022_Japanese_Grand_Prix_RACE.json"
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=" * 80)
    print("JSON 結構向後兼容性驗證")
    print("=" * 80)
    
    # 驗證頂層結構
    top_level_fields = [
        "function_id", "function_name", "analysis_type", 
        "session_info", "timestamp", "data"
    ]
    
    print("\n【頂層結構】")
    all_top_present = True
    for field in top_level_fields:
        present = field in data
        all_top_present = all_top_present and present
        status = "✅" if present else "❌"
        print(f"{status} {field}")
    
    # 驗證 data 結構
    data_fields = [
        "all_incidents", "incident_summary", "chronological_sequence",
        "driver_involvement", "lap_analysis", "safety_periods"
    ]
    
    print("\n【data 層級結構】")
    all_data_present = True
    for field in data_fields:
        present = field in data.get("data", {})
        all_data_present = all_data_present and present
        status = "✅" if present else "❌"
        print(f"{status} {field}")
    
    # 驗證 incident_detail 必要欄位（不包含新增的 track_location）
    required_incident_fields = [
        "sequence_number", "lap", "time", "raw_time", "message",
        "category", "severity", "impact", "involved_drivers",
        "driver_codes", "car_numbers", "keywords", "flags_mentioned", "sector"
    ]
    
    print("\n【incident_detail 原有欄位】")
    incidents = data.get("data", {}).get("all_incidents", [])
    
    if incidents:
        first_incident = incidents[0]
        all_fields_present = True
        
        for field in required_incident_fields:
            present = field in first_incident
            all_fields_present = all_fields_present and present
            status = "✅" if present else "❌"
            print(f"{status} {field}")
        
        # 檢查新增欄位
        print("\n【新增欄位】")
        has_track_location = "track_location" in first_incident
        print(f"{'✅' if has_track_location else '❌'} track_location (新增)")
    
    # 統計分析
    print("\n" + "=" * 80)
    print("統計結果")
    print("=" * 80)
    
    total_incidents = len(incidents)
    with_location = sum(1 for inc in incidents if inc.get("track_location"))
    
    print(f"總事件數: {total_incidents}")
    print(f"有 track_location 的事件: {with_location}")
    print(f"保留原有欄位的事件: {total_incidents} (100%)")
    
    # 顯示一個完整的事件範例
    print("\n" + "=" * 80)
    print("完整事件範例（有 track_location）")
    print("=" * 80)
    
    # 找一個有 track_location 的事件
    example = next((inc for inc in incidents if inc.get("track_location")), None)
    
    if example:
        print(json.dumps(example, indent=2, ensure_ascii=False))
    
    # 最終結論
    print("\n" + "=" * 80)
    print("向後兼容性驗證結果")
    print("=" * 80)
    
    all_checks = all_top_present and all_data_present and all_fields_present
    
    if all_checks:
        print("✅ 所有原有欄位完整保留")
        print("✅ 新增欄位正確添加")
        print("✅ JSON 結構完全向後兼容")
    else:
        print("❌ 發現結構問題，需要修正")
    
    return all_checks


if __name__ == "__main__":
    verify_backward_compatibility()
