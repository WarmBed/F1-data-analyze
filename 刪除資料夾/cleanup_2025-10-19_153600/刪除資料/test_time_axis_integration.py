"""測試時間軸整合功能"""
import sys
from PyQt5.QtWidgets import QApplication

# 創建 QApplication
app = QApplication(sys.argv)

# 導入模組
from modules.gui.lap_analysis.speed_analysis.speed_analysis_chart_widget import SpeedChartWidget
from modules.gui.lap_analysis.speed_analysis.speed_analysis_mdi import SpeedAnalysisModule

print("=" * 60)
print("測試時間軸整合功能")
print("=" * 60)

# 測試 SpeedChartWidget
print("\n1. 測試 SpeedChartWidget 初始化...")
widget = SpeedChartWidget()
print(f"   ✅ SpeedChartWidget 初始化成功")
print(f"   ✅ use_time_axis 屬性存在: {hasattr(widget, 'use_time_axis')}")
print(f"   ✅ driver1_time 屬性存在: {hasattr(widget, 'driver1_time')}")
print(f"   ✅ driver2_time 屬性存在: {hasattr(widget, 'driver2_time')}")
print(f"   ✅ set_time_axis_mode 方法存在: {hasattr(widget, 'set_time_axis_mode')}")
print(f"   ✅ set_speed_data 方法存在: {hasattr(widget, 'set_speed_data')}")

# 測試 set_time_axis_mode 方法
print("\n2. 測試 set_time_axis_mode() 方法...")
try:
    widget.set_time_axis_mode(True)
    print(f"   ✅ set_time_axis_mode(True) 成功，use_time_axis = {widget.use_time_axis}")
    widget.set_time_axis_mode(False)
    print(f"   ✅ set_time_axis_mode(False) 成功，use_time_axis = {widget.use_time_axis}")
except Exception as e:
    print(f"   ❌ 錯誤: {e}")

# 測試 set_speed_data 方法參數
print("\n3. 測試 set_speed_data() 方法參數...")
import inspect
sig = inspect.signature(widget.set_speed_data)
params = list(sig.parameters.keys())
print(f"   參數列表: {params}")
print(f"   ✅ driver1_time 參數存在: {'driver1_time' in params}")
print(f"   ✅ driver2_time 參數存在: {'driver2_time' in params}")

# 測試 SpeedAnalysisModule
print("\n4. 測試 SpeedAnalysisModule...")
try:
    module = SpeedAnalysisModule()
    print(f"   ✅ SpeedAnalysisModule 初始化成功")
    print(f"   ✅ update_lap_parameters 方法存在: {hasattr(module, 'update_lap_parameters')}")
    
    # 檢查 update_lap_parameters 參數
    if hasattr(module, 'update_lap_parameters'):
        sig = inspect.signature(module.update_lap_parameters)
        params = list(sig.parameters.keys())
        print(f"   參數列表: {params}")
        print(f"   ✅ use_time_axis 參數存在: {'use_time_axis' in params}")
    else:
        print(f"   ❌ update_lap_parameters 方法不存在")
except Exception as e:
    print(f"   ❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("測試完成")
print("=" * 60)

sys.exit(0)
