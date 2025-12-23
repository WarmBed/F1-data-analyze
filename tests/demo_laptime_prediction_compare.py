#!/usr/bin/env python3
"""
圈速預測對比模組 - 獨立測試視窗

測試 Real vs F57 vs F91 三曲線對比功能
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication

# 添加專案根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.gui.laptime_prediction_compare import LaptimePredictionCompareMDI


def main():
    """主函數"""
    print("=" * 60)
    print("圈速預測對比模組 - 測試視窗")
    print("=" * 60)
    
    # 測試參數
    year = 2025
    race = "Abu_Dhabi"
    driver = "1"  # Verstappen
    
    print(f"\n測試參數:")
    print(f"  年份: {year}")
    print(f"  賽事: {race}")
    print(f"  車手: {driver}")
    print(f"\n預期載入的數據檔案:")
    print(f"  1. Real: json/LiveF1/{year}/{race}_Race/TimingData.json")
    print(f"  2. F57:  json/combined_laptime_{year}_{race}_R_*.json")
    print(f"  3. F91:  json/fp2_race_ml_prediction_v2_{year}_{race}_*.json")
    print("\n正在啟動 GUI...")
    
    try:
        # 創建應用程式
        app = QApplication(sys.argv)
        
        # 創建視窗
        window = LaptimePredictionCompareMDI(
            year=year,
            race=race,
            driver=driver
        )
        
        # 設置視窗大小
        window.resize(1200, 700)
        
        # 顯示視窗
        window.show()
        
        print("✅ GUI 視窗已啟動！")
        print("\n功能說明:")
        print("  - 綠色實線: Real (實際圈速)")
        print("  - 藍色虛線: F57 (燃油+輪胎模型)")
        print("  - 紅色點線: F91 (機器學習預測)")
        print("\n關閉視窗以結束測試...")
        
        # 執行應用程式
        sys.exit(app.exec_())
        
    except FileNotFoundError as e:
        print(f"\n❌ 找不到數據檔案: {e}")
        print("\n請先執行以下命令生成數據:")
        print(f"  1. F57: python f1_analysis_modular_main.py -f 57 -y {year} -r {race} -s R -d {driver}")
        print(f"  2. F91: python f1_analysis_modular_main.py -f 91 -y {year} -r {race}")
        return 1
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main() or 0)
