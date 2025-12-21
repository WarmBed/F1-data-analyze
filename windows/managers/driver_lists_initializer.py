# -*- coding: utf-8 -*-
"""
DriverListsInitializer - 從 f1t_gui_main.py 提取
"""

from core.gui_i18n import tr
from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class DriverListsInitializer:
    """從 f1t_gui_main.py 提取的 initialize_driver_lists 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def initialize_driver_lists(self):
        """
        初始化車手列表 - 使用主視窗快取
        
        此方法已重構為使用主視窗的統一車手快取機制，
        不再重複讀取 JSON 或調用 API，提升效能並確保數據一致性。
        """
        logger.debug("[LAP_CONTROL] [DEBUG]   🎮 開始初始化車手列表（使用快取）")
            
        try:
            # 檢查控件狀態
            logger.debug(f"[LAP_CONTROL] [DEBUG]   🔍 檢查控件狀態:")
            logger.debug(f"[LAP_CONTROL] [DEBUG]     driver1_combo.isVisible(): {self.main_window.driver1_combo.isVisible()}")
            logger.debug(f"[LAP_CONTROL] [DEBUG]     driver1_combo.count(): {self.main_window.driver1_combo.count()}")
            logger.debug(f"[LAP_CONTROL] [DEBUG]     driver2_combo.isVisible(): {self.main_window.driver2_combo.isVisible()}")
            logger.debug(f"[LAP_CONTROL] [DEBUG]     driver2_combo.count(): {self.main_window.driver2_combo.count()}")
            
            # 獲取當前年份
            year_str = self.main_window.year_combo.currentText() if hasattr(self, 'year_combo') else "2025"
            year = int(year_str)
            
            logger.debug(f"[LAP_CONTROL] [DEBUG]   📅 目標年份: {year} (字串: '{year_str}')")
            
            # 🆕 從主視窗快取獲取車手列表
            logger.debug(f"[LAP_CONTROL] [DEBUG]   🔄 準備調用 self.main_window.get_drivers_for_year({year})...")
            logger.debug(f"[LAP_CONTROL] [DEBUG]   🔍 self 類型: {type(self).__name__}")
            logger.debug(f"[LAP_CONTROL] [DEBUG]   🔍 self.main_window._cached_drivers_by_year 存在: {hasattr(self, '_cached_drivers_by_year')}")
            
            drivers = self.main_window.get_drivers_for_year(year)
            
            logger.debug(f"[LAP_CONTROL] [DEBUG]   � get_drivers_for_year 返回: {type(drivers).__name__}, 長度={len(drivers)}")
            logger.debug(f"[LAP_CONTROL] [DEBUG]   🔍 車手列表內容: {drivers[:5] if len(drivers) > 5 else drivers}")
            
            logger.debug("[LAP_CONTROL] [DEBUG]   �🔄 清空並填充車手列表...")
            # 清空並添加車手到兩個下拉框
            logger.debug(f"[LAP_CONTROL] [DEBUG]   🔍 清空 driver1_combo...")
            self.main_window.driver1_combo.clear()
            logger.debug(f"[LAP_CONTROL] [DEBUG]   🔍 driver1_combo 清空後項目數: {self.main_window.driver1_combo.count()}")
            
            # 🔧 修復：使用 addItem 並設定 UserData
            logger.debug(f"[LAP_CONTROL] [DEBUG]   🔍 開始添加 {len(drivers)} 位車手到 driver1_combo...")
            for idx, driver in enumerate(drivers):
                self.main_window.driver1_combo.addItem(driver, driver)
                if idx < 3:  # 只顯示前 3 個的詳細信息
                    logger.debug(f"[LAP_CONTROL] [DEBUG]     添加 #{idx+1}: {driver}")
            
            logger.debug(f"[LAP_CONTROL] [DEBUG]   🔍 driver1_combo 添加後項目數: {self.main_window.driver1_combo.count()}")
            
            if drivers:
                logger.debug(f"[LAP_CONTROL] [DEBUG]   🔍 設置 driver1_combo 當前文字為: {drivers[0]}")
                self.main_window.driver1_combo.setCurrentText(drivers[0])  # 預設選擇第一個車手
                logger.debug(f"[LAP_CONTROL] [DEBUG]   🔍 driver1_combo.currentText(): {self.main_window.driver1_combo.currentText()}")
            logger.debug("[LAP_CONTROL] [DEBUG]   ✅ driver1_combo 設定完成")
            
            logger.debug(f"[LAP_CONTROL] [DEBUG]   🔍 清空 driver2_combo...")
            self.main_window.driver2_combo.clear()
            # 🔧 修復：第一個選項的 UserData 設為 None
            logger.debug(f"[LAP_CONTROL] [DEBUG]   🔍 添加 'None' 選項到 driver2_combo...")
            self.main_window.driver2_combo.addItem(tr("none_option", "None"), None)
            
            # 🔧 修復：使用 addItem 並設定 UserData（不使用 addItems）
            logger.debug(f"[LAP_CONTROL] [DEBUG]   🔍 開始添加 {len(drivers)} 位車手到 driver2_combo...")
            for idx, driver in enumerate(drivers):
                self.main_window.driver2_combo.addItem(driver, driver)
                if idx < 3:
                    logger.debug(f"[LAP_CONTROL] [DEBUG]     添加 #{idx+1}: {driver}")
            
            logger.debug(f"[LAP_CONTROL] [DEBUG]   🔍 driver2_combo 添加後項目數: {self.main_window.driver2_combo.count()}")
            self.main_window.driver2_combo.setCurrentIndex(0)  # 預設選擇 "None"
            logger.debug(f"[LAP_CONTROL] [DEBUG]   🔍 driver2_combo.currentText(): {self.main_window.driver2_combo.currentText()}")
            logger.debug("[LAP_CONTROL] [DEBUG]   ✅ driver2_combo 設定完成")
            
            # 驗證設定結果
            logger.debug(f"[LAP_CONTROL] [DEBUG]   📊 設定後狀態:")
            logger.debug(f"[LAP_CONTROL] [DEBUG]     driver1_combo當前文字: '{self.main_window.driver1_combo.currentText()}'")
            logger.debug(f"[LAP_CONTROL] [DEBUG]     driver2_combo當前文字: '{self.main_window.driver2_combo.currentText()}'")
            logger.debug(f"[LAP_CONTROL] [DEBUG]     driver1_combo項目數: {self.main_window.driver1_combo.count()}")
            logger.debug(f"[LAP_CONTROL] [DEBUG]     driver2_combo項目數: {self.main_window.driver2_combo.count()}")
            
            logger.debug(f"[LAP_CONTROL] [DEBUG]   ✅ 已初始化車手列表，共 {len(drivers)} 位車手")
            if drivers:
                logger.debug(f"[LAP_CONTROL] [DEBUG]   車手列表: {', '.join(drivers)}")
            
        except Exception as e:
            # 🔴 簡化錯誤日誌避免 traceback 持有 frame 引用
            logger.error(f"[ERROR] [LAP_CONTROL] [DEBUG]   初始化車手列表失敗: {e}")
            e = None  # 🔴 立即釋放異常對象
            # 調試時可以取消註解：
            # import traceback
            # print(f"[ERROR] [LAP_CONTROL] [DEBUG]   異常詳情: {traceback.format_exc()}")
