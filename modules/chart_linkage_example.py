"""
使用連動模組重構圖表組件的示例

展示如何將現有的圖表組件轉換為使用 ChartLinkageMixin
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QRect
from modules.chart_linkage_mixin import ChartLinkageMixin
from typing import Optional


class ExampleChartWidget(QWidget, ChartLinkageMixin):
    """
    使用連動模組的圖表組件示例
    """
    
    def __init__(self, global_signals=None):
        super().__init__()
        
        # 初始化連動功能
        self.init_linkage(global_signals, "lap_analysis")
        
        # 圖表相關數據（示例）
        self.chart_data = []
        self.chart_rect = QRect(50, 50, 400, 300)
        self.distance_range = (0, 5000)  # 距離範圍（米）
    
    def get_chart_rect(self):
        """獲取圖表繪製區域"""
        return self.chart_rect
    
    def distance_to_x_coordinate(self, distance_value: float) -> Optional[float]:
        """將距離值轉換為X座標"""
        if not self.distance_range or self.distance_range[1] <= self.distance_range[0]:
            return None
        
        # 計算比例
        ratio = (distance_value - self.distance_range[0]) / (self.distance_range[1] - self.distance_range[0])
        
        # 轉換為X座標
        x_coord = self.chart_rect.left() + ratio * self.chart_rect.width()
        
        return x_coord if 0 <= ratio <= 1 else None
    
    def x_coordinate_to_distance(self, x_coord: float) -> Optional[float]:
        """將X座標轉換為距離值"""
        if not self.chart_rect.width() or not self.distance_range:
            return None
        
        # 計算比例
        ratio = (x_coord - self.chart_rect.left()) / self.chart_rect.width()
        
        # 轉換為距離值
        distance_value = self.distance_range[0] + ratio * (self.distance_range[1] - self.distance_range[0])
        
        return distance_value if 0 <= ratio <= 1 else None
    
    def mouseMoveEvent(self, event):
        """滑鼠移動事件"""
        chart_rect = self.get_chart_rect()
        
        if chart_rect.contains(event.pos()):
            # 計算Y軸相對位置
            y_relative = (event.pos().y() - chart_rect.top()) / chart_rect.height()
            
            # 處理連動
            self.handle_mouse_move_linkage(
                event.pos().x(), 
                y_relative, 
                getattr(self, 'global_signals', None)
            )
        
        super().mouseMoveEvent(event)
    
    def leaveEvent(self, event):
        """滑鼠離開事件"""
        self.handle_mouse_leave_linkage(getattr(self, 'global_signals', None))
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """滑鼠點擊事件"""
        chart_rect = self.get_chart_rect()
        
        if chart_rect.contains(event.pos()):
            self.handle_mouse_click_linkage(
                event.pos().x(),
                getattr(self, 'global_signals', None)
            )
        
        super().mousePressEvent(event)
    
    def paintEvent(self, event):
        """繪製事件"""
        from PyQt5.QtGui import QPainter
        
        painter = QPainter(self)
        
        # 繪製圖表內容（示例）
        painter.drawRect(self.chart_rect)
        
        # 繪製連動線條
        self.draw_linkage_lines(painter, self.chart_rect)
        
        painter.end()


# 重構現有組件的指南
class RefactoringGuide:
    """
    現有圖表組件重構指南
    """
    
    @staticmethod
    def refactor_existing_chart():
        """
        重構步驟：
        
        1. 添加 ChartLinkageMixin 到類別繼承中
        2. 在 __init__ 中調用 self.init_linkage()
        3. 實現必需的協議方法：
           - get_chart_rect()
           - distance_to_x_coordinate()
           - x_coordinate_to_distance()
        4. 修改滑鼠事件處理：
           - mouseMoveEvent: 調用 handle_mouse_move_linkage()
           - leaveEvent: 調用 handle_mouse_leave_linkage()
           - mousePressEvent: 調用 handle_mouse_click_linkage()
        5. 在 paintEvent 中調用 draw_linkage_lines()
        6. 移除原有的連動相關代碼
        """
        pass
    
    @staticmethod
    def migration_checklist():
        """
        遷移檢查清單：
        
        □ 移除舊的連動狀態變數
        □ 移除舊的信號連接代碼
        □ 移除舊的連動處理方法
        □ 移除舊的連動線條繪製代碼
        □ 測試新的連動功能
        □ 確認性能沒有下降
        """
        pass


if __name__ == "__main__":
    """
    測試新的連動模組
    """
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 創建測試組件
    widget = ExampleChartWidget()
    widget.show()
    
    sys.exit(app.exec_())
