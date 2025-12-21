#!/usr/bin/env python3
"""
深度比較速度模組 vs Rain 模組的存儲和掃描差異
"""
import sys
from PyQt5.QtWidgets import QApplication

def analyze_module_storage():
    """分析模組存儲位置和屬性"""
    
    app = QApplication.instance()
    if not app:
        print("❌ GUI 未運行！請先啟動 GUI")
        return
    
    # 獲取主視窗
    main_window = None
    for widget in app.topLevelWidgets():
        if widget.objectName() == "StyleHMainWindow" or "MainWindow" in type(widget).__name__:
            main_window = widget
            break
    
    if not main_window:
        print("❌ 找不到主視窗！")
        return
    
    print("=" * 80)
    print("🔍 深度分析：速度模組 vs Rain 模組")
    print("=" * 80)
    
    # ========== 1. 檢查 lap_analysis_windows 列表 ==========
    print("\n" + "=" * 80)
    print("📊 第一部分：lap_analysis_windows 列表（速度模組應該在這裡）")
    print("=" * 80)
    
    if hasattr(main_window, 'lap_analysis_windows'):
        windows = main_window.lap_analysis_windows
        print(f"✅ lap_analysis_windows 存在")
        print(f"   列表長度: {len(windows)}")
        
        for i, window in enumerate(windows):
            print(f"\n  [{i}] 類型: {type(window).__name__}")
            print(f"      模組: {type(window).__module__}")
            print(f"      有 analysis_type: {hasattr(window, 'analysis_type')}")
            
            if hasattr(window, 'analysis_type'):
                print(f"      analysis_type = '{window.analysis_type}'")
            
            if hasattr(window, 'update_lap_parameters'):
                print(f"      ✅ 有 update_lap_parameters 方法")
            else:
                print(f"      ❌ 沒有 update_lap_parameters 方法")
    else:
        print("❌ lap_analysis_windows 不存在！")
    
    # ========== 2. 檢查 Tab Widget ==========
    print("\n" + "=" * 80)
    print("📊 第二部分：Tab Widget（Rain 模組應該在這裡）")
    print("=" * 80)
    
    if hasattr(main_window, 'tab_widget'):
        tab_widget = main_window.tab_widget
        print(f"✅ tab_widget 存在")
        print(f"   Tab 數量: {tab_widget.count()}")
        
        for i in range(tab_widget.count()):
            widget = tab_widget.widget(i)
            tab_text = tab_widget.tabText(i)
            
            print(f"\n  Tab [{i}] 標題: '{tab_text}'")
            print(f"         類型: {type(widget).__name__}")
            print(f"         模組: {type(widget).__module__}")
            print(f"         有 analysis_type: {hasattr(widget, 'analysis_type')}")
            
            if hasattr(widget, 'analysis_type'):
                print(f"         analysis_type = '{widget.analysis_type}'")
            else:
                print(f"         ❌ 沒有 analysis_type 屬性")
                
                # 檢查所有屬性
                attrs = [a for a in dir(widget) if not a.startswith('_')]
                print(f"         可用屬性: {', '.join(attrs[:10])}...")
            
            if hasattr(widget, 'update_parameters'):
                print(f"         ✅ 有 update_parameters 方法")
            else:
                print(f"         ❌ 沒有 update_parameters 方法")
            
            # 檢查基類
            print(f"         基類鏈:")
            for base in type(widget).__mro__[:5]:
                print(f"           → {base.__name__}")
    else:
        print("❌ tab_widget 不存在！")
    
    # ========== 3. 模擬 _get_telemetry_analysis_windows() ==========
    print("\n" + "=" * 80)
    print("🔍 第三部分：模擬 _get_telemetry_analysis_windows() 的掃描邏輯")
    print("=" * 80)
    
    all_analysis_types = {
        'speed_analysis', 'speed', 'brake', 'throttle', 'steering',
        'gear', 'rpm', 'acceleration', 'speed_diff', 'Speeddiff', 'distancediff',
        'rain_weather', 'pitstop', 'accident', 'tire', 'ideal_lap',
    }
    
    analysis_windows = []
    
    # 掃描 lap_analysis_windows
    print("\n🔍 掃描 lap_analysis_windows:")
    if hasattr(main_window, 'lap_analysis_windows'):
        for window in main_window.lap_analysis_windows:
            if hasattr(window, 'analysis_type') and window.analysis_type in all_analysis_types:
                analysis_windows.append(window)
                print(f"  ✅ 找到: {window.analysis_type}")
    
    # 掃描 tab_widget
    print("\n🔍 掃描 tab_widget:")
    if hasattr(main_window, 'tab_widget'):
        for i in range(main_window.tab_widget.count()):
            widget = main_window.tab_widget.widget(i)
            tab_text = main_window.tab_widget.tabText(i)
            
            if hasattr(widget, 'analysis_type'):
                analysis_type = widget.analysis_type
                if analysis_type in all_analysis_types:
                    analysis_windows.append(widget)
                    print(f"  ✅ 找到 Tab {i} ('{tab_text}'): {analysis_type}")
                else:
                    print(f"  ⚠️  Tab {i} ('{tab_text}'): analysis_type='{analysis_type}' 不在支援列表中")
            else:
                print(f"  ❌ Tab {i} ('{tab_text}'): 沒有 analysis_type")
    
    print(f"\n📊 總共找到 {len(analysis_windows)} 個分析視窗")
    
    # ========== 4. 對比總結 ==========
    print("\n" + "=" * 80)
    print("📋 對比總結")
    print("=" * 80)
    
    print("\n速度模組特徵:")
    print("  - 存儲在: lap_analysis_windows 列表")
    print("  - 基類: IAnalysisModule")
    print("  - 更新方法: update_lap_parameters()")
    print("  - 能被掃描到: ✅ 是")
    
    print("\nRain 模組特徵:")
    print("  - 存儲在: tab_widget (Tab X)")
    print("  - 基類: UniversalAnalysisMDI")
    print("  - 更新方法: update_parameters()")
    
    # 檢查 Rain 是否被掃描到
    rain_found = any(
        hasattr(w, 'analysis_type') and w.analysis_type == 'rain_weather' 
        for w in analysis_windows
    )
    print(f"  - 能被掃描到: {'✅ 是' if rain_found else '❌ 否'}")
    
    if not rain_found:
        print("\n❌ Rain 模組未被掃描到的可能原因:")
        print("  1. Tab 中的 widget 沒有 analysis_type 屬性")
        print("  2. analysis_type 值不是 'rain_weather'")
        print("  3. Tab 中的 widget 是包裝器，真正的模組在內部")
        print("  4. 初始化順序問題，analysis_type 尚未設置")

if __name__ == "__main__":
    analyze_module_storage()
