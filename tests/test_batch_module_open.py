"""
測試批量開啟模組時的 Worker 生命週期管理
驗證 RuntimeError: wrapped C/C++ object has been deleted 修復
"""
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer

def test_batch_module_lifecycle():
    """模擬批量快速開啟/關閉模組"""
    app = QApplication(sys.argv)
    
    print("=" * 60)
    print("🧪 測試批量模組開啟的 Worker 生命週期管理")
    print("=" * 60)
    
    # 測試模組列表
    test_modules = [
        ("Rain Analysis", "modules.gui.rain_analysis.rain_analysis_mdi", "RainAnalysisModule"),
        ("Ideal Lap Heatmap", "modules.gui.ideal_lap_analysis.ideal_lap_sector_heatmap.ideal_lap_sector_heatmap_mdi", "IdealLapSectorHeatmapMDI"),
        ("Pitstop Analysis", "modules.gui.pitstop_analysis.pitstop_analysis_mdi", "PitstopAnalysisMDI"),
    ]
    
    modules_created = []
    
    # 步驟 1: 快速創建多個模組實例
    print("\n📦 步驟 1: 快速創建 3 個模組實例...")
    for name, module_path, class_name in test_modules:
        try:
            # 動態導入
            parts = module_path.rsplit('.', 1)
            module = __import__(parts[0], fromlist=[parts[1]])
            ModuleClass = getattr(module, class_name)
            
            # 創建實例（不顯示視窗）
            instance = ModuleClass(
                year="2025",
                race="Japan",
                session="R",
                parent=None
            )
            modules_created.append((name, instance))
            print(f"  ✅ {name} 創建成功")
        except Exception as e:
            print(f"  ❌ {name} 創建失敗: {e}")
    
    # 步驟 2: 等待 500ms 後快速關閉所有模組
    def close_all_modules():
        print("\n🔄 步驟 2: 快速關閉所有模組...")
        errors = []
        
        for name, instance in modules_created:
            try:
                # 觸發清理流程
                if hasattr(instance, 'cleanup'):
                    instance.cleanup()
                elif hasattr(instance, 'stop_loading'):
                    instance.stop_loading()
                
                # 刪除實例
                instance.deleteLater()
                print(f"  ✅ {name} 關閉成功")
            except RuntimeError as e:
                if "wrapped C/C++ object" in str(e):
                    errors.append((name, str(e)))
                    print(f"  ❌ {name} 發生 RuntimeError: {e}")
                else:
                    raise
            except Exception as e:
                print(f"  ⚠️  {name} 關閉異常: {e}")
        
        # 步驟 3: 等待 5 秒檢查延遲 QTimer 是否觸發錯誤
        def final_check():
            print("\n✅ 步驟 3: 等待 5 秒檢查延遲清理...")
            if errors:
                print(f"\n❌ 測試失敗！發現 {len(errors)} 個 RuntimeError:")
                for name, error in errors:
                    print(f"  - {name}: {error}")
                app.exit(1)
            else:
                print("\n🎉 測試通過！所有模組正確清理，無 RuntimeError")
                app.exit(0)
        
        QTimer.singleShot(5000, final_check)
    
    QTimer.singleShot(500, close_all_modules)
    
    # 運行事件循環
    return app.exec_()

if __name__ == "__main__":
    sys.exit(test_batch_module_lifecycle())
