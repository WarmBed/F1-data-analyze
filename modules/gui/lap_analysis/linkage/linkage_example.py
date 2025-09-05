#!/usr/bin/env python3
"""
連動模組化示例
展示如何將現有的分析模組遷移到新的連動系統
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QObject
import sys
import os

# 添加專案根目錄到 Python 路徑
current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
sys.path.insert(0, project_root)

from modules.gui.lap_analysis.linkage import (
    LapAnalysisLinkageMixin,
    LapAnalysisLinkageDrawingMixin,
    linkage_manager,
    LinkageButton,
    create_linkage_toolbar
)


class ModernSpeedAnalysisChart(QWidget, LapAnalysisLinkageMixin, LapAnalysisLinkageDrawingMixin):
    """
    現代化的速度分析圖表
    使用連動混合類來實現連動功能
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化連動功能
        self.init_linkage(module_type="speed_analysis")
        
        # 設置UI
        self.setup_ui()
        
        # 註冊到連動管理器
        linkage_manager.register_module(self, "speed_analysis")
    
    def setup_ui(self):
        """設置UI"""
        layout = QVBoxLayout(self)
        
        # 添加連動工具欄
        self.linkage_toolbar = create_linkage_toolbar(
            title="速度分析",
            show_master=False,  # 不顯示主開關（由主視窗控制）
            show_individual=True,
            parent=self
        )
        layout.addWidget(self.linkage_toolbar)
        
        # 連接信號
        self.linkage_toolbar.individual_linkage_toggled.connect(self.set_linkage_enabled)
        self.linkage_toolbar.clear_linkage_requested.connect(self.clear_linkage_marks)
        
        # 模擬圖表區域
        chart_widget = QWidget(self)
        chart_widget.setMinimumHeight(300)
        chart_widget.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        layout.addWidget(chart_widget)
    
    def draw_linkage_lines(self, painter):
        """實現抽象方法：繪製連動線條"""
        # 使用混合類的繪製功能
        self.draw_x_linkage_line(painter, self.current_x_linkage_position)
        self.draw_click_linkage_line(painter, self.current_click_linkage_position)
    
    def get_chart_rect(self):
        """實現抽象方法：獲取圖表區域"""
        # 返回圖表的繪製區域
        return self.rect().adjusted(10, 50, -10, -10)


class ModernRPMAnalysisChart(QWidget, LapAnalysisLinkageMixin, LapAnalysisLinkageDrawingMixin):
    """
    現代化的RPM分析圖表
    使用連動混合類來實現連動功能
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化連動功能
        self.init_linkage(module_type="rpm_analysis")
        
        # 設置UI
        self.setup_ui()
        
        # 註冊到連動管理器
        linkage_manager.register_module(self, "rpm_analysis")
    
    def setup_ui(self):
        """設置UI"""
        layout = QVBoxLayout(self)
        
        # 添加連動工具欄
        self.linkage_toolbar = create_linkage_toolbar(
            title="RPM分析",
            show_master=False,
            show_individual=True,
            parent=self
        )
        layout.addWidget(self.linkage_toolbar)
        
        # 連接信號
        self.linkage_toolbar.individual_linkage_toggled.connect(self.set_linkage_enabled)
        self.linkage_toolbar.clear_linkage_requested.connect(self.clear_linkage_marks)
        
        # 模擬圖表區域
        chart_widget = QWidget(self)
        chart_widget.setMinimumHeight(300)
        chart_widget.setStyleSheet("background-color: #f8f8f8; border: 1px solid #ccc;")
        layout.addWidget(chart_widget)
    
    def draw_linkage_lines(self, painter):
        """實現抽象方法：繪製連動線條"""
        self.draw_x_linkage_line(painter, self.current_x_linkage_position)
        self.draw_click_linkage_line(painter, self.current_click_linkage_position)
    
    def get_chart_rect(self):
        """實現抽象方法：獲取圖表區域"""
        return self.rect().adjusted(10, 50, -10, -10)


def demonstrate_linkage_migration():
    """
    演示如何將現有模組遷移到新的連動系統
    
    遷移步驟：
    1. 讓圖表類繼承 LapAnalysisLinkageMixin 和 LapAnalysisLinkageDrawingMixin
    2. 在 __init__ 中調用 init_linkage()
    3. 實現必要的抽象方法（draw_linkage_lines, get_chart_rect）
    4. 註冊到 linkage_manager
    5. 移除重複的連動代碼
    
    好處：
    - 消除代碼重複：所有連動邏輯統一在混合類中
    - 標準化介面：所有模組使用相同的連動介面
    - 集中管理：通過 linkage_manager 統一管理所有連動
    - 易於擴展：新增模組只需繼承混合類即可
    - 維護性佳：連動邏輯修改只需更新混合類
    """
    
    print("=== 連動模組化遷移示例 ===")
    print()
    
    print("1. 原始模組結構：")
    print("   - speed_analysis_chart.py （包含重複的連動代碼）")
    print("   - rpm_analysis_chart.py   （包含重複的連動代碼）")
    print("   - throttle_analysis_chart.py （包含重複的連動代碼）")
    print()
    
    print("2. 模組化後結構：")
    print("   - modules/gui/lap_analysis/linkage/")
    print("     ├── linkage_mixin.py      （統一的連動邏輯）")
    print("     ├── linkage_manager.py    （集中的連動管理）")
    print("     ├── linkage_ui.py         （標準化的UI組件）")
    print("     └── __init__.py           （模組介面）")
    print()
    
    print("3. 遷移後的圖表類：")
    print("   class SpeedAnalysisChart(QWidget, LapAnalysisLinkageMixin):")
    print("       def __init__(self):")
    print("           super().__init__()")
    print("           self.init_linkage('speed_analysis')")
    print("           linkage_manager.register_module(self, 'speed_analysis')")
    print()
    
    print("4. 連動管理器統計：")
    stats = linkage_manager.get_module_stats()
    print(f"   - 已註冊模組：{stats['total_modules']} 個")
    print(f"   - 模組類型：{stats['module_types']}")
    print(f"   - 主連動狀態：{'啟用' if stats['master_linkage_enabled'] else '停用'}")
    print()
    
    print("5. 遷移好處：")
    print("   ✅ 消除了 20+ 個重複的連動函數")
    print("   ✅ 統一了連動邏輯和狀態管理")
    print("   ✅ 標準化了UI組件和樣式")
    print("   ✅ 提高了代碼可維護性")
    print("   ✅ 簡化了新模組的開發")


if __name__ == "__main__":
    demonstrate_linkage_migration()
