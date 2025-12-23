"""測試所有 8 個遙測模組的時間軸整合"""
import sys
import inspect
from PyQt5.QtWidgets import QApplication

# 創建 QApplication
app = QApplication(sys.argv)

print("=" * 80)
print("測試所有遙測分析模組的時間軸整合功能")
print("=" * 80)

# 定義測試模組 (folder_name, mdi_class_name, widget_class_name, widget_attr, set_data_method)
modules_to_test = [
    ("Speed", "speed_analysis", "SpeedAnalysisModule", "SpeedChartWidget", "speed_chart_widget", "set_speed_data"),
    ("Brake", "brake_analysis", "BrakeAnalysisModule", "BrakeChartWidget", "brake_chart_widget", "set_brake_data"),
    ("Throttle", "Throttle_analysis", "ThrottleAnalysisModule", "ThrottleChartWidget", "throttle_chart_widget", "set_throttle_data"),
    ("Gear", "gear_analysis", "GearAnalysisModule", "GearChartWidget", "gear_chart_widget", "set_gear_data"),
    ("RPM", "rpm_analysis", "RPMAnalysisModule", "RPMChartWidget", "rpm_chart_widget", "set_rpm_data"),
    ("Acceleration", "acceleration_analysis", "accelerationAnalysisModule", "accelerationChartWidget", "acceleration_chart_widget", "set_acceleration_data"),
    ("SpeedDiff", "speeddiff_analysis", "SpeeddiffAnalysisModule", "speeddiffChartWidget", "speeddiff_chart_widget", "set_speeddiff_data"),
    ("DistanceDiff", "distancediff_analysis", "distancediffAnalysisModule", "distancediffChartWidget", "distancediff_chart_widget", "set_distancediff_data"),
]

results = []

for module_name, folder_name, mdi_class_name, widget_class_name, widget_attr, set_data_method in modules_to_test:
    print(f"\n{'='*80}")
    print(f"📊 測試模組: {module_name}")
    print(f"{'='*80}")
    
    try:
        # 特殊處理：資料夾名稱與檔案名稱不同的情況
        mdi_file_name = folder_name.lower() + "_mdi"
        widget_file_name = folder_name.lower() + "_chart_widget"
        
        # 動態導入 MDI 模組
        mdi_module = __import__(
            f"modules.gui.lap_analysis.{folder_name}.{mdi_file_name}",
            fromlist=[mdi_class_name]
        )
        mdi_class = getattr(mdi_module, mdi_class_name)
        
        # 動態導入 Chart Widget
        widget_module = __import__(
            f"modules.gui.lap_analysis.{folder_name}.{widget_file_name}",
            fromlist=[widget_class_name]
        )
        widget_class = getattr(widget_module, widget_class_name)
        
        # 測試 1: Chart Widget 屬性
        print(f"\n1️⃣ Chart Widget ({widget_class_name}) 測試:")
        widget = widget_class()
        
        has_use_time_axis = hasattr(widget, 'use_time_axis')
        has_driver1_time = hasattr(widget, 'driver1_time')
        has_driver2_time = hasattr(widget, 'driver2_time')
        has_set_time_mode = hasattr(widget, 'set_time_axis_mode')
        has_set_data = hasattr(widget, set_data_method)
        
        print(f"   ✅ use_time_axis 屬性: {has_use_time_axis}")
        print(f"   ✅ driver1_time 屬性: {has_driver1_time}")
        print(f"   ✅ driver2_time 屬性: {has_driver2_time}")
        print(f"   ✅ set_time_axis_mode() 方法: {has_set_time_mode}")
        print(f"   ✅ {set_data_method}() 方法: {has_set_data}")
        
        # 測試 2: set_data 方法參數
        if has_set_data:
            sig = inspect.signature(getattr(widget, set_data_method))
            params = list(sig.parameters.keys())
            has_time_params = 'driver1_time' in params and 'driver2_time' in params
            print(f"   ✅ {set_data_method} 時間參數: {has_time_params}")
            if not has_time_params:
                print(f"      ⚠️ 參數列表: {params}")
        else:
            has_time_params = False
        
        # 測試 3: MDI 模組
        print(f"\n2️⃣ MDI 模組 ({mdi_class_name}) 測試:")
        mdi_instance = mdi_class()
        
        has_update_lap = hasattr(mdi_instance, 'update_lap_parameters')
        print(f"   ✅ update_lap_parameters() 方法: {has_update_lap}")
        
        # 測試 4: update_lap_parameters 參數
        if has_update_lap:
            sig = inspect.signature(mdi_instance.update_lap_parameters)
            params = list(sig.parameters.keys())
            has_use_time_axis_param = 'use_time_axis' in params
            print(f"   ✅ use_time_axis 參數: {has_use_time_axis_param}")
            if not has_use_time_axis_param:
                print(f"      ⚠️ 參數列表: {params}")
        else:
            has_use_time_axis_param = False
        
        # 測試 5: 功能測試
        print(f"\n3️⃣ 功能測試:")
        if has_set_time_mode:
            try:
                widget.set_time_axis_mode(True)
                mode_test = widget.use_time_axis == True
                print(f"   ✅ set_time_axis_mode(True): {mode_test}")
                widget.set_time_axis_mode(False)
                print(f"   ✅ set_time_axis_mode(False): {widget.use_time_axis == False}")
            except Exception as e:
                mode_test = False
                print(f"   ❌ 模式切換失敗: {e}")
        else:
            mode_test = False
        
        # 綜合評估
        chart_ok = has_use_time_axis and has_driver1_time and has_driver2_time and has_set_time_mode and has_time_params
        mdi_ok = has_update_lap and has_use_time_axis_param
        overall_ok = chart_ok and mdi_ok and mode_test
        
        status = "✅ 通過" if overall_ok else "❌ 失敗"
        results.append((module_name, overall_ok, chart_ok, mdi_ok))
        
        print(f"\n📋 綜合評估: {status}")
        print(f"   Chart Widget: {'✅' if chart_ok else '❌'}")
        print(f"   MDI 模組: {'✅' if mdi_ok else '❌'}")
        print(f"   功能測試: {'✅' if mode_test else '❌'}")
        
    except Exception as e:
        print(f"\n❌ 模組載入失敗: {e}")
        import traceback
        traceback.print_exc()
        results.append((module_name, False, False, False))

# 最終報告
print(f"\n\n{'='*80}")
print("📊 最終測試報告")
print(f"{'='*80}\n")

print(f"{'模組名稱':<15} {'整體狀態':<12} {'Chart Widget':<15} {'MDI 模組':<12}")
print("-" * 80)

for module_name, overall, chart, mdi in results:
    overall_icon = "✅ 通過" if overall else "❌ 失敗"
    chart_icon = "✅" if chart else "❌"
    mdi_icon = "✅" if mdi else "❌"
    print(f"{module_name:<15} {overall_icon:<12} {chart_icon:<15} {mdi_icon:<12}")

passed_count = sum(1 for _, overall, _, _ in results if overall)
total_count = len(results)

print("-" * 80)
print(f"\n總計: {passed_count}/{total_count} 個模組通過測試")

if passed_count == total_count:
    print("\n🎉 所有模組測試通過！")
else:
    print(f"\n⚠️ 有 {total_count - passed_count} 個模組需要修復")

print("=" * 80)

sys.exit(0)
