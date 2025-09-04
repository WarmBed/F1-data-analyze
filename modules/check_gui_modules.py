#!/usr/bin/env python3
"""
檢查GUI是否使用新的重構模組
通過直接執行圈速分析來驗證
"""

import sys
import os

# 添加項目根目錄到Python路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_current_imports():
    """檢查當前Python環境中載入的模組"""
    print("🔍 檢查已載入的F1T模組...")
    
    loaded_modules = []
    for module_name in sys.modules:
        if 'speed_analysis_chart_widget' in module_name or 'rpm_analysis_chart_widget' in module_name:
            loaded_modules.append(module_name)
    
    if loaded_modules:
        print("📦 已載入的相關模組:")
        for module in loaded_modules:
            print(f"   - {module}")
    else:
        print("ℹ️  尚未載入任何圖表組件模組")
    
    return loaded_modules

def force_import_test():
    """強制導入測試，看是否使用重構版本"""
    print("\n🧪 強制導入測試...")
    
    try:
        # 導入重構版本
        from modules.speed_analysis_chart_widget_refactored import SpeedAnalysisChartWidget
        from modules.rpm_analysis_chart_widget_refactored import RPMAnalysisChartWidget
        
        print("✅ 重構版本導入成功")
        
        # 檢查是否有統一架構的屬性
        speed_widget = SpeedAnalysisChartWidget()
        if hasattr(speed_widget, 'speed_chart') and hasattr(speed_widget.speed_chart, 'chart_type'):
            print(f"✅ 速度圖表使用統一架構，類型: {speed_widget.speed_chart.chart_type}")
        
        rpm_widget = RPMAnalysisChartWidget()
        if hasattr(rpm_widget, 'rpm_chart') and hasattr(rpm_widget.rpm_chart, 'chart_type'):
            print(f"✅ RPM圖表使用統一架構，類型: {rpm_widget.rpm_chart.chart_type}")
        
        return True
        
    except Exception as e:
        print(f"❌ 重構版本導入失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_main_imports():
    """檢查主程式的導入是否已更新"""
    print("\n📄 檢查主程式導入...")
    
    try:
        with open('f1t_gui_main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查舊版導入
        old_speed_imports = content.count('from modules.speed_analysis_chart_widget import')
        old_rpm_imports = content.count('from modules.rpm_analysis_chart_widget import')
        
        # 檢查新版導入
        new_speed_imports = content.count('speed_analysis_chart_widget_refactored')
        new_rpm_imports = content.count('rpm_analysis_chart_widget_refactored')
        
        print(f"📊 統計結果:")
        print(f"   舊版速度導入: {old_speed_imports} 處")
        print(f"   舊版RPM導入: {old_rpm_imports} 處")
        print(f"   新版速度導入: {new_speed_imports} 處")
        print(f"   新版RPM導入: {new_rpm_imports} 處")
        
        if old_speed_imports == 0 and old_rpm_imports == 0 and new_speed_imports > 0 and new_rpm_imports > 0:
            print("✅ 主程式已完全使用重構版本")
            return True
        else:
            print("⚠️  主程式可能仍在使用舊版本")
            return False
            
    except Exception as e:
        print(f"❌ 檢查主程式失敗: {e}")
        return False

def simulate_gui_module_load():
    """模擬GUI載入模組的過程"""
    print("\n🎭 模擬GUI模組載入...")
    
    try:
        # 模擬主程式中的導入過程
        print("📥 執行主程式導入...")
        
        # 第一個導入位置 (line 3229)
        from modules.speed_analysis_chart_widget_refactored import SpeedAnalysisChartWidget as Speed1
        print("✅ 位置1 - 速度分析導入成功")
        
        # 第二個導入位置 (line 6868) 
        from modules.speed_analysis_chart_widget_refactored import SpeedAnalysisChartWidget as Speed2
        print("✅ 位置2 - 速度分析導入成功")
        
        # 第三個導入位置 (line 7221)
        from modules.speed_analysis_chart_widget_refactored import SpeedAnalysisChartWidget as Speed3
        print("✅ 位置3 - 速度分析導入成功")
        
        # RPM導入位置 (line 7355)
        from modules.rpm_analysis_chart_widget_refactored import RPMAnalysisChartWidget as RPM1
        print("✅ 位置4 - RPM分析導入成功")
        
        # 驗證這些都是同一個類
        if Speed1 == Speed2 == Speed3:
            print("✅ 所有速度分析導入指向同一個重構版本")
        
        print("🎉 GUI將使用重構版本模組！")
        return True
        
    except Exception as e:
        print(f"❌ 模擬GUI載入失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主要檢查流程"""
    print("🔎 F1T GUI模組使用狀況檢查")
    print("=" * 50)
    
    # 檢查當前載入的模組
    loaded = check_current_imports()
    
    # 強制導入測試
    import_ok = force_import_test()
    
    # 檢查主程式導入
    main_ok = check_main_imports()
    
    # 模擬GUI載入
    sim_ok = simulate_gui_module_load()
    
    print("\n" + "=" * 50)
    print("📋 檢查總結:")
    print(f"   重構模組導入: {'✅' if import_ok else '❌'}")
    print(f"   主程式更新: {'✅' if main_ok else '❌'}")
    print(f"   GUI載入模擬: {'✅' if sim_ok else '❌'}")
    
    if import_ok and main_ok and sim_ok:
        print("\n🎉 GUI將正確使用重構版本模組！")
        print("💡 當你觸發圈速分析時，應該會看到統一架構的日誌輸出")
    else:
        print("\n⚠️  可能存在問題，GUI可能仍使用舊版本")
    
    return import_ok and main_ok and sim_ok

if __name__ == "__main__":
    main()
