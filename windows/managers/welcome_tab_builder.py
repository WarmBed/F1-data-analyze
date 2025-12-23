# -*- coding: utf-8 -*-
"""
WelcomeTabBuilder - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMdiArea
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QMdiSubWindow
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget
from core.gui_i18n import tr
from core.logger import get_logger

from core.logger import get_logger
from windows.widgets.custom_mdi_area import CustomMdiArea
from PyQt5.QtCore import QObject

logger = get_logger(__name__)


class WelcomeTabBuilder:
    """從 f1t_gui_main.py 提取的 create_welcome_tab 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def create_welcome_tab(self):
        """創建歡迎畫面分頁（不含 toolbar，使用全局工具列）"""
        # 創建主容器
        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        
        # ===== 移除獨立的 toolbar，使用全局工具列 =====
        # 原本的 toolbar、close_all_btn、reset_btn 已移到全局工具列
        
        # 創建歡迎內容區域和MDI區域的分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 歡迎內容區域
        welcome_widget = QWidget()
        welcome_widget.setFixedHeight(150)  # 縮小高度（移除副標題後）
        welcome_widget.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-bottom: 1px solid #CCCCCC;
            }
        """)
        
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setContentsMargins(50, 30, 50, 30)
        welcome_layout.setSpacing(20)
        
        # 主標題
        title_label = QLabel(tr("main_title", "[FINISH] PIT WALL"))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 24px;
                font-weight: bold;
                background: transparent;
            }
        """)
        welcome_layout.addWidget(title_label)
        
        # 創建MDI工作區域
        mdi_area = CustomMdiArea()
        mdi_area.setObjectName("WelcomeMDIArea")
        mdi_area.setViewMode(QMdiArea.SubWindowView)
        
        # 強制設置白色背景
        self.main_window.force_white_background(mdi_area)
        
        # ===== 自動載入積分榜到 MDI 區域 =====
        # 使用新的 UniversalDataLoader 架構
        try:
            # 導入新模組
            from modules.gui.constructor_standings import ConstructorStandingsMDI
            from modules.gui.driver_standings import DriverStandingsMDI
            from modules.gui.season_progress import SeasonProgressMDI
            from modules.gui.race_analysis.weather_timeline import WeatherTimelineMDI
            
            # 獲取當前選擇的年份（動態參數）
            current_year = self.main_window.year_combo.currentText() if hasattr(self.main_window, 'year_combo') else "2024"
            
            # 🌦️ Weather Timeline: 優先選擇下一場未開賽的賽事
            # 使用 SeasonCalendarProvider 獲取賽季日曆
            weather_race = "Japan Grand Prix"  # 預設值
            try:
                year_int = int(current_year)
                events = self.main_window._season_provider.get_completed_events(year_int)
                
                # 分離已完賽和未開賽的賽事
                completed_events = [event for event in events if event.is_completed]
                upcoming_events = [event for event in events if not event.is_completed]
                
                # ✅ 優先選擇下一場未開賽（天氣預報對未來賽事更有意義）
                if upcoming_events:
                    next_event = upcoming_events[0]
                    race_base = next_event.race_key
                    logger.debug(f"[WELCOME] Weather Timeline: 選擇下一場未開賽 → {race_base}")
                elif completed_events:
                    # 回退：如果沒有未開賽的賽事，使用最新已完賽
                    next_event = completed_events[-1]
                    race_base = next_event.race_key
                    logger.debug(f"[WELCOME] Weather Timeline: 無未開賽賽事，使用最新已完賽 → {race_base}")
                else:
                    race_base = "Japan"
                    logger.debug(f"[WELCOME] Weather Timeline: 無賽事數據，使用預設值 → {race_base}")
                
                # ✅ Function 96 期望簡短的賽事名稱（如 "Mexico"），不需要 "Grand Prix" 後綴
                weather_race = race_base
                    
            except Exception as e:
                logger.debug(f"[WELCOME] ⚠️ Weather Timeline 賽事選擇失敗: {e}")
                weather_race = "Japan"  # 使用簡短格式
            
            # 📊 積分榜/進度: 使用當前 race_combo 選擇的賽事
            current_race = "Japan"  # 預設值
            if hasattr(self.main_window, 'race_combo') and self.main_window.race_combo.currentIndex() >= 0:
                display_text = self.main_window.race_combo.currentText()
                if '(' in display_text:
                    current_race = display_text.split('(')[0].strip()
                else:
                    current_race = display_text
            
            logger.debug(f"[WELCOME] 使用年份: {current_year}")
            logger.debug(f"[WELCOME] 積分榜/進度賽事: {current_race}")
            logger.debug(f"[WELCOME] 天氣預報賽事: {weather_race}")
            
            # 創建四個 MDI 子視窗 - 三欄排列 (左欄上下分割)
            # 這四個視窗是固定的歡迎頁面內容，不受 Tile/Cascade 影響
            
            # 1. 賽季進度總覽 (左上)
            season_progress_mdi = SeasonProgressMDI(year=current_year)
            season_progress_sub = QMdiSubWindow()
            season_progress_sub.setWidget(season_progress_mdi)
            season_progress_sub.setWindowTitle(tr("season_progress_title", "Season Progress - {year}").format(year=current_year))
            season_progress_sub.setProperty("is_welcome_fixed", True)  # 標記為固定視窗
            season_progress_sub.setProperty("welcome_position", "left_top")  # 標記位置
            # 隱藏 MDI 標題列（Home 頁面內部 Widget 已有標題）
            season_progress_sub.setWindowFlags(Qt.FramelessWindowHint)
            mdi_area.addSubWindow(season_progress_sub)
            
            # 🔧 修復：追蹤 Season Progress 以便參數更新
            if not hasattr(self, 'welcome_season_progress'):
                self.main_window.welcome_season_progress = season_progress_mdi
            
            # 2. 天氣時間軸 (左下) - 使用下一場未開賽的賽事
            weather_timeline_mdi = WeatherTimelineMDI(year=current_year, event=weather_race)
            weather_timeline_sub = QMdiSubWindow()
            weather_timeline_sub.setWidget(weather_timeline_mdi)
            weather_timeline_sub.setWindowTitle(tr("weather_timeline_title", "Race Weather Forecast"))
            weather_timeline_sub.setProperty("is_welcome_fixed", True)  # 標記為固定視窗
            weather_timeline_sub.setProperty("welcome_position", "left_bottom")  # 標記位置
            # 隱藏 MDI 標題列（Home 頁面內部 Widget 已有標題）
            weather_timeline_sub.setWindowFlags(Qt.FramelessWindowHint)
            mdi_area.addSubWindow(weather_timeline_sub)
            
            # 🔧 修復：追蹤 Weather Timeline 以便參數更新
            if not hasattr(self, 'welcome_weather_timeline'):
                self.main_window.welcome_weather_timeline = weather_timeline_mdi
            
            # 3. 車隊積分榜 (中欄)
            constructor_mdi = ConstructorStandingsMDI(year=current_year)
            constructor_sub = QMdiSubWindow()
            constructor_sub.setWidget(constructor_mdi)
            constructor_sub.setWindowTitle(tr("constructor_standings_window_title", "車隊積分榜"))
            constructor_sub.setProperty("is_welcome_fixed", True)  # 標記為固定視窗
            constructor_sub.setProperty("welcome_position", "middle")  # 標記位置
            # 隱藏 MDI 標題列（Home 頁面內部 Widget 已有標題）
            constructor_sub.setWindowFlags(Qt.FramelessWindowHint)
            mdi_area.addSubWindow(constructor_sub)
            
            # 🔧 修復：追蹤 Constructor Standings 以便參數更新
            if not hasattr(self, 'welcome_constructor_standings'):
                self.main_window.welcome_constructor_standings = constructor_mdi
            
            # 4. 車手積分榜 (右欄)
            driver_mdi = DriverStandingsMDI(year=current_year)
            driver_sub = QMdiSubWindow()
            driver_sub.setWidget(driver_mdi)
            driver_sub.setWindowTitle(tr("driver_standings_window_title", "車手積分榜"))
            driver_sub.setProperty("is_welcome_fixed", True)  # 標記為固定視窗
            driver_sub.setProperty("welcome_position", "right")  # 標記位置
            # 隱藏 MDI 標題列（Home 頁面內部 Widget 已有標題）
            driver_sub.setWindowFlags(Qt.FramelessWindowHint)
            mdi_area.addSubWindow(driver_sub)
            
            # 🔧 修復：追蹤 Driver Standings 以便參數更新
            if not hasattr(self, 'welcome_driver_standings'):
                self.main_window.welcome_driver_standings = driver_mdi
            
            # 使用 QTimer 延遲設定視窗位置（等待 MDI 區域完成佈局）
            from PyQt5.QtCore import QTimer
            def arrange_windows():
                # 計算視窗尺寸 (三欄排列: 左欄上下分割, 中欄, 右欄)
                mdi_width = mdi_area.width()
                mdi_height = mdi_area.height()
                
                logger.debug(f"[WELCOME] 🔧 自動排列視窗: MDI 區域大小 {mdi_width}x{mdi_height}")
                
                # 三欄寬度: 左 33%, 中 33%, 右 34%
                left_width = mdi_width // 3
                middle_width = mdi_width // 3
                right_width = mdi_width - left_width - middle_width
                
                # 左欄高度: 上 45%, 下 55%
                left_top_height = int(mdi_height * 0.45)
                left_bottom_height = mdi_height - left_top_height
                
                # 設定位置和大小
                # 左上: Season Progress
                season_progress_sub.setGeometry(0, 0, left_width, left_top_height)
                
                # 左下: Weather Timeline
                weather_timeline_sub.setGeometry(0, left_top_height, left_width, left_bottom_height)
                
                # 中欄: Constructor Standings
                constructor_sub.setGeometry(left_width, 0, middle_width, mdi_height)
                
                # 右欄: Driver Standings
                driver_sub.setGeometry(left_width + middle_width, 0, right_width, mdi_height)
                
                # 顯示視窗
                season_progress_sub.show()
                weather_timeline_sub.show()
                constructor_sub.show()
                driver_sub.show()
                
                logger.debug(f"[WELCOME] 視窗排列完成 (三欄): 左上{left_width}x{left_top_height} + 左下{left_width}x{left_bottom_height} + 中{middle_width}x{mdi_height} + 右{right_width}x{mdi_height}")
            
            # 儲存 arrange_windows 函數以便 resize 時調用
            mdi_area.arrange_welcome_windows = arrange_windows
            
            # 延遲 500ms 執行排列（增加延遲以確保 MDI 區域完全初始化）
            QTimer.singleShot(500, arrange_windows)
            
            # 🔧 新增: 監聽 MDI 區域大小改變事件，自動重新排列視窗
            from PyQt5.QtCore import QEvent, QObject as QObj
            class ResizeEventFilter(QObj):
                def __init__(self, arrange_func):
                    super().__init__()
                    self.arrange_func = arrange_func
                    self.resize_timer = QTimer()
                    self.resize_timer.setSingleShot(True)
                    self.resize_timer.timeout.connect(self.arrange_func)
                
                def eventFilter(self, obj, event):
                    if event.type() == QEvent.Resize:
                        # 使用定時器防抖，避免頻繁觸發
                        self.resize_timer.start(100)
                    return False
            
            resize_filter = ResizeEventFilter(arrange_windows)
            mdi_area.installEventFilter(resize_filter)
            mdi_area._resize_filter = resize_filter  # 保持引用避免被垃圾回收
            
            logger.debug(f"[WELCOME] ✅ 賽季進度 + 天氣時間軸 + 積分榜模組已載入 (year={current_year}, race={current_race})")
        except Exception as e:
            logger.debug(f"[WELCOME] ❌ 模組載入失敗: {e}")
            import traceback
            traceback.print_exc()
        
        # 將歡迎區域和MDI區域添加到分割器
        splitter.addWidget(welcome_widget)
        splitter.addWidget(mdi_area)
        splitter.setSizes([150, 750])  # 歡迎區域150px（縮小），MDI區域750px（增大）
        
        tab_layout.addWidget(splitter)
        return tab_container
