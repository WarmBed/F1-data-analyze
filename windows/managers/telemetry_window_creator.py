# -*- coding: utf-8 -*-
"""
TelemetryWindowCreator - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger
from functools import partial
from windows.workers.cli_workers import MainWindowParameterProvider
from windows.widgets.popout_subwindow import PopoutSubWindow

logger = get_logger(__name__)


class TelemetryWindowCreator:
    """從 f1t_gui_main.py 提取的 create_telemetry_window 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def create_telemetry_window(self, chart_type, params, driver1=None, driver2=None, lap1_number=1, lap2_number=1, lap_type="最快圈", is_fastest_lap=False, use_time_axis=False):
        """創建單個遙測圖表視窗 - 支援速度分析"""
        logger.debug(f"[CREATE_DEBUG] ========== 創建遙測視窗 ==========")
        logger.debug(f"[CREATE_DEBUG] 圖表類型: {chart_type}")
        logger.debug(f"[CREATE_DEBUG] 參數: {params}")
        logger.debug(f"[CREATE_DEBUG] 車手: {driver1} vs {driver2}")
        logger.debug(f"[CREATE_DEBUG] 圈數: {lap1_number} vs {lap2_number}")
        logger.debug(f"[CREATE_DEBUG] 使用時間軸: {use_time_axis}")
        
        # 檢查並移除歡迎頁面（首次使用分析功能時）
        self.main_window.check_and_remove_welcome_page()
        
        # 獲取當前分頁的 MDI 區域 - 提前定義避免變量未定義錯誤
        current_mdi_area = self.main_window.get_current_mdi_area()
        if not current_mdi_area:
            logger.error("[ERROR] 無法獲取當前 MDI 區域")
            return
        
        try:
            # 檢查是否為速度分析 - 使用新版模組架構
            if chart_type == 'speed_analysis':
                logger.debug(f"[CREATE_DEBUG] 🎯 檢測到速度分析請求，嘗試新版模組架構")
                
                # 使用新版模組化架構創建速度分析
                try:
                    logger.debug(f"[CREATE_DEBUG] 📦 正在導入速度分析模組...")
                    from modules.gui.lap_analysis.speed_analysis.speed_analysis_mdi import SpeedAnalysisModule
                    
                    logger.debug(f"[CREATE_DEBUG] 🔧 創建模組實例...")
                    # 創建模組實例
                    analysis_module = SpeedAnalysisModule()
                    
                    # 創建正確的參數提供者
                    parameter_provider = MainWindowParameterProvider(self.main_window)
                    analysis_module.parameter_provider = parameter_provider
                    
                    # 設置當前參數
                    analysis_module.current_year = str(params['year'])
                    analysis_module.current_race = params['race']
                    analysis_module.current_session = params['session']
                    
                    # 設置車手和圈數參數
                    analysis_module.driver1 = driver1 if driver1 else "VER"
                    analysis_module.driver2 = driver2  # 允許為 None
                    analysis_module.lap1 = lap1_number if lap1_number else 1
                    analysis_module.lap2 = lap2_number  # 允許為 None
                    
                    logger.debug(f"[CREATE_DEBUG] ⚙️ 模組參數已設置: {params['year']} {params['race']} {params['session']}")
                    logger.debug(f"[CREATE_DEBUG] 🏁 車手和圈數已設置: {analysis_module.driver1} vs {analysis_module.driver2 if analysis_module.driver2 else 'None'}, 第{analysis_module.lap1}圈 vs 第{analysis_module.lap2 if analysis_module.lap2 else 'None'}圈")
                    
                    # 初始化模組
                    logger.debug(f"[CREATE_DEBUG] 🚀 初始化速度分析模組...")
                    if analysis_module.initialize_module():
                        logger.debug(f"[CREATE_DEBUG] ✅ 模組初始化成功！")
                        
                        # 獲取模組標題，傳遞當前參數
                        window_title = analysis_module.get_window_title(
                            year=str(params['year']), 
                            race=params['race'], 
                            session=params['session']
                        )
                        logger.debug(f"[CREATE_DEBUG] 📋 視窗標題: {window_title}")
                        
                        # 創建帶有模組的視窗
                        logger.debug(f"[CREATE_DEBUG] 🪟 創建新版模組視窗...")
                        sub_window = PopoutSubWindow(window_title, current_mdi_area, analysis_module)
                        sub_window.setWidget(analysis_module.get_widget())
                        
                        # 設置模組的父視窗引用
                        analysis_module.set_parent_window(sub_window)
                        
                        # 連接視窗關閉信號
                        # 🔴 使用 partial 避免 lambda 閉包洩漏

                        sub_window.window_closed.connect(

                            partial(self.main_window.on_lap_analysis_window_closed, analysis_module)

                        )
                        
                        # 設置視窗大小
                        width, height = analysis_module.get_default_size()
                        sub_window.resize(width, height)
                        
                        # 添加到MDI區域
                        current_mdi_area.addSubWindow(sub_window)
                        sub_window.show()
                        
                        logger.debug(f"[OK] [NEW_MODULE] 速度分析模組視窗已創建: {window_title}")
                        
                        # 建立分析模組和子視窗的對應關係
                        analysis_module._sub_window = sub_window  # 存儲子視窗引用
                        
                        # 通知主視窗圈速分析視窗已開啟（傳遞分析模組而不是子視窗）
                        self.main_window.on_lap_analysis_window_opened(analysis_module, "speed_analysis")
                        
                        # 🔧 修復：自動載入數據（包含最速圈參數和時間軸參數）
                        logger.debug(f"[CREATE_DEBUG] 🚀 自動載入速度分析數據... (use_time_axis={use_time_axis})")
                        success = analysis_module.load_data(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=driver1,
                            driver2=driver2,
                            lap1=lap1_number,
                            lap2=lap2_number,
                            is_fastest=is_fastest_lap,
                            use_time_axis=use_time_axis
                        )
                        
                        if success:
                            logger.debug(f"[CREATE_DEBUG] ✅ 數據載入成功！")
                        else:
                            logger.debug(f"[CREATE_DEBUG] ⚠️ 數據載入失敗")
                        
                        logger.debug(f"[CREATE_DEBUG] ========== 新版模組創建完成 ==========")
                        return
                    else:
                        logger.error(f"[ERROR] 速度分析模組初始化失敗，回退到舊版模式")
                        
                except Exception as e:
                    # 🔴 簡化錯誤日誌避免 traceback 持有 frame 引用（包含 analysis_module）
                    logger.error(f"[ERROR] 速度分析模組創建失敗: {e}，回退到舊版模式")
                    e = None  # 🔴 立即釋放異常對象
                    # 調試時可以取消註解：
                    # import traceback
                    # traceback.print_exc()
                
                logger.debug(f"[CREATE_DEBUG] ⚠️ 回退到舊版速度分析模式")
                
                # 回退：特殊處理速度分析（舊版模式）
                if driver2 is None:
                    driver2 = driver1
                    lap2_number = lap1_number
                    logger.debug(f"[SPEED] 速度分析自動設定: 車手2={driver2}, 圈數={lap2_number} (與車手1相同)")
                
                # 創建速度分析組件（舊版）
                try:
                    from modules.gui.lap_analysis.speed_analysis.speed_analysis_chart_widget import SpeedAnalysisChartWidget
                    from modules.gui.lap_analysis.speed_analysis.speed_analysis_data_loader import SpeedAnalysisDataLoader
                    
                    chart_widget = SpeedAnalysisChartWidget()
                    
                    # 創建數據載入器
                    speed_loader = SpeedAnalysisDataLoader()
                    speed_loader.data_loaded.connect(chart_widget.update_speed_data)
                    speed_loader.load_error.connect(lambda error: print(f"[ERROR] 速度數據載入失敗: {error}"))
                    
                    # 開始載入數據
                    logger.debug(f"[SPEED] 開始載入速度數據: {driver1} vs {driver2}")
                    speed_loader.load_speed_data(
                        year=params['year'],
                        race=params['race'], 
                        session=params['session'],
                        driver1=driver1,
                        driver2=driver2,
                        lap1=lap1_number,
                        lap2=lap2_number,
                        is_fastest_lap=is_fastest_lap
                    )
                    
                    # 將載入器保存到widget以避免被回收
                    chart_widget.speed_loader = speed_loader
                    
                    # 舊版速度分析視窗創建（僅作為回退，應該避免使用）
                    logger.warning(f"[WARNING] [LEGACY] 使用舊版速度分析創建模式")
                    
                except ImportError as e:
                    logger.error(f"[ERROR] 無法導入速度分析模組: {e}")
                    chart_widget = self.main_window.create_placeholder_telemetry_widget('speed_analysis')
                
            elif chart_type == 'rpm':
                # RPM分析 - 使用新版模組架構
                logger.debug(f"[CREATE_DEBUG] 🔄 檢測到RPM分析請求，嘗試新版模組架構")
                
                # 使用新版模組化架構創建RPM分析
                try:
                    logger.debug(f"[CREATE_DEBUG] 📦 正在導入RPM分析模組...")
                    from modules.gui.lap_analysis.rpm_analysis.rpm_analysis_mdi import RPMAnalysisModule
                    logger.debug(f"[CREATE_DEBUG] ✅ RPM分析模組導入成功")
                    
                    logger.debug(f"[CREATE_DEBUG] 🔧 創建模組實例...")
                    # 創建模組實例
                    analysis_module = RPMAnalysisModule()
                    logger.debug(f"[CREATE_DEBUG] ✅ RPM模組實例創建成功")
                    
                    # 創建正確的參數提供者
                    parameter_provider = MainWindowParameterProvider(self.main_window)
                    analysis_module.parameter_provider = parameter_provider
                    logger.debug(f"[CREATE_DEBUG] ✅ 參數提供者設置完成")
                    
                    # 設置當前參數
                    analysis_module.current_year = str(params['year'])
                    analysis_module.current_race = params['race']
                    analysis_module.current_session = params['session']
                    logger.debug(f"[CREATE_DEBUG] ✅ 基本參數設置完成: {params['year']} {params['race']} {params['session']}")
                    
                    # 設置車手和圈數參數
                    analysis_module.driver1 = driver1 if driver1 else "VER"
                    analysis_module.driver2 = driver2  # 允許為 None
                    analysis_module.lap1 = lap1_number if lap1_number else 1
                    analysis_module.lap2 = lap2_number  # 允許為 None
                    
                    logger.debug(f"[CREATE_DEBUG] ⚙️ 模組參數已設置: {params['year']} {params['race']} {params['session']}")
                    logger.debug(f"[CREATE_DEBUG] 🏁 車手和圈數已設置: {analysis_module.driver1} vs {analysis_module.driver2 if analysis_module.driver2 else 'None'}, 第{analysis_module.lap1}圈 vs 第{analysis_module.lap2 if analysis_module.lap2 else 'None'}圈")
                    
                    # 初始化模組
                    logger.debug(f"[CREATE_DEBUG] 🚀 初始化RPM分析模組...")
                    if analysis_module.initialize_module():
                        logger.debug(f"[CREATE_DEBUG] ✅ 模組初始化成功！")
                        
                        # 獲取模組標題，傳遞當前參數
                        window_title = analysis_module.get_window_title(
                            year=str(params['year']), 
                            race=params['race'], 
                            session=params['session']
                        )
                        logger.debug(f"[CREATE_DEBUG] 📋 視窗標題: {window_title}")
                        
                        # 創建帶有模組的視窗
                        logger.debug(f"[CREATE_DEBUG] 🪟 創建新版模組視窗...")
                        sub_window = PopoutSubWindow(window_title, current_mdi_area, analysis_module)
                        sub_window.setWidget(analysis_module.get_widget())
                        
                        # 設置模組的父視窗引用
                        analysis_module.set_parent_window(sub_window)
                        
                        # 連接視窗關閉信號
                        # 🔴 使用 partial 避免 lambda 閉包洩漏

                        sub_window.window_closed.connect(

                            partial(self.main_window.on_lap_analysis_window_closed, analysis_module)

                        )
                        
                        # 設置視窗大小
                        width, height = analysis_module.get_default_size()
                        sub_window.resize(width, height)
                        
                        # 添加到MDI區域
                        current_mdi_area.addSubWindow(sub_window)
                        sub_window.show()
                        
                        logger.debug(f"[OK] [NEW_MODULE] RPM分析模組視窗已創建: {window_title}")
                        
                        # 建立分析模組和子視窗的對應關係
                        analysis_module._sub_window = sub_window  # 存儲子視窗引用
                        
                        # 通知主視窗圈速分析視窗已開啟（傳遞分析模組而不是子視窗）
                        self.main_window.on_lap_analysis_window_opened(analysis_module, "rpm")
                        
                        # 🔧 修復：自動載入數據（包含最速圈參數和時間軸參數）
                        logger.debug(f"[CREATE_DEBUG] 🚀 自動載入RPM分析數據... (use_time_axis={use_time_axis})")
                        success = analysis_module.load_data(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=driver1,
                            driver2=driver2,
                            lap1=lap1_number,
                            lap2=lap2_number,
                            is_fastest=is_fastest_lap,
                            use_time_axis=use_time_axis
                        )
                        
                        if success:
                            logger.debug(f"[CREATE_DEBUG] ✅ 數據載入成功！")
                        else:
                            logger.debug(f"[CREATE_DEBUG] ⚠️ 數據載入失敗")
                        
                        logger.debug(f"[CREATE_DEBUG] ========== 新版模組創建完成 ==========")
                        return
                    else:
                        logger.error(f"[ERROR] RPM分析模組初始化失敗，回退到舊版模式")
                        
                except Exception as e:
                    logger.error(f"[ERROR] ❌ RPM分析模組創建失敗: {e}")
                    logger.error(f"[ERROR] 錯誤類型: {type(e).__name__}")
                    logger.error(f"[ERROR] 回退到舊版模式")
                    import traceback
                    logger.error(f"[ERROR] 詳細錯誤追踪:")
                    traceback.print_exc()
                
                logger.debug(f"[CREATE_DEBUG] ⚠️ 回退到舊版RPM分析模式")
                
                # 回退：舊版RPM分析模式
                
                try:
                    from modules.gui.lap_analysis.rpm_analysis.rpm_analysis_chart_widget import RPMAnalysisChartWidget
                    from modules.gui.lap_analysis.rpm_analysis.rpm_analysis_data_loader import RPMAnalysisDataLoader
                    
                    logger.debug(f"[CREATE_DEBUG] 📦 創建RPM分析組件...")
                    chart_widget = RPMAnalysisChartWidget()
                    
                    # 創建RPM資料載入器
                    logger.debug(f"[CREATE_DEBUG] � 創建RPM資料載入器...")
                    rpm_loader = RPMAnalysisDataLoader()
                    rpm_loader.data_loaded.connect(chart_widget.update_rpm_data)
                    rpm_loader.load_error.connect(lambda error: print(f"[ERROR] RPM資料載入失敗: {error}"))
                    
                    # 開始載入資料
                    logger.debug(f"[CREATE_DEBUG] 🚀 開始載入RPM資料: {driver1} vs {driver2}")
                    
                    session_info = {
                        'year': params['year'],
                        'race': params['race'],
                        'session': params['session'],
                        'driver1': driver1 if driver1 else 'VER',
                        'driver2': driver2 if driver2 else 'VER',
                        'lap1': lap1_number,
                        'lap2': lap2_number,
                        'is_fastest_lap': is_fastest_lap
                    }
                    
                    rpm_loader.load_rpm_analysis_data(session_info)
                    
                    # 將載入器保存到widget以避免被回收
                    chart_widget.rpm_loader = rpm_loader
                    
                    logger.debug(f"[OK] RPM分析組件創建成功")
                    
                except ImportError as e:
                    logger.error(f"[ERROR] 無法導入RPM分析模組: {e}")
                    chart_widget = self.main_window.create_placeholder_telemetry_widget('rpm')
                except Exception as e:
                    logger.error(f"[ERROR] RPM分析組件創建失敗: {e}")
                    import traceback
                    traceback.print_exc()
                    chart_widget = self.main_window.create_placeholder_telemetry_widget('rpm')
                
            elif chart_type == 'gear':
                # 檔位分析 - 使用新版模組架構
                logger.debug(f"[CREATE_DEBUG] 🔄 檢測到檔位分析請求，嘗試新版模組架構")
                
                # 使用新版模組化架構創建檔位分析
                try:
                    logger.debug(f"[CREATE_DEBUG] 📦 正在導入檔位分析模組...")
                    from modules.gui.lap_analysis.gear_analysis.gear_analysis_mdi import GearAnalysisModule
                    logger.debug(f"[CREATE_DEBUG] ✅ 檔位分析模組導入成功")
                    
                    logger.debug(f"[CREATE_DEBUG] 🔧 創建模組實例...")
                    # 創建模組實例
                    analysis_module = GearAnalysisModule()
                    logger.debug(f"[CREATE_DEBUG] ✅ 檔位模組實例創建成功")
                    
                    # 創建正確的參數提供者
                    parameter_provider = MainWindowParameterProvider(self.main_window)
                    analysis_module.parameter_provider = parameter_provider
                    logger.debug(f"[CREATE_DEBUG] ✅ 參數提供者設置完成")
                    
                    # 設置當前參數
                    analysis_module.current_year = str(params['year'])
                    analysis_module.current_race = params['race']
                    analysis_module.current_session = params['session']
                    logger.debug(f"[CREATE_DEBUG] ✅ 基本參數設置完成: {params['year']} {params['race']} {params['session']}")
                    
                    # 設置車手和圈數參數
                    analysis_module.driver1 = driver1 if driver1 else "VER"
                    analysis_module.driver2 = driver2  # 允許為 None
                    analysis_module.lap1 = lap1_number if lap1_number else 1
                    analysis_module.lap2 = lap2_number  # 允許為 None
                    
                    logger.debug(f"[CREATE_DEBUG] ⚙️ 模組參數已設置: {params['year']} {params['race']} {params['session']}")
                    logger.debug(f"[CREATE_DEBUG] 🏁 車手和圈數已設置: {analysis_module.driver1} vs {analysis_module.driver2 if analysis_module.driver2 else 'None'}, 第{analysis_module.lap1}圈 vs 第{analysis_module.lap2 if analysis_module.lap2 else 'None'}圈")
                    
                    # 初始化模組
                    logger.debug(f"[CREATE_DEBUG] 🚀 初始化檔位分析模組...")
                    if analysis_module.initialize_module():
                        logger.debug(f"[CREATE_DEBUG] ✅ 模組初始化成功！")
                        
                        # 獲取模組標題，傳遞當前參數
                        window_title = analysis_module.get_window_title(
                            year=str(params['year']), 
                            race=params['race'], 
                            session=params['session']
                        )
                        logger.debug(f"[CREATE_DEBUG] 📋 視窗標題: {window_title}")
                        
                        # 創建帶有模組的視窗
                        logger.debug(f"[CREATE_DEBUG] 🪟 創建新版模組視窗...")
                        sub_window = PopoutSubWindow(window_title, current_mdi_area, analysis_module)
                        sub_window.setWidget(analysis_module.get_widget())
                        
                        # 設置模組的父視窗引用
                        analysis_module.set_parent_window(sub_window)
                        
                        # 連接視窗關閉信號
                        # 🔴 使用 partial 避免 lambda 閉包洩漏

                        sub_window.window_closed.connect(

                            partial(self.main_window.on_lap_analysis_window_closed, analysis_module)

                        )
                        
                        # 設置視窗大小
                        width, height = analysis_module.get_default_size()
                        sub_window.resize(width, height)
                        
                        # 添加到MDI區域
                        current_mdi_area.addSubWindow(sub_window)
                        sub_window.show()
                        
                        logger.debug(f"[OK] [NEW_MODULE] 檔位分析模組視窗已創建: {window_title}")
                        
                        # 建立分析模組和子視窗的對應關係
                        analysis_module._sub_window = sub_window  # 存儲子視窗引用
                        
                        # 通知主視窗圈速分析視窗已開啟（傳遞分析模組而不是子視窗）
                        self.main_window.on_lap_analysis_window_opened(analysis_module, "gear")
                        
                        # 🔧 修復：自動載入數據（包含最速圈參數和時間軸參數）
                        logger.debug(f"[CREATE_DEBUG] 🚀 自動載入檔位分析數據... (use_time_axis={use_time_axis})")
                        success = analysis_module.load_data(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=driver1,
                            driver2=driver2,
                            lap1=lap1_number,
                            lap2=lap2_number,
                            is_fastest=is_fastest_lap,
                            use_time_axis=use_time_axis
                        )
                        
                        if success:
                            logger.debug(f"[CREATE_DEBUG] ✅ 數據載入成功！")
                        else:
                            logger.debug(f"[CREATE_DEBUG] ⚠️ 數據載入失敗")
                        
                        logger.debug(f"[CREATE_DEBUG] ========== 新版模組創建完成 ==========")
                        return
                    else:
                        logger.error(f"[ERROR] 檔位分析模組初始化失敗，回退到舊版模式")
                        
                except Exception as e:
                    logger.error(f"[ERROR] ❌ 檔位分析模組創建失敗: {e}")
                    logger.error(f"[ERROR] 錯誤類型: {type(e).__name__}")
                    logger.error(f"[ERROR] 回退到舊版模式")
                    import traceback
                    logger.error(f"[ERROR] 詳細錯誤追踪:")
                    traceback.print_exc()
                
                logger.debug(f"[CREATE_DEBUG] ⚠️ 回退到舊版檔位分析模式")
                
                # 回退：舊版檔位分析模式
                try:
                    from modules.gui.lap_analysis.gear_analysis.gear_analysis_chart_widget import GearAnalysisChartWidget
                    from modules.gui.lap_analysis.gear_analysis.gear_analysis_data_loader import GearAnalysisDataLoader
                    
                    logger.debug(f"[CREATE_DEBUG] 📦 創建檔位分析組件...")
                    chart_widget = GearAnalysisChartWidget()
                    
                    # 創建檔位資料載入器
                    logger.debug(f"[CREATE_DEBUG] 📊 創建檔位資料載入器...")
                    gear_loader = GearAnalysisDataLoader()
                    gear_loader.data_loaded.connect(chart_widget.update_gear_data)
                    gear_loader.load_error.connect(lambda error: print(f"[ERROR] 檔位資料載入失敗: {error}"))
                    
                    # 開始載入資料
                    logger.debug(f"[CREATE_DEBUG] 🚀 開始載入檔位資料: {driver1} vs {driver2}")
                    
                    session_info = {
                        'year': params['year'],
                        'race': params['race'],
                        'session': params['session'],
                        'driver1': driver1 if driver1 else 'VER',
                        'driver2': driver2 if driver2 else 'VER',
                        'lap1': lap1_number,
                        'lap2': lap2_number,
                        'is_fastest_lap': is_fastest_lap
                    }
                    
                    gear_loader.load_gear_analysis_data(session_info)
                    
                    # 將載入器保存到widget以避免被回收
                    chart_widget.gear_loader = gear_loader
                    
                    logger.debug(f"[OK] 檔位分析組件創建成功")
                    
                except ImportError as e:
                    logger.error(f"[ERROR] 無法導入檔位分析模組: {e}")
                    chart_widget = self.main_window.create_placeholder_telemetry_widget('gear')
                except Exception as e:
                    logger.error(f"[ERROR] 檔位分析組件創建失敗: {e}")
                    import traceback
                    traceback.print_exc()
                    chart_widget = self.main_window.create_placeholder_telemetry_widget('gear')

            elif chart_type == 'Speeddiff' or chart_type == 'speeddiff' or chart_type == 'speed_diff':
                # 速度差分析 - 使用新版模組架構
                logger.debug(f"[CREATE_DEBUG] 🔄 檢測到速度差分析請求，嘗試新版模組架構")

                # 使用新版模組化架構創建速度差分析
                try:
                    logger.debug(f"[CREATE_DEBUG] 📦 正在導入速度差分析模組...")
                    from modules.gui.lap_analysis.speeddiff_analysis.speeddiff_analysis_mdi import SpeeddiffAnalysisModule
                    logger.debug(f"[CREATE_DEBUG] ✅ 速度差分析模組導入成功")
                    
                    logger.debug(f"[CREATE_DEBUG] 🔧 創建模組實例...")
                    # 創建模組實例
                    analysis_module = SpeeddiffAnalysisModule()
                    logger.debug(f"[CREATE_DEBUG] ✅ 速度差模組實例創建成功")
                    
                    # 創建正確的參數提供者
                    parameter_provider = MainWindowParameterProvider(self.main_window)
                    analysis_module.parameter_provider = parameter_provider
                    logger.debug(f"[CREATE_DEBUG] ✅ 參數提供者設置完成")
                    
                    # 設置當前參數
                    analysis_module.current_year = str(params['year'])
                    analysis_module.current_race = params['race']
                    analysis_module.current_session = params['session']
                    logger.debug(f"[CREATE_DEBUG] ✅ 基本參數設置完成: {params['year']} {params['race']} {params['session']}")
                    
                    # 設置車手和圈數參數
                    analysis_module.driver1 = driver1 if driver1 else "VER"
                    analysis_module.driver2 = driver2  # 允許為 None
                    analysis_module.lap1 = lap1_number if lap1_number else 1
                    analysis_module.lap2 = lap2_number  # 允許為 None
                    
                    logger.debug(f"[CREATE_DEBUG] ⚙️ 模組參數已設置: {params['year']} {params['race']} {params['session']}")
                    logger.debug(f"[CREATE_DEBUG] 🏁 車手和圈數已設置: {analysis_module.driver1} vs {analysis_module.driver2 if analysis_module.driver2 else 'None'}, 第{analysis_module.lap1}圈 vs 第{analysis_module.lap2 if analysis_module.lap2 else 'None'}圈")
                    
                    # 初始化模組
                    logger.debug(f"[CREATE_DEBUG] 🚀 初始化速度差分析模組...")
                    if analysis_module.initialize_module():
                        logger.debug(f"[CREATE_DEBUG] ✅ 模組初始化成功！")
                        
                        # 獲取模組標題，傳遞當前參數
                        window_title = analysis_module.get_window_title(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=analysis_module.driver1,
                            driver2=analysis_module.driver2,
                            lap1=analysis_module.lap1,
                            lap2=analysis_module.lap2
                        )
                        logger.debug(f"[CREATE_DEBUG] 📝 視窗標題: {window_title}")
                        
                        # 創建子視窗並設置標題 - 使用與 RPM 分析相同的模式
                        logger.debug(f"[CREATE_DEBUG] 🖼️ 創建MDI子視窗...")
                        sub_window = PopoutSubWindow(window_title, current_mdi_area, analysis_module)
                        sub_window.setWidget(analysis_module.get_widget())
                        
                        # 設置模組的父視窗引用
                        analysis_module.set_parent_window(sub_window)
                        
                        # 連接視窗關閉信號
                        # 🔴 關鍵修復：連接 window_closed 信號以觸發按鈕清理
                        # 🔴 使用 partial 避免 lambda 閉包洩漏
                        sub_window.window_closed.connect(
                            partial(self.main_window.on_lap_analysis_window_closed, analysis_module)
                        )
                        logger.debug(f"[CREATE_DEBUG] ✅ 視窗關閉信號已連接")
                        
                        # 設置視窗大小
                        sub_window.resize(1200, 800)
                        logger.debug(f"[CREATE_DEBUG] ✅ 子視窗創建成功")
                        
                        # 添加到MDI區域
                        current_mdi_area.addSubWindow(sub_window)
                        sub_window.show()
                        
                        logger.debug(f"[OK] [NEW_MODULE] 速度差分析模組視窗已創建: {window_title}")
                        
                        # 建立分析模組和子視窗的對應關係
                        analysis_module._sub_window = sub_window  # 存儲子視窗引用
                        
                        # 通知主視窗圈速分析視窗已開啟（傳遞分析模組而不是子視窗）
                        self.main_window.on_lap_analysis_window_opened(analysis_module, "Speeddiff")
                        
                        # 🔧 修復：自動載入數據（包含最速圈參數和時間軸參數）
                        logger.debug(f"[CREATE_DEBUG] 🚀 自動載入速度差分析數據... (use_time_axis={use_time_axis})")
                        success = analysis_module.load_data(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=driver1,
                            driver2=driver2,
                            lap1=lap1_number,
                            lap2=lap2_number,
                            is_fastest=is_fastest_lap,
                            use_time_axis=use_time_axis
                        )
                        
                        if success:
                            logger.debug(f"[CREATE_DEBUG] ✅ 數據載入成功！")
                        else:
                            logger.debug(f"[CREATE_DEBUG] ⚠️ 數據載入失敗")
                        
                        logger.debug(f"[CREATE_DEBUG] ========== 新版模組創建完成 ==========")
                        return
                    else:
                        logger.error(f"[ERROR] 速度差分析模組初始化失敗，回退到舊版模式")
                        
                except Exception as e:
                    logger.error(f"[ERROR] ❌ 速度差分析模組創建失敗: {e}")
                    logger.error(f"[ERROR] 錯誤類型: {type(e).__name__}")
                    logger.error(f"[ERROR] 回退到舊版模式")
                    import traceback
                    logger.error(f"[ERROR] 詳細錯誤追踪:")
                    traceback.print_exc()
                
                logger.debug(f"[CREATE_DEBUG] ⚠️ 回退到舊版速度差分析模式")
                
                # 回退：舊版速度差分析模式
                try:
                    from modules.gui.lap_analysis.speeddiff_analysis.speeddiff_analysis_chart_widget import SpeeddiffAnalysisChartWidget
                    from modules.gui.lap_analysis.speeddiff_analysis.speeddiff_analysis_data_loader import SpeeddiffAnalysisDataLoader
                    
                    logger.debug(f"[CREATE_DEBUG] 📦 創建速度差分析組件...")
                    chart_widget = SpeeddiffAnalysisChartWidget()
                    
                    # 創建速度差資料載入器
                    logger.debug(f"[CREATE_DEBUG] 📊 創建速度差資料載入器...")
                    Speeddiff_loader = SpeeddiffAnalysisDataLoader()
                    Speeddiff_loader.data_loaded.connect(chart_widget.update_speeddiff_data)
                    Speeddiff_loader.load_error.connect(lambda error: print(f"[ERROR] 速度差資料載入失敗: {error}"))
                    
                    # 開始載入資料
                    logger.debug(f"[CREATE_DEBUG] 🚀 開始載入速度差資料: {driver1} vs {driver2}")
                    
                    session_info = {
                        'year': params['year'],
                        'race': params['race'],
                        'session': params['session'],
                        'driver1': driver1 if driver1 else 'VER',
                        'driver2': driver2 if driver2 else 'VER',
                        'lap1': lap1_number,
                        'lap2': lap2_number,
                        'is_fastest_lap': is_fastest_lap
                    }
                    
                    Speeddiff_loader.load_speeddiff_analysis_data(session_info)
                    
                    # 將載入器保存到widget以避免被回收
                    chart_widget.Speeddiff_loader = Speeddiff_loader
                    
                    logger.debug(f"[OK] 速度差分析組件創建成功")
                    
                except ImportError as e:
                    logger.error(f"[ERROR] 無法導入速度差分析模組: {e}")
                    chart_widget = self.main_window.create_placeholder_telemetry_widget('speeddiff')
                except Exception as e:
                    logger.error(f"[ERROR] 速度差分析組件創建失敗: {e}")
                    import traceback
                    traceback.print_exc()
                    chart_widget = self.main_window.create_placeholder_telemetry_widget('speeddiff')
                
            elif chart_type == 'acceleration':
                # 加速度分析 - 使用新版模組架構
                logger.debug(f"[CREATE_DEBUG] 🔄 檢測到加速度分析請求，嘗試新版模組架構")
                
                # 使用新版模組化架構創建加速度分析
                try:
                    logger.debug(f"[CREATE_DEBUG] 📦 正在導入加速度分析模組...")
                    from modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_mdi import accelerationAnalysisModule
                    logger.debug(f"[CREATE_DEBUG] ✅ 加速度分析模組導入成功")
                    
                    logger.debug(f"[CREATE_DEBUG] 🔧 創建模組實例...")
                    # 創建模組實例
                    analysis_module = accelerationAnalysisModule()
                    logger.debug(f"[CREATE_DEBUG] ✅ 加速度模組實例創建成功")
                    
                    # 創建正確的參數提供者
                    parameter_provider = MainWindowParameterProvider(self.main_window)
                    analysis_module.parameter_provider = parameter_provider
                    logger.debug(f"[CREATE_DEBUG] ✅ 參數提供者設置完成")
                    
                    # 設置當前參數
                    analysis_module.current_year = str(params['year'])
                    analysis_module.current_race = params['race']
                    analysis_module.current_session = params['session']
                    logger.debug(f"[CREATE_DEBUG] ✅ 基本參數設置完成: {params['year']} {params['race']} {params['session']}")
                    
                    # 設置車手和圈數參數
                    analysis_module.driver1 = driver1 if driver1 else "VER"
                    analysis_module.driver2 = driver2  # 允許為 None
                    analysis_module.lap1 = lap1_number if lap1_number else 1
                    analysis_module.lap2 = lap2_number  # 允許為 None
                    
                    logger.debug(f"[CREATE_DEBUG] ⚙️ 模組參數已設置: {params['year']} {params['race']} {params['session']}")
                    logger.debug(f"[CREATE_DEBUG] 🏁 車手和圈數已設置: {analysis_module.driver1} vs {analysis_module.driver2 if analysis_module.driver2 else 'None'}, 第{analysis_module.lap1}圈 vs 第{analysis_module.lap2 if analysis_module.lap2 else 'None'}圈")
                    
                    # 初始化模組
                    logger.debug(f"[CREATE_DEBUG] 🚀 初始化加速度分析模組...")
                    if analysis_module.initialize_module():
                        logger.debug(f"[CREATE_DEBUG] ✅ 模組初始化成功！")
                        
                        # 獲取模組標題，傳遞當前參數
                        window_title = analysis_module.get_window_title(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=analysis_module.driver1,
                            driver2=analysis_module.driver2,
                            lap1=analysis_module.lap1,
                            lap2=analysis_module.lap2
                        )
                        logger.debug(f"[CREATE_DEBUG] 📝 視窗標題: {window_title}")
                        
                        # 創建子視窗並設置標題 - 使用與 RPM 分析相同的模式
                        logger.debug(f"[CREATE_DEBUG] 🖼️ 創建MDI子視窗...")
                        sub_window = PopoutSubWindow(window_title, current_mdi_area, analysis_module)
                        sub_window.setWidget(analysis_module.get_widget())
                        
                        # 設置模組的父視窗引用
                        analysis_module.set_parent_window(sub_window)
                        
                        # 連接視窗關閉信號
                        # 🔴 關鍵修復：連接 window_closed 信號以觸發按鈕清理
                        # 🔴 使用 partial 避免 lambda 閉包洩漏
                        sub_window.window_closed.connect(
                            partial(self.main_window.on_lap_analysis_window_closed, analysis_module)
                        )
                        logger.debug(f"[CREATE_DEBUG] ✅ 視窗關閉信號已連接")
                        
                        # 設置視窗大小
                        sub_window.resize(1200, 800)
                        logger.debug(f"[CREATE_DEBUG] ✅ 子視窗創建成功")
                        
                        # 添加到MDI區域
                        current_mdi_area.addSubWindow(sub_window)
                        sub_window.show()
                        
                        logger.debug(f"[OK] [NEW_MODULE] 加速度分析模組視窗已創建: {window_title}")
                        
                        # 建立分析模組和子視窗的對應關係
                        analysis_module._sub_window = sub_window  # 存儲子視窗引用
                        
                        # 通知主視窗圈速分析視窗已開啟（傳遞分析模組而不是子視窗）
                        self.main_window.on_lap_analysis_window_opened(analysis_module, "acceleration")
                        
                        # 🔧 修復：自動載入數據（包含最速圈參數和時間軸參數）
                        logger.debug(f"[CREATE_DEBUG] 🚀 自動載入加速度分析數據... (use_time_axis={use_time_axis})")
                        success = analysis_module.load_data(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=driver1,
                            driver2=driver2,
                            lap1=lap1_number,
                            lap2=lap2_number,
                            is_fastest=is_fastest_lap,
                            use_time_axis=use_time_axis
                        )
                        
                        if success:
                            logger.debug(f"[CREATE_DEBUG] ✅ 數據載入成功！")
                        else:
                            logger.debug(f"[CREATE_DEBUG] ⚠️ 數據載入失敗")
                        
                        logger.debug(f"[CREATE_DEBUG] ========== 新版模組創建完成 ==========")
                        return
                    else:
                        logger.error(f"[ERROR] 加速度分析模組初始化失敗，回退到舊版模式")
                        
                except Exception as e:
                    logger.error(f"[ERROR] ❌ 加速度分析模組創建失敗: {e}")
                    logger.error(f"[ERROR] 錯誤類型: {type(e).__name__}")
                    logger.error(f"[ERROR] 回退到舊版模式")
                    import traceback
                    logger.error(f"[ERROR] 詳細錯誤追踪:")
                    traceback.print_exc()
                
                logger.debug(f"[CREATE_DEBUG] ⚠️ 回退到舊版加速度分析模式")
                
                # 回退：舊版加速度分析模式
                try:
                    from modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_chart_widget import accelerationAnalysisChartWidget
                    from modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_data_loader import accelerationAnalysisDataLoader
                    
                    logger.debug(f"[CREATE_DEBUG] 📦 創建加速度分析組件...")
                    chart_widget = accelerationAnalysisChartWidget()
                    
                    # 創建加速度資料載入器
                    logger.debug(f"[CREATE_DEBUG] 📊 創建加速度資料載入器...")
                    acceleration_loader = accelerationAnalysisDataLoader()
                    acceleration_loader.data_loaded.connect(chart_widget.update_acceleration_data)
                    acceleration_loader.load_error.connect(lambda error: print(f"[ERROR] 加速度資料載入失敗: {error}"))
                    
                    # 開始載入資料
                    logger.debug(f"[CREATE_DEBUG] 🚀 開始載入加速度資料: {driver1} vs {driver2}")
                    
                    session_info = {
                        'year': params['year'],
                        'race': params['race'],
                        'session': params['session'],
                        'driver1': driver1 if driver1 else 'VER',
                        'driver2': driver2 if driver2 else 'VER',
                        'lap1': lap1_number,
                        'lap2': lap2_number,
                        'is_fastest_lap': is_fastest_lap
                    }
                    
                    acceleration_loader.load_acceleration_analysis_data(session_info)
                    
                    # 將載入器保存到widget以避免被回收
                    chart_widget.acceleration_loader = acceleration_loader
                    
                    logger.debug(f"[OK] 加速度分析組件創建成功")
                    
                except ImportError as e:
                    logger.error(f"[ERROR] 無法導入加速度分析模組: {e}")
                    chart_widget = self.main_window.create_placeholder_telemetry_widget('acceleration')
                except Exception as e:
                    logger.error(f"[ERROR] 加速度分析組件創建失敗: {e}")
                    import traceback
                    traceback.print_exc()
                    chart_widget = self.main_window.create_placeholder_telemetry_widget('acceleration')

            elif chart_type == 'throttle':
                # 油門分析 - 使用新版模組架構
                logger.debug(f"[CREATE_DEBUG] 🔄 檢測到油門分析請求，使用新版模組架構")
                
                # 使用新版模組化架構創建油門分析
                try:
                    logger.debug(f"[CREATE_DEBUG] 📦 正在導入油門分析模組...")
                    from modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_mdi import ThrottleAnalysisModule
                    logger.debug(f"[CREATE_DEBUG] ✅ 油門分析模組導入成功")
                    
                    logger.debug(f"[CREATE_DEBUG] 🔧 創建模組實例...")
                    # 創建模組實例
                    analysis_module = ThrottleAnalysisModule()
                    logger.debug(f"[CREATE_DEBUG] ✅ 油門模組實例創建成功")
                    
                    # 創建正確的參數提供者
                    parameter_provider = MainWindowParameterProvider(self.main_window)
                    analysis_module.parameter_provider = parameter_provider
                    logger.debug(f"[CREATE_DEBUG] ✅ 參數提供者設置完成")
                    
                    # 設置當前參數
                    analysis_module.current_year = str(params['year'])
                    analysis_module.current_race = params['race']
                    analysis_module.current_session = params['session']
                    logger.debug(f"[CREATE_DEBUG] ✅ 基本參數設置完成: {params['year']} {params['race']} {params['session']}")
                    
                    # 設置車手和圈數參數
                    analysis_module.driver1 = driver1 if driver1 else "VER"
                    analysis_module.driver2 = driver2  # 允許為 None
                    analysis_module.lap1 = lap1_number if lap1_number else 1
                    analysis_module.lap2 = lap2_number  # 允許為 None
                    
                    logger.debug(f"[CREATE_DEBUG] ⚙️ 模組參數已設置: {params['year']} {params['race']} {params['session']}")
                    logger.debug(f"[CREATE_DEBUG] 🏁 車手和圈數已設置: {analysis_module.driver1} vs {analysis_module.driver2 if analysis_module.driver2 else 'None'}, 第{analysis_module.lap1}圈 vs 第{analysis_module.lap2 if analysis_module.lap2 else 'None'}圈")
                    
                    # 初始化模組
                    logger.debug(f"[CREATE_DEBUG] 🚀 初始化油門分析模組...")
                    if analysis_module.initialize_module():
                        logger.debug(f"[CREATE_DEBUG] ✅ 模組初始化成功！")
                        
                        # 獲取模組標題，傳遞當前參數
                        window_title = analysis_module.get_window_title(
                            year=str(params['year']), 
                            race=params['race'], 
                            session=params['session']
                        )
                        logger.debug(f"[CREATE_DEBUG] 📋 視窗標題: {window_title}")
                        
                        # 創建帶有模組的視窗
                        logger.debug(f"[CREATE_DEBUG] 🪟 創建新版模組視窗...")
                        sub_window = PopoutSubWindow(window_title, current_mdi_area, analysis_module)
                        sub_window.setWidget(analysis_module.get_widget())
                        
                        # 設置模組的父視窗引用
                        analysis_module.set_parent_window(sub_window)
                        
                        # 連接視窗關閉信號
                        # 🔴 使用 partial 避免 lambda 閉包洩漏

                        sub_window.window_closed.connect(

                            partial(self.main_window.on_lap_analysis_window_closed, analysis_module)

                        )
                        
                        # 設置視窗大小
                        sub_window.resize(1200, 800)
                        
                        # *** 關鍵修復：添加視窗到MDI區域 ***
                        current_mdi_area.addSubWindow(sub_window)
                        sub_window.show()
                        
                        logger.debug(f"[OK] [NEW_MODULE] 油門分析模組視窗已創建: {window_title}")
                        
                        # 建立分析模組和子視窗的對應關係
                        analysis_module._sub_window = sub_window  # 存儲子視窗引用
                        
                        # 通知主視窗圈速分析視窗已開啟（傳遞分析模組而不是子視窗）
                        self.main_window.on_lap_analysis_window_opened(analysis_module, "throttle")
                        
                        # 🔧 修復：自動載入數據（包含最速圈參數和時間軸參數）- 與速度分析完全一致
                        logger.debug(f"[CREATE_DEBUG] 🚀 自動載入油門分析數據... (use_time_axis={use_time_axis})")
                        success = analysis_module.load_data(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=driver1,
                            driver2=driver2,
                            lap1=lap1_number,
                            lap2=lap2_number,
                            is_fastest=is_fastest_lap,
                            use_time_axis=use_time_axis
                        )
                        
                        if success:
                            logger.debug(f"[CREATE_DEBUG] ✅ 數據載入成功！")
                        else:
                            logger.debug(f"[CREATE_DEBUG] ⚠️ 數據載入失敗")
                        
                        logger.debug(f"[CREATE_DEBUG] ========== 新版模組創建完成 ==========")
                        return
                    else:
                        logger.error(f"[ERROR] 油門分析模組初始化失敗，回退到舊版模式")
                        
                except Exception as e:
                    logger.error(f"[ERROR] 油門分析模組創建失敗: {e}，回退到舊版模式")
                    import traceback
                    traceback.print_exc()
                
                logger.debug(f"[CREATE_DEBUG] ⚠️ 回退到舊版油門分析模式")
                
                # 回退：特殊處理油門分析（舊版模式）
                if driver2 is None:
                    driver2 = driver1
                    lap2_number = lap1_number
                    logger.debug(f"[THROTTLE] 油門分析自動設定: 車手2={driver2}, 圈數={lap2_number} (與車手1相同)")

            elif chart_type == 'distancediff':
                # 距離差分析 - 使用新版模組架構
                logger.debug(f"[CREATE_DEBUG] 🔄 檢測到距離差分析請求，嘗試新版模組架構")

                # 使用新版模組化架構創建距離差分析
                try:
                    logger.debug(f"[CREATE_DEBUG] 📦 正在導入距離差分析模組...")
                    from modules.gui.lap_analysis.distancediff_analysis.distancediff_analysis_mdi import distancediffAnalysisModule
                    logger.debug(f"[CREATE_DEBUG] ✅ 距離差分析模組導入成功")
                    
                    logger.debug(f"[CREATE_DEBUG] 🔧 創建模組實例...")
                    # 創建模組實例
                    analysis_module = distancediffAnalysisModule()
                    logger.debug(f"[CREATE_DEBUG] ✅ 距離差模組實例創建成功")
                    
                    # 創建正確的參數提供者
                    parameter_provider = MainWindowParameterProvider(self.main_window)
                    analysis_module.parameter_provider = parameter_provider
                    logger.debug(f"[CREATE_DEBUG] ✅ 參數提供者設置完成")
                    
                    # 設置當前參數
                    analysis_module.current_year = str(params['year'])
                    analysis_module.current_race = params['race']
                    analysis_module.current_session = params['session']
                    logger.debug(f"[CREATE_DEBUG] ✅ 基本參數設置完成: {params['year']} {params['race']} {params['session']}")
                    
                    # 設置車手和圈數參數
                    analysis_module.driver1 = driver1 if driver1 else "VER"
                    analysis_module.driver2 = driver2  # 允許為 None
                    analysis_module.lap1 = lap1_number if lap1_number else 1
                    analysis_module.lap2 = lap2_number  # 允許為 None
                    
                    logger.debug(f"[CREATE_DEBUG] ⚙️ 模組參數已設置: {params['year']} {params['race']} {params['session']}")
                    logger.debug(f"[CREATE_DEBUG] 🏁 車手和圈數已設置: {analysis_module.driver1} vs {analysis_module.driver2 if analysis_module.driver2 else 'None'}, 第{analysis_module.lap1}圈 vs 第{analysis_module.lap2 if analysis_module.lap2 else 'None'}圈")
                    
                    # 初始化模組
                    logger.debug(f"[CREATE_DEBUG] 🚀 初始化距離差分析模組...")
                    if analysis_module.initialize_module():
                        logger.debug(f"[CREATE_DEBUG] ✅ 模組初始化成功！")
                        
                        # 獲取模組標題，傳遞當前參數
                        window_title = analysis_module.get_window_title(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=analysis_module.driver1,
                            driver2=analysis_module.driver2,
                            lap1=analysis_module.lap1,
                            lap2=analysis_module.lap2
                        )
                        logger.debug(f"[CREATE_DEBUG] 📝 視窗標題: {window_title}")
                        
                        # 創建子視窗並設置標題 - 使用與 RPM 分析相同的模式
                        logger.debug(f"[CREATE_DEBUG] 🖼️ 創建MDI子視窗...")
                        sub_window = PopoutSubWindow(window_title, current_mdi_area, analysis_module)
                        sub_window.setWidget(analysis_module.get_widget())
                        
                        # 設置模組的父視窗引用
                        analysis_module.set_parent_window(sub_window)
                        
                        # 連接視窗關閉信號
                        # 🔴 關鍵修復：連接 window_closed 信號以觸發按鈕清理
                        # 🔴 使用 partial 避免 lambda 閉包洩漏
                        sub_window.window_closed.connect(
                            partial(self.main_window.on_lap_analysis_window_closed, analysis_module)
                        )
                        logger.debug(f"[CREATE_DEBUG] ✅ 視窗關閉信號已連接")
                        
                        # 設置視窗大小
                        sub_window.resize(1200, 800)
                        logger.debug(f"[CREATE_DEBUG] ✅ 子視窗創建成功")
                        
                        # 添加到MDI區域
                        current_mdi_area.addSubWindow(sub_window)
                        sub_window.show()
                        
                        logger.debug(f"[OK] [NEW_MODULE] 距離差分析模組視窗已創建: {window_title}")
                        
                        # 建立分析模組和子視窗的對應關係
                        analysis_module._sub_window = sub_window  # 存儲子視窗引用
                        
                        # 通知主視窗圈速分析視窗已開啟（傳遞分析模組而不是子視窗）
                        self.main_window.on_lap_analysis_window_opened(analysis_module, "distancediff")
                        
                        # 🔧 修復：自動載入數據（包含最速圈參數和時間軸參數）
                        logger.debug(f"[CREATE_DEBUG] 🚀 自動載入距離差分析數據... (use_time_axis={use_time_axis})")
                        success = analysis_module.load_data(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=driver1,
                            driver2=driver2,
                            lap1=lap1_number,
                            lap2=lap2_number,
                            is_fastest=is_fastest_lap,
                            use_time_axis=use_time_axis
                        )
                        
                        if success:
                            logger.debug(f"[CREATE_DEBUG] ✅ 數據載入成功！")
                        else:
                            logger.debug(f"[CREATE_DEBUG] ⚠️ 數據載入失敗")
                        
                        logger.debug(f"[CREATE_DEBUG] ========== 新版模組創建完成 ==========")
                        return
                    else:
                        logger.error(f"[ERROR] 距離差分析模組初始化失敗，回退到舊版模式")
                        
                except Exception as e:
                    logger.error(f"[ERROR] ❌ 距離差分析模組創建失敗: {e}")
                    logger.error(f"[ERROR] 錯誤類型: {type(e).__name__}")
                    logger.error(f"[ERROR] 回退到舊版模式")
                    import traceback
                    logger.error(f"[ERROR] 詳細錯誤追踪:")
                    traceback.print_exc()
                
                logger.debug(f"[CREATE_DEBUG] ⚠️ 回退到舊版距離差分析模式")
                
                # 回退：舊版距離差分析模式
                try:
                    from modules.gui.lap_analysis.distancediff_analysis.distancediff_analysis_chart_widget import distancediffAnalysisChartWidget
                    from modules.gui.lap_analysis.distancediff_analysis.distancediff_analysis_data_loader import distancediffAnalysisDataLoader
                    
                    logger.debug(f"[CREATE_DEBUG] 📦 創建距離差分析組件...")
                    chart_widget = distancediffAnalysisChartWidget()
                    
                    # 創建距離差資料載入器
                    logger.debug(f"[CREATE_DEBUG] 📊 創建距離差資料載入器...")
                    distancediff_loader = distancediffAnalysisDataLoader()
                    distancediff_loader.data_loaded.connect(chart_widget.update_distancediff_data)
                    distancediff_loader.load_error.connect(lambda error: print(f"[ERROR] 距離差資料載入失敗: {error}"))
                    
                    # 開始載入資料
                    logger.debug(f"[CREATE_DEBUG] 🚀 開始載入距離差資料: {driver1} vs {driver2}")
                    
                    session_info = {
                        'year': params['year'],
                        'race': params['race'],
                        'session': params['session'],
                        'driver1': driver1 if driver1 else 'VER',
                        'driver2': driver2 if driver2 else 'VER',
                        'lap1': lap1_number,
                        'lap2': lap2_number,
                        'is_fastest_lap': is_fastest_lap
                    }
                    
                    distancediff_loader.load_distancediff_analysis_data(session_info)
                    
                    # 將載入器保存到widget以避免被回收
                    chart_widget.distancediff_loader = distancediff_loader
                    
                    logger.debug(f"[OK] 距離差分析組件創建成功")
                    
                except ImportError as e:
                    logger.error(f"[ERROR] 無法導入距離差分析模組: {e}")
                    chart_widget = self.main_window.create_placeholder_telemetry_widget('distancediff')
                except Exception as e:
                    logger.error(f"[ERROR] 距離差分析組件創建失敗: {e}")
                    import traceback
                    traceback.print_exc()
                    chart_widget = self.main_window.create_placeholder_telemetry_widget('distancediff')
                
            elif chart_type == 'timediff':
                # 時間差分析 - 使用新版模組架構
                logger.debug(f"[CREATE_DEBUG] ⏱️ 檢測到時間差分析請求，嘗試新版模組架構")

                # 使用新版模組化架構創建時間差分析
                try:
                    logger.debug(f"[CREATE_DEBUG] 📦 正在導入時間差分析模組...")
                    from modules.gui.lap_analysis.timediff_analysis.timediff_analysis_mdi import timediffAnalysisModule
                    logger.debug(f"[CREATE_DEBUG] ✅ 時間差分析模組導入成功")
                    
                    logger.debug(f"[CREATE_DEBUG] 🔧 創建模組實例...")
                    # 創建模組實例
                    analysis_module = timediffAnalysisModule()
                    logger.debug(f"[CREATE_DEBUG] ✅ 時間差模組實例創建成功")
                    
                    # 創建正確的參數提供者
                    parameter_provider = MainWindowParameterProvider(self.main_window)
                    analysis_module.parameter_provider = parameter_provider
                    logger.debug(f"[CREATE_DEBUG] ✅ 參數提供者設置完成")
                    
                    # 設置當前參數
                    analysis_module.current_year = str(params['year'])
                    analysis_module.current_race = params['race']
                    analysis_module.current_session = params['session']
                    logger.debug(f"[CREATE_DEBUG] ✅ 基本參數設置完成: {params['year']} {params['race']} {params['session']}")
                    
                    # 設置車手和圈數參數
                    analysis_module.driver1 = driver1 if driver1 else "VER"
                    analysis_module.driver2 = driver2  # 允許為 None
                    analysis_module.lap1 = lap1_number if lap1_number else 1
                    analysis_module.lap2 = lap2_number  # 允許為 None
                    
                    logger.debug(f"[CREATE_DEBUG] ⚙️ 模組參數已設置: {params['year']} {params['race']} {params['session']}")
                    logger.debug(f"[CREATE_DEBUG] 🏁 車手和圈數已設置: {analysis_module.driver1} vs {analysis_module.driver2 if analysis_module.driver2 else 'None'}, 第{analysis_module.lap1}圈 vs 第{analysis_module.lap2 if analysis_module.lap2 else 'None'}圈")
                    
                    # 初始化模組
                    logger.debug(f"[CREATE_DEBUG] 🚀 初始化時間差分析模組...")
                    if analysis_module.initialize_module():
                        logger.debug(f"[CREATE_DEBUG] ✅ 模組初始化成功！")
                        
                        # 獲取模組標題，傳遞當前參數
                        window_title = analysis_module.get_window_title(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=analysis_module.driver1,
                            driver2=analysis_module.driver2,
                            lap1=analysis_module.lap1,
                            lap2=analysis_module.lap2
                        )
                        logger.debug(f"[CREATE_DEBUG] 📝 視窗標題: {window_title}")
                        
                        # 創建子視窗並設置標題
                        logger.debug(f"[CREATE_DEBUG] 🖼️ 創建MDI子視窗...")
                        sub_window = PopoutSubWindow(window_title, current_mdi_area, analysis_module)
                        sub_window.setWidget(analysis_module.get_widget())
                        
                        # 設置模組的父視窗引用
                        analysis_module.set_parent_window(sub_window)
                        
                        # 連接視窗關閉信號
                        # 🔴 關鍵修復：連接 window_closed 信號以觸發按鈕清理
                        # 🔴 使用 partial 避免 lambda 閉包洩漏
                        sub_window.window_closed.connect(
                            partial(self.main_window.on_lap_analysis_window_closed, analysis_module)
                        )
                        logger.debug(f"[CREATE_DEBUG] ✅ 視窗關閉信號已連接")
                        
                        # 設置視窗大小
                        sub_window.resize(1200, 800)
                        logger.debug(f"[CREATE_DEBUG] ✅ 子視窗創建成功")
                        
                        # 添加到MDI區域
                        current_mdi_area.addSubWindow(sub_window)
                        sub_window.show()
                        
                        logger.debug(f"[OK] [NEW_MODULE] 時間差分析模組視窗已創建: {window_title}")
                        
                        # 建立分析模組和子視窗的對應關係
                        analysis_module._sub_window = sub_window  # 存儲子視窗引用
                        
                        # 通知主視窗圈速分析視窗已開啟
                        self.main_window.on_lap_analysis_window_opened(analysis_module, "timediff")
                        
                        # 自動載入數據（包含時間軸參數）
                        logger.debug(f"[CREATE_DEBUG] 🚀 自動載入時間差分析數據... (use_time_axis={use_time_axis})")
                        success = analysis_module.load_data(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=driver1,
                            driver2=driver2,
                            lap1=lap1_number,
                            lap2=lap2_number,
                            is_fastest=is_fastest_lap,
                            use_time_axis=use_time_axis
                        )
                        
                        if success:
                            logger.debug(f"[CREATE_DEBUG] ✅ 數據載入成功！")
                        else:
                            logger.debug(f"[CREATE_DEBUG] ⚠️ 數據載入失敗")
                        
                        logger.debug(f"[CREATE_DEBUG] ========== 新版模組創建完成 ==========")
                        return
                    else:
                        logger.error(f"[ERROR] 時間差分析模組初始化失敗，回退到舊版模式")
                        
                except Exception as e:
                    logger.error(f"[ERROR] ❌ 時間差分析模組創建失敗: {e}")
                    logger.error(f"[ERROR] 錯誤類型: {type(e).__name__}")
                    logger.error(f"[ERROR] 回退到舊版模式")
                    import traceback
                    logger.error(f"[ERROR] 詳細錯誤追踪:")
                    traceback.print_exc()
                
                logger.debug(f"[CREATE_DEBUG] ⚠️ 回退到舊版時間差分析模式")
                
                # 回退：創建佔位組件
                chart_widget = self.main_window.create_placeholder_telemetry_widget('timediff')
                
            elif chart_type == 'brake':
                # 使用新的煞車分析模組
                logger.debug(f"[CREATE_DEBUG] 🎯 檢測到煞車分析請求，嘗試新版模組架構")
                
                try:
                    logger.debug(f"[CREATE_DEBUG] 📦 正在導入煞車分析模組...")
                    from modules.gui.lap_analysis.brake_analysis.brake_analysis_mdi import BrakeAnalysisModule
                    
                    logger.debug(f"[CREATE_DEBUG] 🔧 創建模組實例...")
                    # 創建模組實例
                    analysis_module = BrakeAnalysisModule()
                    
                    # 創建正確的參數提供者
                    parameter_provider = MainWindowParameterProvider(self.main_window)
                    analysis_module.parameter_provider = parameter_provider
                    
                    # 設置當前參數
                    analysis_module.current_year = str(params['year'])
                    analysis_module.current_race = params['race']
                    analysis_module.current_session = params['session']
                    
                    # 設置車手和圈數參數
                    analysis_module.driver1 = driver1 if driver1 else "VER"
                    analysis_module.driver2 = driver2  # 允許為 None
                    analysis_module.lap1 = lap1_number if lap1_number else 1
                    analysis_module.lap2 = lap2_number  # 允許為 None
                    
                    logger.debug(f"[CREATE_DEBUG] ⚙️ 模組參數已設置: {params['year']} {params['race']} {params['session']}")
                    logger.debug(f"[CREATE_DEBUG] 🏁 車手和圈數已設置: {analysis_module.driver1} vs {analysis_module.driver2 if analysis_module.driver2 else 'None'}, 第{analysis_module.lap1}圈 vs 第{analysis_module.lap2 if analysis_module.lap2 else 'None'}圈")
                    
                    # 初始化模組
                    logger.debug(f"[CREATE_DEBUG] 🚀 初始化煞車分析模組...")
                    if analysis_module.initialize_module():
                        logger.debug(f"[CREATE_DEBUG] ✅ 模組初始化成功！")
                        
                        # 獲取模組標題，傳遞當前參數
                        window_title = analysis_module.get_window_title(
                            year=str(params['year']), 
                            race=params['race'], 
                            session=params['session']
                        )
                        logger.debug(f"[CREATE_DEBUG] 📋 視窗標題: {window_title}")
                        
                        # 創建帶有模組的視窗
                        logger.debug(f"[CREATE_DEBUG] 🪟 創建新版模組視窗...")
                        sub_window = PopoutSubWindow(window_title, current_mdi_area, analysis_module)
                        sub_window.setWidget(analysis_module.get_widget())
                        
                        # 設置模組的父視窗引用
                        analysis_module.set_parent_window(sub_window)
                        
                        # 連接視窗關閉信號
                        # 🔴 使用 partial 避免 lambda 閉包洩漏

                        sub_window.window_closed.connect(

                            partial(self.main_window.on_lap_analysis_window_closed, analysis_module)

                        )
                        
                        # 設置視窗大小
                        width, height = analysis_module.get_default_size()
                        sub_window.resize(width, height)
                        
                        # 添加到MDI區域
                        current_mdi_area.addSubWindow(sub_window)
                        sub_window.show()
                        
                        logger.debug(f"[OK] [NEW_MODULE] 煞車分析模組視窗已創建: {window_title}")
                        
                        # 建立分析模組和子視窗的對應關係
                        analysis_module._sub_window = sub_window  # 存儲子視窗引用
                        
                        # 通知主視窗圈速分析視窗已開啟（傳遞分析模組而不是子視窗）
                        self.main_window.on_lap_analysis_window_opened(analysis_module, "brake")
                        
                        # 🔧 修復：自動載入數據（包含最速圈參數和時間軸參數）
                        logger.debug(f"[CREATE_DEBUG] 🚀 自動載入煞車分析數據... (use_time_axis={use_time_axis})")
                        success = analysis_module.load_data(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=driver1,
                            driver2=driver2,
                            lap1=lap1_number,
                            lap2=lap2_number,
                            is_fastest=is_fastest_lap,
                            use_time_axis=use_time_axis
                        )
                        
                        if success:
                            logger.debug(f"[CREATE_DEBUG] ✅ 數據載入成功！")
                        else:
                            logger.debug(f"[CREATE_DEBUG] ⚠️ 數據載入失敗")
                        
                        logger.debug(f"[CREATE_DEBUG] ========== 新版煞車模組創建完成 ==========")
                        return
                    else:
                        logger.error(f"[ERROR] 煞車分析模組初始化失敗，回退到舊版模式")
                        
                except Exception as e:
                    logger.error(f"[ERROR] 煞車分析模組創建失敗: {e}，回退到舊版模式")
                    import traceback
                    traceback.print_exc()
                
                logger.debug(f"[CREATE_DEBUG] ⚠️ 回退到舊版煞車分析模式")
                # 回退到舊版
                chart_widget = TelemetryChartWidget(chart_type)
                
            elif chart_type in ['speed', 'steering']:
                # 這些是現有的TelemetryChartWidget支援的類型
                chart_widget = TelemetryChartWidget(chart_type)
            else:
                # 對於其他類型，創建佔位符Widget
                chart_widget = self.main_window.create_placeholder_telemetry_widget(chart_type)
            
            # 獲取圖表類型的中文名稱和圖示
            chart_info = self.main_window.get_chart_info(chart_type)
            
            # 構建視窗標題，包含車手和圈數資訊
            driver_info = ""
            if driver1:
                driver_info = f" - {driver1}"
                if driver2:
                    driver_info += f" vs {driver2}"
            
            # 添加圈數資訊
            lap_info = ""
            if is_fastest_lap:
                lap_info = " (最速圈)"
            else:
                if driver2:
                    lap_info = f" (車手1第{lap1_number}圈, 車手2第{lap2_number}圈)"
                else:
                    lap_info = f" (第{lap1_number}圈)"
            
            window_title = f"{chart_info['icon']} {chart_info['name']}{driver_info}{lap_info} - {params['year']} {params['race']} {params['session']}"
            
            sub_window = PopoutSubWindow(window_title, current_mdi_area)
            sub_window.setWidget(chart_widget)
            
            # 檢查是否為圈速分析相關視窗，如果是則連接關閉信號
            lap_analysis_types = ['speed', 'brake', 'throttle', 'steering', 'gear', 'rpm']
            if chart_type in lap_analysis_types:
                # 🔴 使用 partial 避免 lambda 閉包洩漏

                sub_window.window_closed.connect(

                    partial(self.main_window.on_lap_analysis_window_closed, chart_widget)

                )
            
            # 設置視窗大小 - 速度分析需要更大的視窗
            if chart_type == 'speed_analysis':
                sub_window.resize(900, 600)  # 速度分析使用更大尺寸
            else:
                sub_window.resize(600, 400)
            
            # 添加到MDI區域
            current_mdi_area.addSubWindow(sub_window)
            sub_window.show()
            
            logger.debug(f"[OK] 已創建遙測視窗: {window_title}")
            
            # 檢查是否為圈速分析相關視窗，如果是則通知主視窗
            # 包含所有圈速分析子模組類型
            lap_analysis_types = [
                'speed_analysis',  # 速度分析模組
                'speed',           # 傳統速度圖表
                'brake',           # 煞車分析
                'throttle',        # 油門分析
                'steering',        # 轉向分析
                'gear',            # 檔位分析
                'rpm',             # RPM分析模組
                'acceleration',    # 加速度分析
                'speed_diff',      # 速度差分析
                'distancediff'     # 累積距離差分析
            ]
            if chart_type in lap_analysis_types:
                logger.debug(f"[LAP_CONTROL] [DEBUG]   🎯 檢測到圈速分析類型: {chart_type} - 觸發工具欄控件")
                self.main_window.on_lap_analysis_window_opened(chart_widget, chart_type)
            
        except Exception as e:
            logger.error(f"[ERROR] 創建遙測視窗失敗 ({chart_type}): {e}")
