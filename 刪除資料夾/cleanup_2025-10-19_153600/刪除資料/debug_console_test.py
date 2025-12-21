# 在 Python Debug Console 中執行（GUI 運行時）
# 複製整段貼上

from PyQt5.QtWidgets import QApplication

app = QApplication.instance()
main_window = None
for widget in app.topLevelWidgets():
    if "MainWindow" in type(widget).__name__ or widget.objectName() == "StyleHMainWindow":
        main_window = widget
        break

if main_window:
    print("=" * 80)
    print("🔍 速度模組 vs Rain 模組對比")
    print("=" * 80)
    
    # 檢查 lap_analysis_windows
    print("\n📊 lap_analysis_windows (速度模組):")
    if hasattr(main_window, 'lap_analysis_windows'):
        for i, w in enumerate(main_window.lap_analysis_windows):
            print(f"  [{i}] {type(w).__name__}: analysis_type = {getattr(w, 'analysis_type', 'N/A')}")
    
    # 檢查 tab_widget
    print("\n📊 tab_widget (Rain 模組):")
    if hasattr(main_window, 'tab_widget'):
        for i in range(main_window.tab_widget.count()):
            widget = main_window.tab_widget.widget(i)
            tab_text = main_window.tab_widget.tabText(i)
            has_type = hasattr(widget, 'analysis_type')
            type_value = getattr(widget, 'analysis_type', 'N/A')
            print(f"  Tab[{i}] '{tab_text}': {type(widget).__name__}")
            print(f"       has analysis_type: {has_type}, value: {type_value}")
    
    # 模擬掃描
    print("\n🔍 模擬 _get_telemetry_analysis_windows():")
    all_types = {'speed_analysis', 'speed', 'brake', 'throttle', 'gear', 'rpm', 
                 'acceleration', 'Speeddiff', 'distancediff', 'rain_weather', 
                 'pitstop', 'accident', 'tire'}
    
    found = []
    
    # 掃描列表
    if hasattr(main_window, 'lap_analysis_windows'):
        for w in main_window.lap_analysis_windows:
            if hasattr(w, 'analysis_type') and w.analysis_type in all_types:
                found.append(('lap_analysis_windows', w.analysis_type))
    
    # 掃描 Tab
    if hasattr(main_window, 'tab_widget'):
        for i in range(main_window.tab_widget.count()):
            widget = main_window.tab_widget.widget(i)
            if hasattr(widget, 'analysis_type') and widget.analysis_type in all_types:
                found.append((f'Tab[{i}]', widget.analysis_type))
    
    print(f"找到 {len(found)} 個模組:")
    for location, atype in found:
        print(f"  ✅ {location}: {atype}")
    
    # 檢查 Rain 是否被找到
    rain_found = any(atype == 'rain_weather' for _, atype in found)
    print(f"\n❌ Rain 模組被掃描到: {'是' if rain_found else '否'}")
else:
    print("❌ 找不到主視窗")
