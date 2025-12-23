#!/usr/bin/env python3
"""
深度比較報告：Ideal Lap Ranking Table vs All Drivers Straight Line Speed Table
=============================================================================

根據 F1T 開發原則 0（反幻覺編碼四原則），本報告詳細記錄兩個模組的實現差異。

日期: 2025-10-14
作者: AI Programming Assistant
目的: 找出直線速度分析車隊顏色不顯示的根本原因
"""

# ============================================================================
# 📊 核心差異總結
# ============================================================================

"""
【關鍵發現】車隊顏色不顯示的根本原因：

❌ 直線速度分析使用：header.setSectionResizeMode(QHeaderView.ResizeToContents)
✅ 理想圈排名使用：table.setColumnWidth(col, width) 固定寬度

問題分析：
- ResizeToContents 可能在某些情況下導致背景色渲染異常
- 固定寬度設置更穩定，與 PyQt5 的顏色渲染系統相容性更好
"""

# ============================================================================
# 🔍 詳細代碼比較
# ============================================================================

comparison_report = {
    "1. 模組導入": {
        "ideal_lap_ranking_table": """
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QGroupBox, QLabel,
    QGridLayout, QStyledItemDelegate, QStyleOptionViewItem, QStyle
)
from PyQt5.QtCore import pyqtSignal, Qt, QRect
from PyQt5.QtGui import QColor, QFont, QBrush, QPainter

from modules.gui.ideal_lap_analysis.shared_colors import (
    get_team_color,
    get_gap_color,
    get_competitiveness_color,
)
        """,
        "straight_line_speed": """
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QStyledItemDelegate,
    QStyleOptionViewItem, QStyle, QMessageBox
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QColor, QBrush, QFont, QPen

from modules.gui.ideal_lap_analysis.shared_colors import (
    get_team_color,
)
        """,
        "差異": [
            "❌ 直線速度未導入 QRect（可能影響 Delegate 渲染）",
            "❌ 直線速度未導入 get_gap_color, get_competitiveness_color（功能缺失）",
            "✅ 兩者都正確導入 get_team_color",
        ]
    },
    
    "2. 表格欄位寬度設置": {
        "ideal_lap_ranking_table": """
# ✅ 使用固定寬度（每個欄位明確設置）
table.setColumnWidth(0, 60)   # 排名
table.setColumnWidth(1, 100)  # 車手（套用車隊顏色）
table.setColumnWidth(2, 130)  # 車隊
table.setColumnWidth(3, 120)  # 車手最速圈
table.setColumnWidth(4, 120)  # 理想圈
table.setColumnWidth(5, 110)  # S1
table.setColumnWidth(6, 110)  # S2
table.setColumnWidth(7, 110)  # S3
table.setColumnWidth(8, 100)  # 差異
table.setColumnWidth(9, 150)  # 與全場最速差距
table.setColumnWidth(10, 90)  # 分段

# 設置表頭
header = table.horizontalHeader()
header.setStretchLastSection(True)  # 只有最後一欄自動伸展
        """,
        "straight_line_speed": """
# ❌ 使用自適應寬度（所有欄位自動調整）
# 設置行高（增加以容納兩行時間顯示）
table.verticalHeader().setDefaultSectionSize(40)

# 設置表頭為自適應寬度
header = table.horizontalHeader()
header.setSectionResizeMode(QHeaderView.ResizeToContents)  # 所有欄位自適應內容
header.setStretchLastSection(True)  # 最後一欄（視覺化）拉伸填滿剩餘空間
        """,
        "差異": [
            "🚨 **關鍵問題**：直線速度使用 ResizeToContents 可能導致背景色不渲染",
            "✅ 理想圈排名使用固定寬度，穩定可靠",
            "💡 建議：改用固定寬度設置",
        ]
    },
    
    "3. 車隊顏色設置方式": {
        "ideal_lap_ranking_table": """
# 車手欄位（第 1 欄）
driver_item = QTableWidgetItem(driver_code)
driver_item.setTextAlignment(Qt.AlignCenter)
driver_item.setBackground(self._get_team_color(team))  # ✅ 直接傳 QColor
driver_item.setForeground(QBrush(QColor(0, 0, 0)))    # 黑色文字
driver_item.setToolTip(f"{driver_code} - {team}")
self.table.setItem(row, 1, driver_item)

# 車隊欄位（第 2 欄）
team_item = QTableWidgetItem(team)
team_item.setTextAlignment(Qt.AlignCenter)
team_item.setBackground(self._get_team_color(team))  # ✅ 直接傳 QColor
team_item.setForeground(QBrush(QColor(0, 0, 0)))
team_item.setToolTip(team)
self.table.setItem(row, 2, team_item)
        """,
        "straight_line_speed": """
# 車手欄位（第 1 欄）
driver_item = QTableWidgetItem(driver)
driver_item.setTextAlignment(Qt.AlignCenter)
driver_item.setFont(QFont("Arial", 10, QFont.Bold))

# ✅ 設置車隊背景色（使用共用配色模組）
team_color = get_team_color(team)
if row < 3:  # 調試前三行
    print(f"[COLOR_DEBUG] 車手={driver}, 車隊={team}, 顏色=RGB({team_color.red()}, {team_color.green()}, {team_color.blue()})")
driver_item.setBackground(team_color)  # ✅ 已修正：直接傳 QColor
driver_item.setForeground(QBrush(QColor(0, 0, 0)))  # 黑色文字

self.table.setItem(row, 1, driver_item)

# 車隊欄位（第 2 欄）
team_item = QTableWidgetItem(team)
team_item.setTextAlignment(Qt.AlignCenter)
team_item.setFont(QFont("Arial", 9))
self.table.setItem(row, 2, team_item)  # ❌ 車隊欄位沒有設置背景色！
        """,
        "差異": [
            "✅ 兩者都使用 setBackground(QColor) 直接傳顏色（已修正）",
            "❌ 直線速度的車隊欄位（第 2 欄）沒有設置背景色",
            "✅ 理想圈排名的車隊欄位也有背景色",
            "💡 建議：為車隊欄位也添加背景色",
        ]
    },
    
    "4. 表格選擇模式": {
        "ideal_lap_ranking_table": """
# 設置表格屬性
table.setSortingEnabled(True)
table.setSelectionBehavior(QAbstractItemView.SelectRows)
table.setSelectionMode(QAbstractItemView.SingleSelection)
table.setAlternatingRowColors(True)
table.setEditTriggers(QAbstractItemView.NoEditTriggers)
# ✅ 禁用選擇功能
table.setSelectionMode(QAbstractItemView.NoSelection)
        """,
        "straight_line_speed": """
# 設置表格屬性
table.setSortingEnabled(True)
table.setSelectionBehavior(QAbstractItemView.SelectRows)
table.setSelectionMode(QAbstractItemView.SingleSelection)  # ❌ 啟用選擇
table.setAlternatingRowColors(True)
table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        """,
        "差異": [
            "✅ 理想圈排名禁用選擇（NoSelection）",
            "❌ 直線速度啟用單選（SingleSelection）",
            "💡 選擇模式可能影響背景色顯示（選中時背景色被覆蓋）",
        ]
    },
    
    "5. update_data 方法": {
        "ideal_lap_ranking_table": """
def populate_table(self, ranking_data: List[Dict[str, Any]]):
    # 方法名稱：populate_table
    try:
        self._ranking_data = ranking_data
        row_count = len(ranking_data)
        
        self.table.setSortingEnabled(False)  # 暫時禁用排序
        self.table.setRowCount(row_count)
        
        for row, driver in enumerate(ranking_data):
            self._set_row_data(row, driver)  # 調用 _set_row_data
        
        self.table.setSortingEnabled(True)  # 重新啟用排序
        """,
        "straight_line_speed": """
def update_data(self, data: Dict[str, Any]):
    # 方法名稱：update_data
    try:
        # ... 提取 metadata 和 driver_speeds ...
        
        # ❌ 重新創建整個表格（導致閃爍）
        self.table.deleteLater()
        self.table = self._create_table()
        self.layout().addWidget(self.table)
        
        # 計算時間範圍
        self._calculate_max_time()
        
        # 填充表格
        self._populate_table()  # 調用 _populate_table
        """,
        "差異": [
            "❌ 直線速度重新創建整個表格（deleteLater + addWidget）",
            "✅ 理想圈排名只更新表格內容（setRowCount + setItem）",
            "🚨 **關鍵問題**：重新創建表格可能導致樣式丟失",
            "💡 建議：改為只更新內容，不重新創建表格",
        ]
    },
    
    "6. 自定義 Delegate": {
        "ideal_lap_ranking_table": """
# 有兩個自定義 Delegate
class SectorTimeDelegate(QStyledItemDelegate):
    # 繪製雙列分段時間
    
class SectorMarksDelegate(QStyledItemDelegate):
    # 繪製混合顏色的分段標記
    
# 應用到特定欄位
self._sector_time_delegate = SectorTimeDelegate(table)
for col in (5, 6, 7):
    table.setItemDelegateForColumn(col, self._sector_time_delegate)

self._sector_marks_delegate = SectorMarksDelegate(table)
table.setItemDelegateForColumn(10, self._sector_marks_delegate)
        """,
        "straight_line_speed": """
# 有一個自定義 Delegate
class AccelerationBarDelegate(QStyledItemDelegate):
    # 繪製加速時間棒狀圖
    
# 應用到第 8 欄（加速性能視覺化）
self.delegate = AccelerationBarDelegate(0.0, 10.0, self.table)
self.table.setItemDelegateForColumn(8, self.delegate)
        """,
        "差異": [
            "✅ 兩者都正確使用自定義 Delegate",
            "⚠️ Delegate 不影響其他欄位的背景色",
        ]
    },
    
    "7. 表格初始化時機": {
        "ideal_lap_ranking_table": """
def _init_ui(self):
    layout = QVBoxLayout(self)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(10)
    
    # 1. 主表格（只創建一次）
    self.table = self._create_table()
    layout.addWidget(self.table, 1)  # 給予彈性空間
    
    # 2. 統計摘要面板
    self.summary_panel = self._create_summary_panel()
    layout.addWidget(self.summary_panel)
        """,
        "straight_line_speed": """
def _init_ui(self):
    layout = QVBoxLayout(self)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(10)
    
    # 創建表格（只創建一次）
    self.table = self._create_table()
    layout.addWidget(self.table)
    
# ❌ 但在 update_data 中會重新創建！
def update_data(self, data):
    self.table.deleteLater()
    self.table = self._create_table()  # 重新創建
    self.layout().addWidget(self.table)
        """,
        "差異": [
            "✅ 理想圈排名表格只創建一次，永不重建",
            "❌ 直線速度每次 update_data 都重新創建表格",
            "🚨 **核心問題**：重建表格導致樣式和背景色設置丟失",
        ]
    },
}

# ============================================================================
# 🎯 根本原因分析
# ============================================================================

root_cause_analysis = """
【車隊顏色不顯示的根本原因】

問題 1: 表格重新創建 (最嚴重)
-----------------------------
直線速度模組在 update_data() 中執行：
1. self.table.deleteLater()  # 刪除舊表格
2. self.table = self._create_table()  # 創建新表格
3. self.layout().addWidget(self.table)  # 添加到佈局

❌ 問題：
- 新表格使用 ResizeToContents 自適應寬度
- 在某些 PyQt5 版本中，ResizeToContents 會導致背景色不渲染
- QTableWidgetItem 的背景色設置在 _populate_table() 中
- 表格重建後，樣式表可能未正確應用

✅ 解決方案：
- 學習理想圈排名，只創建表格一次
- update_data 時只更新內容，不重建表格
- 使用固定寬度代替 ResizeToContents


問題 2: 欄位寬度設置方式 (次要)
------------------------------
直線速度：header.setSectionResizeMode(QHeaderView.ResizeToContents)
理想圈排名：table.setColumnWidth(col, width)

❌ 問題：
- ResizeToContents 在背景色渲染時可能有兼容性問題
- 自適應寬度可能導致單元格尺寸在渲染前未確定

✅ 解決方案：
- 改用固定寬度（setColumnWidth）
- 只讓最後一欄使用 setStretchLastSection(True)


問題 3: 車隊欄位未設置背景色 (輕微)
----------------------------------
直線速度只為車手欄位設置背景色，車隊欄位（第 2 欄）沒有背景色

❌ 問題：
- 與理想圈排名的視覺風格不一致
- 車隊欄位應該也顯示車隊顏色

✅ 解決方案：
- 為車隊欄位（第 2 欄）也設置背景色
- 完全複製理想圈排名的實現


問題 4: 表格選擇模式 (可能影響)
------------------------------
直線速度：SingleSelection（允許選擇行）
理想圈排名：NoSelection（禁用選擇）

❌ 問題：
- 選中行時，系統高亮色會覆蓋背景色
- 用戶點擊後看到的是高亮色，不是車隊色

✅ 解決方案：
- 設置為 NoSelection（如果不需要選擇功能）
- 或確保選中狀態不覆蓋背景色
"""

# ============================================================================
# 📋 修復建議清單
# ============================================================================

fix_recommendations = {
    "優先級 1 - 立即修復": [
        {
            "問題": "表格重新創建導致樣式丟失",
            "位置": "update_data() 方法，lines 246-250",
            "現有代碼": """
# ❌ 錯誤模式
self.table.deleteLater()
self.table = self._create_table()
self.layout().addWidget(self.table)
            """,
            "修正代碼": """
# ✅ 正確模式（學習理想圈排名）
self.table.setSortingEnabled(False)
self.table.setRowCount(len(self.driver_speeds_data))
# 直接更新內容，不重建表格
self._populate_table()
self.table.setSortingEnabled(True)
            """,
            "影響": "修復後背景色應該正常顯示",
        },
        {
            "問題": "使用 ResizeToContents 導致背景色不渲染",
            "位置": "_create_table() 方法，line 238",
            "現有代碼": """
# ❌ 錯誤模式
header.setSectionResizeMode(QHeaderView.ResizeToContents)
            """,
            "修正代碼": """
# ✅ 正確模式（使用固定寬度）
table.setColumnWidth(0, 60)   # 排名
table.setColumnWidth(1, 100)  # 車手
table.setColumnWidth(2, 120)  # 車隊
table.setColumnWidth(3, 100)  # 最高速度
table.setColumnWidth(4, 120)  # 加速時間
table.setColumnWidth(5, 100)  # 距離
table.setColumnWidth(6, 130)  # 平均加速度
table.setColumnWidth(7, 120)  # 最高時速時間
# 最後一欄（視覺化）使用 stretch
header = table.horizontalHeader()
header.setStretchLastSection(True)
            """,
            "影響": "確保背景色正確渲染",
        },
    ],
    
    "優先級 2 - 改進體驗": [
        {
            "問題": "車隊欄位沒有背景色",
            "位置": "_populate_row() 方法，line 419",
            "修正代碼": """
# 2. 車隊（添加背景色）
team_item = QTableWidgetItem(team)
team_item.setTextAlignment(Qt.AlignCenter)
team_item.setFont(QFont("Arial", 9))
# ✅ 添加車隊背景色
team_color = get_team_color(team)
team_item.setBackground(team_color)
team_item.setForeground(QBrush(QColor(0, 0, 0)))
self.table.setItem(row, 2, team_item)
            """,
            "影響": "視覺一致性更好",
        },
        {
            "問題": "表格選擇模式可能覆蓋背景色",
            "位置": "_create_table() 方法，line 222",
            "修正代碼": """
# ✅ 禁用選擇（如果不需要）
table.setSelectionMode(QAbstractItemView.NoSelection)
            """,
            "影響": "避免高亮色覆蓋車隊色",
        },
    ],
    
    "優先級 3 - 代碼優化": [
        {
            "問題": "調試輸出應該移除",
            "位置": "_populate_row() 方法，lines 410-411",
            "修正代碼": """
# ❌ 移除調試代碼
# if row < 3:
#     print(f"[COLOR_DEBUG] 車手={driver}, 車隊={team}, 顏色=RGB(...)")
            """,
            "影響": "清理日誌輸出",
        },
    ],
}

# ============================================================================
# 📊 測試驗證計劃
# ============================================================================

test_plan = """
【測試驗證計劃】

階段 1: 基礎修復測試
-------------------
1. 移除 table.deleteLater() 和重建邏輯
2. 改用固定寬度設置
3. 重新啟動 GUI
4. 檢查車隊顏色是否顯示

預期結果：
✅ LAW (Racing Bulls) = 藍色 RGB(80, 120, 200)
✅ ANT (Mercedes) = 青色 RGB(39, 180, 160)
✅ SAI (Williams) = 淺藍 RGB(80, 160, 220)


階段 2: 完整性測試
-----------------
1. 為車隊欄位添加背景色
2. 設置 NoSelection 模式
3. 測試所有 20 位車手
4. 驗證顏色映射正確

預期結果：
✅ 所有 10 支車隊都有正確顏色
✅ 車手和車隊欄位顏色一致
✅ 無未映射車隊（灰色）


階段 3: 壓力測試
---------------
1. 切換不同賽事（Singapore, Monza, Japan）
2. 測試不同年份（2024, 2025）
3. 測試正賽、排位賽、練習賽
4. 驗證顏色持久性

預期結果：
✅ 所有會話都正確顯示顏色
✅ 切換參數後顏色不丟失
✅ 無記憶體洩漏或渲染異常
"""

# ============================================================================
# 🏁 總結
# ============================================================================

summary = """
【深度調查總結】

✅ 已識別問題：
1. 表格重新創建導致樣式丟失（最嚴重）
2. ResizeToContents 與背景色渲染不兼容（次要）
3. 車隊欄位未設置背景色（輕微）
4. 表格選擇模式可能覆蓋背景色（可能）

✅ 根本原因：
- 直線速度模組每次 update_data 都重建表格
- 理想圈排名只創建表格一次，僅更新內容
- 這是架構設計差異，不是顏色映射問題

✅ 修復策略：
1. 移除 table.deleteLater() 重建邏輯
2. 改用 setRowCount + setItem 更新內容
3. 使用固定寬度代替 ResizeToContents
4. 為車隊欄位添加背景色

✅ 預期效果：
修復後，直線速度分析的車隊顏色應該與理想圈排名完全一致。
"""

if __name__ == "__main__":
    print("=" * 80)
    print("深度比較報告：Ideal Lap Ranking Table vs Straight Line Speed Table")
    print("=" * 80)
    print()
    print(root_cause_analysis)
    print()
    print("=" * 80)
    print("修復建議")
    print("=" * 80)
    for priority, fixes in fix_recommendations.items():
        print(f"\n{priority}")
        print("-" * 40)
        for i, fix in enumerate(fixes, 1):
            print(f"\n{i}. {fix['問題']}")
            print(f"   位置: {fix['位置']}")
            if '現有代碼' in fix:
                print(f"   現有: {fix['現有代碼'].strip()}")
            print(f"   修正: {fix['修正代碼'].strip()}")
            print(f"   影響: {fix['影響']}")
    print()
    print("=" * 80)
    print(test_plan)
    print()
    print("=" * 80)
    print(summary)
