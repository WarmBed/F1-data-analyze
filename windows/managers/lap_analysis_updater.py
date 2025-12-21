# -*- coding: utf-8 -*-
"""
LapAnalysisUpdater - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox
from core.gui_i18n import tr
from core.logger import get_logger

from core.logger import get_logger
from PyQt5.QtWidgets import QApplication

logger = get_logger(__name__)


class LapAnalysisUpdater:
    """從 f1t_gui_main.py 提取的 update_all_lap_analysis 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def update_all_lap_analysis(self, *args, **kwargs):
        """序列化更新所有遙測分析視窗（防止並發衝突）"""
        # ✅ 調試點 1: 方法入口
        logger.info("🟢 [DEBUG]    ========== update_all_lap_analysis 開始 ==========")
        logger.debug("🟢 [DEBUG]    ========== update_all_lap_analysis 開始 ==========")
        
        from PyQt5.QtWidgets import QProgressDialog
        from PyQt5.QtCore import Qt
        import time
        
        logger.debug("[LAP_CONTROL] [DEBUG]   🔄 開始序列化更新所有圈速分析視窗...")
        logger.info("[LAP_CONTROL] [DEBUG]   開始序列化更新所有圈速分析視窗")
        
        # ✅ 調試點 2: 檢查視窗數量
        lap_window_count = len(self.main_window.lap_analysis_windows)
        logger.info(f"🟢 [DEBUG]    lap_analysis_windows 數量: {lap_window_count}")
        logger.debug(f"🟢 [DEBUG]    lap_analysis_windows 數量: {lap_window_count}")
        
        # 定義應該被更新的分析類型（包含所有模組類型）
        all_analysis_types = {
            # 遙測分析類型
            'speed_analysis',  # 速度分析
            'speed',          # 速度圖表
            'brake',          # 煞車分析
            'throttle',       # 油門分析
            'steering',       # 轉向分析
            'gear',           # 檔位分析
            'rpm',            # RPM分析
            'acceleration',   # 加速度分析
            'speed_diff',     # 速度差分析
            'Speeddiff',      # 速度差分析（大寫變體）
            'distancediff',   # 累積距離差分析
            'Distancediff',   # 累積距離差分析（大寫變體）
            'timediff',       # 累積時間差分析
            'Timediff',       # 累積時間差分析（大寫變體）
            'laptime',        # 詳細圈速分析
            'laptime_boxplot',  # 圈速箱型圖
            'throttle_boxplot',  # 油門箱型圖
            'throttle_line_chart_single_driver',  # 油門折線圖（單車手）
            # 賽事級分析類型
            'rain_weather',   # 天氣分析
            'pitstop',        # 進站分析
            'accident',       # 事故分析
            'tire',           # 輪胎分析
            'ideal_lap',      # 理想圈速分析
            'ideal_lap_ranking',           # 理想圈排名表格
            'ideal_lap_sector_comparison', # 理想圈分段對比
            'ideal_lap_sector_heatmap',    # 理想圈分段熱力圖
            'track_analysis',  # 賽道分析
            'driver_position',  # 車手比賽排名分析 (F25)
            'qualifying_prediction',  # ✅ 排位賽預測 (F74 v3.8) - 新增
            'race_prediction',  # ✅ 正賽預測 (F80) Q → R - 修復參數更新問題
            'all_drivers_straight_line_speed',  # 全車手直線速度分析
            'all_drivers_max_speed',            # 全車手最高速度分析 (F121)
            'all_drivers_acceleration_chart',   # 全車手加速度圖表 (F121)
            'all_drivers_brake_chart',          # 全車手煞車圖表 (F122)
            'all_drivers_brake_performance',    # 全車手煞車性能分析 (F34)
            'all_drivers_brake_all_laps',       # 全車手煞車全圈數分析 (F122)
            'corner_performance',  # 彎道性能分析 (F47) - Low/Mid/High Speed Corners
            'historical_track_map',  # ✅ 歷年賽道旗幟統計 (F100)
        }
        
        # 獲取當前設置
        driver1 = self.main_window.driver1_combo.currentText()
        
        # 獲取時間軸設定
        # ✅ 修復: hasattr 必須檢查 self.main_window，而不是 self
        use_time_axis = self.main_window.use_time_axis_checkbox.isChecked() if hasattr(self.main_window, 'use_time_axis_checkbox') else False
        logger.debug(f"🕒 [TIME_AXIS_DEBUG] ========== 時間軸追蹤開始 ==========")
        logger.debug(f"🕒 [TIME_AXIS_DEBUG] 步驟 1: 讀取復選框狀態")
        logger.debug(f"🕒 [TIME_AXIS_DEBUG]   hasattr(self.main_window, 'use_time_axis_checkbox'): {hasattr(self.main_window, 'use_time_axis_checkbox')}")
        if hasattr(self.main_window, 'use_time_axis_checkbox'):
            logger.debug(f"🕒 [TIME_AXIS_DEBUG]   use_time_axis_checkbox.isChecked(): {self.main_window.use_time_axis_checkbox.isChecked()}")
        logger.debug(f"🕒 [TIME_AXIS_DEBUG]   最終 use_time_axis 值: {use_time_axis}")
        logger.info(f"圈速控制 - 時間軸設定: use_time_axis={use_time_axis}")
        
        # 🔍 詳細診斷：driver2_combo 狀態
        logger.info(f"[DEBUG]    🔍 driver2_combo 詳細狀態檢查:")
        logger.info(f"  currentIndex: {self.main_window.driver2_combo.currentIndex()}")
        logger.info(f"  currentText: '{self.main_window.driver2_combo.currentText()}'")
        logger.info(f"  currentData: {self.main_window.driver2_combo.currentData()}")
        logger.info(f"  count: {self.main_window.driver2_combo.count()}")
        logger.info(f"  所有項目列表:")
        for i in range(min(5, self.main_window.driver2_combo.count())):  # 只顯示前5項避免日誌過長
            logger.info(f"    [{i}] text='{self.main_window.driver2_combo.itemText(i)}', data={self.main_window.driver2_combo.itemData(i)}")
        if self.main_window.driver2_combo.count() > 5:
            logger.info(f"    ... (共 {self.main_window.driver2_combo.count()} 項)")
        
        # 🔧 修復：使用 currentData() 而不是 currentText() 來判斷是否為 "無"
        # 這樣可以正確處理所有語言（中文 "無"、英文 "None"、日語 "なし"）
        driver2_data = self.main_window.driver2_combo.currentData()
        driver2 = self.main_window.driver2_combo.currentText() if driver2_data is not None else None
        logger.info(f"  → 最終 driver2 判斷: driver2_data={driver2_data} → driver2={driver2}")
        
        lap1 = self.main_window.lap1_spinbox.value()
        lap2 = self.main_window.lap2_spinbox.value()
        is_fastest = self.main_window.fastest_lap_checkbox.isChecked()
        
        logger.info(f"圈速控制 - 更新參數: {driver1} vs {driver2}, 第{lap1}圈 vs 第{lap2}圈, 最速圈: {is_fastest}")
        
        # 獲取當前基本設置
        year = self.main_window.year_combo.currentText()
        race_display = self.main_window.race_combo.currentText()
        session = self.main_window.session_combo.currentText()
        
        # 🔧 修復: 清理 race 參數，移除日期後綴 (如 "Japan (2025-04-06)" → "Japan")
        race = self.main_window._get_race_key_from_display(race_display)
        
        logger.info(f"圈速控制 - 基本設置: year={year}, race={race}, session={session}")
        logger.debug(f"圈速控制 - 原始 race_display: {race_display}")
        if race != race_display:
            logger.info(f"圈速控制 - Race 參數已清理: '{race_display}' → '{race}'")
        
        # 過濾出需要更新的分析模組
        modules_to_update = []
        skipped_count = 0

        # ✅ 使用 _get_telemetry_analysis_windows() 獲取所有分析視窗
        all_analysis_windows = self.main_window._get_telemetry_analysis_windows()
        total_analysis_windows = len(all_analysis_windows)
        logger.info(f"🔵 [BATCH_UPDATE] 找到 {total_analysis_windows} 個分析視窗")
        logger.debug(f"🔵 [BATCH_UPDATE] 找到 {total_analysis_windows} 個分析視窗")

        if total_analysis_windows == 0:
            logger.warning("[LAP_CONTROL] [DEBUG]   沒有符合條件的分析視窗")
            logger.debug("[LAP_CONTROL] [DEBUG]   ⚠️ 沒有符合條件的分析視窗")
            QMessageBox.information(self.main_window, tr('update'), tr('update_progress_no_windows'))
            return

        if lap_window_count == 0:
            logger.info("[LAP_CONTROL] [DEBUG]   備註: lap_analysis_windows 為空，但偵測到其他分析模組")
            logger.debug("[LAP_CONTROL] [DEBUG]   ℹ️ lap_analysis_windows 為空，但偵測到其他分析模組")

        # 🔥 [關鍵修復] 通知 LinkageManager 時間軸模式變更
        # 必須在更新各個模組之前調用，確保所有已註冊的模組接收到時間軸模式通知
        try:
            from modules.gui.lap_analysis.linkage import linkage_manager
            logger.info(f"🕒 [TIME_AXIS_DEBUG] 步驟 2: 通知 LinkageManager 時間軸模式")
            logger.debug(f"🕒 [TIME_AXIS_DEBUG] 步驟 2: 通知 LinkageManager 時間軸模式")
            logger.info(f"🕒 [TIME_AXIS_DEBUG]   呼叫 linkage_manager.set_time_axis_mode({use_time_axis})")
            logger.debug(f"🕒 [TIME_AXIS_DEBUG]   呼叫 linkage_manager.set_time_axis_mode({use_time_axis})")
            linkage_manager.set_time_axis_mode(use_time_axis)
            logger.info(f"🕒 [TIME_AXIS_DEBUG]   ✅ LinkageManager 通知完成")
            logger.debug(f"🕒 [TIME_AXIS_DEBUG]   ✅ LinkageManager 通知完成")
        except Exception as e:
            # 🔴 關鍵修復：移除 exc_info=True 避免 logging 持有 frame chain
            logger.error(f"🕒 [TIME_AXIS_DEBUG]   ❌ LinkageManager 通知失敗: {e}")
            logger.debug(f"🕒 [TIME_AXIS_DEBUG]   ❌ LinkageManager 通知失敗: {e}")
            e = None  # 🔴 立即釋放異常對象

        telemetry_types = {
            'speed_analysis', 'speed', 'brake', 'throttle', 'steering',
            'gear', 'rpm', 'acceleration', 'speed_diff', 'Speeddiff',
            'distancediff', 'Distancediff', 'timediff', 'Timediff', 'laptime'
        }
        driver_only_types = {
            'throttle_line_chart_single_driver'
        }
        session_only_types = {
            'rain_weather', 'pitstop', 'accident', 'tire', 'ideal_lap',
            'ideal_lap_ranking', 'ideal_lap_sector_comparison', 'ideal_lap_sector_heatmap',
            'qualifying_prediction',           # 排位賽預測 (F74 v3.8)
            'qualifying_prediction_table',      # 排位賽預測表格 (F74 v3.8) - 別名
            'race_prediction',                  # 正賽預測 (F80) Q → R
            'race_prediction_table',            # 正賽預測表格 (F80) Q → R - 別名
            'laptime_boxplot', 'throttle_boxplot', 'track_analysis', 'driver_position',
            'all_drivers_straight_line_speed',  # 全車手直線速度分析
            'all_drivers_max_speed',            # 全車手最高速度分析 (F121)
            'all_drivers_acceleration_chart',   # 全車手加速度圖表 (F121)
            'all_drivers_brake_chart',          # 全車手煞車圖表 (F122)
            'all_drivers_brake_performance',    # 全車手煞車性能分析 (F34)
            'all_drivers_brake_all_laps',       # 全車手煞車全圈數分析 (F122)
            'corner_performance',               # 彎道性能分析 (F47) - Low/Mid/High Speed Corners
            'historical_track_map',             # ✅ 歷年賽道旗幟統計 (F100)
        }

        def _attempt_module_update(module, attempts):
            for method_name, kwargs, positional_keys in attempts:
                method = None  # 🔴 在循環開始時初始化
                
                try:
                    method = getattr(module, method_name, None)
                    if not callable(method):
                        method = None  # 🔴 立即清理
                        continue

                    logger.info("🔍 [BATCH_DEBUG] 嘗試調用 %s，kwargs=%s", method_name, kwargs)
                    logger.debug(f"🔍 [BATCH_DEBUG] 嘗試調用 {method_name}, kwargs={kwargs}")
                    
                    # 🕒 時間軸追蹤
                    if 'use_time_axis' in kwargs:
                        logger.debug(f"🕒 [TIME_AXIS_DEBUG] 步驟 3: 調用 {method_name}")
                        logger.debug(f"🕒 [TIME_AXIS_DEBUG]   use_time_axis 參數值: {kwargs['use_time_axis']}")

                    result = method(**kwargs)
                    logger.info("🔍 [BATCH_DEBUG] %s 返回: %s", method_name, result)
                    logger.debug(f"🔍 [BATCH_DEBUG] {method_name} 返回: {result}")
                    
                    method = None  # 🔴 成功後立即清理 bound method
                    return True, result
                    
                except TypeError as exc:
                    # 🔴 立即轉換為字串，避免持有異常對象和 traceback
                    error_msg = str(exc)
                    exc = None  # 🔴 立即釋放異常對象
                    
                    logger.warning("🔍 [BATCH_DEBUG] %s 參數不匹配: %s", method_name, error_msg)
                    logger.debug(f"🔍 [BATCH_DEBUG] {method_name} 參數不匹配: {error_msg}")

                    if positional_keys:
                        try:
                            args = [kwargs.get(key) for key in positional_keys]
                            logger.info("🔍 [BATCH_DEBUG] 使用位置參數重試 %s, args=%s", method_name, args)
                            logger.debug(f"🔍 [BATCH_DEBUG] 使用位置參數重試 {method_name}, args={args}")
                            
                            result = method(*args)
                            logger.info("🔍 [BATCH_DEBUG] %s (位置參數) 返回: %s", method_name, result)
                            logger.debug(f"🔍 [BATCH_DEBUG] {method_name} (位置參數) 返回: {result}")
                            
                            method = None  # 🔴 成功後清理
                            args = None  # 🔴 清理參數列表
                            return True, result
                            
                        except Exception as inner_exc:  # noqa: BLE001 - 防禦性
                            # 🔴 立即轉換為字串
                            inner_error_msg = str(inner_exc)
                            inner_exc = None  # 🔴 釋放內部異常
                            
                            logger.warning("🔍 [BATCH_DEBUG] %s 位置參數重試失敗: %s", method_name, inner_error_msg)
                            logger.debug(f"🔍 [BATCH_DEBUG] {method_name} 位置參數重試失敗: {inner_error_msg}")
                            
                            inner_error_msg = None  # 🔴 清理錯誤訊息
                    
                    # 🔴 清理所有局部變量
                    method = None
                    error_msg = None
                    
                    continue
                    
            return False, None
        
        for analysis_module in all_analysis_windows:
            # ✅ 獲取模組的 analysis_type 屬性
            analysis_type = getattr(analysis_module, 'analysis_type', 'unknown')
            
            # ✅ 檢查是否在支援的分析類型列表中
            if analysis_type not in all_analysis_types:
                skipped_count += 1
                logger.debug(f"圈速控制 - 跳過不支援的分析視窗: 類型={analysis_type}")
                continue
            
            modules_to_update.append((analysis_module, analysis_type))
            logger.info(f"  ✅ 將更新: {analysis_type}")
            logger.debug(f"  ✅ 將更新: {analysis_type}")
        
        if not modules_to_update:
            msg = tr('update_progress_no_modules').format(skipped_count)
            QMessageBox.information(self.main_window, tr('update'), msg)
            logger.info(f"圈速控制 - {msg}")
            logger.warning("🟢 [DEBUG]    沒有模組需要更新，退出")
            logger.debug("🟢 [DEBUG]    沒有模組需要更新，退出")
            return
        
        logger.info(f"圈速控制 - 找到 {len(modules_to_update)} 個分析模組需要更新")
        logger.info(f"🟢 [DEBUG]    準備創建進度對話框")
        logger.debug(f"🟢 [DEBUG]    準備創建進度對話框")
        
        # 創建進度對話框
        progress = QProgressDialog(
            tr('update_progress_preparing'), 
            tr('cancel'), 
            0, 
            len(modules_to_update), 
            self.main_window
        )
        
        # ✅ 調試點 3: 進度對話框創建完成
        logger.info("🟢 [DEBUG]    進度對話框已創建")
        logger.debug("🟢 [DEBUG]    進度對話框已創建")
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle(tr('update_progress_title'))
        progress.setMinimumDuration(0)
        progress.setValue(0)
        QApplication.processEvents()
        
        # 序列化更新所有模組
        updated_count = 0
        failed_count = 0
        
        for i, (analysis_module, analysis_type) in enumerate(modules_to_update, 1):
            # 檢查用戶是否取消
            if progress.wasCanceled():
                logger.info(f"圈速控制 - 用戶取消更新操作（已完成 {updated_count}/{len(modules_to_update)}）")
                break
            
            try:
                # 獲取視窗標題用於顯示
                window_title = "未知視窗"
                if hasattr(analysis_module, 'get_window_title'):
                    # 傳遞必要的參數給 get_window_title
                    try:
                        window_title = analysis_module.get_window_title(year, race, session)
                    except TypeError:
                        # 如果新版方法需要參數但舊版不需要，使用備用方案
                        window_title = f"{getattr(analysis_module, 'display_name', 'Analysis Module')} - {year} {race} {session}"
                elif hasattr(analysis_module, '_sub_window') and hasattr(analysis_module._sub_window, 'windowTitle'):
                    window_title = analysis_module._sub_window.windowTitle()
                elif hasattr(analysis_module, 'windowTitle'):
                    window_title = analysis_module.windowTitle()
                
                # 更新進度對話框
                progress_text = f"{tr('update_progress_updating')} {analysis_type} ({i}/{len(modules_to_update)})...\n{window_title}"
                progress.setLabelText(progress_text)
                progress.setValue(i)
                QApplication.processEvents()  # 確保UI響應
                
                logger.info(f"圈速控制 - [{i}/{len(modules_to_update)}] 更新視窗: {window_title} (類型: {analysis_type})")
                
                # ✅ 根據模組類型調用對應的更新方法
                success = False
                
                # 🔍 調試點：開始更新模組
                logger.info(f"🔍 [BATCH_DEBUG] 模組 {i}/{len(modules_to_update)}: analysis_type={analysis_type}")
                logger.debug(f"🔍 [BATCH_DEBUG] 模組 {i}/{len(modules_to_update)}: analysis_type={analysis_type}")
                logger.info(f"🔍 [BATCH_DEBUG] 模組類型: {type(analysis_module).__name__}")
                logger.debug(f"🔍 [BATCH_DEBUG] 模組類型: {type(analysis_module).__name__}")
                logger.info(f"🔍 [BATCH_DEBUG] 模組模組路徑: {type(analysis_module).__module__}")
                logger.debug(f"🔍 [BATCH_DEBUG] 模組模組路徑: {type(analysis_module).__module__}")
                
                base_kwargs = {
                    'year': year,
                    'race': race,
                    'session': session,
                }
                telemetry_kwargs = {
                    **base_kwargs,
                    'driver1': driver1,
                    'driver2': driver2,
                    'lap1': lap1,
                    'lap2': lap2,
                    'is_fastest': is_fastest,
                    'use_time_axis': use_time_axis,  # 新增時間軸參數
                }
                
                logger.debug(f"🕒 [TIME_AXIS_DEBUG] 步驟 2: 準備 telemetry_kwargs")
                logger.debug(f"🕒 [TIME_AXIS_DEBUG]   telemetry_kwargs['use_time_axis'] = {telemetry_kwargs.get('use_time_axis')}")
                driver_primary = driver1 or driver2 or base_kwargs.get('driver')
                driver_kwargs = {
                    **base_kwargs,
                    'driver': driver_primary,
                    'driver1': driver1,
                    'driver2': driver2,
                }

                if analysis_type in telemetry_types:
                    logger.info("🔍 [BATCH_DEBUG] 識別為遙測模組")
                    logger.debug("🔍 [BATCH_DEBUG] 識別為遙測模組")
                    attempts = [
                        ('update_lap_parameters', telemetry_kwargs, None),
                        ('update_analysis_parameters', telemetry_kwargs, ('year', 'race', 'session')),
                        ('update_parameters', telemetry_kwargs, ('year', 'race', 'session')),
                        ('onParametersChanged', telemetry_kwargs, ('year', 'race', 'session')),
                    ]
                elif analysis_type in driver_only_types:
                    logger.info("🔍 [BATCH_DEBUG] 識別為單車手分析模組")
                    logger.debug("🔍 [BATCH_DEBUG] 識別為單車手分析模組")
                    attempts = [
                        ('update_analysis_parameters', driver_kwargs, ('year', 'race', 'session', 'driver')),
                        ('update_parameters', driver_kwargs, ('year', 'race', 'session')),
                        ('onParametersChanged', driver_kwargs, ('year', 'race', 'session')),
                    ]
                elif analysis_type in session_only_types:
                    logger.info("🔍 [BATCH_DEBUG] 識別為賽事級模組")
                    logger.debug("🔍 [BATCH_DEBUG] 識別為賽事級模組")
                    attempts = [
                        ('update_parameters', base_kwargs, ('year', 'race', 'session')),
                        ('update_analysis_parameters', base_kwargs, ('year', 'race', 'session')),
                        ('update_lap_parameters', base_kwargs, ('year', 'race', 'session')),
                        ('onParametersChanged', base_kwargs, ('year', 'race', 'session')),
                    ]
                else:
                    logger.info("🔍 [BATCH_DEBUG] 未定義分類的模組，使用通用流程")
                    logger.debug("🔍 [BATCH_DEBUG] 未定義分類的模組，使用通用流程")
                    attempts = [
                        ('update_parameters', base_kwargs, ('year', 'race', 'session')),
                        ('update_analysis_parameters', base_kwargs, ('year', 'race', 'session')),
                        ('update_lap_parameters', base_kwargs, ('year', 'race', 'session')),
                        ('onParametersChanged', base_kwargs, ('year', 'race', 'session')),
                    ]

                # 🔒 [SYNC_FIX] 檢查視窗的同步狀態（支援多種同步屬性）
                # ⚠️ 關鍵修復：批次更新必須尊重視窗的獨立同步設定
                # 如果視窗已停用同步，則跳過批次更新
                skip_update = False
                
                # 檢查 sync_driver_lap_enabled（遙測模組的同步屬性）
                if hasattr(analysis_module, 'sync_driver_lap_enabled') and not analysis_module.sync_driver_lap_enabled:
                    logger.info(f"🔒 [SYNC_FIX] 視窗 {window_title} 已停用車手圈數同步 (sync_driver_lap_enabled=False)，跳過批次更新")
                    logger.debug(f"🔒 [SYNC_FIX] 視窗 {window_title} 已停用車手圈數同步，跳過批次更新")
                    skip_update = True
                # 檢查子視窗的 sync_enabled 屬性（PopoutSubWindow）
                elif hasattr(analysis_module, '_sub_window'):
                    sub_window = analysis_module._sub_window
                    if hasattr(sub_window, 'sync_enabled') and not sub_window.sync_enabled:
                        logger.info(f"🔒 [SYNC_FIX] 視窗 {window_title} 已停用同步 (sub_window.sync_enabled=False)，跳過批次更新")
                        logger.debug(f"🔒 [SYNC_FIX] 視窗 {window_title} 已停用同步，跳過批次更新")
                        skip_update = True
                # 檢查模組自己的 sync_enabled 屬性
                elif hasattr(analysis_module, 'sync_enabled') and not analysis_module.sync_enabled:
                    logger.info(f"🔒 [SYNC_FIX] 視窗 {window_title} 已停用同步 (sync_enabled=False)，跳過批次更新")
                    logger.debug(f"🔒 [SYNC_FIX] 視窗 {window_title} 已停用同步，跳過批次更新")
                    skip_update = True
                
                if skip_update:
                    logger.info(f"🔒 [SYNC_FIX] ✅ 已跳過 {window_title}，保持獨立參數")
                    logger.debug(f"🔒 [SYNC_FIX] ✅ 已跳過 {window_title}，保持獨立參數")
                    updated_count += 1  # 視為成功（已跳過，不是失敗）
                    continue

                executed, result = _attempt_module_update(analysis_module, attempts)

                if not executed:
                    logger.warning(f"🔍 [BATCH_DEBUG] ❌ 無可用的更新方法: {analysis_type}")
                    logger.debug(f"🔍 [BATCH_DEBUG] ❌ 無可用的更新方法: {analysis_type}")
                    failed_count += 1
                    continue

                if isinstance(result, bool):
                    success = result
                else:
                    # 無返回值 (None) 或其他資料型態皆視為成功
                    success = (result is None) or bool(result)
                
                if success:
                    updated_count += 1
                    logger.info(f"圈速控制 - 更新成功")
                else:
                    logger.warning(f"圈速控制 - 更新返回 False")
                    failed_count += 1

                # 🚑 [緊急修復] 添加延遲避免載入器競爭（100ms 確保 API Worker 完全啟動）
                # 原因：移除 250ms 後，模組啟動太快導致 _is_loading 衝突
                # 詳見：docs/develop task/GUI Develop task/緊急問題診斷_載入器競爭.md
                QApplication.processEvents()
                time.sleep(0.1)  # 100ms - 更穩定的平衡點
            except Exception as e:
                failed_count += 1
                # 🔴 移除 exc_info 避免 traceback 持有 frame
                logger.error(f"圈速控制 - 更新時發生錯誤: {e}")
                e = None  # 🔴 立即釋放異常對象
        
        # 確保進度對話框完成
        progress.setValue(len(modules_to_update))
        
        # 顯示結果摘要
        result_text = f"序列化更新完成！\n\n"
        result_text += f"✅ 成功更新: {updated_count} 個模組\n"
        if failed_count > 0:
            result_text += f"⚠️ 失敗/跳過: {failed_count} 個模組\n"
        if skipped_count > 0:
            result_text += f"⏭️ 跳過非遙測: {skipped_count} 個模組\n"
        result_text += f"\n總共處理: {len(modules_to_update)} 個遙測模組"
        
        logger.info(f"圈速控制 - 序列化更新完成: 成功={updated_count}, 失敗={failed_count}, 跳過={skipped_count}, 總計={len(modules_to_update)}")
        
        # 不再顯示結果對話框（用戶請求取消彈窗）
        # 結果資訊已在終端日誌中顯示，無需額外彈窗
        
        # 額外觸發專用的圖表更新（為了確保chart widget正確更新）
        try:
            logger.debug("圈速控制 - 觸發專用圖表更新邏輯...")
            
            # 檢查當前窗口類型並調用對應的更新方法
            # ✅ 修復：添加日文翻譯支援
            # ⚠️ 注意順序：先檢查更具體的「加速度分析」，再檢查「速度分析」（避免誤判）
            window_title = self.main_window.windowTitle()
            if '加速度分析' in window_title or 'Acceleration Analysis' in window_title or 'アクセラレーション分析' in window_title or '加速度分析' in window_title:
                logger.debug("圈速控制 - 檢測到加速度分析視窗，觸發專用更新")
                self.main_window._update_acceleration_analysis_chart({})
            elif '速度分析' in window_title or 'Speed Analysis' in window_title or '速度分析' in window_title:
                logger.debug("圈速控制 - 檢測到速度分析視窗，觸發專用更新")
                self.main_window._update_speed_analysis_chart({})  # 使用空的json_data，讓方法依賴loader
            elif '油門分析' in window_title or 'Throttle Analysis' in window_title or 'スロットル分析' in window_title:
                logger.debug("圈速控制 - 檢測到油門分析視窗，觸發專用更新")
                self.main_window._update_throttle_analysis_chart({})
            elif 'RPM分析' in window_title or 'RPM Analysis' in window_title or 'RPM分析' in window_title:
                logger.debug("圈速控制 - 檢測到RPM分析視窗，觸發專用更新")
                self.main_window._update_rpm_analysis_chart({})
            elif '檔位分析' in window_title or 'Gear Analysis' in window_title or 'ギア分析' in window_title:
                logger.debug("圈速控制 - 檢測到檔位分析視窗，觸發專用更新")
                self.main_window._update_gear_analysis_chart({})
            else:
                logger.debug(f"圈速控制 - 未識別的視窗類型: {window_title}")
                
        except Exception as e:
            # 🔴 移除 exc_info 避免 traceback 持有 frame 和 bound method
            logger.error(f"圈速控制 - 專用圖表更新失敗: {e}")
            e = None  # 🔴 立即釋放異常對象
