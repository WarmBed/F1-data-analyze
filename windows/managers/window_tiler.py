# -*- coding: utf-8 -*-
"""
WindowTiler - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger
from windows.widgets.custom_mdi_area import CustomMdiArea
from PyQt5.QtWidgets import QApplication

logger = get_logger(__name__)


class WindowTiler:
    """從 f1t_gui_main.py 提取的 tile_windows 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def tile_windows(self):
        """重新排列視窗 - 智能平鋪當前活動MDI區域中的所有子視窗"""
        
        logger.debug(f"[TILE_DEBUG] ===== 開始 Tile Windows =====")
        
        # 獲取當前活動的MDI區域
        current_tab = self.main_window.tab_widget.currentWidget()
        if current_tab is None:
            logger.debug(f"[TILE_DEBUG] ❌ current_tab 為 None")
            return
        
        logger.debug(f"[TILE_DEBUG] 當前分頁: {current_tab.objectName()}")
        logger.debug(f"[TILE_DEBUG] 當前分頁類型: {type(current_tab).__name__}")
        
        # 查找當前分頁中的MDI區域
        mdi_area = None
        
        # 首先檢查當前分頁是否本身就是MDI區域
        logger.debug(f"[TILE_DEBUG] 檢查 current_tab 是否為 CustomMdiArea: {isinstance(current_tab, CustomMdiArea)}")
        
        if isinstance(current_tab, CustomMdiArea):
            mdi_area = current_tab
            logger.debug(f"[TILE_DEBUG] ✅ current_tab 本身就是 MDI 區域")
        else:
            # 否則在分頁的子元件中查找
            logger.debug(f"[TILE_DEBUG] 開始查找子元件中的 CustomMdiArea...")
            children = current_tab.findChildren(CustomMdiArea)
            logger.debug(f"[TILE_DEBUG] 找到 {len(children)} 個 CustomMdiArea 子元件")
            for i, child in enumerate(children):
                logger.debug(f"[TILE_DEBUG]   子元件 {i}: ObjectName={child.objectName()}, 子視窗數={len(child.subWindowList())}")
                mdi_area = child
                break
                
        if mdi_area is None:
            logger.debug(f"[TILE_DEBUG] ❌ 找不到 MDI 區域")
            return
        
        logger.debug(f"[TILE_DEBUG] ✅ 找到 MDI 區域: {mdi_area.objectName()}")
        
        # 獲取所有子視窗並過濾出可見的視窗
        all_subwindows = mdi_area.subWindowList()
        logger.debug(f"[TILE_DEBUG] MDI 區域總共有 {len(all_subwindows)} 個子視窗")
        
        # 只包含可見且未關閉的視窗，並排除固定的歡迎頁面視窗
        subwindows = [
            sw for sw in all_subwindows 
            if sw.isVisible() 
            and not sw.isWindowModified() 
            and not sw.property("is_welcome_fixed")  # 排除固定視窗
        ]
        logger.debug(f"[TILE_DEBUG] 找到 {len(all_subwindows)} 個子視窗，其中 {len(subwindows)} 個可見且非固定")
        
        if not subwindows:
            logger.debug(f"[TILE DEBUG] 沒有可見的非固定子視窗需要排列")
            return
        
        # 移除有問題的清理邏輯 - 直接使用現有的子視窗列表
        logger.debug(f"[TILE DEBUG] 準備排列 {len(subwindows)} 個視窗")
        
        # 計算排列配置 - 右邊和下方保留 10px
        margin_right = 10
        margin_bottom = 10
        available_width = mdi_area.width() - margin_right
        available_height = mdi_area.height() - margin_bottom
        logger.debug(f"[TILE DEBUG] MDI區域大小: {mdi_area.width()}x{mdi_area.height()}")
        logger.debug(f"[TILE DEBUG] 可用空間（扣除右下邊距）: {available_width}x{available_height}")
        
        # 計算最佳的行列配置
        num_windows = len(subwindows)
        logger.debug(f"[TILE DEBUG] 視窗數量: {num_windows}")
        
        if num_windows == 0:
            logger.debug(f"[TILE DEBUG] 視窗數量為0，退出")
            return  # 沒有視窗需要排列
            
        cols = int(num_windows ** 0.5)
        logger.debug(f"[TILE DEBUG] 初始計算 cols: {cols}")
        
        if cols == 0:  # 防止除零錯誤
            cols = 1
            logger.debug(f"[TILE DEBUG] cols 修正為 1")
            
        if cols * cols < num_windows:
            cols += 1
            logger.debug(f"[TILE DEBUG] cols 調整為: {cols}")
            
        rows = (num_windows + cols - 1) // cols
        logger.debug(f"[TILE DEBUG] 計算得到 rows: {rows}")
        
        if rows == 0:  # 額外保護
            rows = 1
            logger.debug(f"[TILE DEBUG] rows 修正為 1")
        
        # 計算每個視窗的尺寸
        window_width = available_width // cols if cols > 0 else available_width
        window_height = available_height // rows if rows > 0 else available_height
        logger.debug(f"[TILE DEBUG] 每個視窗尺寸: {window_width}x{window_height}")
        
        # 檢查最小尺寸限制是否會導致超出範圍
        min_width, min_height = 250, 150
        
        # 計算套用最小尺寸後的總尺寸
        total_width_with_min = max(window_width, min_width) * cols
        total_height_with_min = max(window_height, min_height) * rows
        
        # 只在不會超出範圍時才套用最小尺寸限制
        if total_width_with_min <= available_width:
            window_width = max(window_width, min_width)
            logger.debug(f"[TILE DEBUG] ✅ 套用最小寬度限制: {window_width}")
        else:
            logger.debug(f"[TILE DEBUG] ⚠️ 跳過最小寬度限制（會超出範圍：{total_width_with_min} > {available_width}）")
        
        if total_height_with_min <= available_height:
            window_height = max(window_height, min_height)
            logger.debug(f"[TILE DEBUG] ✅ 套用最小高度限制: {window_height}")
        else:
            logger.debug(f"[TILE DEBUG] ⚠️ 跳過最小高度限制（會超出範圍：{total_height_with_min} > {available_height}）")
        
        logger.debug(f"[TILE DEBUG] 最終視窗尺寸: {window_width}x{window_height}")
        
        # 排列視窗
        logger.debug(f"[TILE DEBUG] 開始排列 {len(subwindows)} 個視窗，配置: {rows}行 x {cols}列")
        
        # 預檢查：確保所有視窗的基本設定一致
        logger.debug(f"[TILE DEBUG] ========== 預檢查視窗設定 ==========")
        for i, subwindow in enumerate(subwindows):
            widget = subwindow.widget()
            if widget:
                min_size = widget.minimumSize()
                size_policy = widget.sizePolicy()
                logger.debug(f"[TILE CHECK] 視窗 {i}: 最小尺寸({min_size.width()}x{min_size.height()}), 尺寸策略({size_policy.horizontalPolicy()}x{size_policy.verticalPolicy()})")
                
                # 檢查是否有調試方法可以調用
                if hasattr(widget, 'debug_window_status'):
                    logger.debug(f"[TILE CHECK] 調用視窗 {i} 的狀態報告:")
                    widget.debug_window_status()
        logger.debug(f"[TILE DEBUG] ========== 預檢查完成 ==========")
        
        for i, subwindow in enumerate(subwindows):
            row = i // cols
            col = i % cols
            
            x = col * window_width
            y = row * window_height
            
            logger.debug(f"[TILE DEBUG] 視窗 {i}: 位置({x}, {y}) 尺寸({window_width}, {window_height})")
            
            # 設置視窗位置和尺寸
            subwindow.setGeometry(x, y, window_width, window_height)
            
            # 確保視窗可見和正常化
            subwindow.showNormal()
            subwindow.raise_()
            
            # 強制處理事件，確保尺寸更新完成
            QApplication.processEvents()
            
            # 檢查實際尺寸並調試
            actual_size = subwindow.size()
            logger.debug(f"[TILE DEBUG] 視窗 {i} 實際尺寸: {actual_size.width()}x{actual_size.height()}")
            
            if actual_size.width() != window_width or actual_size.height() != window_height:
                logger.debug(f"[TILE WARNING] 視窗 {i} 尺寸不匹配！目標: {window_width}x{window_height}, 實際: {actual_size.width()}x{actual_size.height()}")
                
                # 嘗試重新設置
                subwindow.resize(window_width, window_height)
                QApplication.processEvents()
                final_size = subwindow.size()
                logger.debug(f"[TILE DEBUG] 視窗 {i} 重設後尺寸: {final_size.width()}x{final_size.height()}")
        
        # 最終同步步驟：確保所有視窗尺寸一致
        logger.debug(f"[TILE DEBUG] ========== 開始最終尺寸同步 ==========")
        
        # 收集所有視窗的實際尺寸
        actual_sizes = []
        for i, subwindow in enumerate(subwindows):
            size = subwindow.size()
            actual_sizes.append((size.width(), size.height()))
            logger.debug(f"[TILE SYNC] 視窗 {i} 當前尺寸: {size.width()}x{size.height()}")
        
        # 找到最小的共同尺寸（確保所有視窗都能適應）
        if actual_sizes:
            min_width = min(size[0] for size in actual_sizes)
            min_height = min(size[1] for size in actual_sizes)
            logger.debug(f"[TILE SYNC] 統一目標尺寸: {min_width}x{min_height}")
            
            # 將所有視窗設置為相同尺寸
            for i, subwindow in enumerate(subwindows):
                current_pos = subwindow.pos()
                subwindow.setGeometry(current_pos.x(), current_pos.y(), min_width, min_height)
                QApplication.processEvents()
                
                final_size = subwindow.size()
                logger.debug(f"[TILE SYNC] 視窗 {i} 最終尺寸: {final_size.width()}x{final_size.height()}")
        
        logger.debug(f"[TILE DEBUG] ========== 尺寸同步完成 ==========")
        
        # 調試：檢查每個子視窗的邊距設定
        logger.debug(f"[TILE DEBUG] ========== 子視窗邊距檢查 ==========")
        for i, subwindow in enumerate(subwindows):
            widget = subwindow.widget()
            logger.debug(f"[TILE DEBUG] 子視窗 {i}: {subwindow.windowTitle()}")
            
            # 檢查 MDI 子視窗的邊距
            margins = subwindow.contentsMargins()
            logger.debug(f"[TILE DEBUG]   MDI邊距: left={margins.left()}, top={margins.top()}, right={margins.right()}, bottom={margins.bottom()}")
            
            # 檢查子視窗的frameGeometry vs geometry
            frame_geo = subwindow.frameGeometry()
            geo = subwindow.geometry()
            logger.debug(f"[TILE DEBUG]   frameGeometry: {frame_geo.width()}x{frame_geo.height()}")
            logger.debug(f"[TILE DEBUG]   geometry: {geo.width()}x{geo.height()}")
            logger.debug(f"[TILE DEBUG]   邊框差異: width={frame_geo.width()-geo.width()}, height={frame_geo.height()-geo.height()}")
            
            if widget:
                widget_size = widget.size()
                logger.debug(f"[TILE DEBUG]   內部widget尺寸: {widget_size.width()}x{widget_size.height()}")
                
                # 如果有調試方法，調用之
                if hasattr(widget, 'debug_margin_analysis'):
                    logger.debug(f"[TILE DEBUG]   調用 widget 邊距分析...")
                    widget.debug_margin_analysis()
        
        logger.debug(f"[TILE DEBUG] ========== 邊距檢查完成 ==========")
        
        # 刷新MDI區域
        mdi_area.update()
