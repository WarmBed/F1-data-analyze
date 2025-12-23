"""
測試最快圈速深紫色背景顯示功能

驗證 ranking_tower 是否正確：
1. 計算全場最快的 best_lap
2. 為最快車手顯示深紫色背景 (#663399)
3. 白色粗體文字

執行: python test_fastest_best_lap_display.py
"""
import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def test_fastest_lap_display():
    """測試最快圈速顯示"""
    logger.info("=" * 80)
    logger.info("測試最快圈速深紫色背景顯示")
    logger.info("=" * 80)
    
    from f1t_gui_main import StyleHMainWindow
    
    app = QApplication(sys.argv)
    
    # 創建主視窗
    logger.info("✅ 初始化 F1T GUI...")
    main_window = StyleHMainWindow()
    main_window.show()
    
    def open_live_timing():
        """打開 Live Timing Ranking Tower"""
        try:
            logger.info("\n📡 打開 Live Timing Ranking Tower 模組...")
            main_window._open_live_timing_ranking_tower()
            
            # 等待 Live Timing 初始化
            QTimer.singleShot(2000, load_race_data)
            
        except Exception as e:
            logger.error(f"❌ 打開 Live Timing 失敗: {e}", exc_info=True)
            app.quit()
    
    def load_race_data():
        """載入比賽數據"""
        try:
            logger.info("\n📂 載入 2025 Qatar 比賽數據...")
            
            # 獲取 DataManager (使用 singleton)
            from modules.gui.live_timing.core.data_manager import LiveTimingDataManager
            data_manager = LiveTimingDataManager.instance()
            
            # 載入 PKL
            success = data_manager.load_race(2025, "Qatar", "Race")
            
            if success:
                logger.info("✅ 數據載入成功")
                
                # 等待數據處理
                QTimer.singleShot(1000, start_playback)
            else:
                logger.error("❌ 數據載入失敗")
                app.quit()
                
        except Exception as e:
            logger.error(f"❌ 載入數據失敗: {e}", exc_info=True)
            app.quit()
    
    def start_playback():
        """開始播放並檢查最快圈速顯示"""
        try:
            logger.info("\n▶️  開始播放...")
            
            from modules.gui.live_timing.core.data_manager import LiveTimingDataManager
            data_manager = LiveTimingDataManager.instance()
            
            # 開始播放
            data_manager.play()
            
            # 等待幾秒後檢查顯示
            QTimer.singleShot(5000, check_fastest_lap_display)
            
        except Exception as e:
            logger.error(f"❌ 播放失敗: {e}", exc_info=True)
            app.quit()
    
    def check_fastest_lap_display():
        """檢查最快圈速顯示"""
        try:
            logger.info("\n🔍 檢查最快圈速顯示...")
            
            from modules.gui.live_timing.core.data_manager import LiveTimingDataManager
            data_manager = LiveTimingDataManager.instance()
            
            # 獲取 ranking_tower
            ranking_tower = None
            for window_id, module_info in data_manager._active_modules.items():
                module_name = module_info.get('module_name', '')
                if 'ranking' in module_name.lower():
                    ranking_tower = module_info.get('widget')
                    break
            
            if not ranking_tower:
                logger.warning("⚠️  找不到 ranking_tower 模組")
                app.quit()
                return
            
            # 檢查 _fastest_best_lap 屬性
            if hasattr(ranking_tower, '_fastest_best_lap'):
                fastest = ranking_tower._fastest_best_lap
                logger.info(f"✅ 最快圈速: {fastest}")
                
                # 檢查表格中的顯示
                table = ranking_tower.table
                logger.info(f"\n📊 檢查 {table.rowCount()} 位車手的 best_lap 欄位...")
                
                purple_count = 0
                for row in range(table.rowCount()):
                    best_lap_item = table.item(row, 12)  # 欄位 12 = 最佳
                    if best_lap_item:
                        best_lap_time = best_lap_item.text()
                        bg_color = best_lap_item.background().color()
                        fg_color = best_lap_item.foreground().color()
                        is_bold = best_lap_item.font().bold()
                        
                        # 檢查是否為深紫色背景
                        is_purple = (bg_color.red() == 0x66 and 
                                    bg_color.green() == 0x33 and 
                                    bg_color.blue() == 0x99)
                        
                        if is_purple:
                            purple_count += 1
                            driver_item = table.item(row, 1)
                            driver_name = driver_item.text() if driver_item else "???"
                            
                            logger.info(f"  🟣 第 {row+1} 位 {driver_name}: {best_lap_time}")
                            logger.info(f"     背景: RGB({bg_color.red()}, {bg_color.green()}, {bg_color.blue()})")
                            logger.info(f"     文字: RGB({fg_color.red()}, {fg_color.green()}, {fg_color.blue()})")
                            logger.info(f"     粗體: {is_bold}")
                
                logger.info(f"\n✅ 測試完成:")
                logger.info(f"   - 全場最快圈速: {fastest}")
                logger.info(f"   - 深紫色背景車手數: {purple_count}")
                logger.info(f"   - 預期: 1 位車手")
                
                if purple_count == 1:
                    logger.info("\n✅✅✅ 測試通過！最快圈速顯示正確")
                else:
                    logger.warning(f"\n⚠️  測試異常: 應該只有 1 位車手有深紫色背景，但實際有 {purple_count} 位")
                
            else:
                logger.warning("⚠️  ranking_tower 沒有 _fastest_best_lap 屬性")
            
            # 繼續播放，讓用戶可以手動檢視
            logger.info("\n💡 GUI 將繼續運行，請手動檢查 ranking_tower 的最佳圈速欄位")
            logger.info("   (應該只有一位車手的最佳圈速有深紫色背景)")
            
        except Exception as e:
            logger.error(f"❌ 檢查失敗: {e}", exc_info=True)
    
    # 啟動測試流程
    QTimer.singleShot(1000, open_live_timing)
    
    # 運行 GUI
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_fastest_lap_display()
