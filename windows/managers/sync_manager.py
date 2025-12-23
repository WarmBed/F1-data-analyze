# -*- coding: utf-8 -*-
"""
SyncManager - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class SyncManager:
    """從 f1t_gui_main.py 提取的 sync_all_independent_windows 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def sync_all_independent_windows(self, updated_params: dict):
        """
        同步所有停用同步的視窗（全域共享參數池功能）
        
        功能說明：
        - 當任一視窗取消勾選"與主視窗同步車手與圈數"時觸發
        - 更新全域共享參數池 (self.main_window.shared_independent_params)
        - 同步所有停用同步的視窗（跨模組類型：Speed/RPM/Gear 等）
        
        參數：
        - updated_params: 更新後的參數字典
          {
              'year1': str,      # 車手 1 年份
              'race1': str,      # 車手 1 賽事
              'session1': str,   # 車手 1 賽段
              'driver1': str,    # 車手 1 代號
              'lap1': int,       # 車手 1 圈數
              'year2': str,      # 車手 2 年份
              'race2': str,      # 車手 2 賽事
              'session2': str,   # 車手 2 賽段
              'driver2': str,    # 車手 2 代號
              'lap2': int,       # 車手 2 圈數
              'use_time_axis': bool  # 時間軸模式
          }
        
        流程：
        1. 更新全域共享參數池
        2. 遍歷所有 MDI 子視窗
        3. 篩選出 sync_driver_lap_enabled=False 的視窗
        4. 調用 update_from_shared_params() 方法同步參數
        
        使用場景：
        - 用戶在任一視窗取消勾選同步 checkbox
        - 用戶在停用同步的視窗修改 Year/Race/Session/Driver/Lap
        """
        from PyQt5.QtWidgets import QApplication
        
        logger.debug(f"\n{'='*100}")
        logger.debug(f"[SYNC_ALL_INDEPENDENT_WINDOWS] 方法被調用！")
        logger.debug(f"{'='*100}")
        logger.debug(f"[SHARED_PARAMS] 🔄 開始同步所有停用同步的視窗")
        logger.debug(f"[SHARED_PARAMS] 更新參數:")
        for key, value in updated_params.items():
            logger.debug(f"   {key}: {value}")
        logger.debug(f"{'='*100}\n")
        
        # 步驟 1: 更新全域共享參數池
        self.main_window.shared_independent_params.update(updated_params)
        logger.debug(f"[SHARED_PARAMS] ✅ 全域參數池已更新")
        
        # 步驟 2: 遍歷所有 MDI 子視窗
        synchronized_count = 0
        skipped_count = 0
        dialog_sync_count = 0
        total_windows = 0
        no_analysis_module = 0
        no_sync_attribute = 0
        
        for mdi_area in self.main_window.mdi_areas:
            for sub_window in mdi_area.subWindowList():
                total_windows += 1
                
                logger.debug(f"[SHARED_PARAMS] 檢查視窗 {total_windows}: {sub_window.windowTitle()}")
                
                # 步驟 3: 從 PopoutSubWindow 獲取 analysis_module
                # ⚠️ 重要：不是從 widget 獲取，而是從 sub_window 獲取
                if not hasattr(sub_window, 'analysis_module'):
                    logger.debug(f"[SHARED_PARAMS]   ⚠️  sub_window 沒有 analysis_module 屬性")
                    no_analysis_module += 1
                    continue
                
                analysis_module = sub_window.analysis_module
                logger.debug(f"[SHARED_PARAMS]   ✅ 有 analysis_module: {type(analysis_module).__name__}")
                
                # 檢查 sync_driver_lap_enabled 屬性（遙測模組的同步控制）
                if not hasattr(analysis_module, 'sync_driver_lap_enabled'):
                    logger.debug(f"[SHARED_PARAMS]   ⚠️  沒有 sync_driver_lap_enabled 屬性")
                    no_sync_attribute += 1
                    continue
                
                sync_status = analysis_module.sync_driver_lap_enabled
                logger.debug(f"[SHARED_PARAMS]   📊 sync_driver_lap_enabled = {sync_status}")
                
                if analysis_module.sync_driver_lap_enabled:
                    # 啟用同步的視窗，跳過
                    logger.debug(f"[SHARED_PARAMS]   ⏭️  已啟用同步，跳過")
                    skipped_count += 1
                    continue
                
                logger.debug(f"[SHARED_PARAMS]   ✅ 已停用同步，準備同步！")
                
                # 步驟 4: 調用 update_from_shared_params() 同步參數（更新分析模組）
                if hasattr(analysis_module, 'update_from_shared_params'):
                    try:
                        logger.debug(f"[SHARED_PARAMS] 🔄 同步視窗: {sub_window.windowTitle()}")
                        analysis_module.update_from_shared_params(self.main_window.shared_independent_params)
                        synchronized_count += 1
                        logger.debug(f"[SHARED_PARAMS] ✅ 視窗同步成功")
                    except Exception as e:
                        logger.debug(f"[SHARED_PARAMS] ❌ 視窗同步失敗: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    logger.debug(f"[SHARED_PARAMS] ⚠️  視窗 {sub_window.windowTitle()} 沒有 update_from_shared_params() 方法")
                
                # 步驟 5: 同步已打開的設定對話框（實時更新 UI）
                # ⚠️ 設定對話框應該在 sub_window 上，因為 show_settings_dialog() 設置的是 self.main_window.settings_dialog
                if hasattr(sub_window, 'settings_dialog') and sub_window.settings_dialog is not None:
                    try:
                        dialog = sub_window.settings_dialog
                        
                        # 檢查對話框是否可見且停用同步
                        if dialog.isVisible() and hasattr(dialog, 'sync_driver_lap_checkbox'):
                            if not dialog.sync_driver_lap_checkbox.isChecked():
                                logger.debug(f"[SHARED_PARAMS] 🔄 同步已打開的設定對話框: {sub_window.windowTitle()}")
                                dialog._load_shared_params_to_ui()
                                dialog_sync_count += 1
                                logger.debug(f"[SHARED_PARAMS] ✅ 設定對話框已同步")
                    except Exception as e:
                        logger.debug(f"[SHARED_PARAMS] ⚠️  設定對話框同步失敗: {e}")
        
        # 處理 UI 事件
        QApplication.processEvents()
        
        logger.debug(f"\n{'='*100}")
        logger.debug(f"[SHARED_PARAMS] ✅ 同步完成總結:")
        logger.debug(f"   � 總共檢查視窗: {total_windows} 個")
        logger.debug(f"   ⚠️  無 analysis_module: {no_analysis_module} 個")
        logger.debug(f"   ⚠️  無 sync_driver_lap_enabled: {no_sync_attribute} 個")
        logger.debug(f"   ⏭️  已啟用同步（跳過）: {skipped_count} 個")
        logger.debug(f"   📊 分析模組已同步: {synchronized_count} 個")
        logger.debug(f"   🔧 設定對話框已同步: {dialog_sync_count} 個")
        logger.debug(f"{'='*100}\n")
