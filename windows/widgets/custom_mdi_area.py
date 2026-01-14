# -*- coding: utf-8 -*-
"""
F1T GUI - CustomMdiArea and Snap System
========================================

自定義 MDI 區域，支援 Snap 功能、磁吸對齊、Smart Width。

從 f1t_gui_main.py 提取:
- SnapZone (行 200-214)
- MODULE_SIZE_HINTS (行 218-230)
- SnapPreviewOverlay (行 232-313)
- CustomMdiArea (行 315-1259, 944 行)

提取日期: 2025-06-14
"""

import logging
from enum import Enum, auto

from PyQt5.QtCore import Qt, QRect, QTimer
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtWidgets import QWidget, QMdiArea, QMdiSubWindow

# 設定日誌
logger = logging.getLogger(__name__)


class SnapZone(Enum):
    """Snap 區域枚舉 - 定義 9 個 Snap 區域"""
    NONE = auto()
    # 角落 (25% 面積)
    TOP_LEFT = auto()
    TOP_RIGHT = auto()
    BOTTOM_LEFT = auto()
    BOTTOM_RIGHT = auto()
    # 邊緣 (50% 面積)
    TOP = auto()
    BOTTOM = auto()
    LEFT = auto()
    RIGHT = auto()
    # 中心 (100% 面積)
    CENTER = auto()


# 模組尺寸提示 - 用於 Smart Width 配置
MODULE_SIZE_HINTS = {
    'circle_map': {'preferred_ratio': 0.30, 'min_width': 280, 'aspect': 'square'},
    'ranking_tower': {'preferred_ratio': 0.18, 'min_width': 160, 'aspect': 'tall'},
    'lap_time_distribution': {'preferred_ratio': 0.25, 'min_width': 200, 'aspect': 'wide'},
    'driver_strategy': {'preferred_ratio': 0.45, 'min_width': 380, 'aspect': 'wide'},
    'speed_trace': {'preferred_ratio': 0.35, 'min_width': 300, 'aspect': 'wide'},
    'telemetry_comparison': {'preferred_ratio': 0.40, 'min_width': 350, 'aspect': 'wide'},
    'position_analysis': {'preferred_ratio': 0.35, 'min_width': 300, 'aspect': 'wide'},
    'race_calendar': {'preferred_ratio': 0.25, 'min_width': 220, 'aspect': 'tall'},
    'temp_analysis': {'preferred_ratio': 0.30, 'min_width': 280, 'aspect': 'wide'},
    'default': {'preferred_ratio': 0.30, 'min_width': 250, 'aspect': 'wide'},
}


class SnapPreviewOverlay(QWidget):
    """Snap 預覽覆蓋層 - 顯示藍色半透明預覽"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.hide()
        
        # 預覽顏色 (類似 Windows Aero Snap)
        self._preview_color = QColor(0, 120, 215, 80)  # 藍色半透明
        self._border_color = QColor(0, 120, 215, 200)  # 藍色邊框
        self._current_zone = SnapZone.NONE
    
    def set_geometry_direct(self, rect: QRect):
        """直接設置預覽區域幾何形狀（支援 Smart Width）"""
        if rect.isNull():
            self.hide()
            return
        
        self._current_zone = SnapZone.CENTER  # 標記為有效區域
        self.setGeometry(rect)
        self.show()
        self.update()
        
    def set_zone(self, zone: SnapZone, mdi_rect: QRect):
        """設置預覽區域（舊版介面，保持相容）"""
        self._current_zone = zone
        
        if zone == SnapZone.NONE:
            self.hide()
            return
            
        # 計算預覽區域的幾何形狀
        preview_rect = self._calculate_zone_geometry(zone, mdi_rect)
        self.setGeometry(preview_rect)
        self.show()
        self.update()
        
    def _calculate_zone_geometry(self, zone: SnapZone, mdi_rect: QRect) -> QRect:
        """根據 Snap 區域計算預覽幾何形狀"""
        x, y = mdi_rect.x(), mdi_rect.y()
        w, h = mdi_rect.width(), mdi_rect.height()
        half_w, half_h = w // 2, h // 2
        
        zone_map = {
            SnapZone.TOP_LEFT: QRect(x, y, half_w, half_h),
            SnapZone.TOP_RIGHT: QRect(x + half_w, y, half_w, half_h),
            SnapZone.BOTTOM_LEFT: QRect(x, y + half_h, half_w, half_h),
            SnapZone.BOTTOM_RIGHT: QRect(x + half_w, y + half_h, half_w, half_h),
            SnapZone.TOP: QRect(x, y, w, half_h),
            SnapZone.BOTTOM: QRect(x, y + half_h, w, half_h),
            SnapZone.LEFT: QRect(x, y, half_w, h),
            SnapZone.RIGHT: QRect(x + half_w, y, half_w, h),
            SnapZone.CENTER: QRect(x, y, w, h),
        }
        
        return zone_map.get(zone, QRect())
        
    def paintEvent(self, event):
        """繪製預覽"""
        if self._current_zone == SnapZone.NONE:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 填充半透明藍色
        painter.fillRect(self.rect(), self._preview_color)
        
        # 繪製邊框
        pen = QPen(self._border_color, 2)
        painter.setPen(pen)
        painter.drawRect(self.rect().adjusted(1, 1, -1, -1))
        
    def hide_preview(self):
        """隱藏預覽"""
        self._current_zone = SnapZone.NONE
        self.hide()


class CustomMdiArea(QMdiArea):
    """自定義MDI區域，強制執行子視窗最小尺寸限制"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 啟用MDI的內建功能
        self.setActivationOrder(QMdiArea.CreationOrder)  # 設置視窗激活順序
        self.setViewMode(QMdiArea.SubWindowView)  # 確保使用子視窗模式
        
        # 禁用右鍵選單
        self.setContextMenuPolicy(Qt.NoContextMenu)  # 完全禁用右鍵選單
        
        # 允許拖拉視窗
        self.setOption(QMdiArea.DontMaximizeSubWindowOnActivation, True)  # 不自動最大化
        
        # ========== 滾動條策略（支援超出範圍的視窗）==========
        # 當視窗超出可視範圍時，自動顯示滾動條
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        logger.debug(f"[MDI_INIT] 已啟用滾動條策略：當視窗超出範圍時自動顯示")
        
        # ========== Snap 功能 ==========
        self._snap_preview = SnapPreviewOverlay(self)
        self._snap_enabled = True  # 是否啟用 Snap 功能
        self._snap_threshold = 30  # 邊緣檢測閾值 (像素)
        self._snapped_windows = {}  # 追蹤已 Snap 的視窗: {window_id: QRect}
        
        # ========== 磁吸對齊功能 ==========
        self._magnetic_snap_enabled = True  # 是否啟用磁吸對齊
        self._magnetic_snap_distance = 15  # 磁吸距離閾值 (像素)
        self._moving_window = None  # 當前正在移動的視窗
        self._original_move_pos = None  # 原始移動位置
        self._is_applying_snap = False  # 防止遞迴的鎖
        
        # 安裝事件過濾器來監聽子視窗移動
        self.subWindowActivated.connect(self._on_subwindow_activated)
        
        # 用於存儲「視窗邊緣 Snap」的精確目標區域
        self._window_edge_snap_rect = None
    
    def _get_occupied_regions(self, exclude_window=None) -> list:
        """獲取所有已佔用的區域（排除指定視窗）"""
        regions = []
        for sw in self.subWindowList():
            if sw == exclude_window:
                continue
            if sw.property("is_welcome_fixed"):
                continue  # 忽略歡迎頁面固定視窗
            # 只追蹤可見且有有效尺寸的視窗
            if sw.isVisible() and sw.width() > 50 and sw.height() > 50:
                regions.append(sw.geometry())
        return regions
    
    def _find_available_space_for_zone(self, zone: 'SnapZone', exclude_window=None) -> QRect:
        """
        根據 Snap 區域找到可用空間
        這個方法會考慮已存在的視窗，計算出該區域的實際可用空間
        """
        w, h = self.width(), self.height()
        occupied = self._get_occupied_regions(exclude_window)
        
        if not occupied:
            # 沒有其他視窗，返回整個區域
            return self._get_basic_zone_rect(zone, w, h)
        
        # 分析每個方向被佔用的邊界
        # 左側被佔用到哪裡（從左邊開始）
        left_boundary = 0
        # 右側從哪裡開始被佔用（從右邊開始）
        right_boundary = w
        # 上方被佔用到哪裡
        top_boundary = 0
        # 下方從哪裡開始被佔用
        bottom_boundary = h
        
        for region in occupied:
            region_center_x = region.x() + region.width() // 2
            region_center_y = region.y() + region.height() // 2
            
            # 判斷視窗在哪個區域
            is_left_half = region_center_x < w // 2
            is_top_half = region_center_y < h // 2
            
            # 更新邊界
            if is_left_half:
                # 視窗在左半邊
                left_boundary = max(left_boundary, region.right())
            else:
                # 視窗在右半邊
                right_boundary = min(right_boundary, region.x())
            
            if is_top_half:
                # 視窗在上半邊
                top_boundary = max(top_boundary, region.bottom())
            else:
                # 視窗在下半邊
                bottom_boundary = min(bottom_boundary, region.y())
        
        # 根據區域類型計算可用空間
        half_h = h // 2
        
        if zone == SnapZone.LEFT:
            # 左側：從 0 到左邊界，或者如果左邊界是0則使用剩餘空間
            if left_boundary > 0:
                # 左側已被佔用，不能再放
                return QRect()
            return QRect(0, 0, right_boundary, h)
            
        elif zone == SnapZone.RIGHT:
            # 右側：從右邊界到末端
            if right_boundary < w:
                # 右側已被佔用，返回剩餘右側空間
                return QRect(left_boundary, 0, w - left_boundary, h)
            return QRect(left_boundary, 0, w - left_boundary, h)
            
        elif zone == SnapZone.TOP:
            # 上方：從頂部到上邊界，寬度是剩餘寬度
            return QRect(left_boundary, 0, right_boundary - left_boundary, 
                        bottom_boundary if bottom_boundary < h else half_h)
            
        elif zone == SnapZone.BOTTOM:
            # 下方：從下邊界到底部
            return QRect(left_boundary, top_boundary, right_boundary - left_boundary, 
                        h - top_boundary)
            
        elif zone == SnapZone.TOP_LEFT:
            # 左上：左側上半部
            if left_boundary > 0:
                return QRect()  # 左側已被佔用
            return QRect(0, 0, right_boundary // 2, half_h)
            
        elif zone == SnapZone.TOP_RIGHT:
            # 右上：右側上半部
            start_x = max(left_boundary, w // 2)
            return QRect(start_x, 0, w - start_x, half_h)
            
        elif zone == SnapZone.BOTTOM_LEFT:
            # 左下：左側下半部
            # 找到左側上方視窗的底部邊界
            left_top_bottom = 0
            for region in occupied:
                if region.x() < w * 0.4 and region.y() < h * 0.5:
                    left_top_bottom = max(left_top_bottom, region.bottom())
            
            if left_top_bottom > 0:
                # 有左上視窗，填滿其下方空間
                return QRect(0, left_top_bottom, right_boundary // 2, h - left_top_bottom)
            return QRect(0, half_h, right_boundary // 2, half_h)
            
        elif zone == SnapZone.BOTTOM_RIGHT:
            # 右下：右側下半部
            start_x = max(left_boundary, w // 2)
            return QRect(start_x, top_boundary if top_boundary > 0 else half_h, 
                        w - start_x, h - (top_boundary if top_boundary > 0 else half_h))
            
        elif zone == SnapZone.CENTER:
            # 中心：填滿剩餘空間
            return QRect(left_boundary, top_boundary, 
                        right_boundary - left_boundary, bottom_boundary - top_boundary)
        
        return QRect()
    
    def _get_basic_zone_rect(self, zone: 'SnapZone', w: int, h: int) -> QRect:
        """獲取基本區域矩形（沒有其他視窗時）"""
        half_w, half_h = w // 2, h // 2
        
        zone_map = {
            SnapZone.TOP_LEFT: QRect(0, 0, half_w, half_h),
            SnapZone.TOP_RIGHT: QRect(half_w, 0, half_w, half_h),
            SnapZone.BOTTOM_LEFT: QRect(0, half_h, half_w, half_h),
            SnapZone.BOTTOM_RIGHT: QRect(half_w, half_h, half_w, half_h),
            SnapZone.TOP: QRect(0, 0, w, half_h),
            SnapZone.BOTTOM: QRect(0, half_h, w, half_h),
            SnapZone.LEFT: QRect(0, 0, half_w, h),
            SnapZone.RIGHT: QRect(half_w, 0, half_w, h),
            SnapZone.CENTER: QRect(0, 0, w, h),
        }
        return zone_map.get(zone, QRect())
    
    def resizeEvent(self, event):
        """MDI 區域調整大小時，重新排列固定視窗"""
        super().resizeEvent(event)
        
        # 重新排列固定視窗（保持水平並列）
        self._rearrange_fixed_windows()
    
    def _rearrange_fixed_windows(self):
        """重新排列固定的歡迎頁面視窗（三欄排列：左欄上下分割）"""
        # 獲取所有固定視窗
        fixed_windows = [
            sw for sw in self.subWindowList() 
            if sw.property("is_welcome_fixed")
        ]
        
        if not fixed_windows:
            logger.debug(f"[MDI_RESIZE] 沒有找到固定視窗")
            return
        
        # 按位置分類視窗
        left_top_window = None
        left_bottom_window = None
        middle_window = None
        right_window = None
        
        for sw in fixed_windows:
            position = sw.property("welcome_position")
            if position == "left_top":
                left_top_window = sw
            elif position == "left_bottom":
                left_bottom_window = sw
            elif position == "middle":
                middle_window = sw
            elif position == "right":
                right_window = sw
        
        # 計算視窗尺寸
        mdi_width = self.width()
        mdi_height = self.height()
        
        logger.debug(f"[MDI_RESIZE] 重新排列 {len(fixed_windows)} 個固定視窗（三欄排列）")
        logger.debug(f"[MDI_RESIZE] MDI 尺寸: {mdi_width}x{mdi_height}")
        
        # 三欄寬度: 左 33%, 中 33%, 右 34%
        left_width = mdi_width // 3
        middle_width = mdi_width // 3
        right_width = mdi_width - left_width - middle_width
        
        # 左欄高度: 上 45%, 下 55%
        left_top_height = int(mdi_height * 0.45)
        left_bottom_height = mdi_height - left_top_height
        
        # 重新設定每個視窗的位置和大小
        if left_top_window:
            old_geom = left_top_window.geometry()
            left_top_window.setGeometry(0, 0, left_width, left_top_height)
            new_geom = left_top_window.geometry()
            logger.debug(f"[MDI_RESIZE] 左上視窗 ({left_top_window.windowTitle()}): {old_geom.width()}x{old_geom.height()} -> {new_geom.width()}x{new_geom.height()}")
        
        if left_bottom_window:
            old_geom = left_bottom_window.geometry()
            left_bottom_window.setGeometry(0, left_top_height, left_width, left_bottom_height)
            new_geom = left_bottom_window.geometry()
            logger.debug(f"[MDI_RESIZE] 左下視窗 ({left_bottom_window.windowTitle()}): {old_geom.width()}x{old_geom.height()} -> {new_geom.width()}x{new_geom.height()}")
        
        if middle_window:
            old_geom = middle_window.geometry()
            middle_window.setGeometry(left_width, 0, middle_width, mdi_height)
            new_geom = middle_window.geometry()
            logger.debug(f"[MDI_RESIZE] 中欄視窗 ({middle_window.windowTitle()}): {old_geom.width()}x{old_geom.height()} -> {new_geom.width()}x{new_geom.height()}")
        
        if right_window:
            old_geom = right_window.geometry()
            right_window.setGeometry(left_width + middle_width, 0, right_width, mdi_height)
            new_geom = right_window.geometry()
            logger.debug(f"[MDI_RESIZE] 右欄視窗 ({right_window.windowTitle()}): {old_geom.width()}x{old_geom.height()} -> {new_geom.width()}x{new_geom.height()}")

        
    def addSubWindow(self, widget, flags=None):
        """添加子視窗並強制執行最小尺寸 - 簡化版本"""
        if flags is not None:
            subwindow = super().addSubWindow(widget, flags)
        else:
            subwindow = super().addSubWindow(widget)
        
        # 使用樣式表隱藏標題列但保留邊框
        if subwindow:
            subwindow.setStyleSheet("""
                QMdiSubWindow::title {
                    height: 0px;
                    margin: 0px;
                    padding: 0px;
                    background: transparent;
                    border: none;
                }
                QMdiSubWindow {
                    border: 2px solid #666666;
                    border-radius: 2px;
                    background-color: #FFFFFF;
                }
            """)
            
            # 添加視窗後更新滾動範圍
            # 使用 QTimer 延遲執行，確保視窗已完全添加和佈局
            QTimer.singleShot(100, self._update_scroll_area)
        
        return subwindow

    def _update_scroll_area(self):
        """
        更新 MDI 區域的滾動範圍，確保所有視窗都可訪問
        
        計算所有子視窗的實際佔用範圍，並更新 MDI 的虛擬大小
        這樣當視窗超出可視範圍時，滾動條會自動出現
        """
        if not self.subWindowList():
            return
        
        # 計算所有視窗的邊界矩形
        max_right = 0
        max_bottom = 0
        
        for subwindow in self.subWindowList():
            if not subwindow.isVisible():
                continue
            
            geometry = subwindow.geometry()
            right = geometry.x() + geometry.width()
            bottom = geometry.y() + geometry.height()
            
            max_right = max(max_right, right)
            max_bottom = max(max_bottom, bottom)
        
        # 如果有視窗超出當前可視範圍，更新虛擬大小
        current_width = self.width()
        current_height = self.height()
        
        if max_right > current_width or max_bottom > current_height:
            # 添加一些邊距（讓視窗不會緊貼邊緣）
            padding = 50
            required_width = max(current_width, max_right + padding)
            required_height = max(current_height, max_bottom + padding)
            
            # 這個方法會讓 QMdiArea 知道實際內容大小
            # 從而自動顯示滾動條
            logger.debug(f"[MDI_SCROLL] 檢測到視窗超出範圍")
            logger.debug(f"[MDI_SCROLL]   可視範圍: {current_width}x{current_height}")
            logger.debug(f"[MDI_SCROLL]   實際範圍: {max_right}x{max_bottom}")
            logger.debug(f"[MDI_SCROLL]   滾動條已自動啟用")
            
            # QMdiArea 會自動根據子視窗位置調整滾動範圍
            # 但我們可以手動觸發更新
            self.updateGeometry()

    # ========== Snap 功能方法 ==========
    
    def detect_snap_zone(self, global_pos, dragging_window=None) -> SnapZone:
        """
        根據滑鼠全局位置檢測 Snap 區域
        
        檢測優先級：
        1. MDI 區域邊緣（角落和邊緣）
        2. 已存在視窗的邊緣（貼靠在其他視窗旁邊）
        """
        if not self._snap_enabled:
            return SnapZone.NONE
            
        # 清除之前的視窗邊緣 Snap 記錄
        self._window_edge_snap_rect = None
            
        # 將全局座標轉換為 MDI 區域的本地座標
        local_pos = self.mapFromGlobal(global_pos)
        x, y = local_pos.x(), local_pos.y()
        w, h = self.width(), self.height()
        
        # 邊緣閾值 (用於邊緣 Snap)
        edge_threshold = self._snap_threshold  # 30 像素
        # 角落閾值 (更大的區域，更容易觸發角落 Snap)
        corner_threshold = 80  # 80 像素
        
        # ===== 第一優先：MDI 區域邊緣 =====
        
        # 邊界檢查 - 角落使用較大閾值
        at_left_corner = x < corner_threshold
        at_right_corner = x > w - corner_threshold
        at_top_corner = y < corner_threshold
        at_bottom_corner = y > h - corner_threshold
        
        # 邊界檢查 - 邊緣使用較小閾值
        at_left_edge = x < edge_threshold
        at_right_edge = x > w - edge_threshold
        at_top_edge = y < edge_threshold
        at_bottom_edge = y > h - edge_threshold
        
        # 角落優先（25% 區域）- 使用較大的檢測區域
        if at_top_corner and at_left_corner:
            return SnapZone.TOP_LEFT
        if at_top_corner and at_right_corner:
            return SnapZone.TOP_RIGHT
        if at_bottom_corner and at_left_corner:
            return SnapZone.BOTTOM_LEFT
        if at_bottom_corner and at_right_corner:
            return SnapZone.BOTTOM_RIGHT
            
        # 邊緣（50% 區域）
        if at_top_edge:
            return SnapZone.TOP
        if at_bottom_edge:
            return SnapZone.BOTTOM
        if at_left_edge:
            return SnapZone.LEFT
        if at_right_edge:
            return SnapZone.RIGHT
        
        # ===== 第二優先：已存在視窗的邊緣 =====
        snap_rect = self._detect_window_edge_snap(x, y, dragging_window)
        if snap_rect and not snap_rect.isNull():
            self._window_edge_snap_rect = snap_rect
            return SnapZone.CENTER  # 使用 CENTER 作為標記，實際區域在 _window_edge_snap_rect
            
        return SnapZone.NONE
    
    def _detect_window_edge_snap(self, x: int, y: int, exclude_window=None) -> QRect:
        """
        檢測是否靠近其他視窗的邊緣，並計算精確的貼靠區域
        會避開所有已存在的視窗
        
        返回：要貼靠的精確矩形區域，或 None
        """
        w, h = self.width(), self.height()
        window_edge_threshold = 30  # 視窗邊緣檢測閾值
        
        occupied = self._get_occupied_regions(exclude_window)
        if not occupied:
            return None
        
        for region in occupied:
            # 檢查是否靠近該視窗的右邊緣
            if abs(x - region.right()) < window_edge_threshold:
                if region.y() <= y <= region.bottom():
                    # 計算右側可用空間（避開其他視窗）
                    snap_x = region.right()
                    snap_y = region.y()
                    snap_h = region.height()
                    
                    # 找到右側最近的視窗邊界
                    snap_w = w - snap_x  # 預設到 MDI 右邊界
                    for other in occupied:
                        if other == region:
                            continue
                        # 檢查是否在同一水平範圍內
                        if self._ranges_overlap(snap_y, snap_y + snap_h, other.y(), other.bottom()):
                            # 這個視窗可能會擋住
                            if other.x() > snap_x:
                                snap_w = min(snap_w, other.x() - snap_x)
                    
                    if snap_w > 100:
                        return QRect(snap_x, snap_y, snap_w, snap_h)
            
            # 檢查是否靠近該視窗的下邊緣
            if abs(y - region.bottom()) < window_edge_threshold:
                if region.x() <= x <= region.right():
                    # 計算下方可用空間（避開其他視窗）
                    snap_x = region.x()
                    snap_y = region.bottom()
                    snap_w = region.width()
                    
                    # 找到下方最近的視窗邊界
                    snap_h = h - snap_y  # 預設到 MDI 下邊界
                    for other in occupied:
                        if other == region:
                            continue
                        # 檢查是否在同一垂直範圍內
                        if self._ranges_overlap(snap_x, snap_x + snap_w, other.x(), other.right()):
                            if other.y() > snap_y:
                                snap_h = min(snap_h, other.y() - snap_y)
                    
                    if snap_h > 100:
                        return QRect(snap_x, snap_y, snap_w, snap_h)
            
            # 檢查是否靠近該視窗的左邊緣（從左側貼靠）
            if abs(x - region.x()) < window_edge_threshold and x < region.x():
                if region.y() <= y <= region.bottom():
                    # 計算左側可用空間
                    snap_y = region.y()
                    snap_h = region.height()
                    snap_w = region.x()  # 從 0 到視窗左邊
                    
                    # 找到左側最近的視窗邊界
                    snap_x = 0
                    for other in occupied:
                        if other == region:
                            continue
                        if self._ranges_overlap(snap_y, snap_y + snap_h, other.y(), other.bottom()):
                            if other.right() < region.x():
                                snap_x = max(snap_x, other.right())
                    
                    snap_w = region.x() - snap_x
                    if snap_w > 100:
                        return QRect(snap_x, snap_y, snap_w, snap_h)
            
            # 檢查是否靠近該視窗的上邊緣（從上方貼靠）
            if abs(y - region.y()) < window_edge_threshold and y < region.y():
                if region.x() <= x <= region.right():
                    # 計算上方可用空間
                    snap_x = region.x()
                    snap_w = region.width()
                    snap_h = region.y()  # 從 0 到視窗上邊
                    
                    # 找到上方最近的視窗邊界
                    snap_y = 0
                    for other in occupied:
                        if other == region:
                            continue
                        if self._ranges_overlap(snap_x, snap_x + snap_w, other.x(), other.right()):
                            if other.bottom() < region.y():
                                snap_y = max(snap_y, other.bottom())
                    
                    snap_h = region.y() - snap_y
                    if snap_h > 100:
                        return QRect(snap_x, snap_y, snap_w, snap_h)
        
        return None
    
    def _ranges_overlap(self, a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
        """檢查兩個範圍是否有重疊"""
        return a_start < b_end and b_start < a_end
    
    def show_snap_preview(self, zone: SnapZone, module_name: str = None, dragging_window=None):
        """顯示 Snap 預覽（支援 Smart Width 和動態剩餘空間，會檢查碰撞）"""
        if zone == SnapZone.NONE:
            self._snap_preview.hide_preview()
        else:
            # 檢查是否有視窗邊緣 Snap 的精確區域
            if zone == SnapZone.CENTER and self._window_edge_snap_rect:
                preview_rect = self._window_edge_snap_rect
            else:
                # 使用 get_snap_geometry 計算預覽區域
                preview_rect = self.get_snap_geometry(zone, module_name, dragging_window)
            
            # 碰撞檢測：如果會覆蓋其他視窗，不顯示預覽
            if self._would_overlap_other_windows(preview_rect, dragging_window):
                self._snap_preview.hide_preview()
                return
            
            self._snap_preview.set_geometry_direct(preview_rect)
            self._snap_preview.raise_()  # 確保預覽在最上層
    
    def _would_overlap_other_windows(self, target_rect: QRect, exclude_window=None) -> bool:
        """
        檢查目標區域是否會與其他視窗重疊
        
        返回：True 如果會重疊，False 如果不會
        """
        if target_rect.isNull():
            return True
            
        occupied = self._get_occupied_regions(exclude_window)
        
        for region in occupied:
            # 檢查兩個矩形是否相交
            if target_rect.intersects(region):
                # 計算重疊面積
                intersection = target_rect.intersected(region)
                overlap_area = intersection.width() * intersection.height()
                # 如果重疊面積超過 100 平方像素，視為覆蓋
                if overlap_area > 100:
                    return True
        
        return False
            
    def hide_snap_preview(self):
        """隱藏 Snap 預覽"""
        self._snap_preview.hide_preview()
        
    def get_snap_geometry(self, zone: SnapZone, module_name: str = None, exclude_window=None) -> QRect:
        """
        根據 Snap 區域獲取目標幾何形狀（支援動態剩餘空間計算，避免覆蓋任何視窗）
        
        規則：
        - 所有 Snap 區域都會避開已存在的視窗
        - LEFT/RIGHT: 靠邊對齊，寬度 = Smart Width (30%)
        - TOP/BOTTOM: 靠邊對齊，高度 = 50%
        - 角落區域: 固定位置 30%x50%
        - CENTER: 填滿剩餘最大空間
        """
        w, h = self.width(), self.height()
        half_h = h // 2
        
        # 獲取 Smart Width 參數
        size_hints = MODULE_SIZE_HINTS.get(module_name, MODULE_SIZE_HINTS['default'])
        preferred_ratio = size_hints.get('preferred_ratio', 0.30)
        min_width = size_hints.get('min_width', 250)
        
        # 計算 Smart Width (基於總寬度)
        smart_w = max(min_width, int(w * preferred_ratio))
        smart_w = min(smart_w, w // 2)  # 不超過一半寬度
        
        # 獲取已佔用區域
        occupied = self._get_occupied_regions(exclude_window)
        
        # 計算各方向的精確邊界（考慮所有視窗）
        # 左側邊界：所有靠左視窗的最右邊界
        left_boundary = 0
        # 右側邊界：所有靠右視窗的最左邊界  
        right_boundary = w
        # 上方邊界：所有靠上視窗的最下邊界
        top_boundary = 0
        # 下方邊界：所有靠下視窗的最上邊界
        bottom_boundary = h
        
        # 分析每個視窗的位置
        for region in occupied:
            # 判斷視窗相對位置
            # 如果視窗左邊緣靠近左側（在 smart_w 範圍內）
            if region.x() < smart_w:
                left_boundary = max(left_boundary, region.right())
            
            # 如果視窗右邊緣靠近右側
            if region.right() > w - smart_w:
                right_boundary = min(right_boundary, region.x())
            
            # 如果視窗上邊緣靠近頂部（在 half_h 範圍內）
            if region.y() < half_h:
                # 只有當視窗確實在上半部時才更新
                if region.bottom() < h * 0.6:  # 容差
                    top_boundary = max(top_boundary, region.bottom())
            
            # 如果視窗下邊緣靠近底部
            if region.bottom() > half_h:
                # 只有當視窗確實在下半部時才更新
                if region.y() > h * 0.4:  # 容差
                    bottom_boundary = min(bottom_boundary, region.y())
        
        # 根據區域計算幾何形狀
        if zone == SnapZone.LEFT:
            # 靠左對齊，Smart Width，避開上下已佔用區域
            # 檢查左側是否已被完全佔用
            if left_boundary >= smart_w:
                # 左側已被佔用，嘗試在現有左側視窗旁邊
                pass  # 使用預設位置，但縮小高度
            y_start = 0
            y_height = h
            # 尋找左側的垂直可用空間
            for region in occupied:
                if region.x() < smart_w:  # 左側有視窗
                    if region.y() == 0:  # 視窗從頂部開始
                        y_start = max(y_start, region.bottom())
                    if region.bottom() >= h - 10:  # 視窗到底部
                        y_height = min(y_height, region.y())
            if y_start > 0:
                y_height = h - y_start
            return QRect(0, y_start, smart_w, y_height)
            
        elif zone == SnapZone.RIGHT:
            # 靠右對齊，Smart Width，避開上下已佔用區域
            y_start = 0
            y_height = h
            for region in occupied:
                if region.right() > w - smart_w:  # 右側有視窗
                    if region.y() == 0:
                        y_start = max(y_start, region.bottom())
                    if region.bottom() >= h - 10:
                        y_height = min(y_height, region.y())
            if y_start > 0:
                y_height = h - y_start
            return QRect(w - smart_w, y_start, smart_w, y_height)
            
        elif zone == SnapZone.TOP:
            # 靠上對齊，避開左右已佔用區域
            x_start = left_boundary if left_boundary > 0 else 0
            x_end = right_boundary if right_boundary < w else w
            # 避免寬度太小
            if x_end - x_start < min_width:
                x_start = 0
                x_end = w
            return QRect(x_start, 0, x_end - x_start, half_h)
            
        elif zone == SnapZone.BOTTOM:
            # 靠下對齊，避開左右已佔用區域
            x_start = left_boundary if left_boundary > 0 else 0
            x_end = right_boundary if right_boundary < w else w
            if x_end - x_start < min_width:
                x_start = 0
                x_end = w
            return QRect(x_start, half_h, x_end - x_start, half_h)
            
        elif zone == SnapZone.TOP_LEFT:
            # 檢查左上是否已被佔用
            for region in occupied:
                if region.x() < smart_w and region.y() < half_h:
                    # 左上已有視窗，嘗試放在它下面
                    if region.bottom() < h - 50:
                        return QRect(0, region.bottom(), smart_w, half_h)
            return QRect(0, 0, smart_w, half_h)
            
        elif zone == SnapZone.TOP_RIGHT:
            # 檢查右上是否已被佔用
            for region in occupied:
                if region.right() > w - smart_w and region.y() < half_h:
                    if region.bottom() < h - 50:
                        return QRect(w - smart_w, region.bottom(), smart_w, half_h)
            return QRect(w - smart_w, 0, smart_w, half_h)
            
        elif zone == SnapZone.BOTTOM_LEFT:
            # 檢查左下是否已被佔用
            for region in occupied:
                if region.x() < smart_w and region.bottom() > half_h:
                    if region.y() > 50:
                        return QRect(0, region.y() - half_h, smart_w, half_h)
            return QRect(0, half_h, smart_w, half_h)
            
        elif zone == SnapZone.BOTTOM_RIGHT:
            # 檢查右下是否已被佔用
            for region in occupied:
                if region.right() > w - smart_w and region.bottom() > half_h:
                    if region.y() > 50:
                        return QRect(w - smart_w, region.y() - half_h, smart_w, half_h)
            return QRect(w - smart_w, half_h, smart_w, half_h)
            
        elif zone == SnapZone.CENTER:
            # 中心：填滿剩餘最大空間
            return self._find_largest_empty_rect(occupied, w, h)
        
        return QRect()
    
    def _find_largest_empty_rect(self, occupied: list, w: int, h: int) -> QRect:
        """找到最大的空白矩形區域（更精確的計算）"""
        if not occupied:
            return QRect(0, 0, w, h)
        
        # 計算所有視窗的邊界
        all_left_edges = [0]  # 包含左邊界
        all_right_edges = [w]  # 包含右邊界
        all_top_edges = [0]  # 包含上邊界
        all_bottom_edges = [h]  # 包含下邊界
        
        for region in occupied:
            all_left_edges.append(region.right())  # 視窗右邊是空白開始
            all_right_edges.append(region.x())  # 視窗左邊是空白結束
            all_top_edges.append(region.bottom())  # 視窗下邊是空白開始
            all_bottom_edges.append(region.y())  # 視窗上邊是空白結束
        
        # 找到最大的連續空白區域
        # 策略：檢查左側視窗的右邊到 MDI 右邊界
        left_boundary = max(r.right() for r in occupied if r.x() < w * 0.4)  if any(r.x() < w * 0.4 for r in occupied) else 0
        right_boundary = min(r.x() for r in occupied if r.right() > w * 0.6) if any(r.right() > w * 0.6 for r in occupied) else w
        top_boundary = max(r.bottom() for r in occupied if r.y() < h * 0.4) if any(r.y() < h * 0.4 for r in occupied) else 0
        bottom_boundary = min(r.y() for r in occupied if r.bottom() > h * 0.6) if any(r.bottom() > h * 0.6 for r in occupied) else h
        
        # 計算結果
        result_x = left_boundary
        result_y = top_boundary  
        result_w = right_boundary - left_boundary
        result_h = bottom_boundary - top_boundary
        
        # 確保有最小尺寸，否則返回原始區域
        if result_w < 100 or result_h < 100:
            # 嘗試找到任何可用空間
            return QRect(left_boundary, 0, w - left_boundary, h)
        
        return QRect(result_x, result_y, result_w, result_h)
    
    def snap_window_to_zone(self, subwindow, zone: SnapZone):
        """將子視窗 Snap 到指定區域（支援動態剩餘空間計算和視窗邊緣貼靠）"""
        if zone == SnapZone.NONE:
            return
        
        # 檢查是否有視窗邊緣 Snap 的精確區域
        if zone == SnapZone.CENTER and self._window_edge_snap_rect:
            target_geometry = self._window_edge_snap_rect
            self._window_edge_snap_rect = None  # 清除記錄
            
            # 碰撞檢測：確保不會覆蓋其他視窗
            if self._would_overlap_other_windows(target_geometry, subwindow):
                logger.debug(f"[SNAP] 取消：目標區域會覆蓋其他視窗")
                return
            
            logger.debug(f"[SNAP] 視窗邊緣貼靠 '{subwindow.windowTitle()}'")
            logger.debug(f"[SNAP] 目標區域: {target_geometry.x()},{target_geometry.y()} {target_geometry.width()}x{target_geometry.height()}")
            subwindow.setGeometry(target_geometry)
            return
            
        # 獲取模組名稱（用於 Smart Width）
        module_name = None
        if hasattr(subwindow, 'analysis_module') and subwindow.analysis_module:
            if hasattr(subwindow.analysis_module, 'analysis_type'):
                module_name = subwindow.analysis_module.analysis_type
        
        # 嘗試從標題推斷模組名稱
        if not module_name:
            title = subwindow.windowTitle().lower()
            if 'lap time' in title or 'distribution' in title:
                module_name = 'lap_time_distribution'
            elif 'circle' in title:
                module_name = 'circle_map'
            elif 'ranking' in title or 'tower' in title:
                module_name = 'ranking_tower'
            elif 'strategy' in title:
                module_name = 'driver_strategy'
            elif 'track' in title:
                module_name = 'circle_map'
        
        # 獲取目標幾何形狀（排除當前視窗以計算剩餘空間）
        target_geometry = self.get_snap_geometry(zone, module_name, subwindow)
        
        if not target_geometry.isNull():
            # 碰撞檢測：確保不會覆蓋其他視窗
            if self._would_overlap_other_windows(target_geometry, subwindow):
                logger.debug(f"[SNAP] 取消：目標區域會覆蓋其他視窗")
                return
            
            logger.debug(f"[SNAP] Snap 視窗 '{subwindow.windowTitle()}' 到 {zone.name}")
            logger.debug(f"[SNAP] 模組類型: {module_name}")
            logger.debug(f"[SNAP] 目標區域: {target_geometry.x()},{target_geometry.y()} {target_geometry.width()}x{target_geometry.height()}")
            subwindow.setGeometry(target_geometry)
            
    def set_snap_enabled(self, enabled: bool):
        """啟用或禁用 Snap 功能"""
        self._snap_enabled = enabled
        if not enabled:
            self.hide_snap_preview()
    
    # ========== 磁吸對齊功能 ==========
    
    def _on_subwindow_activated(self, window):
        """子視窗激活時安裝事件過濾器"""
        if window and getattr(self, '_magnetic_snap_enabled', False):
            window.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """事件過濾器 - 監聽子視窗移動並實現磁吸對齊"""
        # 防禦性檢查：如果屬性還未初始化，直接返回
        if not getattr(self, '_magnetic_snap_enabled', False):
            return super().eventFilter(obj, event)
        
        # 防止遞迴：如果正在應用 snap，不處理新的移動事件
        if getattr(self, '_is_applying_snap', False):
            return super().eventFilter(obj, event)
        
        # 只處理 QMdiSubWindow 的移動事件
        if isinstance(obj, QMdiSubWindow) and event.type() == event.Move:
            self._apply_magnetic_snap(obj)
        
        return super().eventFilter(obj, event)
    
    def _apply_magnetic_snap(self, moving_window):
        """應用磁吸對齊到正在移動的視窗"""
        if moving_window.property("is_welcome_fixed"):
            return  # 不對固定視窗應用磁吸
        
        # 防止遞迴
        if getattr(self, '_is_applying_snap', False):
            return
        
        current_geo = moving_window.geometry()
        snapped_geo = self._calculate_magnetic_snap_position(moving_window, current_geo)
        
        if snapped_geo != current_geo:
            try:
                self._is_applying_snap = True
                moving_window.setGeometry(snapped_geo)
            finally:
                self._is_applying_snap = False
    
    def _calculate_magnetic_snap_position(self, moving_window, current_geo):
        """計算磁吸對齊後的位置"""
        snap_distance = self._magnetic_snap_distance
        
        # 獲取所有其他視窗
        other_windows = [w for w in self.subWindowList() 
                        if w != moving_window and not w.property("is_welcome_fixed") 
                        and w.isVisible()]
        
        if not other_windows:
            return current_geo
        
        # 當前視窗的邊界
        left = current_geo.left()
        right = current_geo.right()
        top = current_geo.top()
        bottom = current_geo.bottom()
        
        # 用於記錄最近的對齊目標
        snap_left = None
        snap_right = None
        snap_top = None
        snap_bottom = None
        
        # 檢測與其他視窗的磁吸
        for other in other_windows:
            other_geo = other.geometry()
            
            # 垂直對齊檢測（上下邊緣是否在相似高度）
            vertical_overlap = (
                (top >= other_geo.top() - snap_distance * 3 and top <= other_geo.bottom() + snap_distance * 3) or
                (bottom >= other_geo.top() - snap_distance * 3 and bottom <= other_geo.bottom() + snap_distance * 3)
            )
            
            # 水平對齊檢測
            horizontal_overlap = (
                (left >= other_geo.left() - snap_distance * 3 and left <= other_geo.right() + snap_distance * 3) or
                (right >= other_geo.left() - snap_distance * 3 and right <= other_geo.right() + snap_distance * 3)
            )
            
            # 左邊緣對齊其他視窗的右邊緣
            if vertical_overlap and abs(left - other_geo.right()) < snap_distance:
                snap_left = other_geo.right()
            
            # 右邊緣對齊其他視窗的左邊緣
            if vertical_overlap and abs(right - other_geo.left()) < snap_distance:
                snap_right = other_geo.left()
            
            # 上邊緣對齊其他視窗的下邊緣
            if horizontal_overlap and abs(top - other_geo.bottom()) < snap_distance:
                snap_top = other_geo.bottom()
            
            # 下邊緣對齊其他視窗的上邊緣
            if horizontal_overlap and abs(bottom - other_geo.top()) < snap_distance:
                snap_bottom = other_geo.top()
            
            # 左邊緣對齊其他視窗的左邊緣
            if vertical_overlap and abs(left - other_geo.left()) < snap_distance:
                snap_left = other_geo.left()
            
            # 右邊緣對齊其他視窗的右邊緣
            if vertical_overlap and abs(right - other_geo.right()) < snap_distance:
                snap_right = other_geo.right()
            
            # 上邊緣對齊其他視窗的上邊緣
            if horizontal_overlap and abs(top - other_geo.top()) < snap_distance:
                snap_top = other_geo.top()
            
            # 下邊緣對齊其他視窗的下邊緣
            if horizontal_overlap and abs(bottom - other_geo.bottom()) < snap_distance:
                snap_bottom = other_geo.bottom()
        
        # 應用磁吸調整
        new_geo = QRect(current_geo)
        
        if snap_left is not None:
            new_geo.moveLeft(snap_left)
        elif snap_right is not None:
            new_geo.moveRight(snap_right)
        
        if snap_top is not None:
            new_geo.moveTop(snap_top)
        elif snap_bottom is not None:
            new_geo.moveBottom(snap_bottom)
        
        return new_geo
    
    def set_magnetic_snap_enabled(self, enabled: bool):
        """啟用或禁用磁吸對齊"""
        self._magnetic_snap_enabled = enabled
        logger.debug(f"[MDI] 磁吸對齊: {'啟用' if enabled else '禁用'}")
    
    def set_magnetic_snap_distance(self, distance: int):
        """設置磁吸距離閾值"""
        self._magnetic_snap_distance = max(5, min(50, distance))
        logger.debug(f"[MDI] 磁吸距離: {self._magnetic_snap_distance}px")
