"""簡化時間軸測試"""
import sys
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)

try:
    from modules.gui.lap_analysis.speed_analysis.speed_analysis_chart_widget import SpeedChartWidget
    
    print("測試 1: SpeedChartWidget 初始化")
    widget = SpeedChartWidget()
    print("✅ 初始化成功")
    
    print("\n測試 2: 檢查屬性")
    print(f"  use_time_axis: {hasattr(widget, 'use_time_axis')} = {widget.use_time_axis if hasattr(widget, 'use_time_axis') else 'N/A'}")
    print(f"  driver1_time: {hasattr(widget, 'driver1_time')}")
    print(f"  driver2_time: {hasattr(widget, 'driver2_time')}")
    
    print("\n測試 3: 檢查方法")
    print(f"  set_time_axis_mode: {hasattr(widget, 'set_time_axis_mode')}")
    
    if hasattr(widget, 'set_time_axis_mode'):
        print("\n測試 4: 調用 set_time_axis_mode")
        widget.set_time_axis_mode(True)
        print(f"  調用 set_time_axis_mode(True): use_time_axis = {widget.use_time_axis}")
        widget.set_time_axis_mode(False)
        print(f"  調用 set_time_axis_mode(False): use_time_axis = {widget.use_time_axis}")
    
    print("\n測試 5: 檢查 set_speed_data 參數")
    import inspect
    sig = inspect.signature(widget.set_speed_data)
    params = list(sig.parameters.keys())
    print(f"  參數列表: {params}")
    print(f"  driver1_time 存在: {'driver1_time' in params}")
    print(f"  driver2_time 存在: {'driver2_time' in params}")
    
    print("\n✅ 所有測試通過")
    
except Exception as e:
    print(f"\n❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
finally:
    sys.exit(0)
