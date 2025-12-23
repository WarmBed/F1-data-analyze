# -*- coding: utf-8 -*-
"""
LapControlsChecker - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger
from windows.widgets.custom_mdi_area import CustomMdiArea

logger = get_logger(__name__)


class LapControlsChecker:
    """從 f1t_gui_main.py 提取的 check_and_show_lap_controls_if_needed 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def check_and_show_lap_controls_if_needed(self):
        """檢查是否需要顯示遙測控件 - 根據當前分頁的MDI子視窗"""
        # ✅ 獲取當前分頁的MDI區域
        current_tab = self.main_window.tab_widget.currentWidget()
        current_mdi_area = None
        
        if isinstance(current_tab, CustomMdiArea):
            current_mdi_area = current_tab
        else:
            # 嘗試查找子widget中的MDI區域
            for child in current_tab.findChildren(CustomMdiArea):
                current_mdi_area = child
                break
        
        if not current_mdi_area:
            # ✅ 改善日誌訊息：區分歡迎頁和其他情況
            current_tab = self.main_window.tab_widget.currentWidget()
            tab_name = current_tab.objectName() if current_tab else "Unknown"
            
            if tab_name == "welcome_tab":
                # ✅ 歡迎頁是正常的，使用 INFO 級別
                logger.debug("[LAP_CONTROL] [DEBUG]   💡 當前在歡迎頁，無需檢查遙測控件")
            else:
                # ⚠️  非歡迎頁但沒有 MDI，這才可能是問題
                logger.debug(f"[LAP_CONTROL] [DEBUG]   ⚠️  分頁 '{tab_name}' 無 MDI 區域，跳過檢查")
            return
        
        lap_analysis_windows_found = []
        for sub_window in current_mdi_area.subWindowList():
            if not sub_window.isVisible():
                continue

            window_title = sub_window.windowTitle()
            
            # ✅ 修復：過濾進站分析視窗，避免誤認為 lap_analysis 模組
            if any(keyword in window_title for keyword in ["進站分析", "Pitstop", "ピットストップ"]):
                logger.debug(f"[LAP_CONTROL] [DEBUG]   ⏭️  跳過非遙測模組 (Pitstop): {window_title}")
                continue
            
            widget = sub_window.widget()

            # 依序檢查可用的模組引用
            candidate_sources = []

            # 優先使用 PopoutSubWindow 上綁定的 analysis_module
            analysis_module = getattr(sub_window, "analysis_module", None)
            if analysis_module:
                candidate_sources.append((analysis_module, "subwindow.analysis_module"))

            # 子視窗的主widget可能就是分析模組本身
            if widget:
                candidate_sources.append((widget, "subwindow.widget"))

                # 某些圖表widget會暴露 parent_module 指向真正的模組
                parent_module = getattr(widget, "parent_module", None)
                if parent_module:
                    candidate_sources.append((parent_module, "widget.parent_module"))

            matched_module = None
            matched_source = None
            for candidate, source_name in candidate_sources:
                if hasattr(candidate, "update_lap_parameters"):
                    matched_module = candidate
                    matched_source = source_name
                    break

            if matched_module:
                lap_analysis_windows_found.append((sub_window, matched_module, window_title, matched_source))
                logger.debug(
                    f"[LAP_CONTROL] [DEBUG]   🎯 發現遙測分析視窗: {window_title} (source={matched_source})"
                )
                continue

            # 後備：關鍵字判斷（維持舊版相容）
            if any(keyword in window_title for keyword in [
                "Speed Analysis", "RPM Analysis", "⚡", "🔄",
                "Brake Analysis", "煞車分析", "Gear Analysis", "檔位分析",
                "DistanceDiff", "距離差", "Acceleration Analysis", "加速度分析"
            ]):
                lap_analysis_windows_found.append((sub_window, widget, window_title, "title_fallback"))
                logger.debug(f"[LAP_CONTROL] [DEBUG]   🎯 (fallback) 發現遙測分析視窗: {window_title}")
        
        if lap_analysis_windows_found:
            logger.debug(f"[LAP_CONTROL] [DEBUG]   📊 找到 {len(lap_analysis_windows_found)} 個遙測分析視窗")
            
            # 🔧 修復：不清空現有追蹤，而是進行智能合併
            # 保留已正確追蹤的模組，只添加新發現的
            existing_modules = set()
            for existing in self.main_window.lap_analysis_windows:
                if hasattr(existing, 'update_lap_parameters'):
                    existing_modules.add(existing)
                    logger.debug(f"[LAP_CONTROL] [DEBUG]   ✅ 保留現有模組追蹤: {type(existing).__name__}")
            
            # 清空並重建，但保留正確的模組
            self.main_window.lap_analysis_windows.clear()
            self.main_window.lap_analysis_windows.update(existing_modules)
            
            for sub_window, analysis_obj, window_title, source in lap_analysis_windows_found:
                # 檢查是否已經通過模組正確追蹤了這個視窗
                already_tracked = False
                for tracked_module in existing_modules:
                    if (hasattr(tracked_module, '_sub_window') and 
                        tracked_module._sub_window == sub_window):
                        already_tracked = True
                        logger.debug(f"[LAP_CONTROL] [DEBUG]   ✅ 視窗已通過模組正確追蹤: {window_title}")
                        break
                
                if already_tracked:
                    continue
                
                # 優先使用已解析出的分析模組
                if analysis_obj and hasattr(analysis_obj, 'update_lap_parameters'):
                    self.main_window.lap_analysis_windows.add(analysis_obj)
                    logger.debug(
                        f"[LAP_CONTROL] [DEBUG]   ✅ 已添加模組到追蹤: {window_title} (source={source})"
                    )
                # 🔧 修復：檢查子視窗是否仍然保有分析模組引用
                elif hasattr(sub_window, 'analysis_module') and hasattr(sub_window.analysis_module, 'update_lap_parameters'):
                    self.main_window.lap_analysis_windows.add(sub_window.analysis_module)
                    logger.debug(
                        f"[LAP_CONTROL] [DEBUG]   ✅ 已透過子視窗引用添加模組: {window_title}"
                    )
                else:
                    # 如果不是分析模組，最後退回子視窗本身
                    self.main_window.lap_analysis_windows.add(sub_window)
                    logger.debug(f"[LAP_CONTROL] [DEBUG]   ✅ 已添加子視窗到追蹤: {window_title}")
            
            # 強制顯示遙測分析控件
            logger.debug("[LAP_CONTROL] [DEBUG]   🚀 強制顯示遙測分析控件...")
            self.main_window.show_lap_controls()
        else:
            logger.debug("[LAP_CONTROL] [DEBUG]   ℹ️ 未發現遙測分析視窗，不顯示控件")
