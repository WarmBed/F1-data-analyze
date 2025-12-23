"""測試 Parts Analysis Widget 的欄位映射修正"""
import json
from pathlib import Path

def test_json_fields():
    """測試 JSON 欄位是否正確"""
    json_file = Path("json/fia_parts_analysis_2025.json")
    
    if not json_file.exists():
        print("❌ 找不到 JSON 檔案")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not data.get("records"):
        print("❌ JSON 沒有 records 欄位")
        return
    
    print("=" * 70)
    print("✅ JSON 結構驗證")
    print("=" * 70)
    
    # 檢查第一筆記錄的欄位
    first_record = data["records"][0]
    print("\n📋 第一筆記錄的欄位名稱:")
    for key in first_record.keys():
        print(f"  - {key}: {first_record[key]}")
    
    # 驗證關鍵欄位
    print("\n🔍 關鍵欄位驗證:")
    required_fields = ["賽事", "賽事日期", "車隊", "車手", "部件", "變更類型", "主分類", "子分類"]
    missing_fields = []
    
    for field in required_fields:
        if field in first_record:
            value = first_record[field]
            print(f"  ✅ '{field}': '{value}'")
        else:
            print(f"  ❌ '{field}': 缺少")
            missing_fields.append(field)
    
    if missing_fields:
        print(f"\n⚠️  缺少的欄位: {', '.join(missing_fields)}")
    else:
        print(f"\n✅ 所有關鍵欄位都存在")
    
    # 檢查噪音記錄
    print("\n🔍 噪音記錄檢查:")
    noise_records = [r for r in data["records"] if "噪音" in r.get("變更類型", "") or "Noise" in r.get("變更類型", "").upper()]
    print(f"  噪音記錄數: {len(noise_records)} 筆")
    
    if noise_records:
        print(f"  ⚠️  發現噪音記錄，GUI 應該過濾掉:")
        for i, r in enumerate(noise_records[:5], 1):
            print(f"    {i}. {r.get('部件', '')} - {r.get('變更類型', '')}")
    else:
        print(f"  ✅ 沒有噪音記錄")
    
    # 統計賽事分佈
    print("\n📊 賽事分佈 (前 10):")
    race_counts = {}
    for r in data["records"]:
        race = r.get("賽事", "")
        if race:
            race_counts[race] = race_counts.get(race, 0) + 1
    
    for race, count in sorted(race_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {race}: {count} 筆")
    
    # GUI 欄位映射測試
    print("\n" + "=" * 70)
    print("🔧 GUI 欄位映射測試")
    print("=" * 70)
    
    gui_field_mapping = {
        "賽事": "record.get('賽事', '')",  # ✅ 正確
        "賽事日期": "record.get('賽事日期', '')",  # ✅ 正確
        "車隊": "record.get('車隊', '')",
        "車手": "record.get('車手', '')",
        "部件": "record.get('部件', '')",
        "變更類型": "record.get('變更類型', '')",
        "主分類": "record.get('主分類', '')",
        "子分類": "record.get('子分類', '')",
    }
    
    print("\n✅ GUI 應使用的欄位映射:")
    for field_name, code in gui_field_mapping.items():
        value = first_record.get(field_name, "❌ 欄位不存在")
        print(f"  {code:35s} # {value}")
    
    # 錯誤映射警告
    print("\n⚠️  已修正的錯誤映射:")
    wrong_mappings = {
        "record.get('比賽', '')": "❌ 錯誤 → 應改為 record.get('賽事', '')",
        "record.get('日期', '')": "❌ 錯誤 → 應改為 record.get('賽事日期', '')",
    }
    
    for wrong, correct in wrong_mappings.items():
        print(f"  {wrong:35s} {correct}")

if __name__ == "__main__":
    test_json_fields()
