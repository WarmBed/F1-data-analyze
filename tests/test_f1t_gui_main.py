"""
F1T GUI 主要功能測試套件
測試所有核心GUI功能，確保系統穩定性和可靠性
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtTest import QTest
from PyQt5.QtGui import QMouseEvent

# 確保模組路徑正確
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 導入被測試的模組
from f1t_gui_main import F1TMainWindow, CustomMdiArea, TelemetryChartWidget, PopoutSubWindow

class TestF1TMainWindow:
    """
    F1T主視窗測試類別
    
    測試範圍:
    - 主視窗初始化
    - 視窗管理功能
    - 模組載入功能
    - GUI元件互動
    - 錯誤處理機制
    """
    
    @pytest.fixture
    def app(self):
        """設置測試用QApplication"""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        yield app
        # 清理不在這裡執行，因為其他測試可能還需要app
    
    @pytest.fixture
    def main_window(self, app):
        """創建測試用主視窗"""
        window = F1TMainWindow()
        yield window
        window.close()
    
    def test_主視窗初始化_正常情況(self, main_window):
        """測試主視窗的正常初始化流程"""
        # Given & When (已在fixture中完成)
        
        # Then
        assert main_window.windowTitle() == "F1T - Professional Racing Analysis Workstation"
        assert main_window.width() == 1400
        assert main_window.height() == 900
        assert hasattr(main_window, 'mdi_area')
        assert hasattr(main_window, 'module_tree')
        assert hasattr(main_window, 'status_text')
        assert hasattr(main_window, 'analysis_modules')
        assert hasattr(main_window, 'open_windows')
        
        print("[OK] 主視窗初始化測試通過")
    
    def test_MDI區域初始化_正常情況(self, main_window):
        """測試MDI區域的正確初始化"""
        # Given & When
        mdi_area = main_window.mdi_area
        
        # Then
        assert isinstance(mdi_area, CustomMdiArea)
        assert mdi_area.viewMode() == mdi_area.SubWindowView
        assert mdi_area.activationOrder() == mdi_area.CreationOrder
        
        print("[OK] MDI區域初始化測試通過")
    
    def test_控制面板元件_正常情況(self, main_window):
        """測試左側控制面板的元件是否正確初始化"""
        # Given & When
        module_tree = main_window.module_tree
        status_text = main_window.status_text
        
        # Then
        assert module_tree is not None
        assert module_tree.topLevelItemCount() > 0  # 應該有模組分類
        assert status_text is not None
        assert "系統就緒" in status_text.toPlainText()
        
        print("[OK] 控制面板元件測試通過")
    
    def test_視窗管理_tile_windows(self, main_window):
        """測試重新排列視窗功能"""
        # Given - 創建測試子視窗
        test_widget = QWidget()
        subwindow = main_window.mdi_area.addSubWindow(test_widget)
        subwindow.show()
        
        # When
        main_window.tile_windows()
        
        # Then
        # 驗證沒有拋出異常，且狀態已更新
        status_text = main_window.statusBar().currentMessage()
        assert "已重新排列" in status_text or "沒有視窗需要排列" in status_text
        
        print("[OK] Tile視窗功能測試通過")
    
    def test_視窗管理_cascade_windows(self, main_window):
        """測試層疊視窗功能"""
        # Given - 創建測試子視窗
        test_widget = QWidget()
        subwindow = main_window.mdi_area.addSubWindow(test_widget)
        subwindow.show()
        
        # When
        main_window.cascade_windows()
        
        # Then
        status_text = main_window.statusBar().currentMessage()
        assert "已層疊" in status_text or "沒有視窗需要層疊" in status_text
        
        print("[OK] Cascade視窗功能測試通過")
    
    def test_視窗管理_minimize_all_windows(self, main_window):
        """測試最小化所有視窗功能"""
        # Given - 創建測試子視窗
        test_widget = QWidget()
        subwindow = main_window.mdi_area.addSubWindow(test_widget)
        subwindow.show()
        
        # When
        main_window.minimize_all_windows()
        
        # Then
        status_text = main_window.statusBar().currentMessage()
        assert "已最小化" in status_text or "沒有視窗需要最小化" in status_text
        
        print("[OK] 最小化視窗功能測試通過")
    
    def test_視窗管理_maximize_all_windows(self, main_window):
        """測試最大化所有視窗功能"""
        # Given - 創建測試子視窗
        test_widget = QWidget()
        subwindow = main_window.mdi_area.addSubWindow(test_widget)
        subwindow.show()
        
        # When
        main_window.maximize_all_windows()
        
        # Then
        status_text = main_window.statusBar().currentMessage()
        assert "已最大化" in status_text or "沒有視窗需要最大化" in status_text
        
        print("[OK] 最大化視窗功能測試通過")
    
    def test_視窗管理_restore_all_windows(self, main_window):
        """測試還原所有視窗功能"""
        # Given - 創建並最小化測試子視窗
        test_widget = QWidget()
        subwindow = main_window.mdi_area.addSubWindow(test_widget)
        subwindow.show()
        subwindow.showMinimized()
        
        # When
        main_window.restore_all_windows()
        
        # Then
        status_text = main_window.statusBar().currentMessage()
        assert "已還原" in status_text or "沒有視窗需要還原" in status_text
        
        print("[OK] 還原視窗功能測試通過")
    
    def test_視窗管理_close_all_windows(self, main_window):
        """測試關閉所有視窗功能"""
        # Given - 創建測試子視窗
        test_widget = QWidget()
        subwindow = main_window.mdi_area.addSubWindow(test_widget)
        subwindow.show()
        initial_count = len(main_window.mdi_area.subWindowList())
        
        # When
        main_window.close_all_windows()
        
        # Then
        final_count = len(main_window.mdi_area.subWindowList())
        assert final_count == 0
        assert len(main_window.open_windows) == 0
        
        print("[OK] 關閉所有視窗功能測試通過")
    
    def test_全螢幕切換_功能(self, main_window):
        """測試全螢幕模式切換功能"""
        # Given
        initial_fullscreen = main_window.isFullScreen()
        
        # When
        main_window.toggle_fullscreen()
        
        # Then
        assert main_window.isFullScreen() != initial_fullscreen
        
        # 再次切換回來
        main_window.toggle_fullscreen()
        assert main_window.isFullScreen() == initial_fullscreen
        
        print("[OK] 全螢幕切換功能測試通過")
    
    @pytest.mark.parametrize("module_name,expected_method", [
        ("降雨分析", "open_rain_analysis"),
        ("遙測比較", "open_telemetry_comparison"),
        ("圈速分析", "open_laptime_analysis"),
        ("事故分析", "open_accident_analysis")
    ])
    def test_分析模組載入_參數化測試(self, main_window, module_name, expected_method):
        """參數化測試各種分析模組的載入"""
        # Given
        method = getattr(main_window, expected_method)
        
        # When & Then - 確保方法存在且可調用
        assert callable(method)
        
        # 執行方法（這會創建分析視窗）
        method()
        
        # 驗證視窗已創建
        assert len(main_window.open_windows) > 0
        
        print(f"[OK] {module_name} 模組載入測試通過")
    
    def test_狀態更新_功能(self, main_window):
        """測試狀態更新功能"""
        # Given
        test_message = "測試狀態訊息"
        
        # When
        main_window.update_status(test_message)
        
        # Then
        status_bar_message = main_window.statusBar().currentMessage()
        assert status_bar_message == test_message
        
        # 檢查左側狀態面板也有更新
        status_text_content = main_window.status_text.toPlainText()
        assert test_message in status_text_content
        
        print("[OK] 狀態更新功能測試通過")
    
    def test_創建分析視窗_錯誤處理(self, main_window):
        """測試創建分析視窗時的錯誤處理"""
        # Given - 模擬異常情況
        with patch.object(main_window, 'create_analysis_control_panel', side_effect=Exception("測試異常")):
            
            # When
            result = main_window.create_analysis_window("測試分析", "test_analysis")
            
            # Then
            assert result is None  # 應該返回None表示失敗
            
            # 檢查錯誤訊息
            status_message = main_window.statusBar().currentMessage()
            assert "發生錯誤" in status_message
        
        print("[OK] 創建分析視窗錯誤處理測試通過")

class TestCustomMdiArea:
    """
    自定義MDI區域測試類別
    """
    
    @pytest.fixture
    def app(self):
        """設置測試用QApplication"""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        return app
    
    @pytest.fixture
    def mdi_area(self, app):
        """創建測試用MDI區域"""
        mdi = CustomMdiArea()
        yield mdi
        mdi.close()
    
    def test_MDI初始化_正常情況(self, mdi_area):
        """測試MDI區域的初始化"""
        # Given & When (已在fixture中完成)
        
        # Then
        assert mdi_area.activationOrder() == mdi_area.CreationOrder
        assert mdi_area.viewMode() == mdi_area.SubWindowView
        
        print("[OK] MDI初始化測試通過")
    
    def test_添加子視窗_最小尺寸限制(self, mdi_area):
        """測試添加子視窗時的最小尺寸限制"""
        # Given
        test_widget = QWidget()
        
        # When
        subwindow = mdi_area.addSubWindow(test_widget)
        
        # Then
        assert subwindow.minimumWidth() == 600
        assert subwindow.minimumHeight() == 400
        assert subwindow.width() == 800
        assert subwindow.height() == 600
        
        print("[OK] 子視窗尺寸限制測試通過")

class TestTelemetryChartWidget:
    """
    遙測圖表元件測試類別
    """
    
    @pytest.fixture
    def app(self):
        """設置測試用QApplication"""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        return app
    
    @pytest.fixture
    def chart_widget(self, app):
        """創建測試用圖表元件"""
        widget = TelemetryChartWidget()
        widget.show()
        yield widget
        widget.close()
    
    def test_圖表初始化_正常情況(self, chart_widget):
        """測試圖表元件的初始化"""
        # Given & When (已在fixture中完成)
        
        # Then
        assert chart_widget.minimumWidth() == 400
        assert chart_widget.minimumHeight() == 300
        assert chart_widget.chart_data == []
        assert chart_widget.fixed_line_position is None
        assert chart_widget.fixed_line_value is None
        
        print("[OK] 圖表初始化測試通過")
    
    def test_設置圖表數據_正常情況(self, chart_widget):
        """測試設置圖表數據功能"""
        # Given
        test_data = [1.0, 2.5, 3.2, 1.8, 2.1]
        
        # When
        chart_widget.set_chart_data(test_data)
        
        # Then
        assert chart_widget.chart_data == test_data
        
        print("[OK] 設置圖表數據測試通過")
    
    def test_滑鼠點擊_設置固定線(self, chart_widget):
        """測試滑鼠點擊設置固定線功能"""
        # Given
        test_data = [1.0, 2.0, 3.0, 4.0, 5.0]
        chart_widget.set_chart_data(test_data)
        chart_widget.resize(400, 300)
        
        # When - 模擬滑鼠左鍵點擊
        click_pos = QPoint(200, 150)  # 中央位置
        event = QMouseEvent(
            QMouseEvent.MouseButtonPress,
            click_pos,
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier
        )
        chart_widget.mousePressEvent(event)
        
        # Then
        assert chart_widget.fixed_line_position is not None
        assert chart_widget.fixed_line_value is not None
        
        print("[OK] 滑鼠點擊設置固定線測試通過")

class TestPopoutSubWindow:
    """
    彈出子視窗測試類別
    """
    
    @pytest.fixture
    def app(self):
        """設置測試用QApplication"""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        return app
    
    @pytest.fixture
    def subwindow(self, app):
        """創建測試用子視窗"""
        test_widget = QWidget()
        subwindow = PopoutSubWindow(test_widget, "測試視窗")
        yield subwindow
        subwindow.close()
    
    def test_子視窗初始化_正常情況(self, subwindow):
        """測試子視窗的初始化"""
        # Given & When (已在fixture中完成)
        
        # Then
        assert subwindow.windowTitle() == "測試視窗"
        assert subwindow.minimumWidth() == 600
        assert subwindow.minimumHeight() == 400
        assert subwindow.width() == 800
        assert subwindow.height() == 600
        
        print("[OK] 子視窗初始化測試通過")

# 整合測試類別
class TestGUIIntegration:
    """
    GUI整合測試類別
    測試各元件間的協作
    """
    
    @pytest.fixture
    def app(self):
        """設置測試用QApplication"""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        return app
    
    @pytest.fixture
    def full_gui(self, app):
        """創建完整的GUI環境"""
        window = F1TMainWindow()
        yield window
        window.close()
    
    def test_完整工作流程_降雨分析(self, full_gui):
        """測試完整的降雨分析工作流程"""
        # Given
        main_window = full_gui
        initial_window_count = len(main_window.open_windows)
        
        # When - 開啟降雨分析
        main_window.open_rain_analysis()
        
        # Then
        assert len(main_window.open_windows) == initial_window_count + 1
        assert len(main_window.mdi_area.subWindowList()) > 0
        
        # 檢查新視窗的內容
        new_window_info = main_window.open_windows[-1]
        assert new_window_info['title'] == "降雨分析"
        assert new_window_info['type'] == "rain_analysis"
        
        print("[OK] 完整降雨分析工作流程測試通過")
    
    def test_多視窗操作_綜合測試(self, full_gui):
        """測試多視窗操作的綜合場景"""
        # Given
        main_window = full_gui
        
        # When - 開啟多個分析視窗
        main_window.open_rain_analysis()
        main_window.open_telemetry_comparison()
        main_window.open_laptime_analysis()
        
        # 執行視窗管理操作
        main_window.tile_windows()
        main_window.cascade_windows()
        main_window.minimize_all_windows()
        main_window.restore_all_windows()
        
        # Then
        assert len(main_window.open_windows) == 3
        assert len(main_window.mdi_area.subWindowList()) == 3
        
        # 最後關閉所有視窗
        main_window.close_all_windows()
        assert len(main_window.open_windows) == 0
        assert len(main_window.mdi_area.subWindowList()) == 0
        
        print("[OK] 多視窗操作綜合測試通過")

if __name__ == "__main__":
    # 直接執行測試
    pytest.main([__file__, "-v", "--tb=short", "-x"])
