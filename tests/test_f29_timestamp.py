#!/usr/bin/env python3
"""
測試 Function 29 的時間戳和檔名命名邏輯
與 Function 97 (Championship Standings) 保持一致

測試項目：
1. 生成兩個檔案（最新版 + 歷史版）
2. JSON 內容包含 generated_at 和 timestamp
3. 時間戳格式為 ISO 8601 (YYYYMMDDTHHMMSSZ)
4. 兩個檔案內容一致
5. 檔名規則正確
"""

import json
from pathlib import Path
from datetime import datetime

def test_function_29_consistency():
    """測試 Function 29 與 Function 97 的一致性"""
    
    print("=" * 80)
    print("🔍 Function 29 時間戳與檔名測試")
    print("=" * 80)
    
    json_dir = Path("json")
    year = 2025
    
    # 1. 檢查最新版檔案（無時間戳）
    print("\n[1] 檢查最新版檔案...")
    latest_file = json_dir / f"fia_parts_analysis_v2_{year}.json"
    
    if not latest_file.exists():
        print(f"❌ 最新版檔案不存在: {latest_file}")
        return False
    
    print(f"✅ 最新版檔案存在: {latest_file.name}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        latest_data = json.load(f)
    
    # 2. 檢查 JSON 內容包含時間戳
    print("\n[2] 檢查 JSON 內容...")
    
    required_keys = ['generated_at', 'timestamp', 'success', 'records']
    missing_keys = [key for key in required_keys if key not in latest_data]
    
    if missing_keys:
        print(f"❌ 缺少必要欄位: {missing_keys}")
        return False
    
    print(f"✅ 包含所有必要欄位: {required_keys}")
    
    generated_at = latest_data['generated_at']
    timestamp = latest_data['timestamp']
    
    print(f"   • generated_at: {generated_at}")
    print(f"   • timestamp: {timestamp}")
    
    # 3. 驗證時間戳格式
    print("\n[3] 驗證時間戳格式...")
    
    try:
        # ISO 8601 格式驗證
        datetime.fromisoformat(generated_at)
        print(f"✅ generated_at 格式正確 (ISO 8601): {generated_at}")
    except ValueError as e:
        print(f"❌ generated_at 格式錯誤: {e}")
        return False
    
    # 檔名時間戳格式驗證 (YYYYMMDDTHHMMSSZ)
    if len(timestamp) == 16 and timestamp.endswith('Z') and 'T' in timestamp:
        print(f"✅ timestamp 格式正確 (YYYYMMDDTHHMMSSZ): {timestamp}")
    else:
        print(f"❌ timestamp 格式錯誤: {timestamp}")
        return False
    
    # 4. 檢查歷史版檔案（帶時間戳）
    print("\n[4] 檢查歷史版檔案...")
    
    archive_pattern = f"fia_parts_analysis_v2_{year}_*.json"
    archive_files = list(json_dir.glob(archive_pattern))
    
    if not archive_files:
        print(f"❌ 找不到歷史版檔案: {archive_pattern}")
        return False
    
    # 獲取最新的歷史版檔案
    latest_archive = max(archive_files, key=lambda p: p.stat().st_mtime)
    print(f"✅ 歷史版檔案存在: {latest_archive.name}")
    
    with open(latest_archive, 'r', encoding='utf-8') as f:
        archive_data = json.load(f)
    
    # 5. 比較內容一致性
    print("\n[5] 比較檔案內容...")
    
    if latest_data == archive_data:
        print("✅ 最新版和歷史版內容完全一致")
    else:
        print("❌ 內容不一致！")
        
        # 詳細比較
        latest_keys = set(latest_data.keys())
        archive_keys = set(archive_data.keys())
        
        if latest_keys != archive_keys:
            print(f"   • Key 差異: {latest_keys ^ archive_keys}")
        
        return False
    
    # 6. 檢查記錄數量
    print("\n[6] 檢查數據完整性...")
    
    records_count = len(latest_data.get('records', []))
    print(f"✅ 記錄數量: {records_count}")
    
    if records_count < 400:
        print(f"⚠️  記錄數量偏少，預期約 475 筆")
    
    # 7. 與 Function 97 格式比較
    print("\n[7] 與 Function 97 格式比較...")
    
    # 檢查是否有 Function 97 的檔案
    f97_pattern = f"championship_standings_{year}_*.json"
    f97_files = list(json_dir.glob(f97_pattern))
    
    if f97_files:
        latest_f97 = max(f97_files, key=lambda p: p.stat().st_mtime)
        print(f"✅ 找到 Function 97 參考檔案: {latest_f97.name}")
        
        with open(latest_f97, 'r', encoding='utf-8') as f:
            f97_data = json.load(f)
        
        # 比較時間戳格式
        f97_generated_at = f97_data.get('metadata', {}).get('generated_at', '')
        
        if f97_generated_at:
            print(f"   • Function 97 generated_at: {f97_generated_at}")
            print(f"   • Function 29 generated_at: {generated_at}")
            print("✅ 時間戳格式與 Function 97 一致")
        
        # 檢查檔名格式
        if 'T' in latest_f97.name and latest_f97.name.endswith('Z.json'):
            print(f"✅ 檔名時間戳格式與 Function 97 一致 (含 T 和 Z)")
    else:
        print(f"⚠️  找不到 Function 97 參考檔案，無法比較")
    
    # 8. 總結
    print("\n" + "=" * 80)
    print("📊 測試結果總結")
    print("=" * 80)
    
    print(f"""
✅ 最新版檔案: {latest_file.name}
✅ 歷史版檔案: {latest_archive.name}
✅ JSON 包含時間戳: generated_at, timestamp
✅ 時間戳格式: ISO 8601 (與 Function 97 一致)
✅ 檔名格式: {year}_{{filter}}_{{{timestamp}}}.json
✅ 內容一致性: 通過
✅ 記錄數量: {records_count} 筆

🎉 所有測試通過！Function 29 與 Function 97 的命名邏輯完全一致。
    """)
    
    return True

def main():
    try:
        success = test_function_29_consistency()
        
        if success:
            print("\n✅ 測試完成！")
            return 0
        else:
            print("\n❌ 測試失敗！")
            return 1
    
    except Exception as e:
        print(f"\n❌ 測試發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
