# -*- coding: utf-8 -*-
"""
MdiWindowsCloser - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class MdiWindowsCloser:
    """從 f1t_gui_main.py 提取的 close_all_mdi_windows 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def close_all_mdi_windows(self, mdi_area):
        """關閉指定MDI區域中的所有子視窗並徹底清理所有相關註冊（排除固定視窗）"""
        try:
            logger.debug(f"[CLOSE] 開始關閉 MDI 區域中的非固定視窗...")
            
            # 獲取所有子視窗（排除固定視窗）
            all_subwindows = mdi_area.subWindowList()
            subwindows = [sw for sw in all_subwindows if not sw.property("is_welcome_fixed")]
            window_count = len(subwindows)
            
            logger.debug(f"[STATS] MDI區域中共有 {len(all_subwindows)} 個子視窗，其中 {window_count} 個非固定視窗")
            
            if window_count > 0:
                # 1. 在關閉視窗前，先從連動管理器中取消註冊所有相關模組
                linkage_unregister_count = 0
                
                for subwindow in subwindows[:]:  # 使用切片創建副本
                    if subwindow and subwindow.widget():
                        widget = subwindow.widget()
                        
                        # 遞歸查找所有可能的連動模組並取消註冊
                        modules_to_unregister = self.main_window._find_linkage_modules_in_widget(widget)
                        
                        for module in modules_to_unregister:
                            try:
                                linkage_manager.unregister_module(module)
                                linkage_unregister_count += 1
                                logger.debug(f"[CLEANUP] 已從連動管理器取消註冊模組: {type(module).__name__}")
                            except Exception as e:
                                logger.warning(f"[WARNING] 取消註冊連動模組失敗: {e}")
                
                # 2. 逐一關閉並刪除子視窗
                closed_count = 0
                for subwindow in subwindows[:]:  # 使用切片創建副本
                    try:
                        # 獲取視窗標題以供日誌
                        title = subwindow.windowTitle() if subwindow else "Unknown"
                        
                        # 關閉視窗
                        if subwindow:
                            subwindow.close()
                            # 強制從MDI區域移除
                            mdi_area.removeSubWindow(subwindow)
                            # 刪除對象
                            subwindow.deleteLater()
                            closed_count += 1
                            logger.debug(f"[CLEANUP] 已關閉並清理視窗: {title}")
                            
                    except Exception as e:
                        logger.warning(f"[WARNING] 關閉視窗時發生錯誤: {e}")
                
                # 3. 強制清理MDI區域
                try:
                    mdi_area.closeAllSubWindows()  # 確保所有視窗都被關閉
                    
                    # 強制刷新MDI區域狀態
                    mdi_area.update()
                    mdi_area.repaint()
                    
                except Exception as e:
                    logger.warning(f"[WARNING] MDI區域清理時發生錯誤: {e}")
                
                # 4. 強制Qt事件處理和垃圾回收
                try:
                    from PyQt5.QtWidgets import QApplication
                    QApplication.processEvents()  # 處理所有待處理的事件
                    
                    import gc
                    gc.collect()  # 強制垃圾回收
                    
                except Exception as e:
                    logger.warning(f"[WARNING] 事件處理和垃圾回收時發生錯誤: {e}")
                
                # 5. 驗證清理結果
                final_subwindows = mdi_area.subWindowList()
                final_count = len(final_subwindows)
                
                logger.debug(f"[OK] 關閉完成統計:")
                logger.debug(f"    原始視窗數: {window_count}")
                logger.debug(f"    已關閉視窗: {closed_count}")
                logger.debug(f"    連動模組取消註冊: {linkage_unregister_count}")
                logger.debug(f"    清理後剩餘視窗: {final_count}")
                
                if final_count > 0:
                    logger.warning(f"[WARNING] 仍有 {final_count} 個視窗未完全清理")
                    for i, remaining in enumerate(final_subwindows):
                        title = remaining.windowTitle() if remaining else "Unknown"
                        logger.debug(f"    剩餘視窗 {i+1}: {title}")
                else:
                    logger.debug(f"[OK] ✅ 所有視窗已完全清理")
                    
            else:
                logger.debug(f"[INFO] 沒有需要關閉的視窗")
                
        except Exception as e:
            logger.error(f"[ERROR] 關閉視窗時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
