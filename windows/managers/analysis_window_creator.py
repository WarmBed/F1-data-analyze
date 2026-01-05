# -*- coding: utf-8 -*-
"""
AnalysisWindowCreator - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMessageBox
from core.gui_i18n import tr
from core.logger import get_logger
from windows.widgets.custom_mdi_area import CustomMdiArea
from windows.widgets.popout_subwindow import PopoutSubWindow

logger = get_logger(__name__)


class AnalysisWindowCreator:
    """從 f1t_gui_main.py 提取的 create_analysis_window 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def create_analysis_window(self, function_name):
        """為功能樹的分析項目創建新視窗 - 升級支援模組化架構"""
        logger.debug(f"[DEBUG]    [CREATE_WINDOW] =============== 開始創建分析視窗 ===============")
        logger.debug(f"[DEBUG]    [CREATE_WINDOW] 功能名稱: '{function_name}'")
        logger.debug(f"[DEBUG]    [CREATE_WINDOW] 將嘗試調用 _create_analysis_module...")
        
        # 檢查是否為首次使用分析功能
        self.main_window.check_and_remove_welcome_page()
        
        # ✅ 優先檢查：理想圈分析（避免被 "Lap Analysis" 誤判）
        is_ideal_lap_analysis = (
            ("理想圈分析" in function_name)
            or ("Ideal Lap Analysis" in function_name)
            or ("理想ラップ分析" in function_name)
        )

        if is_ideal_lap_analysis:
            logger.debug(f"[IDEAL_LAP] 🏁 檢測到理想圈分析請求: {function_name}")
            
            # 顯示選項對話框
            ideal_lap_selection = self.main_window._prompt_ideal_lap_options()
            if ideal_lap_selection is None:
                logger.debug("[IDEAL_LAP] 使用者取消理想圈分析選項對話框")
                return
            if not ideal_lap_selection:
                logger.debug("[IDEAL_LAP] 未選擇任何理想圈分析模組")
                return

            logger.debug(f"[IDEAL_LAP] ✅ 使用者選擇了 {len(ideal_lap_selection)} 個分析類型: {ideal_lap_selection}")
            
            # 查找當前分頁中的 MDI 區域（與 detailed lap 相同方式）
            current_tab = self.main_window.tab_widget.currentWidget()
            if not current_tab:
                logger.debug("[IDEAL_LAP] ❌ 無法取得當前分頁")
                return
                
            mdi_area = None
            if isinstance(current_tab, CustomMdiArea):
                mdi_area = current_tab
            else:
                for child in current_tab.findChildren(CustomMdiArea):
                    mdi_area = child
                    break
                    
            if mdi_area is None:
                logger.debug("[IDEAL_LAP] ❌ 無法找到 MDI 區域")
                return
            
            # 獲取當前參數
            current_year = self.main_window.get_selected_year()
            current_race = self.main_window.get_selected_race_key()
            current_session = self.main_window.get_selected_session_code()
            logger.debug(f"[IDEAL_LAP] 📋 賽事參數: {current_year} {current_race} {current_session}")
            
            from modules.gui.lap_analysis.ideal_lap.ideal_lap_options_dialog import IdealLapAnalysisOptionsDialog
            
            # 為每個選擇的分析類型創建視窗
            for analysis_type in ideal_lap_selection:
                logger.debug(f"[IDEAL_LAP] 🚀 創建分析視窗: {analysis_type}")
                
                try:
                    if analysis_type == IdealLapAnalysisOptionsDialog.TYPE_RANKING_TABLE:
                        # 創建排名表格模組
                        self.main_window._create_ideal_lap_ranking_window(
                            mdi_area,
                            current_year,
                            current_race,
                            current_session
                        )
                    
                    elif analysis_type == IdealLapAnalysisOptionsDialog.TYPE_SECTOR_HEATMAP:
                        self.main_window._create_ideal_lap_heatmap_window(
                            mdi_area,
                            current_year,
                            current_race,
                            current_session
                        )
                    
                    elif analysis_type == IdealLapAnalysisOptionsDialog.TYPE_SECTOR_COMPARISON:
                        self.main_window._create_ideal_lap_sector_comparison_window(
                            mdi_area,
                            current_year,
                            current_race,
                            current_session
                        )
                    
                except Exception as e:
                    logger.debug(f"[IDEAL_LAP] ❌ 創建分析視窗失敗: {e}")
                    import traceback
                    traceback.print_exc()
                    QMessageBox.critical(
                        self,
                        "錯誤",
                        f"創建理想圈分析視窗時發生錯誤:\n{str(e)}"
                    )
            
            return
        
        # 特殊處理：遙測/圈速分析概覽直接調用 lap_analysis 方法（排除詳細圈速分析、圈速表格和圈速箱型圖）
        # is_detailed_lap_parent: 只有「詳細圈速分析」父項目才彈出選項對話框
        is_detailed_lap_parent = (
            ("詳細圈速分析" in function_name and "表格" not in function_name)
            or ("Detailed Lap Analysis" in function_name and "Table" not in function_name)
            or ("詳細ラップ分析" in function_name)
        )
        
        # is_detailed_lap: 詳細圈速相關（用於排除遙測分析對話框）
        is_detailed_lap = (
            ("詳細圈速" in function_name)
            or ("Detailed Lap" in function_name)
            or ("詳細ラップ" in function_name)
        )
        
        # 排除圈速箱型圖/箱線圖 - 這些是獨立模組，不需要彈出遙測分析選項
        is_boxplot = (
            ("箱型圖" in function_name)
            or ("箱線圖" in function_name)
            or ("Box Plot" in function_name)
            or ("Boxplot" in function_name)
        )
        
        if (not is_detailed_lap) and (not is_boxplot) and (
            ("圈速" in function_name)
            or ("遙測分析" in function_name)
            or ("Telemetry Analysis" in function_name)
            or ("Lap Analysis" in function_name)
            or ("ラップ分析" in function_name)
        ):
            logger.debug(f"[遙測分析] 檢測到遙測分析請求: {function_name}")
            self.main_window.lap_analysis()
            return

        is_throttle_overview = (
            ("油門分析" in function_name)
            or ("Throttle Analysis" in function_name)
            or ("スロットル分析" in function_name)
        )

        if is_throttle_overview:
            throttle_selection = self.main_window._prompt_throttle_analysis_options()

            if throttle_selection is None:
                logger.debug("[THROTTLE] 使用者取消油門分析選項對話框")
                return

            if throttle_selection.get("line_chart"):
                self.main_window._show_throttle_line_chart_placeholder()

            if throttle_selection.get("box_plot"):
                function_name = tr("throttle_box_plot", "Throttle Box Plot")
            else:
                logger.debug("[THROTTLE] 未選擇任何可用的油門分析模組，結束建立流程")
                return

        # 獲取當前活動的分頁
        current_tab = self.main_window.tab_widget.currentWidget()
        if current_tab is None:
            return
            
        # 查找當前分頁中的MDI區域
        mdi_area = None
        
        # 首先檢查當前分頁是否本身就是MDI區域
        if isinstance(current_tab, CustomMdiArea):
            mdi_area = current_tab
        else:
            # 否則在分頁的子元件中查找
            for child in current_tab.findChildren(CustomMdiArea):
                mdi_area = child
                break
            
        if mdi_area is None:
            #print(f"[警告] 無法找到MDI區域來添加視窗: {function_name}")
            return

        current_year = self.main_window.year_combo.currentText()
        current_race = self.main_window.race_combo.currentText()
        current_session = self.main_window.session_combo.currentText()
        
        # � [DISABLED] 重複視窗檢查機制已禁用 (2025-10-20)
        # 原因：使用者希望能夠同時開啟多個相同模組的視窗來比較不同參數
        # 例如：同時開啟多個 Rain Analysis、Ideal Lap Ranking 等視窗
        """
        # 步驟1: 獲取預期的視窗標題模式
        expected_title_patterns = self.main_window._get_expected_window_title_pattern(
            function_name, 
            current_year, 
            current_race, 
            current_session
        )
        
        # 步驟2: 檢查MDI區域中是否已存在相同視窗
        existing_window = self.main_window._find_existing_window(mdi_area, expected_title_patterns)
        
        if existing_window:
            # 找到已存在的視窗，聚焦而不是創建新視窗
            logger.info(f"[DUPLICATE_CHECK] ✅ 找到已存在視窗: {existing_window.windowTitle()}")
            logger.info(f"[DUPLICATE_CHECK] ⏭️ 跳過創建，將聚焦現有視窗")
            
            # 激活並聚焦現有視窗
            mdi_area.setActiveSubWindow(existing_window)
            existing_window.show()
            existing_window.raise_()
            existing_window.setFocus()
            
            return  # 🚫 不創建新視窗，直接返回
        
        logger.info(f"[DUPLICATE_CHECK] ✅ 未找到重複視窗，繼續創建: {function_name}")
        """
        
        logger.info(f"[MULTI_WINDOW] ✅ 允許創建多個視窗: {function_name}")

        detailed_lap_selection = {"detail_table": True, "box_plot": False}
        # 只有點擊「詳細圈速分析」父項目時才彈出選項對話框
        # 直接點擊「詳細圈速表格」或「圈速箱型圖」不需要對話框
        if is_detailed_lap_parent:
            selection = self.main_window._prompt_detailed_lap_options()
            if selection is None:
                logger.debug("[DETAILED_LAP] 使用者取消了詳細圈速分析選項對話框")
                return
            detailed_lap_selection = selection

            if detailed_lap_selection.get("box_plot"):
                self.main_window._create_detailed_lap_boxplot_window(
                    mdi_area,
                    current_year,
                    current_race,
                    current_session,
                )

            if not detailed_lap_selection.get("detail_table"):
                logger.debug("[DETAILED_LAP] 僅選擇圈速箱型圖，跳過詳細圈速模組視窗建立")
                return

        # [TOOL] 新增：嘗試使用模組化架構
        analysis_module = self.main_window._create_analysis_module(function_name)
        
        if analysis_module:
            # [FIX] 獲取當前參數，類似賽道分析模組
            current_year_value = current_year or self.main_window.year_combo.currentText()
            current_race_value = current_race or self.main_window.race_combo.currentText()
            current_session_value = current_session or self.main_window.session_combo.currentText()
            
            # 🔧 [CRITICAL FIX] 清理 race 名稱，移除日期後綴
            # 例如: "Australia (2025-03-16)" → "Australia"
            clean_race_value = self.main_window._get_race_key_from_display(current_race_value)
            logger.debug(f"[TITLE] [CLEAN] 清理 race 名稱: '{current_race_value}' → '{clean_race_value}'")
            
            # 使用 get_window_title 方法並傳入當前參數
            if hasattr(analysis_module, 'get_window_title'):
                window_title = analysis_module.get_window_title(
                    current_year_value,
                    clean_race_value,  # 🔧 使用清理後的 race 名稱
                    current_session_value,
                )
                logger.debug(f"[TITLE] [FIX] 使用當前參數生成標題: {window_title}")
            else:
                window_title = analysis_module.get_title()
                logger.debug(f"[TITLE] [FALLBACK] 使用預設標題: {window_title}")
                
            analysis_window = PopoutSubWindow(window_title, mdi_area, analysis_module)
            
            # 設置模組的widget
            content_widget = analysis_module.get_widget()
            analysis_window.setWidget(content_widget)
            
            # 🔧 [CRITICAL FIX] 設置模組的父視窗引用（與其他模組保持一致）
            if hasattr(analysis_module, 'set_parent_window'):
                analysis_module.set_parent_window(analysis_window)
                logger.debug(f"[LINK] [INIT] 已設置模組的父視窗引用: {window_title}")
            
            # [REMOVED] 不再需要重新設置標題，因為已經使用 get_window_title 設置正確標題
            logger.debug(f"[TITLE] [OK] 視窗標題已設置為: {window_title}")
            
            # 使用模組推薦的尺寸
            width, height = analysis_module.get_default_size()
            analysis_window.resize(width, height)
            
            logger.debug(f"[OK] [MODULE] 使用模組化架構創建視窗: {analysis_window.windowTitle()}")
            
        else:
            # [TOOL] 保留：舊版相容性邏輯
            window_title = self.main_window.format_window_title(self.main_window._extract_module_name(function_name))
            analysis_window = PopoutSubWindow(window_title, mdi_area)
            
            # 舊版內容創建邏輯
            legacy_result = self.main_window._create_legacy_content(function_name)
            
            # 檢查是否返回了模組實例（進站分析等新版模組）
            if isinstance(legacy_result, tuple) and len(legacy_result) == 2:
                content_widget, analysis_module = legacy_result
                analysis_window.setWidget(content_widget)
                analysis_window.analysis_module = analysis_module  # 設置模組引用
                logger.debug(f"[OK] [LEGACY] 設置分析模組到視窗: {analysis_module.__class__.__name__}")
            else:
                content_widget = legacy_result
                analysis_window.setWidget(content_widget)
            
            # 舊版尺寸設定
            if "降雨分析" in function_name:
                analysis_window.resize(800, 600)
            elif "進站分析" in function_name:
                analysis_window.resize(1200, 800)  # 進站分析使用較大尺寸，充分利用MDI區域
            else:
                analysis_window.resize(450, 280)
            
            logger.warning(f"[WARNING] [LEGACY] 使用舊版架構創建視窗: {window_title}")

        # 通用視窗設定
        mdi_area.addSubWindow(analysis_window)
        logger.debug(f"[OK] [MDI] 已創建MDI子視窗: {analysis_window.windowTitle()}")
        
        # 連接關閉信號 - 確保視窗關閉時從追蹤列表移除
        if hasattr(analysis_window, 'window_closed'):
            analysis_window.window_closed.connect(lambda: self.main_window.on_subwindow_closed(analysis_window))
        
        # 添加到追蹤列表
        if hasattr(self, 'active_subwindows'):
            self.main_window.active_subwindows.append(analysis_window)
        
        analysis_window.show()
        
        # 計算新視窗位置（避免重疊）
        self.main_window._position_subwindow(mdi_area, analysis_window)
