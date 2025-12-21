"""
測試 CLI -f13 時間序列提取功能
執行雙車手遙測比較並驗證 JSON 輸出是否包含 time_seconds
"""
import subprocess
import json
import glob
import os
from datetime import datetime

print("=" * 80)
print("🧪 測試 CLI -f13 時間序列提取功能")
print("=" * 80)

# 執行 CLI 命令
print("\n🚀 執行命令: python f1_analysis_modular_main.py -f 13 -y 2024 -r Japan -s R -d VER -d2 LEC")
print("-" * 80)

try:
    result = subprocess.run(
        ["python", "f1_analysis_modular_main.py", "-f", "13", "-y", "2024", "-r", "Japan", "-s", "R", "-d", "VER", "-d2", "LEC"],
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=120
    )
    
    print("\n📋 CLI 輸出:")
    print(result.stdout)
    
    if result.stderr:
        print("\n⚠️  CLI 錯誤輸出:")
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"\n❌ CLI 執行失敗，返回碼: {result.returncode}")
        exit(1)
    
    print(f"\n✅ CLI 執行成功，返回碼: {result.returncode}")
    
except subprocess.TimeoutExpired:
    print("\n❌ CLI 執行超時（120秒）")
    exit(1)
except Exception as e:
    print(f"\n❌ CLI 執行異常: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# 查找生成的 JSON 檔案
print("\n" + "=" * 80)
print("🔍 查找生成的 JSON 檔案")
print("=" * 80)

json_pattern = "json/comparison_telemetry_VER_LEC_2024_Japan_R_*.json"
json_files = sorted(glob.glob(json_pattern), key=os.path.getmtime, reverse=True)

if not json_files:
    print(f"\n❌ 找不到 JSON 檔案，匹配模式: {json_pattern}")
    exit(1)

latest_json = json_files[0]
file_size = os.path.getsize(latest_json) / 1024  # KB
file_time = datetime.fromtimestamp(os.path.getmtime(latest_json)).strftime("%Y-%m-%d %H:%M:%S")

print(f"\n✅ 找到最新 JSON 檔案:")
print(f"   檔案: {latest_json}")
print(f"   大小: {file_size:.2f} KB")
print(f"   時間: {file_time}")

# 讀取 JSON 檔案
print("\n" + "=" * 80)
print("📖 讀取 JSON 檔案")
print("=" * 80)

try:
    with open(latest_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n✅ JSON 檔案讀取成功")
    print(f"   頂層鍵: {list(data.keys())}")
    
except Exception as e:
    print(f"\n❌ JSON 讀取失敗: {e}")
    exit(1)

# 檢查 time_series 結構
print("\n" + "=" * 80)
print("🔍 驗證 time_series 結構")
print("=" * 80)

if 'time_series' not in data:
    print("\n❌ JSON 中沒有 'time_series' 欄位")
    exit(1)

time_series = data['time_series']
print(f"\n✅ 找到 time_series 欄位")
print(f"   時間序列鍵: {list(time_series.keys())}")

# 檢查 driver1 和 driver2
for driver_key in ['driver1', 'driver2']:
    if driver_key not in time_series:
        print(f"\n❌ time_series 中沒有 '{driver_key}' 欄位")
        exit(1)
    
    driver_data = time_series[driver_key]
    driver_code = driver_data.get('driver_code', 'Unknown')
    
    print(f"\n✅ {driver_key} ({driver_code}):")
    print(f"   鍵: {list(driver_data.keys())}")
    
    # 檢查是否有 time_seconds
    if 'time_seconds' in driver_data:
        time_data = driver_data['time_seconds']
        time_ref = driver_data.get('time_reference', 'Unknown')
        time_points = driver_data.get('time_data_points', len(time_data) if isinstance(time_data, list) else 0)
        
        print(f"   ✅ 包含 time_seconds: {time_points} 個數據點")
        print(f"   ✅ 時間參考: {time_ref}")
        
        # 顯示前 5 個時間值
        if isinstance(time_data, list) and len(time_data) > 0:
            sample_data = [t for t in time_data[:5] if t is not None]
            if sample_data:
                print(f"   樣本時間值: {sample_data}")
    else:
        print(f"   ❌ 缺少 time_seconds 欄位")
    
    # 檢查通道數據
    if 'channels' in driver_data:
        channels = driver_data['channels']
        total_channels = driver_data.get('total_channels', len(channels))
        print(f"   ✅ 通道數: {total_channels}")
        print(f"   可用通道: {list(channels.keys())}")
    else:
        print(f"   ❌ 缺少 channels 欄位")

# 檢查元數據
if 'note' in time_series:
    print(f"\n📝 說明: {time_series['note']}")

# 最終結果
print("\n" + "=" * 80)
print("🎉 測試完成")
print("=" * 80)

# 檢查是否所有必要欄位都存在
required_fields = ['time_series']
driver1_required = ['driver_code', 'time_seconds', 'time_reference', 'channels']
driver2_required = ['driver_code', 'time_seconds', 'time_reference', 'channels']

success = True
for field in required_fields:
    if field not in data:
        print(f"❌ 缺少頂層欄位: {field}")
        success = False

if 'time_series' in data:
    for field in driver1_required:
        if field not in data['time_series'].get('driver1', {}):
            print(f"❌ driver1 缺少欄位: {field}")
            success = False
    
    for field in driver2_required:
        if field not in data['time_series'].get('driver2', {}):
            print(f"❌ driver2 缺少欄位: {field}")
            success = False

if success:
    print("\n✅ 所有必要欄位都存在")
    print("✅ time_seconds 數據已成功添加到 JSON 輸出")
    exit(0)
else:
    print("\n❌ 測試失敗：缺少必要欄位")
    exit(1)
