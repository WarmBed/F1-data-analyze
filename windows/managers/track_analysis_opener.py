# -*- coding: utf-8 -*-
"""
TrackAnalysisOpener - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMessageBox
from core.gui_i18n import tr
from core.logger import get_logger
from functools import partial
from windows.workers.cli_workers import MainWindowParameterProvider
from windows.widgets.popout_subwindow import PopoutSubWindow

logger = get_logger(__name__)


class TrackAnalysisOpener:
    """從 f1t_gui_main.py 提取的 open_track_analysis_window 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def open_track_analysis_window(self):
        """開啟賽道分析視窗"""
        import time
        start_time = time.perf_counter()
        
        def log_step(step_name):
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.debug(f"[TRACK_DEBUG] {elapsed:7.2f}ms | {step_name}")
        
        try:
            log_step("🚀 開始 open_track_analysis_window()")
            
            # 檢查是否為首次使用分析功能
            self.main_window.check_and_remove_welcome_page()
            log_step("✅ 檢查歡迎頁面完成")
            
            # 檢查模組是否可用並決定使用的實作
            track_module = None
            track_widget = None
            use_universal = False

            try:
                log_step("📦 開始導入 TrackAnalysisUniversal...")
                from modules.gui.race_analysis.track import TrackAnalysisUniversal
                use_universal = True
                log_step("✅ TrackAnalysisUniversal 導入成功")
            except ImportError as universal_error:
                log_step(f"⚠️  TrackAnalysisUniversal 導入失敗: {universal_error}")
                try:
                    from modules.gui.race_analysis.track import TrackAnalysisModule
                    log_step("⚠️  回退至 legacy TrackAnalysisModule")
                except ImportError:
                    from core.gui_i18n import tr
                    QMessageBox.warning(self.main_window, tr('warning', 'Warning'), tr('track_module_unavailable', 'Track analysis module is not available'))
                    return

            # 創建參數提供者
            log_step("🔧 創建參數提供者...")
            parameter_provider = MainWindowParameterProvider(self.main_window)
            log_step("✅ 參數提供者創建完成")
            
            # 獲取當前參數
            log_step("📝 獲取當前參數...")
            current_year = parameter_provider.get_current_year()
            current_race = parameter_provider.get_current_race()
            current_session = parameter_provider.get_current_session()
            log_step(f"✅ 參數: {current_year}/{current_race}/{current_session}")
            default_size = None

            if use_universal:
                try:
                    log_step("🏗️  開始創建 TrackAnalysisUniversal 實例...")
                    module_instance = TrackAnalysisUniversal(main_window=self.main_window)
                    log_step("✅ TrackAnalysisUniversal 實例創建完成")
                    
                    module_instance.parameter_provider = parameter_provider
                    log_step("✅ 參數提供者設置完成")

                    try:
                        year_value = int(current_year)
                    except (TypeError, ValueError):
                        year_value = current_year

                    log_step(f"⚡ 開始調用 update_parameters({year_value}, {current_race}, {current_session})...")
                    log_step("   ⚠️  【關鍵步驟】這裡會觸發 API 請求，可能導致卡死")
                    
                    module_instance.update_parameters(
                        year=year_value,
                        race=current_race,
                        session=current_session
                    )
                    
                    log_step("✅ update_parameters() 返回")
                    log_step("   💡 如果看到這行，說明 update_parameters 沒有阻塞")

                    track_module = module_instance
                    log_step("🎨 獲取 Widget...")
                    track_widget = module_instance.get_widget()
                    log_step("✅ Widget 獲取完成")
                    
                    window_title = module_instance.get_window_title(current_year, current_race, current_session)
                    default_size = module_instance.get_default_size()
                    log_step(f"✅ 視窗標題: {window_title}")
                except Exception as exc:
                    log_step(f"❌ TrackAnalysisUniversal 初始化失敗: {exc}")
                    import traceback
                    traceback.print_exc()
                    use_universal = False

            if not use_universal:
                # 確保 legacy 類別可用
                log_step("⚠️  使用 Legacy 模式")
                from modules.gui.race_analysis.track import TrackAnalysisModule

                track_module = TrackAnalysisModule(
                    year=current_year,
                    race=current_race,
                    session=current_session
                )
                track_widget = track_module
                window_title = track_module.get_window_title(current_year, current_race, current_session)
                default_size = None
                log_step(f"✅ Legacy 視窗: {window_title}")
            
            # 獲取當前 MDI 區域
            log_step("🔍 獲取當前 MDI 區域...")
            current_mdi_area = self.main_window.get_current_mdi_area()
            if not current_mdi_area:
                log_step("❌ 找不到 MDI 區域")
                from core.gui_i18n import tr
                QMessageBox.warning(self.main_window, tr('warning', 'Warning'), tr('mdi_area_not_found', 'Cannot find current MDI area'))
                return
            log_step("✅ MDI 區域獲取完成")
            
            # 創建 PopoutSubWindow
            log_step("🏗️  創建 PopoutSubWindow...")
            sub_window = PopoutSubWindow(
                title=window_title,
                parent_mdi=current_mdi_area,  # 使用當前 MDI 區域
                analysis_module=track_module,  # 傳遞分析模組
                sync_enabled=True,  # 預設使用同步模式
                parameter_provider=parameter_provider,
                global_signal_manager=getattr(self, 'global_signal_manager', None)
            )
            log_step("✅ PopoutSubWindow 創建完成")
            
            # 設置賽道分析模組為視窗內容
            log_step("🎨 設置 Widget...")
            sub_window.setWidget(track_widget)
            log_step("✅ Widget 設置完成")
            
            # 添加到 MDI 區域
            log_step("➕ 添加到 MDI 區域...")
            current_mdi_area.addSubWindow(sub_window)
            log_step("✅ 添加到 MDI 完成")
            
            log_step("📺 顯示視窗...")
            sub_window.show()
            log_step("✅ 視窗顯示完成")
            
            # 連接信號
            # 🔴 使用 partial 避免 lambda 閉包洩漏
            log_step("🔗 連接信號...")
            sub_window.window_closed.connect(

                partial(self.main_window.on_subwindow_closed, sub_window)

            )
            if hasattr(track_module, 'module_error'):
                track_module.module_error.connect(lambda msg: self.main_window.show_error_message("賽道分析錯誤", msg))
            log_step("✅ 信號連接完成")
            
            # 記錄視窗
            self.main_window.active_subwindows.append(sub_window)
            
            # 更新狀態
            log_step(f"📊 視窗標題: {window_title}")

            # 依模組建議尺寸調整視窗大小
            if default_size and isinstance(default_size, (tuple, list)) and len(default_size) == 2:
                log_step(f"📐 調整視窗大小: {default_size}")
                sub_window.resize(default_size[0], default_size[1])
            
            total_time = (time.perf_counter() - start_time) * 1000
            log_step(f"🎉 完成！總耗時: {total_time:.2f}ms")
            
        except Exception as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.debug(f"[TRACK_DEBUG] {elapsed:7.2f}ms | ❌ 異常: {e}")
            import traceback
            traceback.print_exc()
            from core.gui_i18n import tr
            QMessageBox.critical(self.main_window, tr('error', 'Error'), f"{tr('track_window_error', 'Cannot open track analysis window')}: {str(e)}")
            logger.debug(f"[STATUS] 賽道分析視窗開啟失敗: {str(e)}")
