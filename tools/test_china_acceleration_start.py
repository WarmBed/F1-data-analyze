"""
快速測試 China 站的加速段起點配置

此腳本會：
1. 測量 China 站當前的加速段起點
2. 提供建議的硬編碼值
3. 驗證 STR 車手的加速度是否修正
"""

import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 導入測量工具
from tools.measure_track_acceleration_start import load_json_data, analyze_acceleration_start

def main():
    print("\n" + "=" * 80)
    print("🇨🇳 China 站加速段起點快速測試")
    print("=" * 80)
    print()
    
    # 載入 China 2025 R 的數據
    data = load_json_data(2025, "China", "R")
    if not data:
        print("❌ 請先生成 China 站數據:")
        print("   python f1_analysis_modular_main.py -f 48 -y 2025 -r China -s R")
        return
    
    # 分析起點
    analyze_acceleration_start(data, "China")
    
    # 檢查 STR 的加速度
    driver_speeds = data['data']['driver_speeds']
    str_data = next((d for d in driver_speeds if d['driver'] == 'STR'), None)
    
    if str_data:
        print("\n" + "=" * 80)
        print("【STR 車手加速度檢查】")
        print("=" * 80)
        
        accel = str_data.get('avg_acceleration_100_300_ms2', 'N/A')
        accel_time = str_data.get('acceleration_time_100_300_seconds', 'N/A')
        start_dist = str_data.get('acceleration_100_300_start_distance', 'N/A')
        end_dist = str_data.get('acceleration_100_300_end_distance', 'N/A')
        
        print(f"  加速度: {accel} m/s²")
        print(f"  加速時間: {accel_time} 秒")
        print(f"  起點距離: {start_dist} m")
        print(f"  終點距離: {end_dist} m")
        print()
        
        # 判斷是否正確
        if isinstance(accel, (int, float)):
            if accel >= 7.5 and accel <= 8.0:
                print("  ✅ 加速度正常（預期: 7.80 m/s²）")
            elif accel >= 2.5 and accel <= 3.5:
                print("  ❌ 加速度異常（顯示 ~2.93 m/s²，應為 7.80 m/s²）")
                print("  💡 這是因為搜索範圍錯誤，需要設定硬編碼起點")
            else:
                print(f"  ⚠️  加速度為 {accel} m/s²（請檢查是否合理）")
        
        print()
    
    print("=" * 80)
    print("📝 測試完成")
    print("=" * 80)
    print()

if __name__ == "__main__":
    main()
