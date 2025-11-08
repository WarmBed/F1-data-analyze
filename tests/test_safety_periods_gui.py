"""
GUI Safety Periods 快速測試腳本
直接從 JSON 載入數據並驗證 GUI 顯示
"""
import sys
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from modules.gui.accident_analysis.accident_analysis_mdi import SafetyPeriodsWidget

# 讀取測試數據
with open('json/all_incidents_summary_2021_Bahrain_Grand_Prix_RACE.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

safety_periods_data = data['data'].get('safety_periods', [])

print(f"載入了 {len(safety_periods_data)} 個 Safety Period(s)")
print("數據內容:")
for period in safety_periods_data:
    print(f"  {period}")

# 創建測試視窗
app = QApplication(sys.argv)
window = QMainWindow()
window.setWindowTitle("Safety Periods 測試")
window.setGeometry(100, 100, 600, 400)

# 創建 SafetyPeriodsWidget
central_widget = QWidget()
layout = QVBoxLayout(central_widget)

safety_widget = SafetyPeriodsWidget()
layout.addWidget(safety_widget)

window.setCentralWidget(central_widget)

# 更新數據
print("\n更新 SafetyPeriodsWidget 數據...")
safety_widget.update_safety_periods_data(safety_periods_data)

# 顯示視窗
window.show()
print("✅ GUI 視窗已開啟，請檢查 Safety Periods 表格顯示")

sys.exit(app.exec_())
