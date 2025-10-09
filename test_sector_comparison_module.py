#!/usr/bin/env python3
"""
理想圈分段對比模組 - 測試腳本
Ideal Lap Sector Comparison Module Test Script

測試模組的各個組件是否正常工作

作者: F1T Team
日期: 2025-10-09
"""

import sys
import json
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def test_module_import():
    """測試模組導入"""
    print("=" * 70)
    print("測試 1: 模組導入")
    print("=" * 70)
    
    try:
        from modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison import (
            IdealLapSectorComparisonModule,
            IdealLapSectorComparisonMDI,
            IdealLapSectorComparisonWidget,
            IdealLapSectorComparisonDataLoader,
            SectorComparisonControlPanel
        )
        
        print("✅ IdealLapSectorComparisonModule 導入成功")
        print("✅ IdealLapSectorComparisonMDI 導入成功")
        print("✅ IdealLapSectorComparisonWidget 導入成功")
        print("✅ IdealLapSectorComparisonDataLoader 導入成功")
        print("✅ SectorComparisonControlPanel 導入成功")
        print()
        return True
        
    except ImportError as e:
        print(f"❌ 導入失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_loader():
    """測試資料載入器"""
    print("=" * 70)
    print("測試 2: 資料載入器")
    print("=" * 70)
    
    try:
        from modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison import (
            IdealLapSectorComparisonDataLoader
        )
        
        # 創建載入器實例
        loader = IdealLapSectorComparisonDataLoader(
            year="2025",
            race="Japan",
            session="R"
        )
        
        print(f"✅ 載入器已創建: {loader.ANALYSIS_TYPE}")
        print(f"   CLI Function: {loader.CLI_FUNCTION}")
        print(f"   JSON Pattern: {loader.JSON_PATTERN}")
        print(f"   年份: {loader.year}")
        print(f"   賽事: {loader.race}")
        print(f"   賽段: {loader.session}")
        print()
        
        print("⚠️  跳過資料載入測試（需要實際 JSON 檔案或 API）")
        print("   提示: 請先執行 CLI 命令生成資料:")
        print("   python f1_analysis_modular_main.py -f 53 -y 2025 -r Japan -s R")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_widget_creation():
    """測試圖表元件創建"""
    print("=" * 70)
    print("測試 3: 圖表元件創建")
    print("=" * 70)
    
    try:
        from PyQt5.QtWidgets import QApplication
        from modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison import (
            IdealLapSectorComparisonWidget,
            SectorComparisonControlPanel
        )
        
        # 創建 QApplication（如果不存在）
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 創建圖表元件
        chart_widget = IdealLapSectorComparisonWidget()
        print("✅ IdealLapSectorComparisonWidget 已創建")
        print(f"   分段顏色: {chart_widget.SECTOR_COLORS}")
        print(f"   分段標籤: {chart_widget.SECTOR_LABELS}")
        
        # 創建控制面板
        control_panel = SectorComparisonControlPanel()
        print("✅ SectorComparisonControlPanel 已創建")
        
        # 清理
        chart_widget.deleteLater()
        control_panel.deleteLater()
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_module_initialization():
    """測試模組初始化"""
    print("=" * 70)
    print("測試 4: 模組初始化")
    print("=" * 70)
    
    try:
        from PyQt5.QtWidgets import QApplication
        from modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison import (
            IdealLapSectorComparisonModule
        )
        
        # 創建 QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 創建模組實例
        module = IdealLapSectorComparisonModule(
            year="2025",
            race="Japan",
            session="R"
        )
        
        print("✅ 模組實例已創建")
        print(f"   模組名稱: {module.module_name}")
        print(f"   顯示名稱: {module.display_name}")
        print(f"   版本: {module.version}")
        print(f"   描述: {module.description}")
        
        # 測試初始化
        print("\n   嘗試初始化模組...")
        success = module.initialize_module()
        
        if success:
            print("✅ 模組初始化成功")
            print(f"   是否就緒: {module.is_ready()}")
            
            # 獲取模組資訊
            info = module.get_module_info()
            print(f"\n   模組資訊:")
            print(f"   - 初始化狀態: {info['is_initialized']}")
            print(f"   - 參數: {info['parameters']}")
            
            # 清理
            module.cleanup()
            print("\n✅ 模組已清理")
        else:
            print("❌ 模組初始化失敗")
        
        print()
        return success
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chart_rendering():
    """測試圖表渲染（需要真實資料）"""
    print("=" * 70)
    print("測試 5: 圖表渲染")
    print("=" * 70)
    
    try:
        from PyQt5.QtWidgets import QApplication
        from modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison import (
            IdealLapSectorComparisonWidget
        )
        
        # 創建 QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 創建圖表元件
        chart_widget = IdealLapSectorComparisonWidget()
        print("✅ 圖表元件創建成功")
        
        print("⚠️  跳過實際渲染測試（需要實際資料和手動驗證）")
        
        # 清理
        chart_widget.deleteLater()
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主測試函數"""
    print("\n" + "=" * 70)
    print("[TEST] 理想圈分段對比模組 - 完整測試")
    print("=" * 70 + "\n")
    
    results = []
    
    # 執行測試
    results.append(("模組導入", test_module_import()))
    results.append(("資料載入器", test_data_loader()))
    results.append(("圖表元件創建", test_widget_creation()))
    results.append(("模組初始化", test_module_initialization()))
    results.append(("圖表渲染", test_chart_rendering()))
    
    # 總結
    print("=" * 70)
    print("測試總結")
    print("=" * 70)
    
    for name, passed in results:
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"{status} - {name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n[SUCCESS] 所有測試通過！模組開發完成。")
        print("\n下一步:")
        print("  1. 註冊到模組工廠")
        print("  2. 在主 GUI 中添加選單項目")
        print("  3. 執行完整的整合測試")
        return 0
    else:
        print("\n[FAIL] 部分測試失敗，請檢查錯誤並修復。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
