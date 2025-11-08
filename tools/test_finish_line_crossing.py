"""
測試跨越終點線的賽道（Japan, Spain, Bahrain）

此腳本會：
1. 生成指定賽道的數據
2. 檢查是否正確處理跨越終點線
3. 驗證加速度數據是否合理
"""

import subprocess
import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_track(year: int, race: str, session: str):
    """測試單一賽道"""
    print(f"\n{'='*80}")
    print(f"🧪 測試賽道: {race} ({year} {session})")
    print(f"{'='*80}\n")
    
    # 執行 CLI 生成數據
    print(f"⏳ 生成數據...")
    cmd = [
        "python", "f1_analysis_modular_main.py",
        "-f", "48",
        "-y", str(year),
        "-r", race,
        "-s", session,
        "--force"
    ]
    
    result = subprocess.run(
        cmd,
        cwd=project_root,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    
    # 檢查輸出中的關鍵信息
    output = result.stdout + result.stderr
    
    print("\n📊 關鍵信息:")
    print("-" * 80)
    
    # 檢查是否使用硬編碼起點
    if "使用硬編碼起點" in output:
        print("✅ 使用硬編碼起點")
    elif "使用公式計算起點" in output:
        print("⚠️  使用公式計算起點（建議添加硬編碼值）")
    
    # 檢查是否檢測到跨越終點線
    if "檢測到跨越終點線" in output:
        print("🔄 檢測到跨越終點線")
    
    # 檢查是否合併下一圈數據
    if "已合併下一圈數據" in output:
        print("✅ 已合併下一圈數據")
    
    # 檢查錯誤
    if "ERROR" in output or "Exception" in output:
        print("❌ 發現錯誤:")
        for line in output.split('\n'):
            if "ERROR" in line or "Exception" in line:
                print(f"   {line.strip()}")
    
    # 檢查是否成功生成 JSON
    json_pattern = f"all_drivers_straight_line_speed_{year}_{race}_{session}*.json"
    json_files = list((project_root / "json").glob(json_pattern))
    
    if json_files:
        latest_json = sorted(json_files)[-1]
        print(f"✅ JSON 已生成: {latest_json.name}")
        
        # 快速檢查 JSON 內容
        import json
        try:
            with open(latest_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            driver_speeds = data.get('data', {}).get('driver_speeds', [])
            if driver_speeds:
                print(f"📈 車手數量: {len(driver_speeds)}")
                
                # 檢查前 3 位車手的加速度
                print("\n前 3 位車手的加速度:")
                for i, driver_data in enumerate(driver_speeds[:3]):
                    driver = driver_data.get('driver', 'N/A')
                    accel = driver_data.get('avg_acceleration_100_300_ms2', 'N/A')
                    accel_time = driver_data.get('acceleration_time_100_300_seconds', 'N/A')
                    print(f"  {i+1}. {driver:3s}: {accel} m/s² ({accel_time}s)")
        except Exception as e:
            print(f"⚠️  無法讀取 JSON: {e}")
    else:
        print(f"❌ 未找到 JSON 檔案")
    
    print()

def main():
    """測試跨越終點線的賽道"""
    print("\n" + "=" * 80)
    print("🏁 跨越終點線賽道測試")
    print("=" * 80)
    
    # 測試賽道列表（已知跨越終點線的賽道）
    test_tracks = [
        # (year, race, session, description)
        (2025, "Japan", "Q", "日本站排位賽（5650m → 529m）"),
        # (2025, "Spain", "R", "西班牙站正賽（4333m → 589m）"),
        # (2025, "Bahrain", "R", "巴林站正賽（4850m → 510m）"),
        # (2025, "Austria", "R", "奧地利站正賽（4857m → 160m）"),
    ]
    
    print("\n測試賽道:")
    for i, (year, race, session, desc) in enumerate(test_tracks, 1):
        print(f"  {i}. {desc}")
    
    print("\n開始測試...\n")
    
    for year, race, session, desc in test_tracks:
        test_track(year, race, session)
    
    print("=" * 80)
    print("✅ 測試完成")
    print("=" * 80)
    print()

if __name__ == "__main__":
    main()
