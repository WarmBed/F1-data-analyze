#!/usr/bin/env python3
"""
GUI 國際化模組 - GUI Internationalization Module
專門處理 GUI 介面的語言切換，不影響 CLI print 輸出
Dedicated to GUI interface language switching, does not affect CLI print output
"""

import os
import json
from core.logger import get_logger

logger = get_logger(__name__)
import sys

def get_config_path():
    """
    獲取配置檔案路徑（支援 EXE 模式）
    Returns the configuration file path (supports EXE mode)
    """
    # 檢測是否為 PyInstaller 打包的 EXE
    if getattr(sys, 'frozen', False):
        # EXE 模式：使用用戶目錄下的配置檔案
        app_data_dir = os.path.join(os.path.expanduser('~'), '.f1telemetrystation')
        os.makedirs(app_data_dir, exist_ok=True)
        return os.path.join(app_data_dir, 'gui_language_config.json')
    else:
        # 開發模式：使用專案目錄
        return os.path.join(os.path.dirname(__file__), 'gui_language_config.json')

class GuiTranslator:
    """GUI 專用翻譯器 - 僅處理介面元素"""
    
    def __init__(self, language='en'):
        """
        初始化翻譯器
        Args:
            language: 'zh' (中文), 'en' (英文), 或 'ja' (日文)
        """
        # 先嘗試從設定檔載入語言
        saved_language = self._load_saved_language()
        self.language = saved_language if saved_language else language
        self._translations = self._load_translations()
        self._config_file = get_config_path()
    
    def _load_saved_language(self):
        """從設定檔載入保存的語言設定"""
        try:
            config_file = get_config_path()
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    loaded_lang = config.get('language', 'en')
                    logger.debug(f"[GUI_I18N] 已載入語言設定: {loaded_lang} (檔案: {config_file})")
                    return loaded_lang
        except Exception as e:
            logger.debug(f"[GUI_I18N] 載入語言設定失敗: {e}")
        return None
    
    def _save_language(self, language):
        """保存語言設定到檔案"""
        try:
            config = {'language': language}
            config_file = get_config_path()
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            logger.debug(f"[GUI_I18N] 語言設定已保存: {language} (檔案: {config_file})")
            return True
        except Exception as e:
            logger.debug(f"[GUI_I18N] 保存語言設定失敗: {e}")
            return False
    
    def _load_translations(self):
        """載入翻譯字典"""
        return {
            # 主視窗元素
            'main_window': {'zh': 'F1 TelemetryStation Pro', 'en': 'F1 TelemetryStation Pro', 'ja': 'F1 TelemetryStation Pro'},
            'home_page': {'zh': '主頁', 'en': 'Home', 'ja': 'ホーム'},
            'tab_page': {'zh': '分頁{number}', 'en': 'Tab {number}', 'ja': 'タブ {number}'},
            'help_menu': {'zh': '說明', 'en': 'Help', 'ja': 'ヘルプ'},
            'open_help_center': {'zh': '使用說明...', 'en': 'User Guide...', 'ja': '使用ガイド...'},
            'about_action': {'zh': '關於 F1T', 'en': 'About F1T', 'ja': 'F1T について'},
            
            # F1TV Account 相關
            'f1tv_account_menu': {'zh': 'F1TV 帳號', 'en': 'F1TV Account', 'ja': 'F1TVアカウント'},
            'f1tv_login_action': {'zh': '登入 / 管理帳號', 'en': 'Login / Manage Account', 'ja': 'ログイン / アカウント管理'},
            'f1tv_logout_action': {'zh': '登出', 'en': 'Logout', 'ja': 'ログアウト'},
            'f1tv_login_title': {'zh': 'F1TV 帳號', 'en': 'F1TV Account', 'ja': 'F1TVアカウント'},
            'f1tv_info': {'zh': '資訊', 'en': 'Information', 'ja': '情報'},
            'f1tv_privacy_notice_title': {'zh': '隱私通知', 'en': 'Privacy Notice', 'ja': 'プライバシー通知'},
            'f1tv_privacy_notice_text': {
                'zh': '此 F1 TV 帳號不會傳送至任何地方，僅使用於 Realtime。\n\n您的帳號資訊僅用於存取即時 Live Timing 數據。',
                'en': 'Your F1 TV account credentials will NOT be transmitted anywhere.\n\nThis authentication is only used for accessing Realtime Live Timing data.',
                'ja': 'F1 TVアカウントの認証情報は一切送信されません。\n\nこの認証はリアルタイムライブタイミングデータへのアクセスにのみ使用されます。'
            },
            'f1tv_realtime_info': {
                'zh': '即時 Live Timing 需要有效的 F1TV Pro 訂閱。\n點擊「登入」以驗證您的 F1TV 帳號。',
                'en': 'Realtime Live Timing requires an active F1TV Pro subscription.\nClick "Login" to authenticate with your F1TV account.',
                'ja': 'リアルタイムライブタイミングには有効なF1TV Proサブスクリプションが必要です。\n「ログイン」をクリックしてF1TVアカウントを認証してください。'
            },
            'f1tv_status': {'zh': '狀態', 'en': 'Status', 'ja': 'ステータス'},
            'f1tv_login': {'zh': '登入', 'en': 'Login', 'ja': 'ログイン'},
            'f1tv_logout': {'zh': '登出', 'en': 'Logout', 'ja': 'ログアウト'},
            'f1tv_not_logged_in': {'zh': '未登入', 'en': 'Not Logged In', 'ja': '未ログイン'},
            'f1tv_logged_in': {'zh': '已登入', 'en': 'Logged In', 'ja': 'ログイン済み'},
            'f1tv_expired': {'zh': '已過期', 'en': 'Expired', 'ja': '期限切れ'},
            'f1tv_logging_in': {'zh': '登入中...', 'en': 'Logging in...', 'ja': 'ログイン中...'},
            'f1tv_login_success': {'zh': '成功登入 F1TV!', 'en': 'Successfully logged in to F1TV!', 'ja': 'F1TVにログインしました!'},
            'f1tv_login_failed': {'zh': '登入失敗: {error}', 'en': 'Login failed: {error}', 'ja': 'ログイン失敗: {error}'},
            'f1tv_logout_confirm': {'zh': '確定要登出 F1TV 嗎?', 'en': 'Are you sure you want to logout from F1TV?', 'ja': 'F1TVからログアウトしますか?'},
            'f1tv_click_to_login': {'zh': '點擊登入 F1TV 帳號', 'en': 'Click to login to F1TV account', 'ja': 'クリックしてF1TVアカウントにログイン'},
            'f1tv_token_expired': {'zh': 'Token 已過期，點擊重新登入', 'en': 'Token expired. Click to re-login.', 'ja': 'トークンの有効期限が切れました。再ログインしてください。'},
            'realtime_requires_f1tv': {'zh': '即時模式需要登入 F1TV 帳號', 'en': 'Realtime mode requires F1TV account login', 'ja': 'リアルタイムモードにはF1TVアカウントログインが必要です'},
            'realtime_available': {'zh': '即時模式可用 - 已連接 F1TV', 'en': 'Realtime mode available - Connected to F1TV', 'ja': 'リアルタイムモード利用可能 - F1TV接続済み'},
            'f1tv_subscription': {'zh': '訂閱方案', 'en': 'Subscription', 'ja': 'サブスクリプション'},
            'f1tv_expires': {'zh': '到期時間', 'en': 'Expires', 'ja': '有効期限'},
            'f1tv_how_to_subscribe': {'zh': '如何訂閱 F1TV?', 'en': 'How to subscribe to F1TV?', 'ja': 'F1TVの購読方法は?'},
            'close': {'zh': '關閉', 'en': 'Close', 'ja': '閉じる'},
            'confirm': {'zh': '確認', 'en': 'Confirm', 'ja': '確認'},
            'success': {'zh': '成功', 'en': 'Success', 'ja': '成功'},
            'error': {'zh': '錯誤', 'en': 'Error', 'ja': 'エラー'},
            
            'about_message': {
                'zh': (
                    "F1 TelemetryStation Pro\n\n"
                    "一個專業的 Formula 1 遙測分析工作站\n"
                    "提供全面的賽事數據分析能力。\n\n"
                    "A professional Formula 1 telemetry analysis workstation\n"
                    "providing comprehensive race data analysis capabilities.\n\n"
                    "GitHub:\n"
                    "https://github.com/WarmBed/F1-TelemetryStation-Pro/tree/main"
                ),
                'en': (
                    "F1 TelemetryStation Pro\n\n"
                    "A professional Formula 1 telemetry analysis workstation\n"
                    "providing comprehensive race data analysis capabilities.\n\n"
                    "GitHub:\n"
                    "https://github.com/WarmBed/F1-TelemetryStation-Pro/tree/main"
                ),
                'ja': (
                    "F1 TelemetryStation Pro\n\n"
                    "プロフェッショナルな Formula 1 テレメトリー分析ワークステーション\n"
                    "包括的なレースデータ分析機能を提供します。\n\n"
                    "A professional Formula 1 telemetry analysis workstation\n"
                    "providing comprehensive race data analysis capabilities.\n\n"
                    "GitHub:\n"
                    "https://github.com/WarmBed/F1-TelemetryStation-Pro/tree/main"
                ),
            },
            
            # 遙測分析對話框
            'telemetry_options_title': {'zh': '遙測分析選項', 'en': 'Telemetry Analysis Options', 'ja': 'テレメトリー分析オプション'},
            'detailed_lap_options_title': {'zh': '詳細圈速分析選項', 'en': 'Detailed Lap Analysis Options', 'ja': '詳細ラップ分析オプション'},
            'select_analysis_type': {'zh': '請選擇分析類型', 'en': 'Please select analysis type', 'ja': '分析タイプを選択してください'},
            'analysis_type': {'zh': '分析類型', 'en': 'Analysis Type', 'ja': '分析タイプ'},
            'select_telemetry_charts': {'zh': '請選擇要顯示的遙測圖表', 'en': 'Please select telemetry charts to display', 'ja': '表示するテレメトリーチャートを選択してください'},
            'driver_lap_selection': {'zh': '車手與圈數選擇', 'en': 'Driver & Lap Selection', 'ja': 'ドライバーとラップの選択'},
            'driver1_required': {'zh': '車手1 (必選):', 'en': 'Driver 1 (Required):', 'ja': 'ドライバー1（必須）:'},
            'driver2_optional': {'zh': '車手2 (選用):', 'en': 'Driver 2 (Optional):', 'ja': 'ドライバー2（オプション）:'},
            'lap_number': {'zh': '圈數:', 'en': 'Lap:', 'ja': 'ラップ:'},
            'telemetry_options': {'zh': '遙測選項', 'en': 'Telemetry Options', 'ja': 'テレメトリーオプション'},
            'detail_lap_analysis': {'zh': '詳細圈速分析', 'en': 'Detailed Lap Analysis', 'ja': '詳細ラップ分析'},
            'lap_time_box_plot': {'zh': '圈速箱型圖', 'en': 'Lap Time Box Plot', 'ja': 'ラップタイム箱ひげ図'},
            'detail_analysis_desc': {
                'zh': '詳細圈速分析：逐圈顯示數據表格',
                'en': 'Detailed Lap Analysis: Shows lap-by-lap data table',
                'ja': '詳細ラップ分析：周回ごとのデータテーブルを表示'
            },
            'box_plot_desc': {
                'zh': '圈速箱型圖：可視化所有車手的圈速分佈',
                'en': 'Lap Time Box Plot: Visualizes lap time distribution for all drivers',
                'ja': 'ラップタイム箱ひげ図：全ドライバーのラップタイム分布を可視化'
            },
            
            # 按鈕
            'select_all': {'zh': '全選', 'en': 'Select All', 'ja': 'すべて選択'},
            'select_none': {'zh': '全不選', 'en': 'Select None', 'ja': 'すべて解除'},
            'restore_default': {'zh': '恢復預設', 'en': 'Restore Default', 'ja': 'デフォルトに戻す'},
            'ok': {'zh': '確定', 'en': 'OK', 'ja': 'OK'},
            'cancel': {'zh': '取消', 'en': 'Cancel', 'ja': 'キャンセル'},
            'reanalyze': {'zh': 'R', 'en': 'R', 'ja': 'R'},
            
            # 控制項標籤
            'year': {'zh': '年:', 'en': 'Year:', 'ja': '年:'},
            'race': {'zh': '賽事:', 'en': 'Race:', 'ja': 'レース:'},
            'session': {'zh': '賽段:', 'en': 'Session:', 'ja': 'セッション:'},
            
            # Live Timing 控制按鈕
            'Mode': {'zh': '模式', 'en': 'Mode', 'ja': 'モード'},
            'Year': {'zh': '年份', 'en': 'Year', 'ja': '年'},
            'Race': {'zh': '賽事', 'en': 'Race', 'ja': 'レース'},
            'Session': {'zh': '賽段', 'en': 'Session', 'ja': 'セッション'},
            'Speed': {'zh': '速度', 'en': 'Speed', 'ja': '速度'},
            'Realtime Live Timing': {'zh': '即時直播', 'en': 'Realtime', 'ja': 'リアルタイム'},
            'Historical Playback': {'zh': '歷史回放', 'en': 'Historical', 'ja': '履歴再生'},
            'Connect Live Timing': {'zh': '連接', 'en': 'Connect', 'ja': '接続'},
            'Disconnect': {'zh': '斷開', 'en': 'Disconnect', 'ja': '切断'},
            'Disconnected': {'zh': '未連接', 'en': 'Disconnected', 'ja': '未接続'},
            'Connecting...': {'zh': '連接中...', 'en': 'Connecting...', 'ja': '接続中...'},
            'Load Race': {'zh': '載入', 'en': 'Load', 'ja': '読込'},
            'Select race': {'zh': '選擇賽事', 'en': 'Select race', 'ja': 'レースを選択'},
            'Please select a race': {'zh': '請選擇賽事', 'en': 'Please select a race', 'ja': 'レースを選択してください'},
            'Loaded': {'zh': '已載入', 'en': 'Loaded', 'ja': '読込完了'},
            'Load Failed': {'zh': '載入失敗', 'en': 'Failed', 'ja': '読込失敗'},
            'Stop': {'zh': '停止', 'en': 'Stop', 'ja': '停止'},
            'Play': {'zh': '播放', 'en': 'Play', 'ja': '再生'},
            'Pause': {'zh': '暫停', 'en': 'Pause', 'ja': '一時停止'},
            'Rewind 30s': {'zh': '倒退 30 秒', 'en': 'Rewind 30s', 'ja': '30秒巻戻し'},
            'Forward 30s': {'zh': '快進 30 秒', 'en': 'Forward 30s', 'ja': '30秒早送り'},
            'websockets not installed': {'zh': '未安裝 websockets', 'en': 'websockets not installed', 'ja': 'websocketsがインストールされていません'},

            'year_label': {'zh': '年份:', 'en': 'Year:', 'ja': '年:'},
            'race_label': {'zh': '賽事:', 'en': 'Race:', 'ja': 'レース:'},
            'session_label': {'zh': '賽段:', 'en': 'Session:', 'ja': 'セッション:'},
            'year_tooltip': {'zh': '手動設定年份', 'en': 'Set year manually', 'ja': 'Set year manually'},
            'race_tooltip': {'zh': '手動設定賽事', 'en': 'Set race manually', 'ja': 'Set race manually'},
            'session_tooltip': {'zh': '手動設定賽段', 'en': 'Set session manually', 'ja': 'Set session manually'},
            'driver1_label': {'zh': '車手1:', 'en': 'Driver 1:', 'ja': 'ドライバー1:'},
            'driver2_label': {'zh': '車手2:', 'en': 'Driver 2:', 'ja': 'ドライバー2:'},
            'lap_label': {'zh': '圈數:', 'en': 'Lap:', 'ja': 'ラップ:'},
            'please_select': {'zh': '請選擇', 'en': 'Please Select', 'ja': '選択してください'},
            'none_option': {'zh': '無', 'en': 'None', 'ja': 'なし'},
            'fastest_lap_option': {'zh': '最速圈', 'en': 'Fastest Lap', 'ja': '最速ラップ'},
            'versus': {'zh': '對', 'en': 'vs', 'ja': '対'},
            'tile_windows_action': {'zh': '平鋪視窗', 'en': 'Tile Windows', 'ja': 'ウィンドウを並べて表示'},
            'cascade_windows_action': {'zh': '層疊視窗', 'en': 'Cascade Windows', 'ja': 'ウィンドウを重ねて表示'},
            'sync_checkbox_main': {'zh': '[LINK] 接收主程式同步 (年份/賽事/賽段)', 'en': '[LINK] Receive Main Window Sync (Year/Race/Session)', 'ja': '[LINK] Receive Main Window Sync (Year/Race/Session)'},
            'sync_checkbox_tooltip_main': {'zh': '勾選時接收主程式參數同步，下方分析參數將變為不可編輯', 'en': 'When checked, receive parameters from main window and lock analysis controls', 'ja': 'When checked, receive parameters from main window and lock analysis controls'},
            
            # Window Settings 對話框
            'window_settings_title': {'zh': 'Window Settings', 'en': 'Window Settings', 'ja': 'Window Settings'},
            'window_settings_dialog_title': {'zh': '[TOOL] 視窗分析設定', 'en': '[TOOL] Window Analysis Settings', 'ja': '[TOOL] ウィンドウ分析設定'},
            'window_sync_control_group': {'zh': '視窗同步控制', 'en': 'Window Sync Control', 'ja': 'ウィンドウ同期制御'},
            'analysis_params_group': {'zh': '分析參數', 'en': 'Analysis Parameters', 'ja': '分析パラメータ'},
            'year_label_window_settings': {'zh': '年份:', 'en': 'Year:', 'ja': '年:'},
            'race_label_window_settings': {'zh': '賽事:', 'en': 'Race:', 'ja': 'レース:'},
            'session_label_window_settings': {'zh': '賽段:', 'en': 'Session:', 'ja': 'セッション:'},
            'params_locked_tooltip': {'zh': '已啟用同步接收，參數由主程式控制', 'en': 'Sync enabled, parameters controlled by main window', 'ja': '同期有効、パラメータはメインウィンドウで制御'},
            
            # 車手與圈數同步控制
            'driver_lap_sync_control': {'zh': '車手與圈數同步控制', 'en': 'Driver and Lap Sync Control', 'ja': 'ドライバーとラップの同期制御'},
            'sync_driver_lap_checkbox': {'zh': '[LINK] 與主視窗同步車手與圈數', 'en': '[LINK] Sync Driver and Lap with Main Window', 'ja': '[LINK] メインウィンドウとドライバーとラップを同期'},
            'sync_driver_lap_tooltip': {'zh': '勾選時車手與圈數由主視窗控制，取消勾選可手動設定', 'en': 'When checked, driver and lap are controlled by main window. Uncheck to set manually', 'ja': 'チェックすると、ドライバーとラップはメインウィンドウで制御されます。手動設定するにはチェックを外してください'},
            'driver1_section': {'zh': '車手 1:', 'en': 'Driver 1:', 'ja': 'ドライバー 1:'},
            'driver2_section': {'zh': '車手 2:', 'en': 'Driver 2:', 'ja': 'ドライバー 2:'},
            'year_label': {'zh': '年份:', 'en': 'Year:', 'ja': '年:'},
            'race_label': {'zh': '賽事:', 'en': 'Race:', 'ja': 'レース:'},
            'session_label': {'zh': '賽段:', 'en': 'Session:', 'ja': 'セッション:'},
            'driver_label': {'zh': '車手:', 'en': 'Driver:', 'ja': 'ドライバー:'},
            'lap_label': {'zh': '圈數:', 'en': 'Lap:', 'ja': 'ラップ:'},
            'fastest_lap_label': {'zh': '最速圈', 'en': 'Fastest Lap', 'ja': '最速ラップ'},
            'use_time_axis_checkbox': {'zh': '使用時間軸 (Use Time Axis)', 'en': 'Use Time Axis', 'ja': '時間軸を使用'},
            'use_time_axis_tooltip': {'zh': '使用時間（秒）作為 X 軸，而非距離（米）', 'en': 'Use time (seconds) as X-axis instead of distance (meters)', 'ja': '距離（メートル）ではなく時間（秒）をX軸として使用'},
            
            # 資訊標籤
            'driver_1_info': {'zh': '車手 1:', 'en': 'Driver 1:', 'ja': 'ドライバー 1:'},
            'driver_2_info': {'zh': '車手 2:', 'en': 'Driver 2:', 'ja': 'ドライバー 2:'},
            'race_info': {'zh': '賽事:', 'en': 'Race:', 'ja': 'レース:'},
            'driver_info': {'zh': '車手:', 'en': 'Driver:', 'ja': 'ドライバー:'},
            'lap_info': {'zh': '圈', 'en': 'Lap', 'ja': '周'},

            
            # 進度對話框
            'starting_cli_analysis': {'zh': '正在啟動 CLI 分析...', 'en': 'Starting CLI analysis...', 'ja': 'Starting CLI analysis...'},
            'downloading_data': {'zh': '正在下載數據...', 'en': 'Downloading data...', 'ja': 'Downloading data...'},
            
            # 遙測圖表選項
            'telemetry_speed': {'zh': '速度 (Speed)', 'en': 'Speed (km/h)', 'ja': 'Speed (km/h)'},
            'telemetry_throttle': {'zh': '油門 (Throttle)', 'en': 'Throttle (%)', 'ja': 'Throttle (%)'},
            'telemetry_brake': {'zh': '煞車 (Brake)', 'en': 'Brake (%)', 'ja': 'Brake (%)'},
            'telemetry_gear': {'zh': '檔位 (Gear)', 'en': 'Gear', 'ja': 'ギア'},
            'telemetry_drs': {'zh': 'DRS', 'en': 'DRS', 'ja': 'DRS'},
            'telemetry_rpm': {'zh': '轉速 (RPM)', 'en': 'RPM', 'ja': 'RPM'},
            'telemetry_steering': {'zh': '方向盤轉角 (Steering)', 'en': 'Steering Angle', 'ja': 'Steering Angle'},
            
            # brake 分析專用
            'brake_chart_title': {'zh': ' 煞車分析圖表', 'en': ' Brake Analysis Chart', 'ja': ' ブレーキ分析チャート'},
            'brake_chart_loading': {'zh': '煞車圖表組件正在載入中...', 'en': 'Brake chart component loading...', 'ja': 'ブレーキチャートコンポーネント読み込み中...'},
            'brake_value': {'zh': '煞車', 'en': 'brake', 'ja': 'ブレーキ'},
            
            # throttle 分析專用
            'throttle_chart_title': {'zh': ' 油門分析圖表', 'en': ' Throttle Analysis Chart', 'ja': ' スロットル分析チャート'},
            'throttle_chart_loading': {'zh': '油門圖表組件正在載入中...', 'en': 'Throttle chart component loading...', 'ja': 'スロットルチャートコンポーネント読み込み中...'},
            'throttle_value': {'zh': '油門', 'en': 'throttle', 'ja': 'スロットル'},
            
            # RPM 分析專用
            'rpm_chart_title': {'zh': ' RPM分析圖表', 'en': ' RPM Analysis Chart', 'ja': ' RPM分析チャート'},
            'rpm_chart_loading': {'zh': 'RPM圖表組件正在載入中...', 'en': 'RPM chart component loading...', 'ja': 'RPMチャートコンポーネント読み込み中...'},
            'rpm_value': {'zh': 'RPM', 'en': 'RPM', 'ja': 'RPM'},
            
            # gear 分析專用
            'gear_chart_title': {'zh': ' 檔位分析圖表', 'en': ' Gear Analysis Chart', 'ja': ' ギア分析チャート'},
            'gear_chart_loading': {'zh': '檔位圖表組件正在載入中...', 'en': 'Gear chart component loading...', 'ja': 'ギアチャートコンポーネント読み込み中...'},
            'gear_value': {'zh': '檔位', 'en': 'gear', 'ja': 'ギア'},
            
            # acceleration 分析專用
            'acceleration_chart_title': {'zh': ' 加速度分析圖表', 'en': ' Acceleration Analysis Chart', 'ja': ' アクセラレーション分析チャート'},
            'acceleration_chart_loading': {'zh': '加速度圖表組件正在載入中...', 'en': 'Acceleration chart component loading...', 'ja': 'アクセラレーションチャートコンポーネント読み込み中...'},
            'acceleration_value': {'zh': '加速度', 'en': 'acceleration', 'ja': 'アクセラレーション'},
            'telemetry_acceleration': {'zh': '加速度 (m/s²)', 'en': 'Acceleration (m/s²)', 'ja': 'アクセラレーション (m/s²)'},
            
            # speeddiff 分析專用
            'speeddiff_chart_title': {'zh': ' 速度差分析圖表', 'en': ' Speed Diff Analysis Chart', 'ja': ' スピード差分析チャート'},
            'speeddiff_chart_loading': {'zh': '速度差圖表組件正在載入中...', 'en': 'Speed diff chart component loading...', 'ja': 'スピード差チャートコンポーネント読み込み中...'},
            'speeddiff_value': {'zh': '速度差', 'en': 'speed diff', 'ja': 'スピード差'},
            'loading_speeddiff_data': {'zh': '開始載入速度差數據...', 'en': 'Loading speed diff data...', 'ja': 'スピード差データを読み込み中...'},
            
            # distancediff 分析專用
            'distancediff_chart_title': {'zh': ' 距離差分析圖表', 'en': ' Distance Diff Analysis Chart', 'ja': ' ディスタンス差分析チャート'},
            'distancediff_chart_loading': {'zh': '距離差圖表組件正在載入中...', 'en': 'Distance diff chart component loading...', 'ja': 'ディスタンス差チャートコンポーネント読み込み中...'},
            'distancediff_value': {'zh': '距離差', 'en': 'distance diff', 'ja': 'ディスタンス差'},
            'loading_distancediff_data': {'zh': '開始載入距離差數據...', 'en': 'Loading distance diff data...', 'ja': 'ディスタンス差データを読み込み中...'},
            'loading_acceleration_data': {'zh': '開始載入加速度數據...', 'en': 'Loading acceleration data...', 'ja': 'アクセラレーションデータを読み込み中...'},
            
            # === 圈數標籤格式化 (Lap Label Formatting) ===
            # 用於單車手不同圈數比較時的圖例標籤
            'lap_label_format': {'zh': '{driver} - 第{lap}圈', 'en': '{driver} - Lap {lap}', 'ja': '{driver} - {lap}周目'},
            
            #  單車手雙圈模式 - 僅顯示圈數（不含車手代碼）
            'lap_only_format': {'zh': '第{lap}圈', 'en': 'Lap {lap}', 'ja': '{lap}周目'},
            
            #  SpeedDiff/DistanceDiff 專用 - vs 格式（單行標籤）
            'lap_vs_lap_format': {'zh': '{driver} 第{lap1}圈 vs 第{lap2}圈', 'en': '{driver} Lap {lap1} vs Lap {lap2}', 'ja': '{driver} {lap1}周目 vs {lap2}周目'},
            
            #  Tooltip 標籤
            'speed_diff_label': {'zh': '速度差', 'en': 'Speed Diff', 'ja': '速度差'},
            'distance_diff_label': {'zh': '距離差', 'en': 'Distance Diff', 'ja': '距離差'},
            
            'lap_vs_format': {'zh': '{driver} 第{lap1}圈 vs 第{lap2}圈', 'en': '{driver} Lap {lap1} vs Lap {lap2}', 'ja': '{driver} {lap1}周目 vs {lap2}周目'},
            'leading': {'zh': '領先', 'en': 'Leading', 'ja': 'リード'},
            'zero_line': {'zh': '零點線', 'en': 'Zero Line', 'ja': 'ゼロライン'},
            
            # 通用狀態
            'cleared': {'zh': '已清除', 'en': 'Cleared', 'ja': 'クリア済み'},
            
            # === 新增：QMessageBox 對話框翻譯鍵 ===
            # 關閉確認對話框
            'confirm_exit': {'zh': '確認退出', 'en': 'Confirm Exit', 'ja': '終了確認'},
            'confirm_exit_message': {
                'zh': '確定要退出 F1 TelemetryStation Pro 嗎？\n\n所有正在執行的分析將被停止。', 
                'en': 'Are you sure you want to exit F1 TelemetryStation Pro?\n\nAll running analyses will be stopped.', 
                'ja': 'F1 TelemetryStation Pro を終了してもよろしいですか？\n\n実行中のすべての分析が停止されます。'
            },
            
            # 按鈕選項
            'yes': {'zh': '是', 'en': 'Yes', 'ja': 'はい'},
            'no': {'zh': '否', 'en': 'No', 'ja': 'いいえ'},
            'cancel': {'zh': '取消', 'en': 'Cancel', 'ja': 'キャンセル'},
            
            # === 更新進度對話框翻譯 ===
            'update_progress_title': {'zh': '更新進度', 'en': 'Update Progress', 'ja': '更新進度'},
            'update_progress_preparing': {'zh': '準備序列化更新分析模組...', 'en': 'Preparing to update analysis modules...', 'ja': '分析モジュールの更新を準備中...'},
            'update_progress_updating': {'zh': '正在更新', 'en': 'Updating', 'ja': '更新中'},
            'update_progress_no_windows': {'zh': '沒有需要更新的分析視窗', 'en': 'No analysis windows to update', 'ja': '更新する分析ウィンドウがありません'},
            'update_progress_no_modules': {
                'zh': '找不到符合條件的分析模組\n（已跳過 {0} 個不支援的模組）',
                'en': 'No matching analysis modules found\n({0} unsupported modules skipped)',
                'ja': '条件に一致する分析モジュールが見つかりません\n（{0}個の非対応モジュールをスキップ）'
            },
            'update_progress_no_telemetry': {
                'zh': '沒有需要更新的遙測分析視窗\n（已跳過 {0} 個非遙測模組）',
                'en': 'No telemetry analysis windows to update\n({0} non-telemetry modules skipped)',
                'ja': '更新するテレメトリー分析ウィンドウがありません\n（{0}個の非テレメトリーモジュールをスキップ）'
            },
            'update': {'zh': '更新', 'en': 'Update', 'ja': '更新'},
            'update_race_params_confirm': {
                'zh': '檢測到賽事參數變更：\n年份: {year}\n賽事: {race}\n賽段: {session}\n\n共有 {count} 個遙測分析視窗需要更新。\n是否立即更新所有視窗？',
                'en': 'Race parameters changed:\nYear: {year}\nRace: {race}\nSession: {session}\n\n{count} telemetry analysis windows need update.\nUpdate all windows now?',
                'ja': 'レースパラメータが変更されました：\n年: {year}\nレース: {race}\nセッション: {session}\n\n{count} 個のテレメトリー分析ウィンドウを更新する必要があります。\nすべてのウィンドウを今すぐ更新しますか？'
            },

            # 系統設定
            'system_settings_title': {'zh': '系統設定', 'en': 'System Settings', 'ja': 'システム設定'},
            'boxplot_settings_tab': {'zh': '箱型圖分析', 'en': 'Box Plot Analysis', 'ja': '箱ひげ図分析'},
            'boxplot_settings_group': {'zh': '箱型圖全域設定', 'en': 'Box Plot Global Settings', 'ja': '箱ひげ図グローバル設定'},
            'boxplot_settings_info': {
                'zh': '設定會同步套用至圈速與油門箱型圖模組。',
                'en': 'Settings apply to both lap time and throttle box plot modules.',
                'ja': '設定はラップタイムとスロットルの箱ひげ図モジュールの両方に適用されます。'
            },
            'boxplot_filter_pit': {'zh': '過濾進站圈', 'en': 'Filter pit laps', 'ja': 'ピットラップを除外'},
            'boxplot_filter_outliers': {
                'zh': '過濾統計異常值 (IQR)',
                'en': 'Filter statistical outliers (IQR)',
                'ja': '統計的外れ値 (IQR) を除外'
            },
            'boxplot_filter_yellow_flags': {
                'zh': '過濾黃旗圈',
                'en': 'Filter yellow flag laps',
                'ja': 'イエローフラッグ周回を除外'
            },
            'boxplot_filter_red_flags': {
                'zh': '過濾紅旗圈',
                'en': 'Filter red flag laps',
                'ja': 'レッドフラッグ周回を除外'
            },
            'boxplot_filter_first_laps': {
                'zh': '過濾前兩圈 (Lap 1 & 2)',
                'en': 'Filter first 2 laps (Lap 1 & 2)',
                'ja': '最初の2周を除外 (Lap 1 & 2)'
            },
            'boxplot_outlier_threshold': {'zh': '異常值閾值', 'en': 'Outlier threshold', 'ja': '外れ値の閾値'},
            'boxplot_outlier_threshold_hint': {
                'zh': '設定用於異常值判定的 IQR 倍數',
                'en': 'Interquartile Range multiplier for outlier detection',
                'ja': '外れ値判定用の IQR 乗数を設定'
            },
            'reset_defaults': {'zh': '恢復預設', 'en': 'Reset Defaults', 'ja': 'デフォルトに戻す'},
            
            # Y 軸調整相關
            'adjust_y_axis_range': {'zh': '調整 Y 軸範圍...', 'en': 'Adjust Y Axis Range...', 'ja': 'Y軸範囲を調整...'},
            'reset_y_axis_range': {'zh': '重置 Y 軸為自動', 'en': 'Reset Y Axis to Auto', 'ja': 'Y軸を自動にリセット'},
            'set_y_axis_min': {'zh': '設定 Y 軸最小值', 'en': 'Set Y Axis Minimum', 'ja': 'Y軸最小値を設定'},
            'set_y_axis_max': {'zh': '設定 Y 軸最大值', 'en': 'Set Y Axis Maximum', 'ja': 'Y軸最大値を設定'},
            'enter_min_value': {'zh': '輸入最小值 (秒):', 'en': 'Enter minimum value (seconds):', 'ja': '最小値を入力 (秒):'},
            'enter_max_value': {'zh': '輸入最大值 (秒):', 'en': 'Enter maximum value (seconds):', 'ja': '最大値を入力 (秒):'},
            'invalid_range': {'zh': '無效範圍', 'en': 'Invalid Range', 'ja': '無効な範囲'},
            'max_must_be_greater': {'zh': '最大值必須大於最小值。', 'en': 'Maximum value must be greater than minimum value.', 'ja': '最大値は最小値より大きい必要があります。'},
            
            # 分析錯誤訊息
            'analysis_failed': {'zh': '分析失敗', 'en': 'Analysis Failed', 'ja': '分析失敗'},
            'cli_error': {'zh': 'CLI 分析過程中發生錯誤', 'en': 'Error occurred during CLI analysis', 'ja': 'CLI分析中にエラーが発生しました'},
            
            # 狀態與載入訊息
            'status': {'zh': '狀態', 'en': 'Status', 'ja': 'ステータス'},
            'loading_data': {'zh': '正在載入數據...', 'en': 'Loading data...', 'ja': 'データ読み込み中...'},
            'loading_team_data': {'zh': '正在載入車隊數據...', 'en': 'Loading team data...', 'ja': 'チームデータ読み込み中...'},
            'loading_driver_detailed_records': {'zh': '載入車手詳細記錄中...', 'en': 'Loading driver detailed records...', 'ja': 'ドライバー詳細記録読み込み中...'},
            
            # 對話框類型標題
            'info': {'zh': '提示', 'en': 'Information', 'ja': '情報'},
            'information': {'zh': '資訊', 'en': 'Information', 'ja': '情報'},
            'question': {'zh': '問題', 'en': 'Question', 'ja': '質問'},
            'warning': {'zh': '警告', 'en': 'Warning', 'ja': '警告'},
            'error': {'zh': '錯誤', 'en': 'Error', 'ja': 'エラー'},
            'tip': {'zh': '提示', 'en': 'Tip', 'ja': 'ヒント'},
            
            # API 相關訊息
            'api_check': {'zh': 'API 檢查', 'en': 'API Check', 'ja': 'APIチェック'},
            'api_check_running': {'zh': 'API 健康檢查正在執行中，請稍候。', 'en': 'API health check is already running. Please wait.', 'ja': 'APIヘルスチェックが実行中です。お待ちください。'},
            'api_restored': {'zh': 'API 已恢復', 'en': 'API Restored', 'ja': 'API復元'},
            
            # 使用者提示訊息
            'no_chart_selected': {'zh': '沒有選擇任何圖表，將不會開啟視窗。', 'en': 'No chart selected. Window will not be opened.', 'ja': 'チャートが選択されていません。ウィンドウは開きません。'},
            'select_driver': {'zh': '請選擇至少一位車手。', 'en': 'Please select at least one driver.', 'ja': '少なくとも1人のドライバーを選択してください。'},
            
            # 模組錯誤訊息
            'track_module_unavailable': {'zh': '賽道分析模組不可用', 'en': 'Track analysis module is not available', 'ja': 'トラック分析モジュールは利用できません'},
            'mdi_area_not_found': {'zh': '無法找到當前 MDI 區域', 'en': 'Cannot find current MDI area', 'ja': '現在のMDIエリアが見つかりません'},
            'track_window_error': {'zh': '無法開啟賽道分析視窗', 'en': 'Cannot open track analysis window', 'ja': 'トラック分析ウィンドウを開けません'},
            
            # 分析模組樹狀圖標題
            'analysis_modules': {'zh': '分析模組', 'en': 'Analysis Modules', 'ja': '分析モジュール'},
            
            # 分析模組
            'lap_analysis': {'zh': '圈速分析', 'en': 'Lap Analysis', 'ja': 'ラップ分析'},
            'tire_analysis': {'zh': '輪胎分析', 'en': 'Tire Analysis', 'ja': 'タイヤ分析'},
            'accident_analysis': {'zh': '事故分析', 'en': 'Accident Analysis', 'ja': '事故分析'},
            'temp_analysis': {'zh': '溫度分析', 'en': 'Temperature Analysis', 'ja': '温度分析'},
            'rain_analysis': {'zh': '雨況分析', 'en': 'Rain Analysis', 'ja': '降雨分析'},  # 向後相容
            'historical_track_map': {'zh': '歷年賽道旗幟統計', 'en': 'Historical Track Map', 'ja': '歴年トラック旗統計'},
            'season_start_reaction': {'zh': '年度起跑反應', 'en': 'Season Start Reaction', 'ja': 'シーズンスタート反応'},
            'season_start_reaction_title': {'zh': '0-50 km/h 加速時間分布', 'en': '0-50 km/h Time Distribution', 'ja': '0-50 km/h 加速時間分布'},
            'traffic_timeline': {'zh': '車流時間線', 'en': 'Traffic Timeline', 'ja': 'トラフィックタイムライン'},
            'traffic_timeline.description': {'zh': '顯示每位車手每一圈的車流狀態（乾淨空氣/髒空氣）', 'en': 'Visualizes traffic status (clean air / dirty air) for each lap per driver.', 'ja': '各ドライバーの各ラップのトラフィック状態（クリーンエア/ダーティエア）を表示'},
            'traffic_timeline.loading': {'zh': '載入車流時間線數據...', 'en': 'Loading traffic timeline data...', 'ja': 'トラフィックタイムラインデータを読み込み中...'},
            'traffic_timeline.loaded': {'zh': '數據已從 API 載入', 'en': 'Data loaded from API', 'ja': 'APIからデータを読み込みました'},
            'traffic_timeline.load_failed': {'zh': '無法載入車流時間線數據', 'en': 'Failed to load traffic timeline data', 'ja': 'トラフィックタイムラインデータの読み込みに失敗しました'},
            'traffic_timeline.check_api': {'zh': '請確認 API 伺服器正在運行。', 'en': 'Please check if API server is running.', 'ja': 'APIサーバーが実行中か確認してください。'},
            'traffic_timeline.api_error': {'zh': 'API 請求失敗', 'en': 'API request failed', 'ja': 'APIリクエスト失敗'},
            'traffic_timeline.api_failed': {'zh': 'API 載入失敗', 'en': 'API load failed', 'ja': 'API読み込み失敗'},
            'traffic_timeline.export_dialog_title': {'zh': '儲存車流時間線', 'en': 'Save Traffic Timeline', 'ja': 'トラフィックタイムラインを保存'},
            'traffic_timeline.clean_air': {'zh': '乾淨空氣', 'en': 'Clean Air', 'ja': 'クリーンエア'},
            'traffic_timeline.dirty_air': {'zh': '髒空氣', 'en': 'Dirty Air', 'ja': 'ダーティエア'},
            'traffic_timeline.excluded': {'zh': '已排除', 'en': 'Excluded', 'ja': '除外'},
            'traffic_timeline.no_data': {'zh': '無數據', 'en': 'No Data', 'ja': 'データなし'},
            'traffic_timeline.lap': {'zh': '圈數', 'en': 'Lap', 'ja': 'ラップ'},
            'traffic_timeline.status': {'zh': '狀態', 'en': 'Status', 'ja': 'ステータス'},
            'traffic_timeline.title': {'zh': '車流時間線分析', 'en': 'Traffic Timeline Analysis', 'ja': 'トラフィックタイムライン分析'},
            'laptime_boxplot': {'zh': '圈速箱型圖', 'en': 'Lap Time Box Plot', 'ja': 'ラップタイムボックスプロット'},
            'throttle_box_plot': {'zh': '油門箱型圖', 'en': 'Throttle Box Plot', 'ja': 'スロットル箱ひげ図'},
            'throttle_box_plot.export_dialog_title': {
                'zh': '儲存油門箱型圖',
                'en': 'Save Throttle Box Plot',
                'ja': 'スロットル箱ひげ図を保存'
            },
            'throttle_box_plot.export_success_title': {
                'zh': '匯出成功',
                'en': 'Export Successful',
                'ja': 'エクスポート成功'
            },
            'throttle_box_plot.export_success_body': {
                'zh': '圖表已成功匯出。',
                'en': 'Chart exported successfully.',
                'ja': 'チャートが正常にエクスポートされました。'
            },
            'throttle_box_plot.export_failed_title': {
                'zh': '匯出失敗',
                'en': 'Export Failed',
                'ja': 'エクスポート失敗'
            },
            'throttle_box_plot.export_failed_body': {
                'zh': '無法匯出圖表，請嘗試其他檔名或位置。',
                'en': 'Unable to export chart. Please try another file name or location.',
                'ja': 'チャートをエクスポートできませんでした。別のファイル名または保存先をお試しください。'
            },
            'throttle_box_plot.y_axis_title': {
                'zh': '全油門持續時間 (秒)',
                'en': 'Full Throttle Duration (seconds)',
                'ja': 'フルスロットル継続時間（秒）'
            },
            'throttle_box_plot.no_data': {
                'zh': '沒有可用的油門資料',
                'en': 'No throttle data available',
                'ja': '利用可能なスロットルデータがありません'
            },
            'throttle_box_plot.stat_median': {'zh': '中位數', 'en': 'Median', 'ja': '中央値'},
            'throttle_box_plot.stat_mean': {'zh': '平均值', 'en': 'Mean', 'ja': '平均値'},
            'throttle_box_plot.stat_q1': {'zh': 'Q1', 'en': 'Q1', 'ja': '第1四分位数'},
            'throttle_box_plot.stat_q3': {'zh': 'Q3', 'en': 'Q3', 'ja': '第3四分位数'},
            'throttle_box_plot.stat_count': {'zh': '取樣數', 'en': 'Samples', 'ja': 'サンプル数'},
            'throttle_analysis_options_title': {
                'zh': '油門分析選項',
                'en': 'Throttle Analysis Options',
                'ja': 'スロットル分析オプション'
            },
            'throttle_analysis_options_description': {
                'zh': '請選擇要開啟的油門分析視圖。',
                'en': 'Select the throttle analysis views you want to open.',
                'ja': '開きたいスロットル分析ビューを選択してください。'
            },
            'throttle_analysis_option_box_plot': {
                'zh': '油門箱型圖',
                'en': 'Throttle Box Plot',
                'ja': 'スロットル箱ひげ図'
            },
            'throttle_analysis_option_line_chart': {
                'zh': '油門折線圖',
                'en': 'Throttle Line Chart',
                'ja': 'スロットル折れ線グラフ'
            },
            'throttle_analysis_option_line_chart_hint': {
                'zh': '油門折線圖模組仍在開發中，將於未來更新提供。',
                'en': 'The throttle line chart module is under development and will arrive in a future update.',
                'ja': 'スロットル折れ線グラフモジュールは開発中で、今後の更新で提供予定です。'
            },
            'throttle_box_plot_desc': {
                'zh': '油門箱型圖：視覺化全油門使用分佈情況',
                'en': 'Throttle Box Plot: Visualizes throttle usage distribution',
                'ja': 'スロットル箱ひげ図: スロットル使用分布を可視化'
            },
            'throttle_line_chart_desc': {
                'zh': '油門折線圖：顯示時間序列油門曲線（即將推出）',
                'en': 'Throttle Line Chart: Time-series throttle view (coming soon)',
                'ja': 'スロットル折れ線グラフ: スロットルを時系列で表示（近日公開）'
            },
            'throttle_line_chart_placeholder_title': {
                'zh': '油門折線圖',
                'en': 'Throttle Line Chart',
                'ja': 'スロットル折れ線グラフ'
            },
            'throttle_line_chart_placeholder_body': {
                'zh': '油門折線圖模組仍在開發中，敬請期待。',
                'en': 'The throttle line chart module is still under development. Stay tuned!',
                'ja': 'スロットル折れ線グラフモジュールは現在開発中です。リリースをお待ちください。'
            },
            
            # 事故分析模組
            'waiting_data_load': {'zh': '等待數據載入...', 'en': 'Waiting for data loading...', 'ja': 'データ読み込み待ち...'},
            'accident_analysis_error': {'zh': '事故分析錯誤', 'en': 'Accident Analysis Error', 'ja': '事故分析エラー'},
            'accident_comprehensive_analysis': {'zh': '事故綜合分析', 'en': 'Accident Comprehensive Analysis', 'ja': '事故総合分析'},
            'accident_module_description': {'zh': 'F1 事故統計分析與可視化', 'en': 'F1 Accident Statistics Analysis and Visualization', 'ja': 'F1 事故統計分析と可視化'},
            'invalid_load_parameters': {'zh': '載入參數不正確', 'en': 'Invalid load parameters', 'ja': 'ロードパラメータが無効'},
            'local_data_format_error': {'zh': '本地資料格式錯誤', 'en': 'Local data format error', 'ja': 'ローカルデータフォーマットエラー'},
            'data_load_complete': {'zh': ' 數據載入完成', 'en': ' Data loaded successfully', 'ja': ' データ読み込み完了'},
            'data_cleared': {'zh': '數據已清除', 'en': 'Data cleared', 'ja': 'データがクリアされました'},
            'incident_type': {'zh': '事故類型', 'en': 'Incident Type', 'ja': '事故タイプ'},
            'count': {'zh': '次數', 'en': 'Count', 'ja': '回数'},
            'accident_comprehensive_analysis': {'zh': ' 事故綜合分析', 'en': ' Accident Comprehensive Analysis', 'ja': ' 事故総合分析'},
            
            # Accident Analysis MDI 模組新增翻譯
            'flag_type': {'zh': '旗標類型', 'en': 'Flag Type', 'ja': 'フラグタイプ'},
            'reason': {'zh': '原因', 'en': 'Reason', 'ja': '理由'},
            'track_sector': {'zh': '賽道區域', 'en': 'Track Sector', 'ja': 'トラックセクター'},
            'driver': {'zh': '車手', 'en': 'Driver', 'ja': 'ドライバー'},
            'violation_type': {'zh': '違規類型', 'en': 'Violation Type', 'ja': '違反タイプ'},
            'penalty': {'zh': '處罰', 'en': 'Penalty', 'ja': 'ペナルティ'},
            'lap_number': {'zh': '圈數', 'en': 'Lap', 'ja': 'ラップ'},
            'no_driver_involvement_data': {'zh': '暫無車手涉入數據', 'en': 'No driver involvement data', 'ja': 'ドライバー関与データなし'},
            'no_time_distribution_data': {'zh': '無時間分佈數據', 'en': 'No time distribution data', 'ja': '時間分布データなし'},
            'no_data_to_display': {'zh': '無數據可顯示', 'en': 'No data to display', 'ja': '表示するデータがありません'},
            'lap_incident_distribution': {'zh': '圈數事故分佈', 'en': 'Lap Incident Distribution', 'ja': 'ラップ事故分布'},
            'incident_count': {'zh': '事故數量', 'en': 'Incident Count', 'ja': '事故件数'},
            'unknown': {'zh': '未知', 'en': 'Unknown', 'ja': '不明'},
            'accident_module_info_desc': {'zh': '提供F1事故的綜合統計和分析', 'en': 'Provides comprehensive statistics and analysis of F1 accidents', 'ja': 'F1事故の包括的な統計と分析を提供'},
            'sequence_number': {'zh': '序號', 'en': 'No.', 'ja': '番号'},
            'lap': {'zh': '圈數', 'en': 'Lap', 'ja': 'ラップ'},
            'time': {'zh': '時間', 'en': 'Time', 'ja': '時間'},
            'event_description': {'zh': '事件描述', 'en': 'Event Description', 'ja': 'イベント説明'},
            'category': {'zh': '類別', 'en': 'Category', 'ja': 'カテゴリー'},
            'severity': {'zh': '嚴重程度', 'en': 'Severity', 'ja': '重大度'},
            'impact_level': {'zh': '影響程度', 'en': 'Impact', 'ja': '影響度'},
            'sector': {'zh': '區段', 'en': 'Sector', 'ja': 'セクター'},
            'flags': {'zh': '旗幟', 'en': 'Flags', 'ja': 'フラグ'},
            'drivers': {'zh': '車手', 'en': 'Drivers', 'ja': 'ドライバー'},
            'accident_comprehensive_analysis_title': {'zh': '事故綜合分析', 'en': 'Accident Comprehensive Analysis', 'ja': '事故総合分析'},
            'please_select_params': {'zh': '請選擇年份、賽事和賽段', 'en': 'Please select year, race and session', 'ja': '年、レース、セッションを選択してください'},
            'accident_data_load_failed': {'zh': '事故分析資料載入失敗,請稍後再試。', 'en': 'Accident data failed to load, please try again later.', 'ja': '事故データの読み込みに失敗しました。後でもう一度お試しください。'},
            'accident_session_restriction': {'zh': '事故分析僅適用於正賽 (R) 和排位賽 (Q)，練習賽無賽會控制訊息', 'en': 'Accident analysis is only applicable for Race (R) and Qualifying (Q), practice sessions have no race control messages', 'ja': '事故分析は決勝 (R) と予選 (Q) のみ適用、練習走行にはレースコントロールメッセージがありません'},
            'load_failed': {'zh': '載入失敗', 'en': 'Load failed', 'ja': '読み込み失敗'},
            'all_categories': {'zh': '全部類別', 'en': 'All Categories', 'ja': 'すべてのカテゴリー'},
            'all_severities': {'zh': '全部嚴重程度', 'en': 'All Severities', 'ja': 'すべての重大度'},
            'all_impacts': {'zh': '全部影響程度', 'en': 'All Impacts', 'ja': 'すべての影響度'},
            'refresh': {'zh': '刷新', 'en': 'Refresh', 'ja': '更新'},
            'loading': {'zh': '載入中...', 'en': 'Loading...', 'ja': '読み込み中...'},
            'no_incident_data': {'zh': '無事件數據', 'en': 'No incident data', 'ja': 'イベントデータなし'},
            'loading_incident_data': {'zh': '載入事件數據中...', 'en': 'Loading incident data...', 'ja': 'イベントデータ読み込み中...'},
            
            # 事故分析分頁和搜尋
            'accident_statistics': {'zh': '事故統計', 'en': 'Accident Statistics', 'ja': '事故統計データ'},
            'detailed_records': {'zh': '詳細記錄', 'en': 'Detailed Records', 'ja': '詳細記録'},
            'search_event_description': {'zh': '搜尋事件描述或關鍵字...', 'en': 'Search event description or keywords...', 'ja': 'イベント説明またはキーワードを検索...'},
            'total_events': {'zh': '總事件', 'en': 'Total Events', 'ja': '総イベント'},
            'pit_related': {'zh': 'PIT相關', 'en': 'PIT Related', 'ja': 'PIT関連'},
            'track_limits': {'zh': '賽道限制', 'en': 'Track Limits', 'ja': 'トラックリミット'},
            'investigation': {'zh': '調查', 'en': 'Investigation', 'ja': '調査'},
            'penalty_cat': {'zh': '處罰', 'en': 'Penalty', 'ja': 'ペナルティ'},
            'other': {'zh': '其他', 'en': 'Other', 'ja': 'その他'},
            
            # 事故統計卡片
            'track_limit_violations': {'zh': ' Track Limit', 'en': ' Track Limit', 'ja': ' トラックリミット'},
            'violations_count': {'zh': '(違規次數)', 'en': '(Violations)', 'ja': '(違反回数)'},
            'double_yellow_flag': {'zh': ' 雙黃旗', 'en': ' Double Yellow', 'ja': ' ダブルイエロー'},
            'yellow_flag': {'zh': ' 黃旗', 'en': ' Yellow Flag', 'ja': ' イエローフラッグ'},
            'red_flag': {'zh': ' 紅旗', 'en': ' Red Flag', 'ja': ' レッドフラッグ'},
            'display_count': {'zh': '(出示次數)', 'en': '(Times)', 'ja': '(回数)'},
            
            # 事故統計卡片
            'total_incidents_card': {'zh': '總事故數', 'en': 'Total Incidents', 'ja': '総事故数'},
            'safety_car_count': {'zh': '安全車次數', 'en': 'Safety Car', 'ja': 'セーフティカー'},
            'red_flag_count': {'zh': '紅旗次數', 'en': 'Red Flags', 'ja': 'レッドフラッグ'},
            'avg_severity': {'zh': '平均嚴重程度', 'en': 'Avg Severity', 'ja': '平均深刻度'},
            
            # 右鍵選單
            'execute_analysis': {'zh': '執行分析', 'en': 'Execute Analysis', 'ja': '分析を実行'},
            'export_data': {'zh': '匯出數據', 'en': 'Export Data', 'ja': 'データをエクスポート'},
            'help': {'zh': '說明', 'en': 'Help', 'ja': 'ヘルプ'},
            'batch_execute_analysis': {'zh': '批量執行分析', 'en': 'Batch Execute Analysis', 'ja': 'バッチ分析実行'},
            'batch_export_data': {'zh': '批量匯出數據', 'en': 'Batch Export Data', 'ja': 'バッチデータエクスポート'},
            'expand_all_tree': {'zh': '全展開樹狀圖', 'en': 'Expand All', 'ja': 'すべて展開'},
            'collapse_all_tree': {'zh': '全關閉樹狀圖', 'en': 'Collapse All', 'ja': 'すべて折りたたむ'},
            'modules': {'zh': '個模組', 'en': 'modules', 'ja': 'モジュール'},
            'selected_modules': {'zh': '已選擇的模組', 'en': 'Selected Modules', 'ja': '選択されたモジュール'},
            'items': {'zh': '個', 'en': 'items', 'ja': '個'},
            'track_analysis': {'zh': '賽道分析', 'en': 'Track Analysis', 'ja': 'トラック分析'},
            'telemetry_analysis': {'zh': '遙測分析', 'en': 'Telemetry Analysis', 'ja': 'テレメトリー分析'},
            'lap_analysis': {'zh': '圈速分析', 'en': 'Lap Analysis', 'ja': 'ラップ分析'},
            'driver_analysis': {'zh': '車手分析', 'en': 'Driver Analysis', 'ja': 'ドライバー分析'},
            'pitstop_analysis': {'zh': '進站分析', 'en': 'Pitstop Analysis', 'ja': 'ピットストップ分析'},
            
            # 圈速分析子模組
            'speed_analysis': {'zh': '速度分析', 'en': 'Speed Analysis', 'ja': '速度分析'},
            'speed_analysis_description': {
                'zh': 'F1賽車速度分析模組，支援雙車手圈速對比',
                'en': 'F1 racing speed analysis with dual driver comparison',
                'ja': 'F1レーシング速度分析、2ドライバー比較対応'
            },
            'throttle_analysis': {'zh': '油門分析', 'en': 'Throttle Analysis', 'ja': 'スロットル分析'},
            'throttle_analysis_description': {
                'zh': 'F1賽車油門分析模組，支援雙車手油門對比',
                'en': 'F1 racing throttle analysis with dual driver comparison',
                'ja': 'F1レーシングスロットル分析、2ドライバー比較対応'
            },
            'brake_analysis': {'zh': '煞車分析', 'en': 'Brake Analysis', 'ja': 'ブレーキ分析'},
            'brake_analysis_description': {
                'zh': 'F1賽車煞車分析模組，支援雙車手煞車對比',
                'en': 'F1 racing brake analysis with dual driver comparison',
                'ja': 'F1レーシングブレーキ分析、2ドライバー比較対応'
            },
            'rpm_analysis': {'zh': 'RPM分析', 'en': 'RPM Analysis', 'ja': 'RPM分析'},
            'rpm_analysis_description': {
                'zh': 'F1賽車RPM轉速對比分析工具',
                'en': 'F1 racing RPM analysis tool',
                'ja': 'F1レーシングRPM分析ツール'
            },
            'gear_analysis': {'zh': '檔位分析', 'en': 'Gear Analysis', 'ja': 'ギア分析'},
            'gear_analysis_description': {
                'zh': 'F1賽車檔位分析模組，支援雙車手檔位對比',
                'en': 'F1 racing gear analysis with dual driver comparison',
                'ja': 'F1レーシングギア分析、2ドライバー比較対応'
            },
            'speeddiff_analysis': {'zh': '速度差異分析', 'en': 'Speed Diff Analysis', 'ja': 'スピード差分析'},
            'speeddiff_analysis_description': {
                'zh': 'F1賽車速度差異對比分析工具',
                'en': 'F1 racing speed difference analysis tool',
                'ja': 'F1レーシングスピード差分析ツール'
            },
            'distancediff_analysis': {'zh': '距離差異分析', 'en': 'Distance Diff Analysis', 'ja': 'ディスタンス差分析'},
            'distancediff_analysis_description': {
                'zh': 'F1賽車距離差異對比分析工具',
                'en': 'F1 racing distance difference analysis tool',
                'ja': 'F1レーシングディスタンス差分析ツール'
            },
            'acceleration_analysis': {'zh': '加速度分析', 'en': 'Acceleration Analysis', 'ja': 'アクセラレーション分析'},
            'acceleration_analysis_description': {
                'zh': 'F1賽車加速度分析模組',
                'en': 'F1 racing acceleration analysis module',
                'ja': 'F1レーシングアクセラレーション分析モジュール'
            },
            
            # 統計面板通用標籤
            'detailed_statistics': {'zh': '詳細統計信息', 'en': 'Detailed Statistics', 'ja': '詳細統計情報'},
            'lap_time': {'zh': '圈時間', 'en': 'Lap Time', 'ja': 'ラップタイム'},
            'tire_compound': {'zh': '輪胎配方', 'en': 'Tire Compound', 'ja': 'タイヤコンパウンド'},
            'lap_number_short': {'zh': '圈數', 'en': 'Lap', 'ja': 'ラップ'},
            'lap_number_label': {'zh': ' 圈數:', 'en': ' Lap:', 'ja': ' ラップ:'},
            
            # 速度差分析專用標籤
            'speed_diff_kmh': {'zh': '速度差距 (km/h)', 'en': 'Speed Diff (km/h)', 'ja': 'スピード差 (km/h)'},
            'speeddiff_window_title': {'zh': ' 速度差分析', 'en': ' Speed Diff Analysis', 'ja': ' 速度差分析'},
            
            # 累積距離差分析專用標籤
            'distance_diff_m': {'zh': '距離差距 (m)', 'en': 'Distance Diff (m)', 'ja': 'ディスタンス差 (m)'},
            'distancediff_window_title': {'zh': ' 累積距離差分析', 'en': ' Distance Diff Analysis', 'ja': ' ディスタンス差分析'},
            
            # 表格標題
            'item': {'zh': '項目', 'en': 'Item', 'ja': '項目'},
            'driver1': {'zh': '車手1', 'en': 'Driver 1', 'ja': 'ドライバー1'},
            'driver2': {'zh': '車手2', 'en': 'Driver 2', 'ja': 'ドライバー2'},
            'difference': {'zh': '差值', 'en': 'Difference', 'ja': '差分'},
            
            # 軸標籤和單位
            'distance_m': {'zh': '距離 (m)', 'en': 'Distance (m)', 'ja': '距離 (m)'},
            'distance_label': {'zh': '距離', 'en': 'Distance', 'ja': '距離'},
            'linkage_distance': {'zh': '連動距離', 'en': 'Linkage Distance', 'ja': '連動距離'},
            
            # 時間軸相關翻譯
            'time_s': {'zh': '時間 (s)', 'en': 'Time (s)', 'ja': '時間 (s)'},
            'time_label': {'zh': '時間', 'en': 'Time', 'ja': '時間'},
            'linkage_time': {'zh': '連動時間', 'en': 'Linkage Time', 'ja': '連動時間'},
            
            # 連動系統專用翻譯
            'linkage_button': {'zh': ' 連動', 'en': ' Link', 'ja': ' 連動'},
            'master_linkage_button': {'zh': ' 主連動', 'en': ' Master Link', 'ja': ' マスター連動'},
            'linkage_enabled': {'zh': '連動已啟用', 'en': 'Linkage Enabled', 'ja': '連動有効'},
            'linkage_disabled': {'zh': '連動已停用', 'en': 'Linkage Disabled', 'ja': '連動無効'},
            'master_linkage_enabled': {'zh': '主連動已啟用', 'en': 'Master Linkage Enabled', 'ja': 'マスター連動有効'},
            'master_linkage_disabled': {'zh': '主連動已停用', 'en': 'Master Linkage Disabled', 'ja': 'マスター連動無効'},
            'master_linkage_enabled_individual_disabled': {'zh': '主連動已啟用，個別連動已停用', 'en': 'Master linkage enabled, individual linkage disabled', 'ja': 'マスター連動有効、個別連動無効'},
            'clear_all_linkage_marks': {'zh': '清除所有連動標記', 'en': 'Clear all linkage marks', 'ja': 'すべての連動マークをクリア'},
            'enabled_status': {'zh': '啟用', 'en': 'Enabled', 'ja': '有効'},
            'disabled_status': {'zh': '停用', 'en': 'Disabled', 'ja': '無効'},
            
            # 狀態訊息
            'na': {'zh': 'N/A', 'en': 'N/A', 'ja': 'N/A'},
            'error': {'zh': '錯誤', 'en': 'Error', 'ja': 'エラー'},
            'loading_speed_data': {'zh': '開始載入速度數據...', 'en': 'Loading speed data...', 'ja': '速度データを読み込み中...'},
            'loading_throttle_data': {'zh': '開始載入油門數據...', 'en': 'Loading throttle data...', 'ja': 'スロットルデータを読み込み中...'},
            'loading_brake_data': {'zh': '開始載入煞車數據...', 'en': 'Loading brake data...', 'ja': 'ブレーキデータを読み込み中...'},
            'loading_rpm_data': {'zh': '開始載入RPM數據...', 'en': 'Loading RPM data...', 'ja': 'RPMデータを読み込み中...'},
            'loading_gear_data': {'zh': '開始載入檔位數據...', 'en': 'Loading gear data...', 'ja': 'ギアデータを読み込み中...'},
            'detailed_lap_analysis': {'zh': '詳細圈速分析', 'en': 'Detailed Lap Analysis', 'ja': '詳細ラップ分析'},
            'driver_analysis': {'zh': '車手分析', 'en': 'Driver Analysis', 'ja': 'ドライバー分析'},
            'driver_ranking': {'zh': '車手排名', 'en': 'Driver Ranking', 'ja': 'Driver Ranking'},
            'tire_strategy_analysis': {'zh': '輪胎策略分析', 'en': 'Tire Strategy Analysis', 'ja': 'Tire Strategy Analysis'},
            
            # 視窗標題模板
            'window_title_track': {'zh': '賽道', 'en': 'Track', 'ja': 'Track'},
            'window_title_temp_analysis': {'zh': '溫度分析', 'en': 'Temperature Analysis', 'ja': '温度分析'},
            'window_title_rain_analysis': {'zh': '️ 降雨分析', 'en': '️ Rain Analysis', 'ja': '️ Rain Analysis'},  # 向後相容
            'window_title_pitstop_analysis': {'zh': '進站分析', 'en': 'Pitstop Analysis', 'ja': 'ピットストップ分析'},
            
            # 功能表和工具列
            'file_menu': {'zh': '檔案', 'en': 'File', 'ja': 'ファイル'},
            'analysis_menu': {'zh': '分析', 'en': 'Analysis', 'ja': '分析'},
            'view_menu': {'zh': '檢視', 'en': 'View', 'ja': '表示'},
            'tools_menu': {'zh': '工具', 'en': 'Tools', 'ja': 'ツール'},
            'help_menu': {'zh': '說明', 'en': 'Help', 'ja': 'ヘルプ'},
            
            # File Menu 項目
            'open_session': {'zh': '開啟會話...', 'en': 'Open Session...', 'ja': 'セッションを開く...'},
            'save_workspace': {'zh': '儲存工作區', 'en': 'Save Workspace', 'ja': 'ワークスペースを保存'},
            'load_workspace': {'zh': '載入工作區', 'en': 'Load Workspace', 'ja': 'ワークスペース読込'},
            'load_workspace_dev': {
                'zh': '載入工作區…（開發中）',
                'en': 'Load Workspace… (In Development)',
                'ja': 'ワークスペースを読み込み…（開発中）'
            },
            'save_workspace_dev': {
                'zh': '儲存工作區（開發中）',
                'en': 'Save Workspace (In Development)',
                'ja': 'ワークスペースを保存（開発中）'
            },
            'export_report': {'zh': '匯出報告...', 'en': 'Export Report...', 'ja': 'レポートをエクスポート...'},
            'exit': {'zh': '結束', 'en': 'Exit', 'ja': '終了'},
            
            # Analysis Menu 項目
            'rain_analysis': {'zh': '降雨分析', 'en': 'Rain Analysis', 'ja': '降雨分析'},
            'track_analysis': {'zh': '賽道分析', 'en': 'Track Analysis', 'ja': 'トラック分析'},
            'race_overview': {'zh': '賽事概覽', 'en': 'Race Overview', 'ja': 'レース概要'},
            'telemetry_analysis': {'zh': '遙測分析', 'en': 'Telemetry Analysis', 'ja': 'テレメトリー分析'},
            'telemetry_comparison': {'zh': '遙測對比', 'en': 'Telemetry Comparison', 'ja': 'テレメトリー比較'},
            'driver_comparison': {'zh': '車手對比', 'en': 'Driver Comparison', 'ja': 'ドライバー比較'},
            'sector_analysis': {'zh': '賽段分析', 'en': 'Sector Analysis', 'ja': 'セクター分析'},
            
            # View Menu 項目
            'tile_windows': {'zh': '平鋪視窗', 'en': 'Tile Windows', 'ja': 'ウィンドウを並べて表示'},
            'cascade_windows': {'zh': '層疊視窗', 'en': 'Cascade Windows', 'ja': 'ウィンドウを重ねて表示'},
            'minimize_all_windows': {'zh': '最小化所有視窗', 'en': 'Minimize All Windows', 'ja': 'すべてのウィンドウを最小化'},
            'maximize_all_windows': {'zh': '最大化所有視窗', 'en': 'Maximize All Windows', 'ja': 'すべてのウィンドウを最大化'},
            'restore_all_windows': {'zh': '還原所有視窗', 'en': 'Restore All Windows', 'ja': 'すべてのウィンドウを元に戻す'},
            'close_all_windows': {'zh': '關閉所有視窗', 'en': 'Close All Windows', 'ja': 'すべてのウィンドウを閉じる'},
            'full_screen': {'zh': '全螢幕', 'en': 'Full Screen', 'ja': 'フルスクリーン'},
            
            # Tools Menu 項目
            'data_validation': {'zh': '數據驗證', 'en': 'Data Validation', 'ja': 'データ検証'},
            'system_settings': {'zh': '系統設定', 'en': 'System Settings', 'ja': 'システム設定'},
            'check_api_status': {'zh': '檢查 API 狀態', 'en': 'Check API Status', 'ja': 'APIステータスを確認'},
            'check_api_status_tip': {'zh': '立即執行 API 健康檢查', 'en': 'Run an API health check immediately', 'ja': 'APIヘルスチェックを即座に実行'},
            'run_api_health_check': {'zh': '立即執行 API 健康檢查', 'en': 'Run an API health check immediately', 'ja': 'APIヘルスチェックを即座に実行'},
            'language_menu': {'zh': '語言', 'en': 'Language', 'ja': '言語'},
            'objgraph_diagnostic': {'zh': '記憶體診斷', 'en': 'Memory Diagnostics', 'ja': 'メモリ診断'},
            'objgraph_diagnostic_tip': {'zh': '開啟記憶體和物件診斷工具', 'en': 'Open memory and object diagnostic tool', 'ja': 'メモリとオブジェクト診断ツールを開く'},
            
            # Objgraph Diagnostic Window
            'objgraph_diagnostic_title': {'zh': '物件記憶體診斷工具', 'en': 'Memory Diagnostics', 'ja': 'メモリ診断ツール'},
            'objgraph_control_panel': {'zh': '控制面板', 'en': 'Control Panel', 'ja': 'コントロールパネル'},
            'objgraph_scan_objects': {'zh': '掃描物件', 'en': 'Scan Objects', 'ja': 'オブジェクトスキャン'},
            'objgraph_track_growth': {'zh': '追蹤成長', 'en': 'Track Growth', 'ja': '成長追跡'},
            'objgraph_force_gc': {'zh': '強制垃圾回收', 'en': 'Force GC', 'ja': '強制ガベージコレクション'},
            'objgraph_display_limit': {'zh': '顯示數量', 'en': 'Display Limit', 'ja': '表示数'},
            'objgraph_auto_refresh': {'zh': '自動刷新', 'en': 'Auto Refresh', 'ja': '自動更新'},
            'objgraph_interval': {'zh': '間隔(秒)', 'en': 'Interval(s)', 'ja': '間隔(秒)'},
            'objgraph_export': {'zh': '導出報告', 'en': 'Export Report', 'ja': 'レポートエクスポート'},
            'objgraph_tab_stats': {'zh': '物件統計', 'en': 'Object Stats', 'ja': 'オブジェクト統計'},
            'objgraph_tab_growth': {'zh': '成長追蹤', 'en': 'Growth Track', 'ja': '成長追跡'},
            'objgraph_tab_graph': {'zh': '引用圖', 'en': 'Reference Graph', 'ja': '参照グラフ'},
            'objgraph_tab_action': {'zh': '操作記錄', 'en': 'Action Log', 'ja': '操作記録'},
            'objgraph_tab_log': {'zh': '診斷日誌', 'en': 'Diagnostic Log', 'ja': '診断ログ'},
            'objgraph_ready': {'zh': '就緒', 'en': 'Ready', 'ja': '準備完了'},
            'objgraph_action_note': {'zh': '操作記錄', 'en': 'Action Notes', 'ja': '操作メモ'},
            'objgraph_action_placeholder': {'zh': '輸入操作描述...', 'en': 'Enter action description...', 'ja': '操作説明を入力...'},
            'objgraph_add_action': {'zh': '新增記錄', 'en': 'Add Note', 'ja': '記録追加'},
            'objgraph_quick_actions': {'zh': '快速操作', 'en': 'Quick Actions', 'ja': 'クイックアクション'},
            'objgraph_quick_open': {'zh': '開啟模組', 'en': 'Open Module', 'ja': 'モジュールを開く'},
            'objgraph_quick_close': {'zh': '關閉模組', 'en': 'Close Module', 'ja': 'モジュールを閉じる'},
            'objgraph_quick_analyze': {'zh': '執行分析', 'en': 'Run Analysis', 'ja': '分析実行'},
            'objgraph_quick_export': {'zh': '導出資料', 'en': 'Export Data', 'ja': 'データエクスポート'},
            'objgraph_quick_clear': {'zh': '清理緩存', 'en': 'Clear Cache', 'ja': 'キャッシュクリア'},
            'objgraph_action_time': {'zh': '時間', 'en': 'Time', 'ja': '時刻'},
            'objgraph_action_description': {'zh': '操作描述', 'en': 'Description', 'ja': '説明'},
            'objgraph_action_objects': {'zh': '物件總數', 'en': 'Total Objects', 'ja': 'オブジェクト総数'},
            'objgraph_action_change': {'zh': '變化', 'en': 'Change', 'ja': '変化'},
            'objgraph_snapshot': {'zh': '快照當前狀態', 'en': 'Snapshot State', 'ja': '状態スナップショット'},
            'objgraph_snapshot_in_progress': {'zh': '正在拍攝快照並追蹤成長...', 'en': 'Taking snapshot and tracking growth...', 'ja': 'スナップショット作成と成長追跡中...'},
            'objgraph_clear_actions': {'zh': '清空記錄', 'en': 'Clear Records', 'ja': '記録クリア'},
            'objgraph_empty_action': {'zh': '請輸入操作描述', 'en': 'Please enter action description', 'ja': '操作説明を入力してください'},
            'objgraph_confirm_clear': {'zh': '確認清空', 'en': 'Confirm Clear', 'ja': 'クリア確認'},
            'objgraph_confirm_clear_actions': {'zh': '確定要清空所有操作記錄嗎？', 'en': 'Clear all action records?', 'ja': 'すべての操作記録をクリアしますか？'},
            'objgraph_type': {'zh': '類型', 'en': 'Type', 'ja': 'タイプ'},
            'objgraph_count': {'zh': '數量', 'en': 'Count', 'ja': '数量'},
            'objgraph_percentage': {'zh': '百分比', 'en': 'Percentage', 'ja': 'パーセンテージ'},
            'objgraph_previous': {'zh': '之前', 'en': 'Previous', 'ja': '以前'},
            'objgraph_current': {'zh': '目前', 'en': 'Current', 'ja': '現在'},
            'objgraph_growth': {'zh': '成長', 'en': 'Growth', 'ja': '成長'},
            'objgraph_growth_info': {'zh': '此功能追蹤兩次掃描之間的物件數量變化。點擊「追蹤成長」開始追蹤。', 'en': 'This feature tracks object count changes between scans. Click "Track Growth" to start.', 'ja': 'この機能は、スキャン間のオブジェクト数の変化を追跡します。「成長追跡」をクリックして開始します。'},
            'objgraph_select_type': {'zh': '選擇類型', 'en': 'Select Type', 'ja': 'タイプを選択'},
            'objgraph_max_depth': {'zh': '最大深度', 'en': 'Max Depth', 'ja': '最大深度'},
            'objgraph_generate_graph': {'zh': '生成引用圖', 'en': 'Generate Graph', 'ja': 'グラフ生成'},
            'objgraph_no_graph': {'zh': '尚未生成引用圖', 'en': 'No graph generated yet', 'ja': 'まだグラフが生成されていません'},
            'objgraph_clear_log': {'zh': '清除日誌', 'en': 'Clear Log', 'ja': 'ログクリア'},
            'objgraph_scanning': {'zh': '正在掃描物件...', 'en': 'Scanning objects...', 'ja': 'オブジェクトをスキャン中...'},
            'objgraph_start_scan': {'zh': '開始掃描物件', 'en': 'Start scanning objects', 'ja': 'オブジェクトスキャン開始'},
            'objgraph_scan_complete': {'zh': '掃描完成', 'en': 'Scan complete', 'ja': 'スキャン完了'},
            'objgraph_scan_success': {'zh': '掃描成功，找到 {0} 種類型', 'en': 'Scan successful, found {0} types', 'ja': 'スキャン成功、{0}種類見つかりました'},
            'objgraph_scan_error': {'zh': '掃描失敗', 'en': 'Scan failed', 'ja': 'スキャン失敗'},
            'objgraph_tracking_growth': {'zh': '正在追蹤成長...', 'en': 'Tracking growth...', 'ja': '成長追跡中...'},
            'objgraph_start_growth_track': {'zh': '開始追蹤物件成長', 'en': 'Start tracking object growth', 'ja': 'オブジェクト成長追跡開始'},
            'objgraph_growth_complete': {'zh': '成長追蹤完成', 'en': 'Growth tracking complete', 'ja': '成長追跡完了'},
            'objgraph_growth_success': {'zh': '追蹤完成，發現 {0} 種類型有變化', 'en': 'Tracking complete, {0} types changed', 'ja': '追跡完了、{0}種類が変化'},
            'objgraph_growth_error': {'zh': '成長追蹤失敗', 'en': 'Growth tracking failed', 'ja': '成長追跡失敗'},
            'objgraph_force_gc_start': {'zh': '執行強制垃圾回收...', 'en': 'Forcing garbage collection...', 'ja': '強制ガベージコレクション実行中...'},
            'objgraph_gc_complete': {'zh': '垃圾回收完成，總共回收 {0} 個物件', 'en': 'GC complete, collected {0} objects', 'ja': 'GC完了、{0}個のオブジェクトを回収'},
            'objgraph_gc_done': {'zh': '垃圾回收完成 ({0} 個物件)', 'en': 'GC complete ({0} objects)', 'ja': 'GC完了({0}個)'},
            'objgraph_gc_title': {'zh': '垃圾回收', 'en': 'Garbage Collection', 'ja': 'ガベージコレクション'},
            'objgraph_gc_message': {'zh': '已回收 {0} 個物件', 'en': 'Collected {0} objects', 'ja': '{0}個のオブジェクトを回収しました'},
            'objgraph_select_type_warning': {'zh': '請選擇或輸入物件類型', 'en': 'Please select or enter object type', 'ja': 'オブジェクトタイプを選択または入力してください'},
            'objgraph_generating_graph': {'zh': '正在生成 {0} 的引用圖...', 'en': 'Generating reference graph for {0}...', 'ja': '{0}の参照グラフを生成中...'},
            'objgraph_generate_graph_start': {'zh': '開始生成 {0} 的引用圖', 'en': 'Start generating reference graph for {0}', 'ja': '{0}の参照グラフ生成開始'},
            'objgraph_graph_complete': {'zh': '引用圖已生成: {0}', 'en': 'Reference graph generated: {0}', 'ja': '参照グラフ生成完了: {0}'},
            'objgraph_graph_success': {'zh': '引用圖已保存至: {0}', 'en': 'Reference graph saved to: {0}', 'ja': '参照グラフ保存先: {0}'},
            'objgraph_graph_saved': {'zh': '引用圖已保存至:\n{0}', 'en': 'Reference graph saved to:\n{0}', 'ja': '参照グラフ保存先:\n{0}'},
            'objgraph_graph_load_error': {'zh': '無法載入圖片', 'en': 'Failed to load image', 'ja': '画像の読み込みに失敗'},
            'objgraph_graph_error': {'zh': '引用圖生成失敗', 'en': 'Reference graph generation failed', 'ja': '参照グラフ生成失敗'},
            'objgraph_export_report': {'zh': '導出診斷報告', 'en': 'Export Diagnostic Report', 'ja': '診断レポートエクスポート'},
            'objgraph_export_success': {'zh': '報告已導出至:\n{0}', 'en': 'Report exported to:\n{0}', 'ja': 'レポートエクスポート先:\n{0}'},
            'objgraph_export_error': {'zh': '導出失敗:\n{0}', 'en': 'Export failed:\n{0}', 'ja': 'エクスポート失敗:\n{0}'},
            'objgraph_open_error': {'zh': '無法開啟記憶體診斷工具:\n{0}', 'en': 'Failed to open Memory Diagnostic tool:\n{0}', 'ja': 'メモリ診断ツールを開けません:\n{0}'},
            
            # DraggableTitleBar 工具提示和按鈕
            'sync_main_window_tooltip_enabled': {'zh': '接收主程式同步：啟用 (綠色)', 'en': 'Receive Main Window Sync: Enabled (Green)', 'ja': 'メインウィンドウと同期：有効（緑）'},
            'sync_main_window_tooltip_disabled': {'zh': '接收主程式同步：停用 (紅色)', 'en': 'Receive Main Window Sync: Disabled (Red)', 'ja': 'メインウィンドウと同期：無効（赤）'},
            'individual_linkage_tooltip_enabled': {'zh': '個別連動：啟用', 'en': 'Individual Linkage: Enabled', 'ja': '個別連携：有効'},
            'individual_linkage_tooltip_disabled': {'zh': '個別連動：停用', 'en': 'Individual Linkage: Disabled', 'ja': '個別連携：無効'},
            'restore_normal_size_tooltip': {'zh': '恢復正常大小', 'en': 'Restore Normal Size', 'ja': '通常サイズに戻す'},
            'window_settings_tooltip': {'zh': '視窗設定', 'en': 'Window Settings', 'ja': 'ウィンドウ設定'},
            'minimize_tooltip': {'zh': '最小化', 'en': 'Minimize', 'ja': '最小化'},
            'maximize_restore_tooltip': {'zh': '最大化/還原', 'en': 'Maximize/Restore', 'ja': '最大化/元に戻す'},
            'popout_window_tooltip': {'zh': '彈出為獨立視窗', 'en': 'Pop Out as Independent Window', 'ja': '独立ウィンドウとして表示'},
            'close_tooltip': {'zh': '關閉', 'en': 'Close', 'ja': '閉じる'},
            
            # DraggableTitleBar 右鍵選單
            'context_menu_restore': {'zh': '恢復正常大小', 'en': 'Restore Normal Size', 'ja': '通常サイズに戻す'},
            'context_menu_maximize': {'zh': ' 最大化', 'en': ' Maximize', 'ja': ' 最大化'},
            
            # DraggableTitleBar 狀態訊息
            'sync_enabled_message': {'zh': '接收同步已啟動 - 將接收主程式參數', 'en': 'Sync Enabled - Will Receive Main Window Parameters', 'ja': '同期有効 - メインウィンドウのパラメータを受信'},
            'sync_disabled_message': {'zh': '接收同步已停用 - 獨立運作模式', 'en': 'Sync Disabled - Independent Operation Mode', 'ja': '同期無効 - 独立動作モード'},
            'linkage_enabled_message': {'zh': '個別連動已啟用', 'en': 'Individual Linkage Enabled', 'ja': '個別連携が有効'},
            'linkage_disabled_message': {'zh': '個別連動已停用', 'en': 'Individual Linkage Disabled', 'ja': '個別連携が無効'},
            'window_sync_status_updated': {'zh': '視窗 \'{title}\' 同步接收狀態已更新: {status}', 'en': 'Window \'{title}\' Sync Status Updated: {status}', 'ja': 'ウィンドウ \'{title}\' 同期状態が更新されました: {status}'},
            'window_linkage_status_updated': {'zh': '視窗 \'{title}\' 個別連動狀態已更新: {status}', 'en': 'Window \'{title}\' Linkage Status Updated: {status}', 'ja': 'ウィンドウ \'{title}\' 連携状態が更新されました: {status}'},
            
            # 狀態訊息
            'ready': {'zh': '就緒', 'en': 'Ready', 'ja': '準備完了'},
            'loading': {'zh': '載入中...', 'en': 'Loading...', 'ja': 'Loading...'},
            'analysis_complete': {'zh': '分析完成', 'en': 'Analysis Complete', 'ja': 'Analysis Complete'},
            'error_occurred': {'zh': '發生錯誤', 'en': 'Error Occurred', 'ja': 'Error Occurred'},
            
            # 圖表和視覺化
            'chart_title': {'zh': '圖表', 'en': 'Chart', 'ja': 'Chart'},
            'export_chart': {'zh': '匯出圖表', 'en': 'Export Chart', 'ja': 'Export Chart'},
            'save_data': {'zh': '儲存數據', 'en': 'Save Data', 'ja': 'Save Data'},
            
            # 功能樹標題
            'analysis_modules': {'zh': '分析模組', 'en': 'Analysis Modules', 'ja': '分析モジュール'},
            
            # 功能樹項目 - 主分類
            'race_overview_analysis': {'zh': '賽事總覽分析', 'en': 'Race Overview Analysis', 'ja': 'レース概要分析'},
            'driver_performance_analysis': {'zh': '車手表現分析', 'en': 'Driver Performance Analysis', 'ja': 'ドライバーパフォーマンス分析'},
            'multi_season_analysis': {'zh': '多賽季分析', 'en': 'Multi-Season Analysis', 'ja': 'マルチシーズン分析'},
            
            # Season Start Reaction 年度起跑反應分析
            'season': {'zh': '賽季', 'en': 'Season', 'ja': 'シーズン'},
            'time_seconds': {'zh': '時間 (秒)', 'en': 'Time (seconds)', 'ja': '時間（秒）'},
            'median': {'zh': '中位數', 'en': 'Median', 'ja': '中央値'},
            'average': {'zh': '平均', 'en': 'Average', 'ja': '平均'},
            'min': {'zh': '最小', 'en': 'Min', 'ja': '最小'},
            'max': {'zh': '最大', 'en': 'Max', 'ja': '最大'},
            'race_count': {'zh': '比賽數', 'en': 'Races', 'ja': 'レース数'},
            'races': {'zh': '場比賽', 'en': 'races', 'ja': 'レース'},
            'api_error': {'zh': 'API 錯誤', 'en': 'API Error', 'ja': 'APIエラー'},
            'api_timeout': {'zh': 'API 請求逾時', 'en': 'API request timed out', 'ja': 'APIリクエストタイムアウト'},
            'api_connection_error': {'zh': '無法連接 API 服務器', 'en': 'Cannot connect to API server', 'ja': 'APIサーバーに接続できません'},
            'data_process_error': {'zh': '數據處理錯誤', 'en': 'Error processing data', 'ja': 'データ処理エラー'},
            'data_loaded': {'zh': '數據已載入', 'en': 'Data loaded', 'ja': 'データ読み込み完了'},
            
            # 功能樹項目 - 舊版（保留兼容性）
            'single_race_analysis': {'zh': '單場賽事分析', 'en': 'Single Race Analysis', 'ja': '単一レース分析'},
            'single_race_driver_analysis': {'zh': ' 單場賽事車手分析', 'en': ' Single Race Driver Analysis', 'ja': ' 単一レースドライバー分析'},
            
            # Lap Analysis 子模組
            'speed_analysis': {'zh': '速度分析', 'en': 'Speed Analysis', 'ja': '速度分析'},
            'brake_analysis': {'zh': '煞車分析', 'en': 'Brake Analysis', 'ja': 'ブレーキ分析'},
            'throttle_analysis_sub': {'zh': '油門分析', 'en': 'Throttle Analysis', 'ja': 'スロットル分析'},
            'gear_analysis': {'zh': '檔位分析', 'en': 'Gear Analysis', 'ja': 'ギア分析'},
            'rpm_analysis': {'zh': '轉速分析', 'en': 'RPM Analysis', 'ja': 'RPM分析'},
            'acceleration_analysis': {'zh': '加速度分析', 'en': 'Acceleration Analysis', 'ja': '加速度分析'},
            'speed_diff_analysis': {'zh': '速度差分析', 'en': 'Speed Diff Analysis', 'ja': '速度差分析'},
            'distance_diff_analysis': {'zh': '距離差分析', 'en': 'Distance Diff Analysis', 'ja': '距離差分析'},
            
            # Detailed Lap Analysis 子模組
            'detailed_lap_table': {'zh': '詳細圈速表格', 'en': 'Detailed Lap Table', 'ja': '詳細ラップテーブル'},
            'lap_time_box_plot_sub': {'zh': '圈速箱線圖', 'en': 'Lap Time Box Plot', 'ja': 'ラップタイム箱ひげ図'},
            
            # Throttle Analysis 子模組
            'throttle_box_plot': {'zh': '油門箱線圖', 'en': 'Throttle Box Plot', 'ja': 'スロットル箱ひげ図'},
            'throttle_line_chart': {'zh': '油門折線圖', 'en': 'Throttle Line Chart', 'ja': 'スロットルライン'},
            
            # Ideal Lap Analysis 主項目與子模組
            'ideal_lap_analysis': {'zh': '理想圈分析', 'en': 'Ideal Lap Analysis', 'ja': '理想ラップ分析'},
            'ideal_lap_ranking_table': {'zh': '理想圈排名表格', 'en': 'Ideal Lap Ranking Table', 'ja': '理想ラップランキングテーブル'},
            'ideal_lap_sector_heatmap': {'zh': '分段熱力圖', 'en': 'Sector Heat Map', 'ja': 'セクターヒートマップ'},
            'ideal_lap_sector_comparison': {'zh': '分段比較', 'en': 'Sector Comparison', 'ja': 'セクター比較'},
            
            # Straight Speed Analysis 主項目與子模組
            'straight_speed_analysis': {'zh': '直線速度分析(實驗)', 'en': 'Straight Speed Analysis (Experimental)', 'ja': '直線速度分析(実験)'},
            'all_drivers_straight_speed': {'zh': '全車手速度與加速(開發中)', 'en': 'All Drivers Speed & Acceleration (Dev)', 'ja': '全ドライバー速度と加速(開発中)'},
            'all_drivers_max_speed': {'zh': '全車手最高速度', 'en': 'All Drivers Max Speed', 'ja': '全ドライバー最高速度'},
            'all_drivers_brake_performance': {'zh': '全車手煞車性能(開發中)', 'en': 'All Drivers Brake Performance (Dev)', 'ja': '全ドライバーブレーキ性能(開発中)'},
            
            # Driver Position Analysis 車手比賽排名分析 (F25)
            'driver_position_analysis': {'zh': '車手比賽排名', 'en': 'Driver Race Position', 'ja': 'ドライバーレースポジション'},
            
            # Qualifying Prediction 排位賽預測分析 (F74)
            'qualifying_prediction': {'zh': '排位賽預測', 'en': 'Qualifying Prediction', 'ja': '予選予測'},
            'qualifying_prediction_table': {'zh': 'FP3 → Q 預測表格', 'en': 'FP3 → Q Prediction Table', 'ja': 'FP3 → Q 予測テーブル'},
            
            # FP2 to Qualifying Prediction FP2→Q 排位賽預測分析 (F76)
            'fp2_qualifying_prediction': {'zh': 'FP2→Q 排位賽預測', 'en': 'FP2 to Qualifying Prediction', 'ja': 'FP2→Q 予選予測'},
            'fp2_qualifying_prediction_table': {'zh': 'FP2 → Q 預測表格', 'en': 'FP2 → Q Prediction Table', 'ja': 'FP2 → Q 予測テーブル'},
            
            # Race Prediction 正賽預測分析 (F80)
            'race_prediction': {'zh': '正賽預測', 'en': 'Race Prediction', 'ja': 'レース予測'},
            'race_prediction_table': {'zh': 'Q → R 預測表格', 'en': 'Q → R Prediction Table', 'ja': 'Q → R 予測テーブル'},
            'race_prediction_title': {'zh': '正賽預測', 'en': 'Race Prediction', 'ja': 'レース予測'},
            
            # Driver Position Analysis Widget - Table Headers (F25)
            'table_header_position': {'zh': '排名', 'en': 'Position', 'ja': '順位'},
            'table_header_driver': {'zh': '車手', 'en': 'Driver', 'ja': 'ドライバー'},
            'table_header_team': {'zh': '車隊', 'en': 'Team', 'ja': 'チーム'},
            'table_header_starting_position': {'zh': '起始排名', 'en': 'Starting Position', 'ja': '開始順位'},
            'table_header_finishing_position': {'zh': '結束排名', 'en': 'Finishing Position', 'ja': '最終順位'},
            'table_header_best_position': {'zh': '最佳排名', 'en': 'Best Position', 'ja': '最高順位'},
            'table_header_worst_position': {'zh': '最差排名', 'en': 'Worst Position', 'ja': '最低順位'},
            'table_header_position_change': {'zh': '位置變化', 'en': 'Position Change', 'ja': '順位変動'},
            
            # Driver Position Analysis - Common Strings
            'unknown_team': {'zh': 'Unknown', 'en': 'Unknown', 'ja': '不明'},
            
            # Corner Performance Analysis 主項目與子模組 (F47)
            'corner_performance_analysis': {'zh': '彎道速度分析', 'en': 'Corner Performance Analysis', 'ja': 'コーナー速度分析'},
            'low_speed_corner_analysis': {'zh': '低速彎分析', 'en': 'Low-Speed Corner Analysis', 'ja': '低速コーナー分析'},
            'mid_speed_corner_analysis': {'zh': '中速彎分析', 'en': 'Mid-Speed Corner Analysis', 'ja': '中速コーナー分析'},
            'high_speed_corner_analysis': {'zh': '高速彎分析', 'en': 'High-Speed Corner Analysis', 'ja': '高速コーナー分析'},
            'low_speed_corner': {'zh': '低速彎', 'en': 'Low-Speed Corner', 'ja': '低速コーナー'},
            'mid_speed_corner': {'zh': '中速彎', 'en': 'Mid-Speed Corner', 'ja': '中速コーナー'},
            'high_speed_corner': {'zh': '高速彎', 'en': 'High-Speed Corner', 'ja': '高速コーナー'},
            'corner_type': {'zh': '彎道類型', 'en': 'Corner Type', 'ja': 'コーナータイプ'},
            'corner_performance': {'zh': '彎道性能', 'en': 'Corner Performance', 'ja': 'コーナーパフォーマンス'},
            'corner_missing_params': {'zh': '缺少必要參數', 'en': 'Missing required parameters', 'ja': '必須パラメータが不足しています'},
            'corner_data_loaded': {'zh': '彎道性能數據載入完成', 'en': 'Corner performance data loaded', 'ja': 'コーナーパフォーマンスデータ読み込み完了'},
            
            # Corner Performance Scatter Widget 圖表標籤
            'apex_speed_kmh': {'zh': '彎中心速度 (km/h)', 'en': 'Apex Speed (km/h)', 'ja': 'コーナー頂点速度 (km/h)'},
            'entry_speed_50m': {'zh': '進彎速度 (-50m) [km/h]', 'en': 'Entry Speed (-50m) [km/h]', 'ja': '進入速度 (-50m) [km/h]'},
            'exit_speed_50m': {'zh': '出彎速度 (+50m) [km/h]', 'en': 'Exit Speed (+50m) [km/h]', 'ja': '出口速度 (+50m) [km/h]'},
            'no_corner_data': {'zh': '該彎道無數據', 'en': 'No data for this corner', 'ja': 'このコーナーのデータがありません'},
            'entry_label': {'zh': '進彎', 'en': 'Entry', 'ja': '進入'},
            'apex_label': {'zh': '彎心', 'en': 'Apex', 'ja': '頂点'},
            'exit_label': {'zh': '出彎', 'en': 'Exit', 'ja': '出口'},
            'save_chart': {'zh': '儲存圖表', 'en': 'Save Chart', 'ja': 'チャート保存'},
            'chart_exported_to': {'zh': '圖表已匯出至', 'en': 'Chart exported to', 'ja': 'チャートをエクスポートしました'},
            
            # Corner Performance Loader 載入器訊息
            'corner_perf_load_param_validation_failed': {'zh': '載入參數驗證失敗', 'en': 'Load parameter validation failed', 'ja': 'ロードパラメータの検証に失敗しました'},
            'corner_perf_load_param_invalid': {'zh': '載入參數不正確', 'en': 'Invalid load parameters', 'ja': 'ロードパラメータが無効です'},
            'corner_perf_no_local_file': {'zh': '找不到本地彎道性能檔案，準備透過 API 取得最新資料', 'en': 'Local corner performance file not found, fetching latest data via API', 'ja': 'ローカルのコーナーパフォーマンスファイルが見つかりません、API経由で最新データを取得します'},
            'corner_perf_invalid_data_format': {'zh': '數據格式不正確', 'en': 'Invalid data format', 'ja': 'データ形式が無効です'},
            'corner_perf_load_success': {'zh': '彎道性能數據載入完成', 'en': 'Corner performance data loaded successfully', 'ja': 'コーナーパフォーマンスデータの読み込みが完了しました'},
            'corner_perf_fetching_api': {'zh': '正在從 API 獲取彎道性能數據...', 'en': 'Fetching corner performance data from API...', 'ja': 'APIからコーナーパフォーマンスデータを取得しています...'},
            
            # 通用錯誤訊息
            'data_empty': {'zh': '資料為空', 'en': 'Data is empty', 'ja': 'データが空です'},
            'data_processing_error': {'zh': '資料處理錯誤', 'en': 'Data processing error', 'ja': 'データ処理エラー'},
            'load_error': {'zh': '載入錯誤', 'en': 'Load Error', 'ja': '読み込みエラー'},
            
            # 通用項目
            'coming_soon': {'zh': '即將推出...', 'en': 'Coming Soon...', 'ja': '近日公開...'},
            'select_specific_module': {'zh': '請選擇具體的分析模組', 'en': 'Please select specific analysis module', 'ja': '具体的な分析モジュールを選択してください'},
            
            # 其他功能項目
            'pitstop_analysis': {'zh': '進站分析', 'en': 'Pitstop Analysis', 'ja': 'ピットストップ分析'},
            'driver_ranking': {'zh': '車手排名', 'en': 'Driver Ranking', 'ja': 'ドライバーランキング'},
            'tire_strategy_analysis': {'zh': '輪胎策略分析', 'en': 'Tire Strategy Analysis', 'ja': 'タイヤ戦略分析'},
            'detailed_lap_analysis': {'zh': '詳細圈速分析', 'en': 'Detailed Lap Analysis', 'ja': '詳細ラップ分析'},
            
            # Championship Standings (錦標賽積分榜)
            'driver_standings_title_with_round': {'zh': '車手積分榜 - {year} 第 {round} 站', 'en': 'Driver Standings - {year} Round {round}', 'ja': 'ドライバーランキング - {year} 第{round}戦'},
            'constructor_standings_title_with_round': {'zh': '車隊積分榜 - {year} 第 {round} 站', 'en': 'Constructor Standings - {year} Round {round}', 'ja': 'コンストラクターランキング - {year} 第{round}戦'},
            'season_progress_title': {'zh': '賽季進度 - {year}', 'en': 'Season Progress - {year}', 'ja': 'シーズン進行状況 - {year}'},
            
            # Season Progress Widget - Group Titles
            'season_summary_group': {'zh': '賽季總結', 'en': 'Season Summary', 'ja': 'シーズンサマリー'},
            'current_leaders_group': {'zh': '目前領先者', 'en': 'Current Leaders', 'ja': '現在のリーダー'},
            
            # Season Progress Widget - Race Statistics
            'completed_races': {'zh': '已完成賽事：{count} / {total}', 'en': 'Completed Races: {count} / {total}', 'ja': '完了レース：{count} / {total}'},
            'remaining_races': {'zh': '剩餘賽事：{count}', 'en': 'Remaining Races: {count}', 'ja': '残りレース：{count}'},
            'next_race': {'zh': '下一場賽事：{name}', 'en': 'Next Race: {name}', 'ja': '次のレース：{name}'},
            'race_date': {'zh': '日期：{date}', 'en': 'Date: {date}', 'ja': '日付：{date}'},
            'no_upcoming_races': {'zh': '賽季已完成', 'en': 'Season Completed', 'ja': 'シーズン終了'},
            
            # Season Progress Widget - Championship Leaders
            'driver_leader': {'zh': '車手領先者：{name} ({team}) - {points} 分', 'en': 'Driver Leader: {name} ({team}) - {points} pts', 'ja': 'ドライバーリーダー：{name} ({team}) - {points} pts'},
            'constructor_leader': {'zh': '車隊領先者：{name} - {points} 分', 'en': 'Constructor Leader: {name} - {points} pts', 'ja': 'コンストラクターリーダー：{name} - {points} pts'},
            
            # Standings Table Columns (積分榜表格欄位)
            'standings_col_position': {'zh': '名次', 'en': 'Pos', 'ja': '順位'},
            'standings_col_driver_code': {'zh': '代碼', 'en': 'Code', 'ja': 'コード'},
            'standings_col_driver': {'zh': '車手', 'en': 'Driver', 'ja': 'ドライバー'},
            'standings_col_team': {'zh': '車隊', 'en': 'Team', 'ja': 'チーム'},
            'standings_col_constructor': {'zh': '車隊', 'en': 'Constructor', 'ja': 'コンストラクター'},
            'standings_col_points': {'zh': '積分', 'en': 'Points', 'ja': 'ポイント'},
            'standings_col_wins': {'zh': '勝場', 'en': 'Wins', 'ja': '勝利数'},
            'standings_col_delta': {'zh': '落後差', 'en': 'Gap', 'ja': '差分'},
            
            # Season Progress Module (賽季進度模組)
            'menu_analysis': {'zh': '分析', 'en': 'Analysis', 'ja': '分析'},
            'menu_driver_standings': {'zh': '車手積分榜', 'en': 'Driver Standings', 'ja': 'ドライバーランキング'},
            'menu_constructor_standings': {'zh': '車隊積分榜', 'en': 'Constructor Standings', 'ja': 'コンストラクターランキング'},
            'menu_season_progress': {'zh': '賽季進度總覽', 'en': 'Season Progress', 'ja': 'シーズン進行状況'},
            
            # Live Timing Module (即時計時模組)
            'menu_live_timing': {'zh': 'Live Timing', 'en': 'Live Timing', 'ja': 'Live Timing'},
            'menu_live_timing_control_panel': {'zh': '顯示控制面板', 'en': 'Show Control Panel', 'ja': 'コントロールパネルを表示'},
            'menu_live_timing_track_map': {'zh': '賽道地圖', 'en': 'Track Map', 'ja': 'トラックマップ'},
            'menu_live_timing_circle_map': {'zh': '圓形地圖', 'en': 'Circle Map', 'ja': 'サークルマップ'},
            'menu_live_timing_ranking': {'zh': '即時排名', 'en': 'Live Ranking', 'ja': 'ライブランキング'},
            'menu_live_timing_pit_window': {'zh': 'Pit Window', 'en': 'Pit Window', 'ja': 'ピットウィンドウ'},
            'menu_live_timing_tyre_strategy': {'zh': '輪胎策略', 'en': 'Tyre Strategy', 'ja': 'タイヤ戦略'},
            'menu_live_timing_driver_strategy': {'zh': '車手策略', 'en': 'Driver Strategy', 'ja': 'ドライバー戦略'},
            'live_timing_driver_strategy_tip': {'zh': '開啟車手策略分析', 'en': 'Open Driver Strategy Analysis', 'ja': 'ドライバー戦略分析を開く'},
            'menu_live_timing_chase_strategy': {'zh': '追趕策略', 'en': 'Chase Strategy', 'ja': '追撃戦略'},
            'chase_strategy_tip': {'zh': '分析 P2 追趕 P1 的策略可行性', 'en': 'Analyze P2 to P1 chase strategy feasibility', 'ja': 'P2からP1への追撃戦略の実現可能性を分析'},
            'menu_live_timing_race_control': {'zh': '比賽控制訊息', 'en': 'Race Control Messages', 'ja': 'レースコントロールメッセージ'},
            'menu_live_timing_race_insights': {'zh': '賽況提示', 'en': 'Race Insights', 'ja': 'レースインサイト'},
            'menu_live_timing_shap_analysis': {'zh': 'SHAP 分析', 'en': 'SHAP Analysis', 'ja': 'SHAP分析'},
            'menu_live_timing_lap_distribution': {'zh': '圈速分佈', 'en': 'Lap Time Distribution', 'ja': 'ラップタイム分布'},
            'menu_live_timing_pit_stop_table': {'zh': '進站統計', 'en': 'Pit Stop Statistics', 'ja': 'ピットストップ統計'},
            'menu_live_timing_presets': {'zh': '預設佈局', 'en': 'Preset Layouts', 'ja': 'プリセットレイアウト'},
            'menu_live_timing_preset_full': {'zh': '完整佈局', 'en': 'Full Layout', 'ja': 'フルレイアウト'},
            'menu_live_timing_preset_compact': {'zh': '精簡佈局', 'en': 'Compact Layout', 'ja': 'コンパクトレイアウト'},
            'menu_live_timing_preset_strategy': {'zh': '策略佈局', 'en': 'Strategy Layout', 'ja': '戦略レイアウト'},
            'menu_live_timing_close_all': {'zh': '關閉所有 Live Timing 視窗', 'en': 'Close All Live Timing Windows', 'ja': 'すべてのLive Timingウィンドウを閉じる'},
            'live_timing_coming_soon': {'zh': '開發中', 'en': 'Coming Soon', 'ja': '開発中'},
            
            # Live Timing 樹狀圖項目
            'live_timing_tree': {'zh': 'Live Timing', 'en': 'Live Timing', 'ja': 'Live Timing'},
            'live_timing_track_map': {'zh': '賽道地圖', 'en': 'Track Map', 'ja': 'トラックマップ'},
            'live_timing_circle_map': {'zh': '圓形地圖', 'en': 'Circle Map', 'ja': 'サークルマップ'},
            'live_timing_ranking': {'zh': '即時排名', 'en': 'Live Ranking', 'ja': 'ライブランキング'},
            'live_timing_pit_window': {'zh': 'Pit Window', 'en': 'Pit Window', 'ja': 'ピットウィンドウ'},
            'live_timing_tyre_strategy': {'zh': '輪胎策略', 'en': 'Tyre Strategy', 'ja': 'タイヤ戦略'},
            'live_timing_driver_strategy': {'zh': '車手策略', 'en': 'Driver Strategy', 'ja': 'ドライバー戦略'},
            'live_timing_chase_strategy': {'zh': '追趕策略', 'en': 'Chase Strategy', 'ja': '追撃戦略'},
            'live_timing_race_control': {'zh': '比賽控制訊息', 'en': 'Race Control Messages', 'ja': 'レースコントロールメッセージ'},
            'live_timing_race_insights': {'zh': '賽況提示', 'en': 'Race Insights', 'ja': 'レースインサイト'},
            'live_timing_shap_analysis': {'zh': 'SHAP 分析', 'en': 'SHAP Analysis', 'ja': 'SHAP分析'},
            'live_timing_lap_distribution': {'zh': '圈速分佈', 'en': 'Lap Time Distribution', 'ja': 'ラップタイム分布'},
            'live_timing_pit_stop_table': {'zh': '進站統計', 'en': 'Pit Stop Statistics', 'ja': 'ピットストップ統計'},
            
            # Driver Strategy 翻譯
            'driver_strategy_title': {'zh': '車手策略', 'en': 'Driver Strategy', 'ja': 'ドライバー戦略'},
            'right_click_select_driver': {'zh': '右鍵點擊選擇車手', 'en': 'Right-click to select driver', 'ja': '右クリックでドライバーを選択'},
            'Predicted': {'zh': '預測', 'en': 'Predicted', 'ja': '予測'},
            'SC/VSC': {'zh': 'SC/VSC', 'en': 'SC/VSC', 'ja': 'SC/VSC'},
            'PIT Est.': {'zh': 'PIT 預估', 'en': 'PIT Est.', 'ja': 'PIT 予測'},
            'Soft Strategy': {'zh': '軟胎策略', 'en': 'Soft Strategy', 'ja': 'ソフト戦略'},
            'Medium Strategy': {'zh': '中性胎策略', 'en': 'Medium Strategy', 'ja': 'ミディアム戦略'},
            'Hard Strategy': {'zh': '硬胎策略', 'en': 'Hard Strategy', 'ja': 'ハード戦略'},
            
            # Live Ranking Tower 翻譯
            'fuel_save': {'zh': 'SF%', 'en': 'SF%', 'ja': 'SF%'},
            
            # Live Ranking 右鍵選單項目
            'modify_pit_windows': {'zh': '修改 Pit Window 參數', 'en': 'Modify Pit Window Parameters', 'ja': 'ピットウィンドウパラメータを変更'},
            'set_pit_window_reference': {'zh': '設定為 Pit Window 參考', 'en': 'Set as Pit Window Reference', 'ja': 'ピットウィンドウ参照に設定'},
            'optimal_stint_soft': {'zh': 'SOFT 最佳 Stint: {0} 圈', 'en': 'SOFT Optimal Stint: {0} laps', 'ja': 'SOFT 最適スティント: {0} 周'},
            'optimal_stint_medium': {'zh': 'MEDIUM 最佳 Stint: {0} 圈', 'en': 'MEDIUM Optimal Stint: {0} laps', 'ja': 'MEDIUM 最適スティント: {0} 周'},
            'optimal_stint_hard': {'zh': 'HARD 最佳 Stint: {0} 圈', 'en': 'HARD Optimal Stint: {0} laps', 'ja': 'HARD 最適スティント: {0} 周'},
            'modify_optimal_stint_title': {'zh': '修改 {0} 最佳 Stint', 'en': 'Modify {0} Optimal Stint', 'ja': '{0} 最適スティントを変更'},
            'modify_optimal_stint_prompt': {'zh': '請輸入 {0} 胎的最佳 Stint 圈數:', 'en': 'Enter optimal stint laps for {0} compound:', 'ja': '{0} タイヤの最適スティント周回数を入力してください:'},
            'optimal_stint_updated': {'zh': '{0} 最佳 Stint 已更新為 {1} 圈', 'en': '{0} optimal stint updated to {1} laps', 'ja': '{0} 最適スティントが {1} 周に更新されました'},
            
            # Pit Window 右鍵選單項目
            'reset_to_p1': {'zh': '重設為 P1', 'en': 'Reset to P1', 'ja': 'P1にリセット'},
            'select_driver_action': {'zh': '選擇 {0}', 'en': 'Select {0}', 'ja': '{0} を選択'},
            'modify_pit_loss_time': {'zh': '修改 Pit Loss 時間', 'en': 'Modify Pit Loss Time', 'ja': 'ピットロスタイムを変更'},
            'pit_loss_green': {'zh': 'GREEN: {0:.1f}s', 'en': 'GREEN: {0:.1f}s', 'ja': 'GREEN: {0:.1f}s'},
            'pit_loss_sc': {'zh': 'SC: {0:.1f}s', 'en': 'SC: {0:.1f}s', 'ja': 'SC: {0:.1f}s'},
            'pit_loss_vsc': {'zh': 'VSC: {0:.1f}s', 'en': 'VSC: {0:.1f}s', 'ja': 'VSC: {0:.1f}s'},
            'modify_pit_loss_green_title': {'zh': '修改 GREEN Pit Loss', 'en': 'Modify GREEN Pit Loss', 'ja': 'GREEN ピットロスを変更'},
            'modify_pit_loss_green_prompt': {'zh': '請輸入綠旗狀態的進站損失時間 (秒):', 'en': 'Enter pit loss time for GREEN flag (seconds):', 'ja': 'グリーンフラッグ時のピットロスタイム (秒) を入力:'},
            'modify_pit_loss_sc_title': {'zh': '修改 SC Pit Loss', 'en': 'Modify SC Pit Loss', 'ja': 'SC ピットロスを変更'},
            'modify_pit_loss_sc_prompt': {'zh': '請輸入安全車狀態的進站損失時間 (秒):', 'en': 'Enter pit loss time for Safety Car (seconds):', 'ja': 'セーフティカー時のピットロスタイム (秒) を入力:'},
            'modify_pit_loss_vsc_title': {'zh': '修改 VSC Pit Loss', 'en': 'Modify VSC Pit Loss', 'ja': 'VSC ピットロスを変更'},
            'modify_pit_loss_vsc_prompt': {'zh': '請輸入虛擬安全車狀態的進站損失時間 (秒):', 'en': 'Enter pit loss time for Virtual Safety Car (seconds):', 'ja': 'バーチャルセーフティカー時のピットロスタイム (秒) を入力:'},
            'waiting_for_data': {'zh': '等待數據...', 'en': 'Waiting for data...', 'ja': 'データ待機中...'},
            
            # Chase Strategy 追趕策略模組
            'chase_strategy': {'zh': '追趕策略', 'en': 'Chase Strategy', 'ja': '追撃戦略'},
            'refresh_strategy': {'zh': '刷新策略', 'en': 'Refresh', 'ja': '更新'},
            'active_simulation': {'zh': '主動模擬', 'en': 'Active Simulation', 'ja': 'シミュレーション'},
            'active_simulation_title': {'zh': '主動進站模擬', 'en': 'Active Pit Simulation', 'ja': 'ピットシミュレーション'},
            'pit_lap': {'zh': '進站圈數', 'en': 'Pit Lap', 'ja': 'ピット周'},
            'target_compound': {'zh': '目標輪胎', 'en': 'Target Compound', 'ja': 'ターゲットタイヤ'},
            'strategy_name': {'zh': '策略名稱', 'en': 'Strategy', 'ja': '戦略'},
            'feasible': {'zh': '可行性', 'en': 'Feasible', 'ja': '実現可能'},
            'catchup_lap': {'zh': '追上圈數', 'en': 'Catchup Lap', 'ja': '追い上げ周'},
            'total_advantage': {'zh': '總優勢', 'en': 'Advantage', 'ja': 'アドバンテージ'},
            'drs_required': {'zh': 'DRS 需求', 'en': 'DRS Needed', 'ja': 'DRS必要'},
            'rating': {'zh': '推薦度', 'en': 'Rating', 'ja': '評価'},
            'strategy_tire_age': {'zh': '繼續當前輪胎', 'en': 'Continue Current Tyres', 'ja': '現在のタイヤを継続'},
            'strategy_undercut': {'zh': '立即進站 Undercut', 'en': 'Immediate Pit (Undercut)', 'ja': '即時ピット (アンダーカット)'},
            'strategy_sc_opportunity': {'zh': '等待安全車機會', 'en': 'Wait for Safety Car', 'ja': 'セーフティカー待ち'},
            'strategy_active_pit': {'zh': '主動進站模擬', 'en': 'Active Pit Simulation', 'ja': 'ピットシミュレーション'},
            'strategy_both_pit': {'zh': '雙重進站分析', 'en': 'Both Pit Scenario', 'ja': '両者ピットシナリオ'},
            'strategy_no_tire_advantage': {'zh': '無輪胎齡優勢', 'en': 'No tyre age advantage', 'ja': 'タイヤ年齢のアドバンテージなし'},
            'strategy_not_enough_laps': {'zh': '剩餘圈數不足', 'en': 'Not enough laps remaining', 'ja': '残り周回数不足'},
            'strategy_undercut_fail': {'zh': '進站損失過大', 'en': 'Pit loss too high', 'ja': 'ピットロスが大きすぎる'},
            'strategy_not_configured': {'zh': '未設定 - 請使用主動模擬按鈕', 'en': 'Not configured - use Active Simulation button', 'ja': '未設定 - シミュレーションボタンを使用'},
            'strategy_age_diff': {'zh': '輪胎齡差', 'en': 'Tyre age diff', 'ja': 'タイヤ年齢差'},
            'strategy_pit_loss': {'zh': '進站損失', 'en': 'Pit loss', 'ja': 'ピットロス'},
            'strategy_pit_saving': {'zh': 'SC 進站節省', 'en': 'SC pit saving', 'ja': 'SCピット節約'},
            'strategy_pit_at': {'zh': '第 {0} 圈進站', 'en': 'Pit at lap', 'ja': '周目にピット'},
            'both_pit_analysis': {'zh': '雙重進站情境分析', 'en': 'Both Pit Scenario Analysis', 'ja': '両者ピットシナリオ分析'},
            'pits_first': {'zh': '先進站', 'en': 'pits first', 'ja': '先にピット'},
            'leads': {'zh': '領先', 'en': 'leads', 'ja': 'リード'},
            'same_lap_pit': {'zh': '同圈進站', 'en': 'Same lap pit', 'ja': '同周ピット'},
            'gap_unchanged': {'zh': '差距維持', 'en': 'Gap unchanged', 'ja': 'ギャップ維持'},
            'laps': {'zh': '圈', 'en': 'laps', 'ja': '周'},
            'lap': {'zh': '圈', 'en': 'Lap', 'ja': '周'},
            'gap': {'zh': '差距', 'en': 'Gap', 'ja': 'ギャップ'},
            'no_data': {'zh': '無數據', 'en': 'No data available', 'ja': 'データなし'},
            'select_drivers': {'zh': '請選擇 P1 和 P2', 'en': 'Please select P1 and P2', 'ja': 'P1とP2を選択してください'},
            'driver_not_found': {'zh': '找不到選中的車手', 'en': 'Selected driver not found', 'ja': '選択したドライバーが見つかりません'},
            'show_details': {'zh': '顯示詳情', 'en': 'Show Details', 'ja': '詳細を表示'},
            'hide_details': {'zh': '隱藏詳情', 'en': 'Hide Details', 'ja': '詳細を非表示'},
            
            # 歡迎頁面
            'main_title': {'zh': 'PIT WALL', 'en': 'PIT WALL', 'ja': 'PIT WALL'},
            'subtitle': {'zh': '專業級 F1 數據分析平台', 'en': 'Professional F1 Data Analysis Platform', 'ja': 'Professional F1 Data Analysis Platform'},
            'welcome_info': {'zh': ' 左鍵選擇模組 • 右鍵執行分析 • 支援 Ctrl/Shift 多選批量分析 • Version 0.0', 'en': ' Left click to select module • Right click to execute analysis • Support Ctrl/Shift multi-select batch analysis • Version 0.0', 'ja': ' Left click to select module • Right click to execute analysis • Support Ctrl/Shift multi-select batch analysis • Version 0.0'},
            
            # 統計和數據
            'statistics_data': {'zh': '統計數據', 'en': 'Statistics Data', 'ja': 'Statistics Data'},
            'season_statistics': {'zh': '[CHART] 賽季統計數據\n• 總圈數: 1,247\n• 平均圈速: 1:18.456\n• 最快圈速: 1:16.123', 'en': '[CHART] Season Statistics\n• Total Laps: 1,247\n• Average Lap Time: 1:18.456\n• Fastest Lap: 1:16.123', 'ja': '[CHART] Season Statistics\n• Total Laps: 1,247\n• Average Lap Time: 1:18.456\n• Fastest Lap: 1:16.123'},
            'data_overview': {'zh': '[STATS] 數據總覽', 'en': '[STATS] Data Overview', 'ja': '[STATS] Data Overview'},
            
            # === 賽程日曆相關 (Race Calendar) ===
            # 未開賽賽事後綴標籤（用於賽事下拉選單）
            'season_calendar_upcoming_suffix': {'zh': '[未開賽]', 'en': '[Upcoming]', 'ja': '[未開催]'},
            
            # 統計卡片
            'track_limit_violations': {'zh': ' Track Limit', 'en': ' Track Limit', 'ja': ' Track Limit'},
            'double_yellow_flag': {'zh': ' 雙黃旗', 'en': ' Double Yellow', 'ja': ' Double Yellow'},
            'yellow_flag': {'zh': ' 黃旗', 'en': ' Yellow Flag', 'ja': ' Yellow Flag'},
            'red_flag': {'zh': ' 紅旗', 'en': ' Red Flag', 'ja': ' Red Flag'},
            'fastest_driver': {'zh': '最快車手', 'en': 'Fastest Driver', 'ja': 'Fastest Driver'},
            'avg_laptime': {'zh': '平均圈速', 'en': 'Avg Lap Time', 'ja': 'Avg Lap Time'},
            'violations_count': {'zh': '(違規次數)', 'en': '(Violations)', 'ja': '(Violations)'},
            'display_count': {'zh': '(出示次數)', 'en': '(Displayed)', 'ja': '(Displayed)'},
            
            # 圖表軸標籤
            'lap_number_axis': {'zh': '圈數 (Lap)', 'en': 'Lap Number', 'ja': 'Lap Number'},
            'track_temperature': {'zh': '賽道溫度 (°C)', 'en': 'Track Temperature (°C)', 'ja': 'Track Temperature (°C)'},
            'air_track_temp_comparison': {'zh': '氣溫與賽道溫度對比', 'en': 'Air vs Track Temperature', 'ja': 'Air vs Track Temperature'},
            
            # 分頁標籤
            'driver_fastest_pitstop_ranking': {'zh': ' 車手最快進站排行榜', 'en': ' Driver Fastest Pitstop Ranking', 'ja': ' Driver Fastest Pitstop Ranking'},
            'team_pitstop_statistics': {'zh': ' 車隊進站統計', 'en': ' Team Pitstop Statistics', 'ja': ' Team Pitstop Statistics'},
            'detailed_records': {'zh': ' 詳細記錄', 'en': ' Detailed Records', 'ja': ' Detailed Records'},
            
            # 圖表控制
            'select_chart': {'zh': '選擇圖表:', 'en': 'Select Chart:', 'ja': 'Select Chart:'},
            'chart_type': {'zh': '圖表類型', 'en': 'Chart Type', 'ja': 'チャートタイプ'},
            
            # 降雨分析圖表選項
            'main_chart_rain_temperature': {'zh': '主要圖表 (降雨+氣溫)', 'en': 'Main Chart (Rain+Temperature)', 'ja': 'Main Chart (Rain+Temperature)'},
            'temperature_comparison_air_track': {'zh': '溫度對比 (氣溫vs賽道溫度)', 'en': 'Temperature Comparison (Air vs Track)', 'ja': 'Temperature Comparison (Air vs Track)'},
            'humidity_windspeed': {'zh': '濕度風速 (濕度+風速)', 'en': 'Humidity & Wind Speed', 'ja': 'Humidity & Wind Speed'},
            'pressure_changes': {'zh': '氣壓變化', 'en': 'Pressure Changes', 'ja': 'Pressure Changes'},
            
            # 降雨分析顯示選項
            'display_options': {'zh': '顯示選項', 'en': 'Display Options', 'ja': '表示オプション'},
            'show_grid_checkbox': {'zh': '顯示網格', 'en': 'Show Grid', 'ja': 'グリッド表示'},
            'show_legend_checkbox': {'zh': '顯示圖例', 'en': 'Show Legend', 'ja': '凡例表示'},
            
            # Window management controls
            'close_all_windows': {'zh': '關閉所有視窗', 'en': 'Close All Windows', 'ja': 'すべてのウィンドウを閉じる'},
            'show_all_data': {'zh': '顯示所有資料', 'en': 'Show All Data', 'ja': '全データ表示'},
            
            # Rain analysis specific axis labels
            'temperature_celsius': {'zh': '溫度 (°C)', 'en': 'Temperature (°C)', 'ja': 'Temperature (°C)'},
            'lap_number_rain': {'zh': '圈數', 'en': 'Lap Number', 'ja': 'Lap Number'},
            
            # Driver Overview
            'driver_overview': {'zh': '車手概覽', 'en': 'Driver Overview', 'ja': 'Driver Overview'},
            
            # ============================================================
            # 新增：完整英文化翻譯鍵值（200+ 項）
            # ============================================================
            
            # 錯誤訊息
            'json_load_failed': {'zh': 'JSON檔案載入失敗', 'en': 'Failed to load JSON file', 'ja': 'JSONファイルの読み込みに失敗しました'},
            'file_search_error': {'zh': '搜尋檔案時發生錯誤', 'en': 'Error occurred while searching files', 'ja': 'ファイル検索中にエラーが発生しました'},
            'data_processing_failed': {'zh': '數據處理失敗', 'en': 'Data processing failed', 'ja': 'データ処理に失敗しました'},
            'cli_analysis_failed': {'zh': 'CLI 分析失敗', 'en': 'CLI analysis failed', 'ja': 'CLI分析に失敗しました'},
            'encoding_error': {'zh': '編碼錯誤', 'en': 'Encoding error', 'ja': 'エンコーディングエラー'},
            'unable_to_decode': {'zh': '無法解碼部分輸出', 'en': 'Unable to decode partial output', 'ja': '出力の一部をデコードできません'},
            'cli_execution_error': {'zh': 'CLI執行異常', 'en': 'CLI execution exception', 'ja': 'CLI execution exception'},
            'load_failed': {'zh': '載入失敗', 'en': 'Load failed', 'ja': '読み込みに失敗しました'},
            'search_telemetry_file_error': {'zh': '搜尋遙測檔案時發生錯誤', 'en': 'Error searching telemetry files', 'ja': 'Error searching telemetry files'},
            'chart_update_failed': {'zh': '圖表更新失敗', 'en': 'Chart update failed', 'ja': 'チャート更新に失敗しました'},
            'parameter_update_failed': {'zh': '參數更新失敗', 'en': 'Parameter update failed', 'ja': 'パラメーター更新に失敗しました'},
            'lap_parameter_update_failed': {'zh': '圈速參數更新失敗', 'en': 'Lap parameter update failed', 'ja': 'Lap parameter update failed'},
            
            # 進度和狀態訊息
            'loading_data': {'zh': '正在載入數據...', 'en': 'Loading data...', 'ja': 'データ読み込み中...'},
            'processing': {'zh': '處理中...', 'en': 'Processing...', 'ja': '処理中...'},
            'generating_data': {'zh': '正在生成數據...', 'en': 'Generating data...', 'ja': 'データ生成中...'},
            'starting_generation': {'zh': '啟動生成時發生錯誤', 'en': 'Error starting generation', 'ja': 'Error starting generation'},
            'generation_timeout': {'zh': 'JSON等待超時', 'en': 'JSON wait timeout', 'ja': 'JSON wait timeout'},
            'data_validation_failed': {'zh': '數據格式驗證失敗', 'en': 'Data format validation failed', 'ja': 'Data format validation failed'},
            
            # 視窗控制
            'cascade_windows': {'zh': '層疊視窗', 'en': 'Cascade Windows', 'ja': 'ウィンドウを重ねて表示'},
            'tile_windows': {'zh': '平舖視窗', 'en': 'Tile Windows', 'ja': 'ウィンドウを並べて表示'},
            'close_window': {'zh': '關閉視窗', 'en': 'Close Window', 'ja': 'ウィンドウを閉じる'},
            'restore_normal_size': {'zh': '恢復正常大小', 'en': 'Restore Normal Size', 'ja': 'Restore Normal Size'},
            'minimize': {'zh': '最小化', 'en': 'Minimize', 'ja': 'Minimize'},
            'maximize': {'zh': '最大化', 'en': 'Maximize', 'ja': 'Maximize'},
            'maximize_restore': {'zh': '最大化/還原', 'en': 'Maximize/Restore', 'ja': 'Maximize/Restore'},
            'popout': {'zh': '彈出為獨立視窗', 'en': 'Pop Out as Independent Window', 'ja': 'Pop Out as Independent Window'},
            'window_settings': {'zh': '視窗設定', 'en': 'Window Settings', 'ja': 'Window Settings'},
            'forced_close_gui': {'zh': 'F1 TelemetryStation Pro GUI 已強制關閉', 'en': 'F1 TelemetryStation Pro GUI has been force closed', 'ja': 'F1 TelemetryStation Pro GUI has been force closed'},
            
            # Tab Context Menu
            'tab_popout_menu': {'zh': '彈出為獨立視窗', 'en': 'Pop Out as Independent Window', 'ja': '独立ウィンドウとして表示'},
            'tab_return_menu': {'zh': '返回主視窗', 'en': 'Return to Main Window', 'ja': 'メインウィンドウに戻す'},
            'tab_rename_menu': {'zh': '重新命名分頁', 'en': 'Rename Tab', 'ja': 'タブ名を変更'},
            'tab_already_popped': {'zh': '已彈出為獨立視窗', 'en': 'Already popped out as independent window', 'ja': '既に独立ウィンドウとして表示されています'},
            'home_tab_no_popout': {'zh': 'HOME 主頁不支援彈出功能', 'en': 'HOME page does not support pop-out', 'ja': 'HOMEページはポップアウトをサポートしていません'},
            'home_tab_no_rename': {'zh': 'HOME 主頁不支援重新命名', 'en': 'HOME page cannot be renamed', 'ja': 'HOMEページの名前は変更できません'},
            'tab_popout_success': {'zh': '分頁 {index} 已成功彈出', 'en': 'Tab {index} successfully popped out', 'ja': 'タブ {index} を独立ウィンドウとして表示しました'},
            'tab_return_success': {'zh': '分頁 {index} 已返回主視窗', 'en': 'Tab {index} returned to main window', 'ja': 'タブ {index} をメインウィンドウに戻しました'},
            'tab_not_popped': {'zh': '分頁 {index} 未彈出或已返回', 'en': 'Tab {index} not popped out or already returned', 'ja': 'タブ {index} はポップアウトされていないか既に戻されています'},
            'tab_starting_popout': {'zh': '開始彈出分頁 {index}: {name}', 'en': 'Starting to pop out tab {index}: {name}', 'ja': 'タブ {index} のポップアウトを開始: {name}'},
            'tab_starting_return': {'zh': '開始返回分頁 {index}', 'en': 'Starting to return tab {index}', 'ja': 'タブ {index} の復帰を開始'},
            'tab_placeholder_label': {'zh': '{name} 已彈出為獨立視窗', 'en': '{name} popped out as independent window', 'ja': '{name} を独立ウィンドウとして表示中'},
            'tab_rename_dialog_title': {'zh': '重新命名分頁', 'en': 'Rename Tab', 'ja': 'タブ名を変更'},
            'tab_rename_dialog_label': {'zh': '請輸入新的分頁名稱:', 'en': 'Enter new tab name:', 'ja': '新しいタブ名を入力:'},
            'tab_rename_success': {'zh': '分頁 {index} 已重新命名為: {name}', 'en': 'Tab {index} renamed to: {name}', 'ja': 'タブ {index} の名前を変更: {name}'},
            
            # Workspace Dialog
            'load_workspace_title': {'zh': '載入 Workspace', 'en': 'Load Workspace', 'ja': 'ワークスペース読込'},
            'available_workspaces': {'zh': '可用的 Workspace', 'en': 'Available Workspaces', 'ja': '利用可能なワークスペース'},
            'workspace_details': {'zh': 'Workspace 詳細資訊', 'en': 'Workspace Details', 'ja': 'ワークスペース詳細'},
            'workspace_search': {'zh': '搜尋:', 'en': 'Search:', 'ja': '検索:'},
            'search_placeholder': {'zh': '輸入關鍵字搜尋（名稱、描述、標籤）', 'en': 'Enter keywords to search (name, description, tags)', 'ja': 'キーワードを入力して検索（名前、説明、タグ）'},
            'refresh': {'zh': '重新整理', 'en': 'Refresh', 'ja': '更新'},
            'workspace_id': {'zh': 'ID', 'en': 'ID', 'ja': 'ID'},
            'workspace_name': {'zh': '名稱', 'en': 'Name', 'ja': '名前'},
            'tab_count': {'zh': '分頁數', 'en': 'Tabs', 'ja': 'タブ数'},
            'window_count': {'zh': '視窗數', 'en': 'Windows', 'ja': 'ウィンドウ数'},
            'created_time': {'zh': '建立時間', 'en': 'Created', 'ja': '作成日時'},
            'description': {'zh': '描述', 'en': 'Description', 'ja': '説明'},
            'preview_placeholder': {'zh': '請選擇一個 Workspace 查看詳細資訊...', 'en': 'Please select a Workspace to view details...', 'ja': 'ワークスペースを選択して詳細を表示...'},
            'load_workspace_btn': {'zh': '載入 Workspace', 'en': 'Load Workspace', 'ja': 'ワークスペース読込'},
            'delete': {'zh': '刪除', 'en': 'Delete', 'ja': '削除'},
            'load_failed': {'zh': '載入失敗', 'en': 'Load Failed', 'ja': '読込失敗'},
            'load_workspaces_error': {'zh': '無法載入 Workspace 列表：{error}', 'en': 'Failed to load workspace list: {error}', 'ja': 'ワークスペースリストの読込に失敗: {error}'},
            'workspace_loaded_count': {'zh': '載入 {count} 個 Workspace', 'en': 'Loaded {count} workspaces', 'ja': '{count} 個のワークスペースを読込'},
            'search_results': {'zh': '搜尋結果: {count} 個', 'en': 'Search results: {count}', 'ja': '検索結果: {count} 個'},
            'preview_name': {'zh': '名稱: {name}', 'en': 'Name: {name}', 'ja': '名前: {name}'},
            'preview_id': {'zh': 'ID: {id}', 'en': 'ID: {id}', 'ja': 'ID: {id}'},
            'preview_created': {'zh': '建立時間: {time}', 'en': 'Created: {time}', 'ja': '作成日時: {time}'},
            'preview_modified': {'zh': '修改時間: {time}', 'en': 'Modified: {time}', 'ja': '更新日時: {time}'},
            'preview_tags': {'zh': '標籤: {tags}', 'en': 'Tags: {tags}', 'ja': 'タグ: {tags}'},
            'preview_statistics': {'zh': '統計:', 'en': 'Statistics:', 'ja': '統計:'},
            'preview_total_tabs': {'zh': '  總分頁數: {count}', 'en': '  Total tabs: {count}', 'ja': '  タブ総数: {count}'},
            'preview_total_windows': {'zh': '  總視窗數: {count}', 'en': '  Total windows: {count}', 'ja': '  ウィンドウ総数: {count}'},
            'preview_tab_details': {'zh': '分頁詳情:', 'en': 'Tab details:', 'ja': 'タブ詳細:'},
            'preview_tab_entry': {'zh': '  {index}. {name}{status} - {count} 個視窗', 'en': '  {index}. {name}{status} - {count} windows', 'ja': '  {index}. {name}{status} - {count} ウィンドウ'},
            'preview_popped_out': {'zh': ' [彈出]', 'en': ' [Popped out]', 'ja': ' [ポップアウト]'},
            'confirm_load_workspace': {'zh': '確定要載入 Workspace \'{name}\' 嗎？\n\n這將會替換當前所有分頁和視窗。\n\n• 分頁數: {tabs}\n• 視窗數: {windows}\n\n 當前未儲存的變更將會遺失！', 'en': 'Are you sure you want to load workspace \'{name}\'?\n\nThis will replace all current tabs and windows.\n\n• Tabs: {tabs}\n• Windows: {windows}\n\n Unsaved changes will be lost!', 'ja': 'ワークスペース \'{name}\' を読み込みますか？\n\n現在のすべてのタブとウィンドウが置き換えられます。\n\n• タブ数: {tabs}\n• ウィンドウ数: {windows}\n\n 未保存の変更は失われます！'},
            'confirm_delete_workspace': {'zh': '確定要刪除 Workspace \'{name}\' 嗎？\n\n 此操作無法復原！', 'en': 'Are you sure you want to delete workspace \'{name}\'?\n\n This operation cannot be undone!', 'ja': 'ワークスペース \'{name}\' を削除しますか？\n\n この操作は元に戻せません！'},
            'confirm_delete_multiple_workspaces': {'zh': '確定要刪除 {count} 個 Workspace 嗎？\n\n將刪除以下項目：\n  • {names}\n\n 此操作無法復原！', 'en': 'Are you sure you want to delete {count} workspaces?\n\nThe following items will be deleted:\n  • {names}\n\n This operation cannot be undone!', 'ja': '{count} 個のワークスペースを削除しますか？\n\n次の項目が削除されます：\n  • {names}\n\n この操作は元に戻せません！'},
            'delete_success': {'zh': '刪除成功', 'en': 'Delete Successful', 'ja': '削除成功'},
            'workspace_deleted': {'zh': 'Workspace \'{name}\' 已刪除', 'en': 'Workspace \'{name}\' has been deleted', 'ja': 'ワークスペース \'{name}\' を削除しました'},
            'workspaces_deleted_success': {'zh': '已成功刪除 {count} 個 Workspace', 'en': 'Successfully deleted {count} workspaces', 'ja': '{count} 個のワークスペースを削除しました'},
            'workspaces_deleted_partial': {'zh': '刪除完成：成功 {success} 個，失敗 {failed} 個', 'en': 'Delete completed: {success} succeeded, {failed} failed', 'ja': '削除完了：成功 {success} 個、失敗 {failed} 個'},
            'delete_failed': {'zh': '刪除失敗', 'en': 'Delete Failed', 'ja': '削除失敗'},
            'delete_workspace_error': {'zh': '無法刪除 Workspace：{error}', 'en': 'Failed to delete workspace: {error}', 'ja': 'ワークスペースの削除に失敗: {error}'},
            'load_workspace_error': {'zh': '無法載入 Workspace：{error}', 'en': 'Failed to load workspace: {error}', 'ja': 'ワークスペースの読込に失敗: {error}'},
            
            # Workspace 載入成功訊息
            'workspace_load_success_title': {'zh': '載入成功', 'en': 'Load Successful', 'ja': '読込成功'},
            'workspace_load_success_message': {'zh': 'Workspace 已成功載入！\n\n已重建：\n• {tabs} 個分頁\n• {windows} 個視窗', 'en': 'Workspace loaded successfully!\n\nRestored:\n• {tabs} tabs\n• {windows} windows', 'ja': 'ワークスペースを読込しました！\n\n復元内容：\n• {tabs} タブ\n• {windows} ウィンドウ'},
            'workspace_load_failed_title': {'zh': '載入失敗', 'en': 'Load Failed', 'ja': '読込失敗'},
            'workspace_load_failed_message': {'zh': 'Workspace 載入過程中發生錯誤，請查看日誌獲取詳細資訊。', 'en': 'An error occurred while loading workspace. Please check logs for details.', 'ja': 'ワークスペース読込中にエラーが発生しました。詳細はログを確認してください。'},
            'workspace_load_error_title': {'zh': '載入失敗', 'en': 'Load Failed', 'ja': '読込失敗'},
            'workspace_load_error_message': {'zh': '無法載入 Workspace：{error}', 'en': 'Failed to load workspace: {error}', 'ja': 'ワークスペースの読込に失敗: {error}'},
            
            # SaveWorkspaceDialog
            'save_workspace_title': {'zh': '儲存 Workspace', 'en': 'Save Workspace', 'ja': 'ワークスペース保存'},
            'save_workspace_dialog_title': {'zh': '儲存當前 Workspace', 'en': 'Save Current Workspace', 'ja': '現在のワークスペースを保存'},
            'workspace_basic_info': {'zh': '基本資訊', 'en': 'Basic Information', 'ja': '基本情報'},
            'workspace_name_label': {'zh': '名稱', 'en': 'Name', 'ja': '名前'},
            'workspace_name_required': {'zh': '名稱 *', 'en': 'Name *', 'ja': '名前 *'},
            'workspace_name_placeholder': {'zh': '請輸入 Workspace 名稱（必填）', 'en': 'Enter workspace name (required)', 'ja': 'ワークスペース名を入力（必須）'},
            'workspace_description_label': {'zh': '描述', 'en': 'Description', 'ja': '説明'},
            'workspace_description_placeholder': {'zh': '請輸入 Workspace 描述（選填）\n例如：2025 USA GP 正賽分析，包含 VER vs LEC 比較', 'en': 'Enter workspace description (optional)\nExample: 2025 USA GP Race Analysis, including VER vs LEC comparison', 'ja': 'ワークスペースの説明を入力（任意）\n例：2025 USA GP レース分析、VER vs LEC 比較を含む'},
            'workspace_tags_label': {'zh': '標籤', 'en': 'Tags', 'ja': 'タグ'},
            'workspace_tags_placeholder': {'zh': '請輸入標籤，用逗號分隔（例如：2025,USA,正賽）', 'en': 'Enter tags, separated by commas (e.g., 2025,USA,Race)', 'ja': 'タグを入力、カンマ区切り（例：2025,USA,レース）'},
            'workspace_statistics': {'zh': 'Workspace 統計', 'en': 'Workspace Statistics', 'ja': 'ワークスペース統計'},
            'workspace_loading_stats': {'zh': '正在載入統計資訊...', 'en': 'Loading statistics...', 'ja': '統計情報を読込中...'},
            'workspace_total_tabs': {'zh': '總分頁數', 'en': 'Total Tabs', 'ja': 'タブ総数'},
            'workspace_total_windows': {'zh': '總視窗數', 'en': 'Total Windows', 'ja': 'ウィンドウ総数'},
            'workspace_window_types': {'zh': '視窗類型分布', 'en': 'Window Type Distribution', 'ja': 'ウィンドウタイプ分布'},
            'workspace_parameters': {'zh': '參數資訊', 'en': 'Parameter Information', 'ja': 'パラメータ情報'},
            'workspace_year': {'zh': '年份', 'en': 'Year', 'ja': '年'},
            'workspace_race': {'zh': '賽事', 'en': 'Race', 'ja': 'レース'},
            'workspace_session': {'zh': '會話', 'en': 'Session', 'ja': 'セッション'},
            'workspace_preview': {'zh': '儲存預覽', 'en': 'Save Preview', 'ja': '保存プレビュー'},
            'workspace_preview_placeholder': {'zh': '配置預覽將在這裡顯示...', 'en': 'Configuration preview will be displayed here...', 'ja': '設定プレビューがここに表示されます...'},
            'workspace_cancel': {'zh': '取消', 'en': 'Cancel', 'ja': 'キャンセル'},
            'workspace_save_button': {'zh': '儲存 Workspace', 'en': 'Save Workspace', 'ja': 'ワークスペース保存'},
            'workspace_cannot_save': {'zh': '無法儲存', 'en': 'Cannot Save', 'ja': '保存不可'},
            'workspace_no_tabs_message': {'zh': '當前沒有可儲存的分頁或視窗。\n請先開啟一些分析模組。', 'en': 'No tabs or windows to save.\nPlease open some analysis modules first.', 'ja': '保存可能なタブまたはウィンドウがありません。\nまず分析モジュールを開いてください。'},
            'workspace_load_error': {'zh': '錯誤', 'en': 'Error', 'ja': 'エラー'},
            'workspace_load_data_failed': {'zh': '載入 Workspace 數據失敗：{error}', 'en': 'Failed to load workspace data: {error}', 'ja': 'ワークスペースデータの読込に失敗: {error}'},
            'workspace_name_hint_exists': {'zh': '此名稱已存在，儲存時將自動附加序號', 'en': 'Name already exists, a number will be appended when saving', 'ja': 'この名前は既に存在します。保存時に番号が追加されます'},
            'workspace_name_hint_available': {'zh': '名稱可用', 'en': 'Name available', 'ja': '名前は利用可能'},
            'workspace_validation_failed': {'zh': '驗證失敗', 'en': 'Validation Failed', 'ja': '検証失敗'},
            'workspace_name_required_message': {'zh': '請輸入 Workspace 名稱', 'en': 'Please enter workspace name', 'ja': 'ワークスペース名を入力してください'},
            'workspace_name_duplicate': {'zh': '名稱重複', 'en': 'Duplicate Name', 'ja': '名前の重複'},
            'workspace_name_duplicate_message': {'zh': '名稱 \'{old_name}\' 已存在。\n是否使用 \'{new_name}\'？', 'en': 'Name \'{old_name}\' already exists.\nUse \'{new_name}\' instead?', 'ja': '名前 \'{old_name}\' は既に存在します。\n\'{new_name}\' を使用しますか？'},
            'workspace_save_success': {'zh': '儲存成功', 'en': 'Save Successful', 'ja': '保存成功'},
            'workspace_save_success_message': {'zh': 'Workspace \'{name}\' 已成功儲存！\n\n• 分頁數: {tabs}\n• 視窗數: {windows}', 'en': 'Workspace \'{name}\' saved successfully!\n\n• Tabs: {tabs}\n• Windows: {windows}', 'ja': 'ワークスペース \'{name}\' を保存しました！\n\n• タブ数: {tabs}\n• ウィンドウ数: {windows}'},
            'workspace_save_failed': {'zh': '儲存失敗', 'en': 'Save Failed', 'ja': '保存失敗'},
            'workspace_save_failed_message': {'zh': '無法儲存 Workspace：{error}', 'en': 'Failed to save workspace: {error}', 'ja': 'ワークスペースの保存に失敗: {error}'},
            
            # Tooltips
            'sync_main_window_tooltip': {'zh': '接收主程式同步：啟用 (綠色) / 停用 (紅色)', 'en': 'Receive Main Window Sync: Enabled (Green) / Disabled (Red)', 'ja': 'Receive Main Window Sync: Enabled (Green) / Disabled (Red)'},
            'individual_linkage_tooltip': {'zh': '個別連動：啟用 / 停用', 'en': 'Individual Linkage: Enabled / Disabled', 'ja': 'Individual Linkage: Enabled / Disabled'},
            'restore_normal_size_tooltip': {'zh': '恢復正常大小', 'en': 'Restore to normal size', 'ja': 'Restore to normal size'},
            'window_settings_tooltip': {'zh': '視窗設定', 'en': 'Window settings', 'ja': 'Window settings'},
            'minimize_tooltip': {'zh': '最小化', 'en': 'Minimize', 'ja': 'Minimize'},
            'maximize_tooltip': {'zh': '最大化/還原', 'en': 'Maximize/Restore', 'ja': 'Maximize/Restore'},
            'popout_tooltip': {'zh': '彈出為獨立視窗', 'en': 'Pop out as independent window', 'ja': 'Pop out as independent window'},
            'close_tooltip': {'zh': '關閉', 'en': 'Close', 'ja': '閉じる'},
            
            # MDI 標題欄按鈕 (S, L, D)
            'sync_button_tooltip_enabled': {'zh': '接收主程式同步：啟用 (S)', 'en': 'Receive sync from main: Enabled (S)', 'ja': 'メイン同期を受信：有効 (S)'},
            'sync_button_tooltip_disabled': {'zh': '接收主程式同步：停用 (X)', 'en': 'Receive sync from main: Disabled (X)', 'ja': 'メイン同期を受信：無効 (X)'},
            'linkage_button_tooltip_enabled': {'zh': '個別連動：啟用 (L)', 'en': 'Individual linkage: Enabled (L)', 'ja': '個別リンク：有効 (L)'},
            'linkage_button_tooltip_disabled': {'zh': '個別連動：停用 (X)', 'en': 'Individual linkage: Disabled (X)', 'ja': '個別リンク：無効 (X)'},
            'driver_lap_sync_tooltip_enabled': {'zh': '與主視窗同步車手與圈數：啟用 (D)', 'en': 'Sync driver & lap with main window: Enabled (D)', 'ja': 'メインウィンドウとドライバー・ラップを同期：有効 (D)'},
            'driver_lap_sync_tooltip_disabled': {'zh': '與主視窗同步車手與圈數：停用 (X)', 'en': 'Sync driver & lap with main window: Disabled (X)', 'ja': 'メインウィンドウとドライバー・ラップを同期：無効 (X)'},
            'restore_normal_size': {'zh': '恢復正常大小', 'en': 'Restore Normal Size', 'ja': '通常サイズに復元'},
            'window_settings': {'zh': '視窗設定', 'en': 'Window Settings', 'ja': 'ウィンドウ設定'},
            'minimize': {'zh': '最小化', 'en': 'Minimize', 'ja': '最小化'},
            'maximize_restore': {'zh': '最大化/還原', 'en': 'Maximize/Restore', 'ja': '最大化/復元'},
            
            # 彈出視窗 (Popout Window)
            'sync_other_windows': {'zh': '[連動] 同步其他視窗', 'en': '[LINK] Sync Other Windows', 'ja': '[リンク] 他のウィンドウと同期'},
            'sync_windows_tooltip': {'zh': '同步其他視窗 (Race/Session/Year 連動)', 'en': 'Sync other windows (Race/Session/Year sync)', 'ja': '他のウィンドウを同期 (Race/Session/Year連動)'},
            'return_to_main': {'zh': '返回主畫面', 'en': 'Return to Main', 'ja': 'メインに戻る'},
            'controls': {'zh': '控制', 'en': 'Controls', 'ja': 'コントロール'},
            
            # 圖表標籤
            'rain_main_chart': {'zh': '主要圖表 (降雨+氣溫)', 'en': 'Main Chart (Rain + Temperature)', 'ja': 'Main Chart (Rain + Temperature)'},
            'temperature_comparison': {'zh': '溫度對比 (氣溫vs賽道溫度)', 'en': 'Temperature Comparison (Air vs Track)', 'ja': 'Temperature Comparison (Air vs Track)'},
            
            # 賽道資訊
            'track_name': {'zh': '賽道名稱', 'en': 'Track Name', 'ja': 'Track Name'},
            'total_distance': {'zh': '總長度', 'en': 'Total Distance', 'ja': 'Total Distance'},
            'position_points': {'zh': '位置點數', 'en': 'Position Points', 'ja': 'Position Points'},
            'coordinate_range': {'zh': '座標範圍', 'en': 'Coordinate Range', 'ja': 'Coordinate Range'},
            'fastest_lap': {'zh': '最快圈', 'en': 'Fastest Lap', 'ja': '最速ラップ'},
            'data_quality': {'zh': '數據品質', 'en': 'Data Quality', 'ja': 'Data Quality'},
            'track_map': {'zh': '賽道地圖', 'en': 'Track Map', 'ja': 'Track Map'},
            'track_map_loaded': {'zh': '賽道地圖已載入', 'en': 'Track map loaded', 'ja': 'Track map loaded'},
            'track_map_preparing': {'zh': '賽道地圖\n(準備中...)', 'en': 'Track Map\n(Preparing...)', 'ja': 'Track Map\n(Preparing...)'},
            'track_coordinates_detail': {'zh': '賽道座標詳細資訊', 'en': 'Track Coordinates Detail', 'ja': 'Track Coordinates Detail'},
            'export_failed': {'zh': '匯出失敗', 'en': 'Export Failed', 'ja': 'Export Failed'},
            'export_error_occurred': {'zh': '匯出過程中發生錯誤', 'en': 'Error occurred during export', 'ja': 'Error occurred during export'},
            
            # 車手資訊
            'driver_comparison': {'zh': '車手對比', 'en': 'Driver Comparison', 'ja': 'Driver Comparison'},
            'driver': {'zh': '車手', 'en': 'Driver', 'ja': 'Driver'},
            'lap': {'zh': '圈數', 'en': 'Lap', 'ja': 'ラップ'},
            'fastest_lap_analysis': {'zh': '最速圈分析', 'en': 'Fastest Lap Analysis', 'ja': 'Fastest Lap Analysis'},
            'telemetry_analysis_triggered': {'zh': '遙測分析已觸發', 'en': 'Telemetry analysis triggered', 'ja': 'Telemetry analysis triggered'},
            'no_telemetry_analysis_method': {'zh': '主視窗沒有遙測分析方法', 'en': 'Main window has no telemetry analysis method', 'ja': 'Main window has no telemetry analysis method'},
            'trigger_telemetry_analysis_error': {'zh': '觸發遙測分析時發生錯誤', 'en': 'Error triggering telemetry analysis', 'ja': 'Error triggering telemetry analysis'},
            'get_fastest_lap_from_telemetry': {'zh': '從遙測分析數據獲取指定車手的最速圈數', 'en': 'Get fastest lap number from telemetry data for specified driver', 'ja': 'Get fastest lap number from telemetry data for specified driver'},
            'found_telemetry_file': {'zh': '找到遙測檔案', 'en': 'Found telemetry file', 'ja': 'Found telemetry file'},
            'telemetry_file_not_found': {'zh': '找不到遙測分析檔案，使用預設圈數 1', 'en': 'Telemetry file not found, using default lap 1', 'ja': 'Telemetry file not found, using default lap 1'},
            'telemetry_file_read_success': {'zh': '遙測檔案讀取成功，開始解析最速圈數據...', 'en': 'Telemetry file read successfully, parsing fastest lap data...', 'ja': 'Telemetry file read successfully, parsing fastest lap data...'},
            'fastest_lap_for_driver': {'zh': '車手 {driver} 最速圈: 第{lap}圈', 'en': 'Driver {driver} fastest lap: Lap {lap}', 'ja': 'Driver {driver} fastest lap: Lap {lap}'},
            'user_selected_fastest_lap': {'zh': '用戶選擇了最速圈選項，檢查遙測分析數據...', 'en': 'User selected fastest lap option, checking telemetry data...', 'ja': 'User selected fastest lap option, checking telemetry data...'},
            'calling_main_window_telemetry': {'zh': '調用主視窗開啟遙測分析...', 'en': 'Calling main window to open telemetry analysis...', 'ja': 'Calling main window to open telemetry analysis...'},
            'checking_fastest_lap_option': {'zh': '檢測到最速圈選項，檢查遙測分析數據...', 'en': 'Detected fastest lap option, checking telemetry data...', 'ja': 'Detected fastest lap option, checking telemetry data...'},
            'checking_telemetry_analysis': {'zh': '檢查並在需要時載入遙測分析', 'en': 'Check and load telemetry analysis if needed', 'ja': 'Check and load telemetry analysis if needed'},
            
            # 事故分析
            'accident_severity': {'zh': '事故嚴重程度', 'en': 'Accident Severity', 'ja': 'Accident Severity'},
            'track_limit_violation': {'zh': '賽道限制違規', 'en': 'Track Limit Violation', 'ja': 'Track Limit Violation'},
            'penalty_event': {'zh': '處罰事件', 'en': 'Penalty Event', 'ja': 'Penalty Event'},
            'safety_status': {'zh': '安全狀況', 'en': 'Safety Status', 'ja': 'Safety Status'},
            'no_accidents_found': {'zh': '本場比賽未發現任何事故記錄，安全狀況優良！', 'en': 'No accident records found, excellent safety status!', 'ja': 'No accident records found, excellent safety status!'},
            'flag_statistics_details': {'zh': ' 旗標統計詳情', 'en': ' Flag Statistics Details', 'ja': ' フラッグ統計詳細'},
            'penalty_list': {'zh': '️ 處罰清單', 'en': '️ Penalty List', 'ja': '️ ペナルティリスト'},
            'accident_time_distribution_chart': {'zh': ' 事故時間分佈圖表', 'en': ' Accident Time Distribution Chart', 'ja': ' アクシデント時間分布チャート'},
            'lap_label': {'zh': '圈數', 'en': 'Lap', 'ja': 'ラップ'},
            'status_total_accidents': {'zh': ' 總計: {count}起事故', 'en': ' Total: {count} accidents', 'ja': ' 合計: {count}件の事故'},
            'status_data_source_json': {'zh': ' 來源: JSON', 'en': ' Source: JSON', 'ja': ' ソース: JSON'},
            'status_last_updated': {'zh': ' 更新: {timestamp}', 'en': ' Updated: {timestamp}', 'ja': ' 更新: {timestamp}'},
            'status_most_dangerous_lap': {'zh': ' 最危險圈數: {lap}', 'en': ' Most risky lap: {lap}', 'ja': ' 最も危険なラップ: {lap}'},
            'status_most_involved_driver': {'zh': ' 最多涉入: {driver}', 'en': ' Most involved: {driver}', 'ja': ' 最多関与: {driver}'},
            'status_ai_generation_enabled': {'zh': ' 智能生成: 開啟', 'en': ' Smart insights: enabled', 'ja': ' スマートインサイト: 有効'},
            'most_involved_driver_format': {'zh': '{driver} ({count}次)', 'en': '{driver} ({count} incidents)', 'ja': '{driver} ({count}件)'},
            'main_risk_type': {'zh': '主要風險類型', 'en': 'Main Risk Type', 'ja': 'Main Risk Type'},
            'most_common_severity': {'zh': '最常見的事故嚴重程度', 'en': 'Most common accident severity', 'ja': 'Most common accident severity'},
            'critical_incidents_count': {'zh': '關鍵事件數量', 'en': 'Critical Incidents Count', 'ja': 'Critical Incidents Count'},
            'serious_accidents_requiring_attention': {'zh': '需特別關注的嚴重事故', 'en': 'Serious accidents requiring special attention', 'ja': 'Serious accidents requiring special attention'},
            'strengthen_track_safety': {'zh': '建議加強賽道安全措施', 'en': 'Recommend strengthening track safety measures', 'ja': 'Recommend strengthening track safety measures'},
            'strengthen_driver_training': {'zh': '加強車手安全培訓', 'en': 'Strengthen driver safety training', 'ja': 'Strengthen driver safety training'},
            'strengthen_track_behavior_supervision': {'zh': '加強車手賽道行為監管', 'en': 'Strengthen driver track behavior supervision', 'ja': 'Strengthen driver track behavior supervision'},
            'accident_escalation_trend': {'zh': '事故升級趨勢', 'en': 'Accident Escalation Trend', 'ja': 'Accident Escalation Trend'},
            'top_5_events': {'zh': '前5個事件', 'en': 'Top 5 Events', 'ja': 'Top 5 Events'},
            'total_incidents': {'zh': '總事故數量', 'en': 'Total Incidents', 'ja': 'Total Incidents'},
            
            # 語言切換
            'language': {'zh': '語言', 'en': 'Language', 'ja': '言語'},
            'switch_language': {'zh': '切換語言', 'en': 'Switch Language', 'ja': '言語切り替え'},
            'chinese': {'zh': '繁體中文', 'en': 'Traditional Chinese', 'ja': '繁体字中国語'},
            'english': {'zh': 'English', 'en': 'English', 'ja': '英語'},
            'japanese': {'zh': '日本語', 'en': 'Japanese', 'ja': '日本語'},
            'language_switched': {'zh': '語言已切換', 'en': 'Language switched', 'ja': '言語が切り替わりました'},
            'restart_required': {'zh': '部分更改需要重啟程式才能完全生效', 'en': 'Some changes require program restart to take full effect', 'ja': '一部の変更は、完全に有効にするためにプログラムの再起動が必要です'},
            'language_switched_to': {'zh': '語言已切換為: {language}', 'en': 'Language switched to: {language}', 'ja': '言語が{language}に切り替わりました'},
            
            # 日誌訊息標籤
            'debug': {'zh': '調試', 'en': 'DEBUG', 'ja': 'DEBUG'},
            'info': {'zh': '資訊', 'en': 'INFO', 'ja': 'INFO'},
            'warning': {'zh': '警告', 'en': 'WARNING', 'ja': 'WARNING'},
            'error': {'zh': '錯誤', 'en': 'ERROR', 'ja': 'ERROR'},
            'success': {'zh': '成功', 'en': 'SUCCESS', 'ja': 'SUCCESS'},
            
            # 單位和格式
            'km': {'zh': '公里', 'en': 'km', 'ja': 'km'},
            'lap_count': {'zh': '第{n}圈', 'en': 'Lap {n}', 'ja': 'Lap {n}'},
            'position_points_count': {'zh': '{n} 個位置點', 'en': '{n} position points', 'ja': '{n} position points'},
            'click_to_view_coordinates': {'zh': '(點擊可查看詳細座標)', 'en': '(Click to view detailed coordinates)', 'ja': '(Click to view detailed coordinates)'},
            
            # 模組更新訊息
            'module_error': {'zh': '模組錯誤', 'en': 'Module error', 'ja': 'Module error'},
            'parameters_updated': {'zh': '參數已更新', 'en': 'Parameters updated', 'ja': 'Parameters updated'},
            'module_update_success': {'zh': '模組更新成功', 'en': 'Module update successful', 'ja': 'Module update successful'},
            'module_update_failed': {'zh': '模組更新失敗', 'en': 'Module update failed', 'ja': 'Module update failed'},
            'using_new_module_update': {'zh': '使用新版模組更新邏輯', 'en': 'Using new module update logic', 'ja': 'Using new module update logic'},
            'using_legacy_update': {'zh': '使用舊版更新邏輯', 'en': 'Using legacy update logic', 'ja': 'Using legacy update logic'},
            'analysis_module_is_none': {'zh': 'analysis_module 為 None', 'en': 'analysis_module is None', 'ja': 'analysis_module is None'},
            'update_window_data': {'zh': '更新視窗數據', 'en': 'Update window data', 'ja': 'Update window data'},
            'window_title': {'zh': '視窗標題', 'en': 'Window Title', 'ja': 'Window Title'},
            'using_module_title': {'zh': '使用模組標題', 'en': 'Using module title', 'ja': 'Using module title'},
            'using_legacy_title_format': {'zh': '使用舊版標題格式', 'en': 'Using legacy title format', 'ja': 'Using legacy title format'},
            'title_updated': {'zh': '標題已更新', 'en': 'Title updated', 'ja': 'Title updated'},
            'title_update_failed': {'zh': '標題更新失敗', 'en': 'Title update failed', 'ja': 'Title update failed'},
            'local_parameters_updated': {'zh': '本地參數已更新', 'en': 'Local parameters updated', 'ja': 'Local parameters updated'},
            'legacy_update': {'zh': '舊版更新', 'en': 'Legacy update', 'ja': 'Legacy update'},
            'legacy_update_failed': {'zh': '舊版更新失敗', 'en': 'Legacy update failed', 'ja': 'Legacy update failed'},
            
            # 同步和連動
            'sync_enabled': {'zh': '接收同步已啟動 - 將接收主程式參數', 'en': 'Sync enabled - Will receive main window parameters', 'ja': 'Sync enabled - Will receive main window parameters'},
            'sync_disabled': {'zh': '接收同步已停用 - 獨立運作模式', 'en': 'Sync disabled - Independent operation mode', 'ja': 'Sync disabled - Independent operation mode'},
            'window_sync_status_updated': {'zh': '視窗同步接收狀態已更新', 'en': 'Window sync status updated', 'ja': 'Window sync status updated'},
            'linkage_enabled': {'zh': '個別連動已啟用', 'en': 'Individual linkage enabled', 'ja': 'Individual linkage enabled'},
            'linkage_disabled': {'zh': '個別連動已停用', 'en': 'Individual linkage disabled', 'ja': 'Individual linkage disabled'},
            'window_linkage_status_updated': {'zh': '視窗個別連動狀態已更新', 'en': 'Window linkage status updated', 'ja': 'Window linkage status updated'},
            'receive_sync_enabled': {'zh': '接收同步：啟用', 'en': 'Receive Sync: Enabled', 'ja': 'Receive Sync: Enabled'},
            'receive_sync_disabled': {'zh': '接收同步：停用', 'en': 'Receive Sync: Disabled', 'ja': 'Receive Sync: Disabled'},
            'individual_linkage_enabled': {'zh': '個別連動：啟用', 'en': 'Individual Linkage: Enabled', 'ja': 'Individual Linkage: Enabled'},
            'individual_linkage_disabled': {'zh': '個別連動：停用', 'en': 'Individual Linkage: Disabled', 'ja': 'Individual Linkage: Disabled'},
            
            # 雙車手模式
            'dual_driver_mode': {'zh': '雙車手模式', 'en': 'Dual Driver Mode', 'ja': 'Dual Driver Mode'},
            'single_driver_mode': {'zh': '單車手模式', 'en': 'Single Driver Mode', 'ja': 'Single Driver Mode'},
            'no_driver_data': {'zh': '無車手數據時顯示基本信息', 'en': 'Display basic info when no driver data', 'ja': 'Display basic info when no driver data'},
            'format_grouped_by_driver': {'zh': '直接在data下按車手分組', 'en': 'Directly grouped by driver under data', 'ja': 'Directly grouped by driver under data'},
            
            # 主視窗
            'main_window_title': {'zh': 'F1 TelemetryStation Pro v0.0', 'en': 'F1 TelemetryStation Pro v0.0', 'ja': 'F1 TelemetryStation Pro v0.0'},
            'ready': {'zh': '就緒', 'en': 'Ready', 'ja': '準備完了'},
            'close_all_windows': {'zh': '關閉所有視窗', 'en': 'Close All Windows', 'ja': 'すべてのウィンドウを閉じる'},
            'show_all_windows': {'zh': '顯示所有視窗', 'en': 'Show All Windows', 'ja': 'すべてのウィンドウを表示'},
            'lap_linkage': {'zh': '圈速連動', 'en': 'Lap Linkage', 'ja': 'ラップ連動'},
            
            # 事故分析分頁
            'accident_statistics_overview': {'zh': '統計總覽', 'en': 'Statistics Overview', 'ja': '統計概要'},
            'accident_distribution_analysis': {'zh': '分佈分析', 'en': 'Distribution Analysis', 'ja': '分布分析'},
            'accident_severity_level': {'zh': '嚴重程度', 'en': 'Severity Level', 'ja': '重大度'},
            'accident_key_events': {'zh': '關鍵事件', 'en': 'Key Events', 'ja': 'キーイベント'},
            'accident_detailed_list': {'zh': '詳細列表', 'en': 'Detailed List', 'ja': '詳細リスト'},
            'under_development': {'zh': '待開發', 'en': 'Under Development', 'ja': '開発中'},
            
            # 圈速分析模組
            'detailed_lap_analysis': {'zh': '詳細圈速分析', 'en': 'Detailed Lap Analysis', 'ja': '詳細ラップ分析'},
            'lap_analysis': {'zh': '圈速分析', 'en': 'Lap Analysis', 'ja': 'ラップ分析'},
            
            # 按鈕文字
            'clear_button': {'zh': '清除', 'en': 'Clear', 'ja': 'クリア'},
            'export_button': {'zh': '匯出', 'en': 'Export', 'ja': 'エクスポート'},
            'analysis_workspace': {'zh': '分析工作區', 'en': 'Analysis Workspace', 'ja': '分析ワークスペース'},
            
            # Rain Analysis 座標軸
            'lap_number_rain': {'zh': '圈數', 'en': 'Lap Number', 'ja': 'ラップ数'},
            'temperature_celsius': {'zh': '溫度 (°C)', 'en': 'Temperature (°C)', 'ja': '温度 (°C)'},
            'rainfall': {'zh': '降雨', 'en': 'Rainfall', 'ja': '降雨量'},
            'air_temperature': {'zh': '氣溫', 'en': 'Air Temperature', 'ja': '気温'},
            
            # 右鍵選單視窗控制
            'cascade_windows': {'zh': '層疊視窗', 'en': 'Cascade Windows', 'ja': 'ウィンドウを重ねて表示'},
            'tile_windows': {'zh': '平舖視窗', 'en': 'Tile Windows', 'ja': 'ウィンドウを並べて表示'},
            'close_window': {'zh': '關閉視窗', 'en': 'Close Window', 'ja': 'ウィンドウを閉じる'},
            'restore_window': {'zh': '還原視窗', 'en': 'Restore Window', 'ja': 'ウィンドウを元に戻す'},
            'maximize_window': {'zh': '最大化視窗', 'en': 'Maximize Window', 'ja': 'ウィンドウを最大化'},
            'minimize_window': {'zh': '最小化視窗', 'en': 'Minimize Window', 'ja': 'ウィンドウを最小化'},
            'cascade_all_windows': {'zh': '層疊所有視窗', 'en': 'Cascade All Windows', 'ja': 'すべてのウィンドウを重ねて表示'},
            'tile_all_windows': {'zh': '平舖所有視窗', 'en': 'Tile All Windows', 'ja': 'すべてのウィンドウを並べて表示'},
            
            # CLI 分析訊息
            'cli_analysis_starting': {'zh': '啟動 CLI 分析: {year} {race} {session}', 'en': 'Starting CLI Analysis: {year} {race} {session}', 'ja': 'CLI分析開始: {year} {race} {session}'},
            'cli_analysis_success': {'zh': 'CLI 分析成功完成', 'en': 'CLI analysis completed successfully', 'ja': 'CLI分析が正常に完了しました'},
            'return_code': {'zh': '返回碼', 'en': 'Return code', 'ja': 'リターンコード'},
            'error_output': {'zh': '錯誤輸出', 'en': 'Error output', 'ja': 'エラー出力'},
            'error_output_encoding_issue': {'zh': '錯誤輸出編碼問題', 'en': 'Error output encoding issue', 'ja': 'エラー出力のエンコーディング問題'},
            'analysis_cancelled': {'zh': '分析被用戶取消', 'en': 'Analysis cancelled by user', 'ja': 'ユーザーによって分析がキャンセルされました'},
            
            # 遙測分析選項對話框
            'telemetry_options_title': {'zh': '遙測分析選項', 'en': 'Telemetry Analysis Options', 'ja': 'テレメトリー分析オプション'},
            'select_telemetry_charts': {'zh': '請選擇要顯示的遙測圖表', 'en': 'Please select telemetry charts to display', 'ja': '表示するテレメトリーチャートを選択してください'},
            'driver_lap_selection': {'zh': '車手和圈數選擇', 'en': 'Driver and Lap Selection', 'ja': 'ドライバーとラップの選択'},
            'driver1_required': {'zh': '車手1 (必選):', 'en': 'Driver 1 (Required):', 'ja': 'ドライバー1（必須）:'},
            'driver2_optional': {'zh': '車手2 (選用):', 'en': 'Driver 2 (Optional):', 'ja': 'ドライバー2（オプション）:'},
            'lap_number': {'zh': '圈數:', 'en': 'Lap:', 'ja': 'ラップ:'},
            'fastest_lap': {'zh': '最速圈', 'en': 'Fastest Lap', 'ja': '最速ラップ'},
            'telemetry_options': {'zh': '遙測選項', 'en': 'Telemetry Options', 'ja': 'テレメトリーオプション'},
            'select_all': {'zh': '全選', 'en': 'Select All', 'ja': 'すべて選択'},
            'select_none': {'zh': '全不選', 'en': 'Select None', 'ja': 'すべて解除'},
            'restore_default': {'zh': '恢復預設', 'en': 'Restore Default', 'ja': 'デフォルトに戻す'},
            'ok': {'zh': '確定', 'en': 'OK', 'ja': 'OK'},
            'lap': {'zh': '圈', 'en': 'Lap', 'ja': 'ラップ'},
            'fastest_lap_type': {'zh': '最速圈', 'en': 'Fastest Lap', 'ja': '最速ラップ'},
            'specific_lap': {'zh': '指定圈數', 'en': 'Specific Lap', 'ja': '特定ラップ'},
            
            # ========== Ideal Lap 分析模組翻譯 (2025-10-09) ==========
            
            # Options Dialog (對話框標題與描述)
            'ideal_lap_options_title': {'zh': '理想圈分析選項', 'en': 'Ideal Lap Analysis Options', 'ja': '理想ラップ分析オプション'},
            'select_ideal_lap_analysis_type': {'zh': '請選擇要開啟的理想圈分析類型。', 'en': 'Please select the ideal lap analysis types you want to open.', 'ja': '開きたい理想ラップ分析タイプを選択してください。'},
            'analysis_type': {'zh': '分析類型', 'en': 'Analysis Type', 'ja': '分析タイプ'},
            
            # Options Dialog - 分析選項
            'ranking_table': {'zh': '排名表格', 'en': 'Ranking Table', 'ja': 'ランキングテーブル'},
            'sector_heatmap': {'zh': '分段熱力圖', 'en': 'Sector Heatmap', 'ja': 'セクターヒートマップ'},
            'sector_comparison': {'zh': '分段比較', 'en': 'Sector Comparison', 'ja': 'セクター比較'},
            
            # Options Dialog - 描述
            'ranking_table_desc': {'zh': '排名表格：顯示所有車手的理想圈排名', 'en': 'Ranking Table: Shows ideal lap ranking for all drivers', 'ja': 'ランキングテーブル: 全ドライバーの理想ラップランキングを表示'},
            'sector_heatmap_desc': {'zh': '分段熱力圖：視覺化各車手 S1/S2/S3 表現', 'en': 'Sector Heatmap: Visualizes S1/S2/S3 performance for all drivers', 'ja': 'セクターヒートマップ: 各ドライバーのS1/S2/S3パフォーマンスを可視化'},
            'sector_comparison_desc': {'zh': '分段比較：比較車手間的分段差異（開發中）', 'en': 'Sector Comparison: Compares sector differences between drivers (under development)', 'ja': 'セクター比較: ドライバー間のセクター差異を比較（開発中）'},
            
            # Ranking Table Widget - 統計摘要面板
            'race_statistics_summary': {'zh': ' 賽事統計摘要', 'en': ' Race Statistics Summary', 'ja': ' レース統計サマリー'},
            'total_drivers': {'zh': '總車手數', 'en': 'Total Drivers', 'ja': '総ドライバー数'},
            'session_fastest_lap': {'zh': '全場最速實際圈', 'en': 'Session Fastest Lap', 'ja': 'セッション最速ラップ'},
            'fastest_ideal_lap': {'zh': '最快理想圈', 'en': 'Fastest Ideal Lap', 'ja': '最速理想ラップ'},
            'ideal_lap_range': {'zh': '理想圈範圍', 'en': 'Ideal Lap Range', 'ja': '理想ラップ範囲'},
            'average_gap': {'zh': '平均差異', 'en': 'Average Gap', 'ja': '平均ギャップ'},
            'perfect_lap_rate': {'zh': '完美單圈達成率', 'en': 'Perfect Lap Rate', 'ja': '完璧ラップ達成率'},
            
            # Ranking Table Widget - 表格欄位標題
            'table_header_position': {'zh': '排名', 'en': 'Pos', 'ja': '順位'},
            'table_header_driver': {'zh': '車手', 'en': 'Driver', 'ja': 'ドライバー'},
            'table_header_fastest_lap': {'zh': '車手最速圈', 'en': 'Fastest Lap', 'ja': '最速ラップ'},
            'table_header_ideal_lap': {'zh': '理想圈', 'en': 'Ideal Lap', 'ja': '理想ラップ'},
            'table_header_gap': {'zh': '差異', 'en': 'Gap', 'ja': 'ギャップ'},
            'table_header_gap_to_fastest': {'zh': '與全場最速差距', 'en': 'Gap to Session Fastest', 'ja': 'セッション最速との差'},
            'table_header_sector_breakdown': {'zh': '分段', 'en': 'Sectors', 'ja': 'セクター'},
            'table_header_action': {'zh': '操作', 'en': 'Action', 'ja': 'アクション'},
            
            # Ranking Table Widget - 按鈕與工具列
            'export_csv': {'zh': ' 匯出 CSV', 'en': ' Export CSV', 'ja': ' CSV出力'},
            'detail_button': {'zh': '詳情', 'en': 'Details', 'ja': '詳細'},
            'status_ready': {'zh': '就緒', 'en': 'Ready', 'ja': '準備完了'},
            'status_loaded_drivers': {'zh': '已載入 {count} 位車手', 'en': 'Loaded {count} drivers', 'ja': '{count}人のドライバーを読み込みました'},
            'status_table_cleared': {'zh': '表格已清空', 'en': 'Table cleared', 'ja': 'テーブルをクリアしました'},
            
            # Ranking Table Widget - Tooltip 內容
            'tooltip_no_fastest_lap_data': {'zh': '無最速圈資料', 'en': 'No fastest lap data', 'ja': '最速ラップデータなし'},
            'tooltip_fastest_lap': {'zh': '最速圈: {time}', 'en': 'Fastest Lap: {time}', 'ja': '最速ラップ: {time}'},
            'tooltip_fastest_lap_with_number': {'zh': '最速圈: {time} (Lap {lap_num})', 'en': 'Fastest Lap: {time} (Lap {lap_num})', 'ja': '最速ラップ: {time} (Lap {lap_num})'},
            'tooltip_no_ideal_lap_data': {'zh': '無理想圈資料', 'en': 'No ideal lap data', 'ja': '理想ラップデータなし'},
            'tooltip_ideal_lap': {'zh': '理想圈: {time}', 'en': 'Ideal Lap: {time}', 'ja': '理想ラップ: {time}'},
            'tooltip_sector_detail': {'zh': 'S{sector_num}: {time}s (Lap {lap_num})', 'en': 'S{sector_num}: {time}s (Lap {lap_num})', 'ja': 'S{sector_num}: {time}s (Lap {lap_num})'},
            'tooltip_gap_cannot_calculate': {'zh': '無法計算差異', 'en': 'Cannot calculate gap', 'ja': 'ギャップを計算できません'},
            'tooltip_gap_value': {'zh': '差異: +{gap}s (+{percentage}%)', 'en': 'Gap: +{gap}s (+{percentage}%)', 'ja': 'ギャップ: +{gap}s (+{percentage}%)'},
            'tooltip_gap_near_perfect': {'zh': '評估: 接近完美單圈', 'en': 'Assessment: Near perfect lap', 'ja': '評価: ほぼ完璧なラップ'},
            'tooltip_gap_moderate': {'zh': '評估: 有中等提升空間', 'en': 'Assessment: Moderate improvement potential', 'ja': '評価: 中程度の改善余地あり'},
            'tooltip_gap_significant': {'zh': '評估: 有明顯改善空間', 'en': 'Assessment: Significant improvement potential', 'ja': '評価: 大幅な改善余地あり'},
            
            # Ranking Table Widget - 除錯與錯誤訊息
            'export_not_implemented': {'zh': '[TABLE_WIDGET] 匯出功能尚未實作', 'en': '[TABLE_WIDGET] Export feature not yet implemented', 'ja': '[TABLE_WIDGET] エクスポート機能は未実装'},
            'table_populate_failed': {'zh': '[TABLE_WIDGET] 填充表格失敗', 'en': '[TABLE_WIDGET] Failed to populate table', 'ja': '[TABLE_WIDGET] テーブルの入力に失敗しました'},
            'statistics_update_failed': {'zh': '[TABLE_WIDGET] 更新統計面板失敗', 'en': '[TABLE_WIDGET] Failed to update statistics panel', 'ja': '[TABLE_WIDGET] 統計パネルの更新に失敗しました'},
            'set_row_data_failed': {'zh': '[TABLE_WIDGET] 設置行資料失敗', 'en': '[TABLE_WIDGET] Failed to set row data', 'ja': '[TABLE_WIDGET] 行データの設定に失敗しました'},
            
            # Ideal Lap MDI - 視窗標題
            'ideal_lap_ranking_window_title': {'zh': '理想圈排名表格 - {year} {race} {session}', 'en': 'Ideal Lap Ranking - {year} {race} {session}', 'ja': '理想ラップランキング - {year} {race} {session}'},
            'ideal_lap_module_description': {'zh': 'F1 理想圈排名分析', 'en': 'F1 Ideal Lap Ranking Analysis', 'ja': 'F1 理想ラップランキング分析'},
            
            # Driver Position Analysis - 視窗標題 (F25)
            'driver_position_window_title': {'zh': '車手比賽排名 - {year} {race} {session}', 'en': 'Driver Race Position - {year} {race} {session}', 'ja': 'ドライバーレースポジション - {year} {race} {session}'},
            'driver_position_module_description': {'zh': 'F1 車手比賽排名分析', 'en': 'F1 Driver Race Position Analysis', 'ja': 'F1 ドライバーレースポジション分析'},
            
            # Sector Comparison - 表格欄位標題
            'sector_comparison_header_position': {'zh': '排名', 'en': 'Pos', 'ja': '順位'},
            'sector_comparison_header_driver': {'zh': '車手', 'en': 'Driver', 'ja': 'ドライバー'},
            'sector_comparison_header_s1_delta': {'zh': 'S1 差異', 'en': 'S1 Delta', 'ja': 'S1 差分'},
            'sector_comparison_header_s2_delta': {'zh': 'S2 差異', 'en': 'S2 Delta', 'ja': 'S2 差分'},
            'sector_comparison_header_s3_delta': {'zh': 'S3 差異', 'en': 'S3 Delta', 'ja': 'S3 差分'},
            'sector_comparison_header_cumulative': {'zh': '累積總差異', 'en': 'Cumulative Delta', 'ja': '累積差分'},
            
            # All Drivers Brake Performance Analysis - 表格欄位標題
            'brake_header_driver': {'zh': '車手', 'en': 'Driver', 'ja': 'ドライバー'},
            'brake_header_team': {'zh': '車隊', 'en': 'Team', 'ja': 'チーム'},
            'brake_header_max_deceleration_g': {'zh': '最大減速度 (G)', 'en': 'Max Decel (G)', 'ja': '最大減速度 (G)'},
            'brake_header_brake_time': {'zh': '煞車時間 (s)', 'en': 'Brake Time (s)', 'ja': 'ブレーキ時間 (s)'},
            'brake_header_avg_deceleration': {'zh': '平均減速度 (m/s²)', 'en': 'Avg Decel (m/s²)', 'ja': '平均減速度 (m/s²)'},
            'brake_header_brake_start_speed': {'zh': '起始速度 (km/h)', 'en': 'Start Speed (km/h)', 'ja': '開始速度 (km/h)'},
            'brake_header_brake_bar': {'zh': '煞車性能視覺化', 'en': 'Brake Performance', 'ja': 'ブレーキ性能ビジュアル'},
            
            # All Drivers Brake Performance Analysis - 資訊標籤
            'brake_performance_info_no_data': {'zh': '煞車範圍: 未載入資料', 'en': 'Brake Range: No Data Loaded', 'ja': 'ブレーキ範囲: データ未読み込み'},
            'brake_performance_info_range': {'zh': '煞車範圍: {start}m → {end}m (長度: {length}m)', 'en': 'Brake Range: {start}m → {end}m (Length: {length}m)', 'ja': 'ブレーキ範囲: {start}m → {end}m (長さ: {length}m)'},
            'brake_performance_info_reference': {'zh': ' | 參考車手: {driver}', 'en': ' | Reference Driver: {driver}', 'ja': ' | 基準ドライバー: {driver}'},
            
            # All Drivers Brake Performance Analysis - Tooltip
            'brake_performance_driver_tooltip': {'zh': '{driver} - {team}', 'en': '{driver} - {team}', 'ja': '{driver} - {team}'},
            'brake_performance_team_tooltip': {'zh': '{team}', 'en': '{team}', 'ja': '{team}'},
            'brake_deceleration_tooltip': {'zh': '{g:.2f} G ({ms2:.2f} m/s²)', 'en': '{g:.2f} G ({ms2:.2f} m/s²)', 'ja': '{g:.2f} G ({ms2:.2f} m/s²)'},
            'brake_speed_range': {'zh': '煞車前→煞車後: {start} → {end} km/h (減速 {reduction} km/h)', 'en': 'Before→After: {start} → {end} km/h (Reduction: {reduction} km/h)', 'ja': 'ブレーキ前→後: {start} → {end} km/h (減速: {reduction} km/h)'},
            
            # All Drivers Straight Line Speed Analysis - 表格欄位標題
            'speed_analysis_header_driver': {'zh': '車手', 'en': 'Driver', 'ja': 'ドライバー'},
            'speed_analysis_header_team': {'zh': '車隊', 'en': 'Team', 'ja': 'チーム'},
            'speed_analysis_header_max_speed': {'zh': '最高速度 (km/h)', 'en': 'Max Speed (km/h)', 'ja': '最高速度 (km/h)'},
            'speed_analysis_header_segment_accel_time': {'zh': '加速時間 (s)', 'en': 'Accel Time (s)', 'ja': '加速時間 (s)'},
            'speed_analysis_header_segment_avg_accel': {'zh': '平均加速度 (m/s²)', 'en': 'Avg Accel (m/s²)', 'ja': '平均加速度 (m/s²)'},
            'speed_analysis_header_segment_start_speed': {'zh': '起始速度 (km/h)', 'en': 'Start Speed (km/h)', 'ja': '開始速度 (km/h)'},
            'speed_analysis_header_max_speed_time': {'zh': '最高速度時間 (s)', 'en': 'Max Speed Time (s)', 'ja': '最高速度時間 (s)'},
            'speed_analysis_header_accel_bar': {'zh': '加速性能視覺化', 'en': 'Accel Performance', 'ja': '加速性能ビジュアル'},
            
            # All Drivers Straight Line Speed Analysis - 資訊標籤
            'straight_speed_info_no_data': {'zh': '分析範圍: 未載入資料', 'en': 'Analysis Range: No Data Loaded', 'ja': '分析範囲: データ未読み込み'},
            'straight_speed_info_range': {'zh': '分析範圍: {start}m → {end}m (長度: {length}m)', 'en': 'Analysis Range: {start}m → {end}m (Length: {length}m)', 'ja': '分析範囲: {start}m → {end}m (長さ: {length}m)'},
            'straight_speed_info_reference': {'zh': ' | 參考車手: {driver}', 'en': ' | Reference Driver: {driver}', 'ja': ' | 基準ドライバー: {driver}'},
            
            # All Drivers Straight Line Speed Analysis - Tooltip
            'straight_speed_driver_tooltip': {'zh': '{driver} - {team}', 'en': '{driver} - {team}', 'ja': '{driver} - {team}'},
            'straight_speed_team_tooltip': {'zh': '{team}', 'en': '{team}', 'ja': '{team}'},
            'straight_speed_start_speed_tooltip': {'zh': '起始→結束: {start} → {end} km/h', 'en': 'Start→End: {start} → {end} km/h', 'ja': '開始→終了: {start} → {end} km/h'},
            
            # All Drivers Straight Line Speed Analysis - 車手詳細資訊
            'straight_speed_driver_details': {
                'zh': '''車手詳細資訊 - {driver}

車手: {driver}
車隊: {team}

最高速度: {max_speed} km/h

加速性能 (100 → 300 km/h):
  時間: {accel_100_300_time} s
  距離: {accel_distance} m
  平均加速度: {accel_avg} m/s²

加速性能 (100 → {max_speed_full} km/h):
  時間: {time_to_max} s''',
                'en': '''Driver Details - {driver}

Driver: {driver}
Team: {team}

Max Speed: {max_speed} km/h

Acceleration (100 → 300 km/h):
  Time: {accel_100_300_time} s
  Distance: {accel_distance} m
  Avg Acceleration: {accel_avg} m/s²

Acceleration (100 → {max_speed_full} km/h):
  Time: {time_to_max} s''',
                'ja': '''ドライバー詳細 - {driver}

ドライバー: {driver}
チーム: {team}

最高速度: {max_speed} km/h

加速性能 (100 → 300 km/h):
  時間: {accel_100_300_time} s
  距離: {accel_distance} m
  平均加速度: {accel_avg} m/s²

加速性能 (100 → {max_speed_full} km/h):
  時間: {time_to_max} s'''
            },
            'straight_speed_driver_info_title': {'zh': '車手資訊 - {driver}', 'en': 'Driver Info - {driver}', 'ja': 'ドライバー情報 - {driver}'},
            
            # 通用字串
            'na': {'zh': 'N/A', 'en': 'N/A', 'ja': 'N/A'},
            'unknown': {'zh': '未知', 'en': 'Unknown', 'ja': '不明'},
            
            # Weather Timeline Widget - 標題與區塊
            'weather_timeline_title': {'zh': '比賽週末天氣時間軸', 'en': 'Race Weekend Weather Timeline', 'ja': 'レースウィークエンド天気タイムライン'},
            'weather_history_title': {'zh': '歷史天氣對比', 'en': 'Historical Weather Comparison', 'ja': '過去の天気比較'},
            'weather_test_window': {'zh': '天氣時間軸測試視窗', 'en': 'Weather Timeline Widget Test', 'ja': 'ウェザータイムラインテストウィンドウ'},
            'weather_loading_status': {'zh': '正在從 API 載入天氣數據...', 'en': 'Loading weather data from API...', 'ja': 'APIから天気データを読み込んでいます...'},
            
            # Weather Timeline Widget - 日期標籤
            'weather_day_minus_2': {'zh': '前2天\n{date}', 'en': '2 Days Before\n{date}', 'ja': '2日前\n{date}'},
            'weather_day_minus_1': {'zh': '前1天\n{date}', 'en': '1 Day Before\n{date}', 'ja': '1日前\n{date}'},
            'weather_race_day': {'zh': '比賽日\n{date}', 'en': 'Race Day\n{date}', 'ja': 'レース当日\n{date}'},
            
            # Weather Timeline Widget - 時間軸節點預設值
            'weather_temp_loading': {'zh': '--', 'en': '--', 'ja': '--'},
            'weather_icon_loading': {'zh': '...', 'en': '...', 'ja': '...'},
            'weather_rain_loading': {'zh': '--', 'en': '--', 'ja': '--'},
            'weather_wind_loading': {'zh': '--', 'en': '--', 'ja': '--'},
            
            # Weather Timeline Widget - 數據顯示格式
            'weather_temp_celsius': {'zh': '{temp:.1f}°C', 'en': '{temp:.1f}°C', 'ja': '{temp:.1f}°C'},
            'weather_rain_mm': {'zh': '{precip:.1f}mm', 'en': '{precip:.1f}mm', 'ja': '{precip:.1f}mm'},
            'weather_wind_kmh': {'zh': '{arrow} {speed:.0f}km/h', 'en': '{arrow} {speed:.0f}km/h', 'ja': '{arrow} {speed:.0f}km/h'},
            'weather_wind_speed': {'zh': ', 風速 {speed:.0f}km/h', 'en': ', Wind Speed {speed:.0f}km/h', 'ja': ', 風速 {speed:.0f}km/h'},
            
            # Weather Timeline Widget - 歷史數據格式
            'weather_history_2024': {
                'zh': '2024 年 ({date}): {icon} {temp_min:.1f}°C ~ {temp_max:.1f}°C, 降雨 {precip:.1f}mm',
                'en': '2024 ({date}): {icon} {temp_min:.1f}°C ~ {temp_max:.1f}°C, Precipitation {precip:.1f}mm',
                'ja': '2024年 ({date}): {icon} {temp_min:.1f}°C ~ {temp_max:.1f}°C, 降水量 {precip:.1f}mm'
            },
            'weather_history_2023': {
                'zh': '2023 年 ({date}): {icon} {temp_min:.1f}°C ~ {temp_max:.1f}°C, 降雨 {precip:.1f}mm',
                'en': '2023 ({date}): {icon} {temp_min:.1f}°C ~ {temp_max:.1f}°C, Precipitation {precip:.1f}mm',
                'ja': '2023年 ({date}): {icon} {temp_min:.1f}°C ~ {temp_max:.1f}°C, 降水量 {precip:.1f}mm'
            },
            
            # Qualifying Prediction Widget (F74) - 視窗標題與模組描述
            'qualifying_prediction_window_title': {'zh': '排位賽預測 - {year} {race}', 'en': 'Qualifying Prediction - {year} {race}', 'ja': '予選予測 - {year} {race}'},
            'qualifying_prediction_module_description': {'zh': 'F1 排位賽預測分析', 'en': 'F1 Qualifying Prediction Analysis', 'ja': 'F1 予選予測分析'},
            
            # Qualifying Prediction Widget - 統計摘要面板
            'prediction_statistics': {'zh': '預測統計摘要', 'en': 'Prediction Statistics', 'ja': '予測統計サマリー'},
            'total_drivers_label': {'zh': '總車手數: -', 'en': 'Total Drivers: -', 'ja': '総ドライバー数: -'},
            'total_drivers_value': {'zh': '總車手數: {count}', 'en': 'Total Drivers: {count}', 'ja': '総ドライバー数: {count}'},
            'track_info_label': {'zh': '賽道: -', 'en': 'Track: -', 'ja': 'サーキット: -'},
            'track_info_value': {'zh': '賽道: {track} {year}', 'en': 'Track: {track} {year}', 'ja': 'サーキット: {track} {year}'},
            'model_r2_label': {'zh': '模型 R²: -', 'en': 'Model R²: -', 'ja': 'モデル R²: -'},
            'model_r2_value': {'zh': '模型 R²: {r2} (樣本數: {count})', 'en': 'Model R²: {r2} (Samples: {count})', 'ja': 'モデル R²: {r2} (サンプル数: {count})'},
            'model_mae_label': {'zh': '模型 MAE: -', 'en': 'Model MAE: -', 'ja': 'モデル MAE: -'},
            'model_mae_value': {'zh': '模型 MAE: {mae}s (平均誤差)', 'en': 'Model MAE: {mae}s (Avg Error)', 'ja': 'モデル MAE: {mae}s (平均誤差)'},
            'r2_explanation': {'zh': 'R² 說明: {text}', 'en': 'R² Explanation: {text}', 'ja': 'R² 説明: {text}'},
            
            # Qualifying Prediction Widget - 表格欄位標題
            'rank': {'zh': '排名', 'en': 'Rank', 'ja': '順位'},
            'driver': {'zh': '車手', 'en': 'Driver', 'ja': 'ドライバー'},
            'team': {'zh': '車隊', 'en': 'Team', 'ja': 'チーム'},
            'fp3_time': {'zh': 'FP3 時間', 'en': 'FP3 Time', 'ja': 'FP3 タイム'},
            'fp2_time': {'zh': 'FP2 時間', 'en': 'FP2 Time', 'ja': 'FP2 タイム'},
            'predicted_time': {'zh': '預測時間', 'en': 'Predicted Time', 'ja': '予測タイム'},
            'q_result': {'zh': 'Q 時間', 'en': 'Q Time', 'ja': 'Q タイム'},
            'delta_fp3': {'zh': '△ FP3', 'en': '△ FP3', 'ja': '△ FP3'},
            'delta_fp2': {'zh': '△ FP2', 'en': '△ FP2', 'ja': '△ FP2'},
            'fp3_rank': {'zh': '預測名次', 'en': 'Pred Rank', 'ja': '予測順位'},
            'fp2_rank': {'zh': 'FP2 名次', 'en': 'FP2 Rank', 'ja': 'FP2 順位'},
            'q_rank': {'zh': 'Q 名次', 'en': 'Q Rank', 'ja': 'Q 順位'},
            'rank_change': {'zh': '變化', 'en': 'Change', 'ja': '変化'},
            
            # Splash Screen - Startup Progress Messages
            'splash_initializing': {'zh': '正在初始化系統', 'en': 'Initializing System', 'ja': 'システムを初期化中'},
            'splash_loading_window': {'zh': '正在載入視窗', 'en': 'Loading Window', 'ja': 'ウィンドウを読み込み中'},
            'splash_loading_state': {'zh': '正在載入狀態管理', 'en': 'Loading State Manager', 'ja': '状態管理を読み込み中'},
            'splash_loading_calendar': {'zh': '正在載入賽季日曆', 'en': 'Loading Season Calendar', 'ja': 'シーズンカレンダーを読み込み中'},
            'splash_loading_colors': {'zh': '正在載入顏色配置', 'en': 'Loading Color Palette', 'ja': 'カラーパレットを読み込み中'},
            'splash_loading_ui': {'zh': '正在載入使用者介面', 'en': 'Loading User Interface', 'ja': 'ユーザーインターフェースを読み込み中'},
            'splash_applying_style': {'zh': '正在套用視覺樣式', 'en': 'Applying Visual Style', 'ja': 'ビジュアルスタイルを適用中'},
            'splash_setup_linkage': {'zh': '正在設定連動管理器', 'en': 'Setting up Linkage Manager', 'ja': 'リンク管理を設定中'},
            'splash_setup_api': {'zh': '正在設定API監控', 'en': 'Setting up API Monitor', 'ja': 'APIモニターを設定中'},
            'splash_complete': {'zh': '初始化完成', 'en': 'Initialization Complete', 'ja': '初期化完了'},
            'splash_error_continue': {'zh': '發生錯誤，繼續初始化', 'en': 'Error occurred, continuing', 'ja': 'エラー発生、続行中'},
            'splash_error_opening': {'zh': '初始化失敗，嘗試開啟', 'en': 'Init failed, attempting to open', 'ja': '初期化失敗、開こうとしています'},
            'error_initialization_failed': {'zh': '初始化失敗', 'en': 'Initialization Failed', 'ja': '初期化失敗'},
            'error_init_message': {'zh': 'GUI 初始化過程中發生錯誤，部分功能可能無法使用', 'en': 'An error occurred during GUI initialization. Some features may be unavailable.', 'ja': 'GUI初期化中にエラーが発生しました。一部の機能が利用できない可能性があります'},
            
            # ==== FIA Parts Analysis Module ====
            # 類型說明翻譯 (Description)
            'desc_repair': {
                'zh': '損壞後更換舊件/備件、小零件維護、冷卻系統管路',
                'en': 'Replacement of damaged parts/spares, minor maintenance, cooling system lines',
                'ja': '破損部品/スペアの交換、小部品のメンテナンス、冷却システム配管'
            },
            'desc_major_update': {
                'zh': '結構性改動、觸發 FIA 重新檢驗、非全新套件',
                'en': 'Structural modifications, triggers FIA re-inspection, non-new package',
                'ja': '構造的変更、FIA再検査トリガー、非新パッケージ'
            },
            'desc_change': {
                'zh': 'Parc Fermé 內合法調整、空力/配置切換、摩擦材料、懸吊',
                'en': 'Legal adjustments within Parc Fermé, aero/config switches, friction materials, suspension',
                'ja': 'Parc Fermé内合法調整、空力/設定切替、摩擦材料、サスペンション'
            },
            'desc_param_adjustment': {
                'zh': '純軟體參數變更，無硬體更換',
                'en': 'Software parameter changes only, no hardware replacement',
                'ja': 'ソフトウェアパラメータ変更のみ、ハードウェア交換なし'
            },
            'desc_safety_standard': {
                'zh': 'FIA 標準安全設備、駕駛介面',
                'en': 'FIA standard safety equipment, driver interface',
                'ja': 'FIA標準安全装備、ドライバーインターフェース'
            },
            'desc_unclassified': {
                'zh': '無法根據現有規則分類（信心度低於 0.60）',
                'en': 'Cannot be classified by existing rules (confidence below 0.60)',
                'ja': '既存ルールで分類不可（信頼度0.60未満）'
            },
            
            # 選單和樹狀圖項目
            'parts_analysis': {
                'zh': '車輛零件變動',
                'en': 'Vehicle Parts Changes',
                'ja': '車両部品変更'
            },
            'menu_parts_analysis': {
                'zh': '車輛零件變動',
                'en': 'Vehicle Parts Changes',
                'ja': '車両部品変更'
            },
        }
    
    def t(self, key, default=None):
        """
        翻譯指定的鍵值
        Args:
            key: 翻譯鍵值
            default: 預設值（如果找不到翻譯）
        Returns:
            翻譯後的文字
        """
        if key in self._translations:
            return self._translations[key].get(self.language, 
                                              self._translations[key].get('en', key))
        return default or key
    
    def set_language(self, language):
        """切換語言 (支援 zh/en/ja)"""
        if language in ['zh', 'en', 'ja']:
            self.language = language
            # 保存語言設定
            self._save_language(language)
            logger.debug(f"[GUI_I18N]  語言已切換至: {language}")
            return True
        logger.debug(f"[GUI_I18N]  不支援的語言: {language}")
        return False
    
    def get_language(self):
        """取得當前語言"""
        return self.language


# 全域翻譯器實例
_gui_translator = GuiTranslator('en')  # 預設為英文

def set_gui_language(language):
    """設定 GUI 語言"""
    return _gui_translator.set_language(language)

def get_gui_language():
    """取得當前 GUI 語言"""
    return _gui_translator.get_language()


def set_current_language(language):
    """向後相容別名，等同於 set_gui_language"""
    return set_gui_language(language)


def get_current_language():
    """向後相容別名，等同於 get_gui_language"""
    return get_gui_language()

def tr(key, default=None):
    """
    翻譯函數的簡寫
    Args:
        key: 翻譯鍵值
        default: 預設值
    Returns:
        翻譯後的文字
    """
    return _gui_translator.t(key, default)

# 遙測選項的完整翻譯對應
TELEMETRY_OPTIONS = {
    'Speed (km/h)': {'zh': '速度 (Speed)', 'en': 'Speed (km/h)', 'ja': 'Speed (km/h)'},
    'Throttle (%)': {'zh': '油門 (Throttle)', 'en': 'Throttle (%)', 'ja': 'Throttle (%)'},
    'Brake (%)': {'zh': '煞車 (Brake)', 'en': 'Brake (%)', 'ja': 'Brake (%)'},
    'Gear': {'zh': '檔位 (Gear)', 'en': 'Gear', 'ja': 'ギア'},
    'DRS': {'zh': 'DRS', 'en': 'DRS', 'ja': 'DRS'},
    'RPM': {'zh': '轉速 (RPM)', 'en': 'RPM', 'ja': 'RPM'},
    'Steering Angle': {'zh': '方向盤轉角 (Steering)', 'en': 'Steering Angle', 'ja': 'Steering Angle'},
}

def get_telemetry_option_text(option_key, language=None):
    """取得遙測選項的翻譯文字"""
    if language is None:
        language = _gui_translator.get_language()
    
    if option_key in TELEMETRY_OPTIONS:
        return TELEMETRY_OPTIONS[option_key].get(language, option_key)
    return option_key

# F1 車隊名稱的完整翻譯對應
TEAM_NAMES = {
    'Red Bull': {'zh': '紅牛', 'en': 'Red Bull', 'ja': 'レッドブル'},
    'Red Bull Racing': {'zh': '紅牛車隊', 'en': 'Red Bull Racing', 'ja': 'レッドブル・レーシング'},
    'Ferrari': {'zh': '法拉利', 'en': 'Ferrari', 'ja': 'フェラーリ'},
    'Mercedes': {'zh': '梅賽德斯', 'en': 'Mercedes', 'ja': 'メルセデス'},
    'McLaren': {'zh': '麥拉倫', 'en': 'McLaren', 'ja': 'マクラーレン'},
    'Aston Martin': {'zh': '奧斯頓馬丁', 'en': 'Aston Martin', 'ja': 'アストンマーティン'},
    'Alpine': {'zh': '阿爾派', 'en': 'Alpine', 'ja': 'アルピーヌ'},
    'Williams': {'zh': '威廉斯', 'en': 'Williams', 'ja': 'ウィリアムズ'},
    'RB': {'zh': 'RB', 'en': 'RB', 'ja': 'RB'},
    'Haas': {'zh': '哈斯', 'en': 'Haas', 'ja': 'ハース'},
    'Sauber': {'zh': '索伯', 'en': 'Sauber', 'ja': 'ザウバー'},
    'Kick Sauber': {'zh': 'Kick 索伯', 'en': 'Kick Sauber', 'ja': 'キック・ザウバー'},
    'AlphaTauri': {'zh': '紅牛二隊', 'en': 'AlphaTauri', 'ja': 'アルファタウリ'},
    'Alfa Romeo': {'zh': '愛快羅密歐', 'en': 'Alfa Romeo', 'ja': 'アルファロメオ'},
    'Unknown': {'zh': '未知車隊', 'en': 'Unknown', 'ja': '不明'},
}

def get_team_name_text(team_key, language=None):
    """
    取得車隊名稱的翻譯文字
    
    Args:
        team_key: 車隊名稱（英文原始名稱）
        language: 語言代碼 ('zh', 'en', 'ja')，若為 None 則使用當前語言
    
    Returns:
        str: 翻譯後的車隊名稱
    """
    if language is None:
        language = _gui_translator.get_language()
    
    # 完全匹配
    if team_key in TEAM_NAMES:
        return TEAM_NAMES[team_key].get(language, team_key)
    
    # 模糊匹配（處理可能包含 "F1 Team" 後綴的情況）
    team_key_normalized = team_key.replace(" F1 Team", "").strip()
    if team_key_normalized in TEAM_NAMES:
        return TEAM_NAMES[team_key_normalized].get(language, team_key)
    
    # 部分匹配（檢查是否包含已知車隊名稱）
    for known_team in TEAM_NAMES.keys():
        if known_team in team_key or team_key in known_team:
            return TEAM_NAMES[known_team].get(language, team_key)
    
    # 找不到匹配，返回原始名稱
    return team_key
