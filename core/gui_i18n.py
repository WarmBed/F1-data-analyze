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
            'about_action': {'zh': '關於 PITWALL', 'en': 'About PITWALL', 'ja': 'PITWALL について'},
            
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
            
            # 超車事件 Tooltip
            'overtake_event': {'zh': '超車事件', 'en': 'Overtake Event', 'ja': '追い抜き'},
            'overtaking_driver': {'zh': '超車車手', 'en': 'Overtaking Driver', 'ja': '追い抜きドライバー'},
            'overtaken_driver': {'zh': '被超車手', 'en': 'Overtaken Driver', 'ja': '追い抜かれたドライバー'},
            'position_change': {'zh': '排名變化', 'en': 'Position Change', 'ja': '順位変動'},
            
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
            
            # Box Plot Tab 翻譯
            'boxplot.tab.chart': {'zh': '圖表', 'en': 'Chart', 'ja': 'チャート'},
            'boxplot.tab.stint_selection': {'zh': 'Stint 選擇', 'en': 'Stint Selection', 'ja': 'スティント選択'},
            
            # Stint Selector 翻譯
            'stint.merge_mode': {'zh': '合併模式 (每車手一個 Box)', 'en': 'Merge Mode (One Box per Driver)', 'ja': 'マージモード (ドライバーごとに1ボックス)'},
            'stint.merge_mode_tooltip': {
                'zh': '勾選時，每位車手選中的所有 Stint 合併為一個 Box。\n取消勾選時，每個 Stint 顯示為獨立的 Box。',
                'en': 'When checked, all selected stints for each driver are merged into one box.\nWhen unchecked, each stint is shown as a separate box.',
                'ja': 'チェック時、各ドライバーの選択されたスティントが1つのボックスに統合されます。\nチェック解除時、各スティントが個別のボックスとして表示されます。'
            },
            'stint.select_all': {'zh': '全選', 'en': 'Select All', 'ja': '全選択'},
            'stint.deselect_all': {'zh': '取消全選', 'en': 'Deselect All', 'ja': '全選択解除'},
            'stint.detected_stints': {'zh': '偵測到的 Stints', 'en': 'Detected Stints', 'ja': '検出されたスティント'},
            'stint.col.driver': {'zh': '車手 / Stint', 'en': 'Driver / Stint', 'ja': 'ドライバー / スティント'},
            'stint.col.laps': {'zh': '圈數範圍', 'en': 'Lap Range', 'ja': 'ラップ範囲'},
            'stint.col.compound': {'zh': '胎型', 'en': 'Compound', 'ja': 'コンパウンド'},
            'stint.col.count': {'zh': '圈數', 'en': 'Laps', 'ja': 'ラップ数'},
            'stint.col.avg_time': {'zh': '平均圈速', 'en': 'Avg Time', 'ja': '平均タイム'},
            'stint.legend': {
                'zh': 'Stints 基於進站標記自動偵測。勾選/取消勾選以包含在分析中。',
                'en': 'Stints are detected by pit stop markers. Check/uncheck to include in analysis.',
                'ja': 'スティントはピットストップマーカーで検出されます。分析に含めるにはチェック/チェック解除してください。'
            },
            'stint.waiting': {'zh': '等待數據...', 'en': 'Waiting for data...', 'ja': 'データを待っています...'},
            'stint.stats': {'zh': '車手: {drivers} | Stints: {selected}/{total}', 'en': 'Drivers: {drivers} | Stints: {selected}/{total}', 'ja': 'ドライバー: {drivers} | スティント: {selected}/{total}'},
            
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
            
            # Pedal Behavior Analysis 油門/煞車行為分析模組
            'pedal_behavior_analysis': {'zh': '油門/煞車行為分析', 'en': 'Pedal Behavior Analysis', 'ja': 'ペダル動作分析'},
            'pedal_behavior_analysis_desc': {
                'zh': '顯示油門、煞車、Trail Braking、滑行四種狀態的堆疊百分比',
                'en': 'Stacked bar chart showing Throttle, Brake, Trail Braking, Coasting percentages',
                'ja': 'スロットル、ブレーキ、トレイルブレーキ、コースティングの割合を積み上げ棒グラフで表示'
            },
            'pedal_state.throttle_only': {'zh': '全油門', 'en': 'Throttle Only', 'ja': 'スロットルのみ'},
            'pedal_state.brake_only': {'zh': '全煞車', 'en': 'Brake Only', 'ja': 'ブレーキのみ'},
            'pedal_state.trail_braking': {'zh': 'Trail Braking', 'en': 'Trail Braking', 'ja': 'トレイルブレーキ'},
            'pedal_state.coasting': {'zh': '滑行', 'en': 'Coasting', 'ja': 'コースティング'},
            'pedal_behavior.chart_title': {
                'zh': '{year} {race} {session} - 油門/煞車行為分析',
                'en': '{year} {race} {session} - Pedal Behavior Analysis',
                'ja': '{year} {race} {session} - ペダル動作分析'
            },
            'pedal_behavior.no_data': {'zh': '無數據', 'en': 'No Data', 'ja': 'データなし'},
            'pedal_behavior.reload': {'zh': '重新載入', 'en': 'Reload', 'ja': '再読み込み'},
            'pedal_behavior.export': {'zh': '匯出圖表', 'en': 'Export Chart', 'ja': 'チャートをエクスポート'},
            'pedal_behavior.filter_pit': {'zh': '排除進站圈', 'en': 'Exclude Pit Laps', 'ja': 'ピットラップを除外'},
            'pedal_behavior.filter_yellow': {'zh': '排除黃旗', 'en': 'Exclude Yellow Flag', 'ja': '黄旗を除外'},
            'pedal_behavior.filter_red': {'zh': '排除紅旗', 'en': 'Exclude Red Flag', 'ja': '赤旗を除外'},
            'pedal_behavior.filter_sc': {'zh': '排除 SC', 'en': 'Exclude SC', 'ja': 'SCを除外'},
            'pedal_behavior.filter_vsc': {'zh': '排除 VSC', 'en': 'Exclude VSC', 'ja': 'VSCを除外'},
            'pedal_behavior.legend': {'zh': '圖例', 'en': 'Legend', 'ja': '凡例'},
            'pedal_behavior.percentage': {'zh': '百分比 (%)', 'en': 'Percentage (%)', 'ja': 'パーセント (%)'},
            'pedal_behavior.tab_chart': {'zh': '圖表', 'en': 'Chart', 'ja': 'チャート'},
            'pedal_behavior.tab_stint': {'zh': 'Stint 選擇', 'en': 'Stint Selection', 'ja': 'スティント選択'},
            
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
            'export_pdf_report': {'zh': '匯出所有分頁為 PDF', 'en': 'Export All Tabs to PDF', 'ja': '全タブをPDFにエクスポート'},
            'pdf_export_error': {'zh': 'PDF 匯出錯誤', 'en': 'PDF Export Error', 'ja': 'PDFエクスポートエラー'},
            'pdf_reportlab_missing': {
                'zh': 'reportlab 函式庫未安裝。\n\n請執行：\npip install reportlab',
                'en': 'reportlab library is not installed.\n\nPlease install it with:\npip install reportlab',
                'ja': 'reportlabライブラリがインストールされていません。\n\n次のコマンドでインストールしてください:\npip install reportlab'
            },
            'pdf_export_info': {'zh': 'PDF 匯出', 'en': 'PDF Export', 'ja': 'PDFエクスポート'},
            'pdf_no_tabs': {'zh': '沒有分頁可匯出（Home 分頁已跳過）。', 'en': 'No tabs to export (Home tab is skipped).', 'ja': 'エクスポートするタブがありません（ホームタブはスキップ）。'},
            'pdf_no_content': {'zh': '沒有內容可匯出的分頁。', 'en': 'No tabs with content to export.', 'ja': 'エクスポートするコンテンツのあるタブがありません。'},
            'pdf_export_success': {'zh': 'PDF 匯出成功', 'en': 'PDF Export Successful', 'ja': 'PDFエクスポート成功'},
            'pdf_export_saved': {'zh': '報告已儲存至：\n{path}', 'en': 'Report saved to:\n{path}', 'ja': 'レポートの保存先:\n{path}'},
            'pdf_export_failed': {'zh': 'PDF 匯出失敗：\n{error}', 'en': 'Failed to export PDF:\n{error}', 'ja': 'PDFエクスポートに失敗しました:\n{error}'},
            'exit': {'zh': '結束', 'en': 'Exit', 'ja': '終了'},
            
            # Analysis Menu 項目
            'rain_analysis': {'zh': '降雨分析', 'en': 'Rain Analysis', 'ja': '降雨分析'},
            'track_analysis': {'zh': '賽道分析', 'en': 'Track Analysis', 'ja': 'トラック分析'},
            'race_overview': {'zh': '賽事概覽', 'en': 'Race Overview', 'ja': 'レース概要'},
            'telemetry_analysis': {'zh': '遙測分析', 'en': 'Telemetry Analysis', 'ja': 'テレメトリー分析'},
            'telemetry_comparison': {'zh': '遙測對比', 'en': 'Telemetry Comparison', 'ja': 'テレメトリー比較'},
            'driver_comparison': {'zh': '車手對比', 'en': 'Driver Comparison', 'ja': 'ドライバー比較'},
            'sector_analysis': {'zh': '賽段分析', 'en': 'Sector Analysis', 'ja': 'セクター分析'},
            
            # === 樹狀圖主分類翻譯 ===
            'historical_analysis': {'zh': '歷史分析', 'en': 'Historical Analysis', 'ja': '歴史分析'},
            'lap_performance': {'zh': '圈速表現', 'en': 'Lap Performance', 'ja': 'ラップパフォーマンス'},
            'ideal_lap_sectors': {'zh': '理想圈與分段', 'en': 'Ideal Lap & Sectors', 'ja': '理想ラップ＆セクター'},
            'speed_corner_analysis': {'zh': '速度與彎道分析', 'en': 'Speed & Corner Analysis', 'ja': 'スピード＆コーナー分析'},
            'prediction_models': {'zh': '預測模型', 'en': 'Prediction Models', 'ja': '予測モデル'},
            'all_drivers_acceleration_chart': {'zh': '加速度圖表', 'en': 'Acceleration Chart', 'ja': '加速度チャート'},
            'all_drivers_brake_chart': {'zh': '煞車圖表', 'en': 'Brake Chart', 'ja': 'ブレーキチャート'},
            'all_drivers_brake_all_laps_analysis': {'zh': '全車手煞車全圈數分析', 'en': 'All Drivers Brake All Laps Analysis', 'ja': '全ドライバーブレーキ全周分析'},
            'long_run_analysis': {'zh': '長距離與輪胎衰退', 'en': 'Long Run & Degradation', 'ja': 'ロングラン＆劣化'},
            
            # Long Run Analysis Tab Labels
            'long_run.tab.stint': {'zh': '長跑選擇', 'en': 'Stint Selection', 'ja': 'スティント選択'},
            'long_run.tab.fuel': {'zh': '燃油設定', 'en': 'Fuel Settings', 'ja': '燃料設定'},
            'long_run.tab.track': {'zh': '賽道演進', 'en': 'Track Evolution', 'ja': 'トラック進化'},
            'long_run.tab.results': {'zh': '衰退結果', 'en': 'Degradation Results', 'ja': '劣化結果'},
            'long_run.tab.chart': {'zh': '圖表檢視', 'en': 'Chart View', 'ja': 'チャートビュー'},
            
            # Long Run Analysis Translations
            'long_run.chart.drivers': {'zh': '車手', 'en': 'Drivers', 'ja': 'ドライバー'},
            'long_run.chart.options': {'zh': '圖表選項', 'en': 'Chart Options', 'ja': 'チャートオプション'},
            'long_run.filter.all': {'zh': '所有配方', 'en': 'All Compounds', 'ja': 'すべてのコンパウンド'},
            'long_run.filter.soft': {'zh': '僅 SOFT', 'en': 'SOFT only', 'ja': 'SOFTのみ'},
            'long_run.filter.medium': {'zh': '僅 MEDIUM', 'en': 'MEDIUM only', 'ja': 'MEDIUMのみ'},
            'long_run.filter.hard': {'zh': '僅 HARD', 'en': 'HARD only', 'ja': 'HARDのみ'},
            'long_run.sim.label': {'zh': '模擬:', 'en': 'Sim:', 'ja': 'シム:'},
            'long_run.sim.tooltip_recommended': {'zh': '建議 Sim 值: {0} (基於 {1} 車隊燃油習慣)\n0 = FP2 模式, >0 = 賽車模擬模式', 'en': 'Recommended Sim: {0} (based on {1} fuel habits)\n0 = FP2 mode, >0 = Race simulation mode', 'ja': '推奨Sim値: {0} ({1}の燃料習慣に基づく)\n0 = FP2モード, >0 = レースシミュレーションモード'},
            'long_run.sim.tooltip_default': {'zh': '模擬 {0} 的賽車圈速 (0 = FP2 模式)', 'en': 'Simulate race lap for {0} (0 = FP2 mode)', 'ja': '{0}のレースラップをシミュレート (0 = FP2モード)'},
            'long_run.excl.placeholder': {'zh': '排除: 20,22', 'en': 'Excl: 20,22', 'ja': '除外: 20,22'},
            'long_run.excl.tooltip': {'zh': '排除 {0} 的圈數: 例如 20,22 或 18-20', 'en': 'Exclude laps for {0}: e.g. 20,22 or 18-20', 'ja': '{0}の周回を除外: 例: 20,22 または 18-20'},
            'long_run.status.long_run': {'zh': '長距離 (std={0:.2f}s)', 'en': 'Long Run (std={0:.2f}s)', 'ja': 'ロングラン (std={0:.2f}s)'},
            'long_run.status.short': {'zh': '短距離 ({0} 圈)', 'en': 'Short ({0} laps)', 'ja': '短距離 ({0}周)'},
            'long_run.status.inconsistent': {'zh': '不穩定 (std={0:.2f}s)', 'en': 'Inconsistent (std={0:.2f}s)', 'ja': '不安定 (std={0:.2f}s)'},
            'long_run.action.double_click': {'zh': '雙擊以編輯', 'en': 'Double-click to edit', 'ja': 'ダブルクリックして編集'},
            
            'pole_defense_statistics': {'zh': '桿位防守統計', 'en': 'Pole Defense Statistics', 'ja': 'ポールディフェンス統計'},
            'traffic_analysis': {'zh': '車流分析', 'en': 'Traffic Analysis', 'ja': 'トラフィック分析'},
            'time_diff_analysis': {'zh': '時間差分析', 'en': 'Time Diff Analysis', 'ja': 'タイム差分析'},
            
            # Pit Loss Table Module 翻譯
            'pit_loss_table.title': {'zh': '進站時間損失表', 'en': 'Pit Loss Table', 'ja': 'ピットタイムロス表'},
            'pit_loss_table.window_title': {'zh': '賽道進站時間損失總覽', 'en': 'Circuit Pit Time Loss Overview', 'ja': 'サーキットピットタイムロス概要'},
            'pit_loss_table.col_circuit': {'zh': '賽道', 'en': 'Circuit', 'ja': 'サーキット'},
            'pit_loss_table.col_green_flag': {'zh': '綠旗 (秒)', 'en': 'Green Flag (s)', 'ja': 'グリーンフラッグ (秒)'},
            'pit_loss_table.col_vsc': {'zh': 'VSC (秒)', 'en': 'VSC (s)', 'ja': 'VSC (秒)'},
            'pit_loss_table.col_sc': {'zh': 'SC (秒)', 'en': 'SC (s)', 'ja': 'SC (秒)'},
            'pit_loss_table.col_samples': {'zh': '樣本數', 'en': 'Samples', 'ja': 'サンプル数'},
            'pit_loss_table.col_source': {'zh': '來源', 'en': 'Source', 'ja': 'ソース'},
            'pit_loss_table.sort_by': {'zh': '排序方式', 'en': 'Sort by', 'ja': '並び替え'},
            'pit_loss_table.trained': {'zh': '訓練', 'en': 'Trained', 'ja': '訓練済み'},
            'pit_loss_table.estimated': {'zh': '估算', 'en': 'Estimated', 'ja': '推定'},
            'pit_loss_table.status.ready': {'zh': '就緒 - 共 {} 條賽道記錄', 'en': 'Ready - {} circuit records loaded', 'ja': '準備完了 - {}サーキット記録読込済み'},
            'pit_loss_table.status.load_error': {'zh': '載入錯誤', 'en': 'Load Error', 'ja': '読込エラー'},
            'pit_loss_table.status.load_error_msg': {'zh': '無法載入進站時間損失數據:\n{}', 'en': 'Failed to load pit loss data:\n{}', 'ja': 'ピットタイムロスデータの読込失敗:\n{}'},
            
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
            
            # Module Help System / 模組說明系統
            'module_help_tooltip': {'zh': '模組說明', 'en': 'Module Help', 'ja': 'モジュールヘルプ'},
            'module_help_title': {'zh': '模組說明', 'en': 'Module Help', 'ja': 'モジュールヘルプ'},
            'help_section_description': {'zh': '功能說明', 'en': 'Description', 'ja': '機能説明'},
            'help_section_features': {'zh': '功能特點', 'en': 'Features', 'ja': '機能'},
            'help_section_colors': {'zh': '顏色圖例', 'en': 'Color Legend', 'ja': 'カラー凡例'},
            'close': {'zh': '關閉', 'en': 'Close', 'ja': '閉じる'},
            
            # Driver Strategy Help / 車手策略說明
            'help_driver_strategy_title': {'zh': '車手策略', 'en': 'Driver Strategy', 'ja': 'ドライバー戦略'},
            'help_driver_strategy_desc': {
                'zh': '車手策略模組以視覺化方式顯示每位車手的進站策略和輪胎使用時間軸。\n\n演算法邏輯：\n1. 資料來源：整合 OpenF1 API 的 stints 和 pit 端點資料\n2. Stint 識別：根據進站記錄自動分割輪胎使用區間\n3. 輪胎配對：將每個 stint 與對應的輪胎化合物配對\n4. 時間軸計算：計算每套輪胎的使用圈數和累計時間\n5. 策略比較：自動對齊所有車手的時間軸便於比較',
                'en': 'Driver Strategy module visualizes pit strategy and tire usage timeline for each driver.\n\nAlgorithm Logic:\n1. Data Source: Integrates OpenF1 API stints and pit endpoints\n2. Stint Identification: Auto-segments tire usage intervals based on pit records\n3. Tire Matching: Pairs each stint with corresponding tire compound\n4. Timeline Calculation: Computes laps and cumulative time for each tire set\n5. Strategy Comparison: Auto-aligns all driver timelines for easy comparison',
                'ja': 'ドライバー戦略モジュールは各ドライバーのピット戦略とタイヤ使用タイムラインを視覚化します。\n\nアルゴリズムロジック：\n1. データソース：OpenF1 APIのstintsとpitエンドポイントを統合\n2. スティント識別：ピット記録に基づいてタイヤ使用区間を自動分割\n3. タイヤマッチング：各スティントを対応するタイヤコンパウンドとペアリング\n4. タイムライン計算：各タイヤセットのラップ数と累積時間を計算\n5. 戦略比較：比較しやすいようにすべてのドライバーのタイムラインを自動整列'
            },
            'help_driver_strategy_features': {
                'zh': '- 將滑鼠懸停在色塊上查看詳細資訊（輪胎類型、圈數、實際時間、與領先者差距）\n- 顯示每段輪胎的實際圈數和相對差距\n- 支援實時更新（約每 5 秒刷新一次）\n- 點擊車手可高亮該車手的策略線',
                'en': '- Hover over blocks for detailed info (tire type, laps, actual time, gap to leader)\n- Shows actual laps and delta for each stint\n- Supports real-time updates (~5 second refresh)\n- Click driver to highlight their strategy line',
                'ja': '- ブロック上にマウスを置くと詳細情報を表示（タイヤタイプ、ラップ数、実際の時間、リーダーとのギャップ）\n- 各スティントの実際のラップとデルタを表示\n- リアルタイム更新に対応（約5秒ごとに更新）\n- ドライバーをクリックすると戦略ラインをハイライト'
            },
            'help_driver_strategy_colors': {
                'zh': '- 紅色 (SOFT): 軟胎 - 最快但磨損最快，適合短 stint 或追趕\n- 黃色 (MEDIUM): 中性胎 - 平衡的選擇，最常見的比賽輪胎\n- 白色 (HARD): 硬胎 - 最耐久但較慢，適合長 stint\n- 綠色 (INTERMEDIATE): 中雨胎 - 適合濕滑但無積水的賽道\n- 藍色 (WET): 全雨胎 - 重度降雨時使用\n- 灰色邊框: 使用過的輪胎（非新胎）',
                'en': '- Red (SOFT): Soft tire - Fastest but degrades quickly, good for short stints or chasing\n- Yellow (MEDIUM): Medium tire - Balanced choice, most common race tire\n- White (HARD): Hard tire - Most durable but slower, good for long stints\n- Green (INTERMEDIATE): Intermediate wet - For damp tracks without standing water\n- Blue (WET): Full wet - For heavy rain conditions\n- Gray border: Used tires (not new)',
                'ja': '- 赤 (SOFT): ソフトタイヤ - 最速だが摩耗が早い、短いスティントや追跡に適する\n- 黄 (MEDIUM): ミディアムタイヤ - バランスの取れた選択、最も一般的なレースタイヤ\n- 白 (HARD): ハードタイヤ - 最も耐久性があるが遅い、長いスティントに適する\n- 緑 (INTERMEDIATE): インターミディエイトタイヤ - 水溜まりのない湿ったトラック用\n- 青 (WET): ウェットタイヤ - 激しい雨の条件用\n- グレー枠: 使用済みタイヤ（新品ではない）'
            },
            
            # Top Speed History Help / 最高速歷史說明
            'help_top_speed_history_title': {'zh': '最高速歷史', 'en': 'Top Speed History', 'ja': '最高速度履歴'},
            'help_top_speed_history_desc': {
                'zh': '最高速歷史模組追蹤每位車手每圈的最高速度，用於分析引擎性能、DRS 使用效果和尾流影響。\n\n演算法邏輯：\n1. 資料採集：從 OpenF1 car_data 端點獲取遙測速度資料（約 3.7Hz）\n2. 每圈最大值：對每圈的所有速度樣本取最大值\n3. 速度來源識別：根據賽道位置判斷最高速出現在哪個 DRS 區\n4. 趨勢分析：計算速度變化趨勢識別引擎模式或機械問題\n5. 尾流檢測：異常高的最高速可能表示獲得尾流加成',
                'en': 'Top Speed History module tracks maximum speed per lap for each driver, analyzing engine performance, DRS effectiveness, and slipstream effects.\n\nAlgorithm Logic:\n1. Data Collection: Gets telemetry speed data from OpenF1 car_data (~3.7Hz)\n2. Per-Lap Maximum: Takes maximum of all speed samples for each lap\n3. Speed Source Identification: Determines which DRS zone top speed occurred based on track position\n4. Trend Analysis: Calculates speed change trends to identify engine modes or mechanical issues\n5. Slipstream Detection: Abnormally high top speed may indicate slipstream benefit',
                'ja': '最高速度履歴モジュールは各ドライバーの各ラップの最高速度を追跡し、エンジン性能、DRS効果、スリップストリームの影響を分析します。\n\nアルゴリズムロジック：\n1. データ収集：OpenF1 car_dataからテレメトリ速度データを取得（約3.7Hz）\n2. ラップ毎最大値：各ラップのすべての速度サンプルの最大値を取得\n3. 速度ソース識別：トラック位置に基づいてどのDRSゾーンで最高速が発生したかを判定\n4. トレンド分析：速度変化トレンドを計算してエンジンモードや機械的問題を識別\n5. スリップストリーム検出：異常に高い最高速はスリップストリームの恩恵を示す可能性'
            },
            'help_top_speed_history_features': {
                'zh': '- 每圈最高速度的歷史趨勢\n- 可比較多位車手的速度差異\n- 識別 DRS 區域的速度優勢\n- 支援即時更新和歷史回放',
                'en': '- Historical trend of maximum speed per lap\n- Compare speed differences between drivers\n- Identify DRS zone speed advantages\n- Supports real-time updates and historical replay',
                'ja': '- ラップごとの最高速度の履歴トレンド\n- ドライバー間の速度差を比較\n- DRSゾーンでの速度優位性を識別\n- リアルタイム更新と履歴再生をサポート'
            },
            'help_top_speed_history_colors': {
                'zh': '【線條顏色 - 車隊官方色】\n• Red Bull (VER/PER)：深藍色線條\n• Ferrari (LEC/SAI)：紅色線條\n• Mercedes (HAM/RUS)：青綠色線條\n• McLaren (NOR/PIA)：橙色線條\n• Aston Martin (ALO/STR)：深綠色線條\n\n【線條粗細】\n• 粗線條 = 您選中的車手\n• 細淡線條 = 其他車手（供參考）\n\n【數值顏色意義】\n• 紫色數字 = 全場最快（當圈最高速）\n• 綠色數字 = 個人最佳\n• 紅色閃爍 = 速度異常下降（可能有機械問題）\n\n【實例解讀】\n• VER 線條最高點 342 km/h (紫) = Verstappen 全場最快\n• LEC 線條最高點 338 km/h (綠) = Leclerc 個人最佳\n• 線條突然下降 = 可能遇到尾流或引擎問題',
                'en': '【Line Colors - Team Official】\n• Red Bull (VER/PER): Navy blue line\n• Ferrari (LEC/SAI): Red line\n• Mercedes (HAM/RUS): Teal line\n• McLaren (NOR/PIA): Orange line\n• Aston Martin (ALO/STR): Dark green line\n\n【Line Thickness】\n• Thick line = Driver you selected\n• Thin faded line = Other drivers (for reference)\n\n【Number Color Meaning】\n• Purple number = Overall fastest (lap top speed)\n• Green number = Personal best\n• Red flashing = Abnormal speed drop (possible issue)\n\n【Reading Examples】\n• VER line peak 342 km/h (purple) = Verstappen overall fastest\n• LEC line peak 338 km/h (green) = Leclerc personal best\n• Sudden line drop = May indicate traffic or engine issue',
                'ja': '【ライン色 - チーム公式】\n• Red Bull (VER/PER)：ネイビーブルーライン\n• Ferrari (LEC/SAI)：赤ライン\n• Mercedes (HAM/RUS)：ティールライン\n• McLaren (NOR/PIA)：オレンジライン\n• Aston Martin (ALO/STR)：ダークグリーンライン\n\n【ラインの太さ】\n• 太いライン = 選択したドライバー\n• 細く薄いライン = 他のドライバー（参考用）\n\n【数字の色の意味】\n• 紫の数字 = 全体最速（ラップ最高速）\n• 緑の数字 = 個人ベスト\n• 赤点滅 = 異常な速度低下（問題の可能性）\n\n【読み取り例】\n• VERラインピーク 342 km/h (紫) = Verstappenが全体最速\n• LECラインピーク 338 km/h (緑) = Leclercの個人ベスト\n• 急なライン低下 = トラフィックかエンジン問題の可能性'
            },
            
            # Track Map Help / 賽道地圖說明
            'help_track_map_title': {'zh': '賽道地圖', 'en': 'Track Map', 'ja': 'トラックマップ'},
            'help_track_map_desc': {
                'zh': '顯示賽道佈局和車手即時位置，提供直觀的賽況視圖。',
                'en': 'Displays track layout and real-time driver positions, providing an intuitive view of the race situation.',
                'ja': 'トラックレイアウトとドライバーのリアルタイム位置を表示し、レース状況を直感的に把握できます。'
            },
            'help_track_map_features': {
                'zh': '- 即時顯示所有車手位置\n- 顯示 DRS 區域和檢測點\n- 標示彎道編號和重要地標\n- 支援縮放和平移操作',
                'en': '- Real-time display of all driver positions\n- Shows DRS zones and detection points\n- Marks corner numbers and key landmarks\n- Supports zoom and pan operations',
                'ja': '- すべてのドライバー位置をリアルタイム表示\n- DRSゾーンと検出ポイントを表示\n- コーナー番号と主要なランドマークを表示\n- ズームとパン操作をサポート'
            },
            'help_track_map_colors': {
                'zh': '【背景說明】\n• 深灰色背景 = 地圖整體底色\n• 白色/淺灰線條 = 賽道路線\n• 綠色半透明區域 = DRS 可啟用區段\n\n【車手標記】\n• 圓形標記顏色 = 車隊官方色\n  範例：Red Bull (VER/PER) = 深藍圓點\n         Ferrari (LEC/SAI) = 紅色圓點\n         Mercedes (HAM/RUS) = 青綠圓點\n• 標記大小：選中車手較大，未選中較小\n• 車手代碼：白色文字顯示 3 字母縮寫\n\n【賽道狀態標示】\n• 綠色區段 = 賽道正常/安全\n• 黃色區段 = 單黃旗（減速）\n• 雙黃區段 = 雙黃旗（大幅減速）\n• 紅色區段 = 紅旗或危險區域\n• 藍色標記 = 接受藍旗警告的車手\n\n【特殊標示範例】\n• 閃爍標記 = 剛完成進站的車手\n• 灰色標記 = 已退賽車手\n• 虛線軌跡 = 車手最近行駛路線',
                'en': '【Background】\n• Dark gray background = Map overall base color\n• White/light gray lines = Track route\n• Green transparent zone = DRS activation areas\n\n【Driver Markers】\n• Circle marker color = Team official color\n  Example: Red Bull (VER/PER) = Navy blue dot\n           Ferrari (LEC/SAI) = Red dot\n           Mercedes (HAM/RUS) = Teal dot\n• Marker size: Selected drivers larger, unselected smaller\n• Driver code: White text showing 3-letter abbreviation\n\n【Track Status Indicators】\n• Green zone = Track clear/safe\n• Yellow zone = Single yellow (slow down)\n• Double yellow = Double yellow (significant slowdown)\n• Red zone = Red flag or danger area\n• Blue marker = Driver receiving blue flag\n\n【Special Indicator Examples】\n• Flashing marker = Driver just completed pit stop\n• Gray marker = Retired driver\n• Dashed trail = Driver recent path',
                'ja': '【背景】\n• ダークグレー背景 = マップの基本背景色\n• 白/ライトグレー線 = トラック経路\n• 緑の半透明エリア = DRS有効化ゾーン\n\n【ドライバーマーカー】\n• 円形マーカー色 = チーム公式カラー\n  例：Red Bull (VER/PER) = ネイビーブルードット\n      Ferrari (LEC/SAI) = 赤ドット\n      Mercedes (HAM/RUS) = ティールドット\n• マーカーサイズ：選択ドライバーは大、未選択は小\n• ドライバーコード：3文字略称を白文字で表示\n\n【トラック状態表示】\n• 緑ゾーン = トラッククリア/安全\n• 黄ゾーン = シングルイエロー（減速）\n• ダブルイエロー = ダブルイエロー（大幅減速）\n• 赤ゾーン = レッドフラッグまたは危険エリア\n• 青マーカー = ブルーフラッグを受けているドライバー\n\n【特別表示例】\n• 点滅マーカー = ピットストップを完了したばかりのドライバー\n• グレーマーカー = リタイアしたドライバー\n• 破線軌跡 = ドライバーの最近の経路'
            },
            
            # Ranking Tower Help / 排名塔說明
            'help_ranking_tower_title': {'zh': '即時排名', 'en': 'Live Ranking', 'ja': 'ライブランキング'},
            'help_ranking_tower_desc': {
                'zh': '顯示車手即時排名、差距和圈速資訊，是追蹤比賽進程的核心視圖。',
                'en': 'Shows real-time driver rankings, gaps, and lap times - the core view for tracking race progress.',
                'ja': 'ドライバーのリアルタイムランキング、ギャップ、ラップタイムを表示 - レース進行を追跡するための中心的なビュー。'
            },
            'help_ranking_tower_features': {
                'zh': '- 即時更新排名變化\n- 顯示與領先者和前車的差距\n- 標示進站狀態和輪胎類型',
                'en': '- Real-time ranking updates\n- Shows gap to leader and car ahead\n- Indicates pit status and tire type',
                'ja': '- リアルタイムのランキング更新\n- リーダーと前車とのギャップを表示\n- ピット状態とタイヤタイプを表示'
            },
            'help_ranking_tower_colors': {
                'zh': '【背景顏色意義】\n• 深灰背景 = 正常狀態\n• 黃色背景 = 車手正在進站\n  範例：VER 整行變黃 = Verstappen 進站中\n• 紅色背景 = 車手已退賽\n  範例：RIC 整行變紅 = Ricciardo 退賽\n\n【圈速數字顏色】\n• 紫色數字 = 全場最快圈或分段\n  範例：「1:28.123」紫色 = 目前全場最快\n• 綠色數字 = 個人最佳圈\n  範例：「1:28.456」綠色 = 該車手本場最快\n• 黃色數字 = 一般圈速\n• 紅色數字 = 慢圈（進站圈或失誤）\n\n【差距變化顏色】\n• 綠色差距 = 正在追近前車\n  範例：「-0.3s」綠色 = 比上圈縮小 0.3 秒\n• 紅色差距 = 正在被拉開\n  範例：「+0.5s」紅色 = 比上圈擴大 0.5 秒\n\n【輪胎圓圈顏色】\n• 紅色圓圈 = 軟胎 (SOFT)\n• 黃色圓圈 = 中性胎 (MEDIUM)\n• 白色圓圈 = 硬胎 (HARD)',
                'en': '【Background Color Meaning】\n• Dark gray background = Normal status\n• Yellow background = Driver in pit\n  Example: VER row turns yellow = Verstappen pitting\n• Red background = Driver retired\n  Example: RIC row turns red = Ricciardo retired\n\n【Lap Time Number Colors】\n• Purple number = Overall fastest lap or sector\n  Example: "1:28.123" purple = Currently overall fastest\n• Green number = Personal best lap\n  Example: "1:28.456" green = Driver\'s fastest this session\n• Yellow number = Normal lap time\n• Red number = Slow lap (pit or mistake)\n\n【Gap Change Colors】\n• Green gap = Catching the car ahead\n  Example: "-0.3s" green = Gained 0.3s from last lap\n• Red gap = Being pulled away\n  Example: "+0.5s" red = Lost 0.5s from last lap\n\n【Tire Circle Colors】\n• Red circle = Soft tire (SOFT)\n• Yellow circle = Medium tire (MEDIUM)\n• White circle = Hard tire (HARD)',
                'ja': '【背景色の意味】\n• ダークグレー背景 = 通常状態\n• 黄色背景 = ドライバーがピット中\n  例：VER行が黄色 = Verstappenがピット中\n• 赤背景 = ドライバーがリタイア\n  例：RIC行が赤 = Ricciardoがリタイア\n\n【ラップタイム数字の色】\n• 紫の数字 = 全体最速ラップまたはセクター\n  例：「1:28.123」紫 = 現在の全体最速\n• 緑の数字 = 個人ベストラップ\n  例：「1:28.456」緑 = そのドライバーのセッション最速\n• 黄の数字 = 通常のラップタイム\n• 赤の数字 = スローラップ（ピットまたはミス）\n\n【ギャップ変化の色】\n• 緑のギャップ = 前車に接近中\n  例：「-0.3s」緑 = 前ラップから0.3秒短縮\n• 赤のギャップ = 引き離されている\n  例：「+0.5s」赤 = 前ラップから0.5秒遅れ\n\n【タイヤ丸の色】\n• 赤丸 = ソフトタイヤ (SOFT)\n• 黄丸 = ミディアムタイヤ (MEDIUM)\n• 白丸 = ハードタイヤ (HARD)'
            },
            
            # Lap History Help / 圈速歷史說明
            'help_lap_history_title': {'zh': '圈速歷史', 'en': 'Lap History', 'ja': 'ラップ履歴'},
            'help_lap_history_desc': {
                'zh': '追蹤車手每圈的圈速變化，幫助分析節奏和策略執行。',
                'en': 'Tracks lap time changes for each driver, helping analyze pace and strategy execution.',
                'ja': '各ドライバーのラップタイムの変化を追跡し、ペースと戦略実行の分析に役立ちます。'
            },
            'help_lap_history_features': {
                'zh': '- 視覺化圈速趨勢\n- 識別輪胎衰退和進站效果\n- 比較車手之間的節奏差異',
                'en': '- Visualize lap time trends\n- Identify tire degradation and pit effects\n- Compare pace between drivers',
                'ja': '- ラップタイムトレンドを視覚化\n- タイヤの劣化とピット効果を識別\n- ドライバー間のペース差を比較'
            },
            'help_lap_history_colors': {
                'zh': '【數據點顏色 - 車隊官方色】\n• Mercedes (HAM/RUS)：青綠色點\n• McLaren (NOR/PIA)：橙色點\n• Alpine (GAS/OCO)：粉藍色點\n• Williams (ALB/SAR)：淺藍色點\n\n【點大小】\n• 大點 = 您選中的車手\n• 小點 = 其他車手\n\n【數字顏色意義】\n• 紫色數字 = 全場最快圈\n• 綠色數字 = 個人最佳圈\n• 黃色數字 = 進站圈\n\n【圖表趨勢解讀】\n• 向上突起 = 慢圈（進站、黃旗、失誤）\n  範例：VER 第 15 圈突起 = 進站圈\n• 向下趨勢 = 輪胎衰退或油量減輕\n  範例：LEC 第 20-30 圈逐漸下降 = 輪胎老化\n• 平穩線條 = 節奏一致，狀態穩定',
                'en': '【Data Point Colors - Team Official】\n• Mercedes (HAM/RUS): Teal dots\n• McLaren (NOR/PIA): Orange dots\n• Alpine (GAS/OCO): Light blue dots\n• Williams (ALB/SAR): Blue dots\n\n【Point Size】\n• Large dot = Driver you selected\n• Small dot = Other drivers\n\n【Number Color Meaning】\n• Purple number = Overall fastest lap\n• Green number = Personal best lap\n• Yellow number = Pit lap\n\n【Chart Trend Reading】\n• Upward spike = Slow lap (pit, yellow flag, mistake)\n  Example: VER spike at lap 15 = Pit stop lap\n• Downward trend = Tire degradation or fuel reduction\n  Example: LEC laps 20-30 gradual drop = Tire aging\n• Flat line = Consistent pace, stable condition',
                'ja': '【データポイント色 - チーム公式】\n• Mercedes (HAM/RUS)：ティールドット\n• McLaren (NOR/PIA)：オレンジドット\n• Alpine (GAS/OCO)：ライトブルードット\n• Williams (ALB/SAR)：ブルードット\n\n【ポイントサイズ】\n• 大きいドット = 選択したドライバー\n• 小さいドット = 他のドライバー\n\n【数字の色の意味】\n• 紫の数字 = 全体最速ラップ\n• 緑の数字 = 個人ベストラップ\n• 黄の数字 = ピットラップ\n\n【チャートトレンドの読み取り】\n• 上向きスパイク = スローラップ（ピット、イエローフラッグ、ミス）\n  例：VER 15周目のスパイク = ピットストップ\n• 下降傾向 = タイヤ劣化または燃料減少\n  例：LEC 20-30周目の徐々の低下 = タイヤの老化\n• フラットライン = 一貫したペース、安定した状態'
            },
            
            # SF% History Help / SF% 歷史說明
            'help_sf_percentage_title': {'zh': 'SF% 歷史', 'en': 'SF% History', 'ja': 'SF%履歴'},
            'help_sf_percentage_desc': {
                'zh': 'Speed Fraction (SF%) 顯示車手速度佔理論最大速度的百分比，用於評估車手效率。',
                'en': 'Speed Fraction (SF%) shows the percentage of theoretical maximum speed achieved, used to evaluate driver efficiency.',
                'ja': 'Speed Fraction (SF%) は理論上の最大速度に対する達成率を表示し、ドライバーの効率を評価するために使用されます。'
            },
            'help_sf_percentage_features': {
                'zh': '- 追蹤每圈的 SF% 變化\n- 識別效率下降的圈數\n- 評估輪胎衰退對效率的影響',
                'en': '- Track SF% changes per lap\n- Identify laps with efficiency drops\n- Evaluate tire degradation impact on efficiency',
                'ja': '- ラップごとのSF%変化を追跡\n- 効率低下のラップを識別\n- タイヤ劣化が効率に与える影響を評価'
            },
            'help_sf_percentage_colors': {
                'zh': '【線條顏色 - 車隊官方色】\n• Alpine (GAS/OCO)：粉藍色線條\n• Aston Martin (ALO/STR)：深綠色線條\n• Haas (MAG/HUL)：白色/紅色線條\n\n【數值解讀】\n• SF% = 98%：接近理論極限，全力推進\n  範例：VER 第 10 圈 SF% = 98.2% = 狀態極佳\n• SF% = 92-95%：可能節油或輪胎問題\n  範例：LEC 後段 SF% 降至 93% = 輪胎衰退\n• SF% 突降 (<90%)：遇到黃旗或賽道問題\n  範例：第 25 圈 SF% = 85% = 可能黃旗\n\n【參考線】\n• 100% 水平線 = 理論最大效率基準',
                'en': '【Line Colors - Team Official】\n• Alpine (GAS/OCO): Light blue line\n• Aston Martin (ALO/STR): Dark green line\n• Haas (MAG/HUL): White/Red line\n\n【Value Interpretation】\n• SF% = 98%: Near theoretical limit, full push\n  Example: VER lap 10 SF% = 98.2% = Excellent condition\n• SF% = 92-95%: Possibly fuel saving or tire issues\n  Example: LEC late-race SF% drops to 93% = Tire degradation\n• SF% sudden drop (<90%): Yellow flag or track issue\n  Example: Lap 25 SF% = 85% = Likely yellow flag\n\n【Reference Line】\n• 100% horizontal line = Theoretical maximum efficiency baseline',
                'ja': '【ライン色 - チーム公式】\n• Alpine (GAS/OCO)：ライトブルーライン\n• Aston Martin (ALO/STR)：ダークグリーンライン\n• Haas (MAG/HUL)：白/赤ライン\n\n【値の解釈】\n• SF% = 98%：理論限界に近い、フルプッシュ\n  例：VER 10周目 SF% = 98.2% = 優れた状態\n• SF% = 92-95%：燃費節約またはタイヤ問題の可能性\n  例：LEC レース後半 SF% が93%に低下 = タイヤ劣化\n• SF% 急降下 (<90%)：イエローフラッグまたはトラック問題\n  例：25周目 SF% = 85% = おそらくイエローフラッグ\n\n【参照線】\n• 100% 水平線 = 理論最大効率基準'
            },
            
            # Throttle 95% History Help / 油門 95% 歷史說明
            'help_throttle_history_title': {'zh': '油門 95% 歷史', 'en': 'Throttle 95% History', 'ja': 'スロットル95%履歴'},
            'help_throttle_history_desc': {
                'zh': '顯示每圈油門開度達到 95% 以上的時間百分比，反映全油門比例。',
                'en': 'Shows the percentage of time throttle is above 95% per lap, reflecting full throttle ratio.',
                'ja': '各ラップでスロットルが95%以上の時間の割合を表示し、フルスロットル比率を反映します。'
            },
            'help_throttle_history_features': {
                'zh': '- 監控全油門使用率\n- 識別節油或保守駕駛的圈數\n- 評估引擎模式變化',
                'en': '- Monitor full throttle usage\n- Identify fuel-saving or conservative driving laps\n- Evaluate engine mode changes',
                'ja': '- フルスロットル使用率を監視\n- 燃費節約または保守的な走行ラップを識別\n- エンジンモードの変化を評価'
            },
            'help_throttle_history_colors': {
                'zh': '【線條顏色 - 車隊官方色】\n• Williams (ALB/SAR)：淺藍色線條\n• Haas (MAG/HUL)：白色/紅色線條\n• Sauber (BOT/ZHO)：綠色線條\n\n【數值顏色意義】\n• 綠色數字 = 高效率圈（>60% 全油門）\n• 橙色數字 = 中等效率\n• 紅色數字 = 低效率或問題圈\n\n【數值解讀範例】\n• 65%：正常全力推進，高攻擊性\n  範例：VER 第 5 圈 = 67% = 全力衝刺\n• 55%：輕微節油或應對車流\n  範例：HAM 第 30 圈 = 54% = 保護引擎\n• 40%：明顯節油或機械問題\n  範例：ALO 第 45 圈 = 42% = 節油模式\n• 突降至 30%：可能引擎問題\n  範例：突然從 60% 降至 28% = 檢查問題\n\n【參考線】\n• 95% 虛線 = 全油門判定基準',
                'en': '【Line Colors - Team Official】\n• Williams (ALB/SAR): Light blue line\n• Haas (MAG/HUL): White/Red line\n• Sauber (BOT/ZHO): Green line\n\n【Number Color Meaning】\n• Green number = High efficiency lap (>60% full throttle)\n• Orange number = Medium efficiency\n• Red number = Low efficiency or problem lap\n\n【Value Interpretation Examples】\n• 65%: Normal full push, high aggression\n  Example: VER lap 5 = 67% = Full attack\n• 55%: Slight fuel saving or traffic\n  Example: HAM lap 30 = 54% = Protecting engine\n• 40%: Obvious fuel saving or mechanical issue\n  Example: ALO lap 45 = 42% = Fuel save mode\n• Sudden drop to 30%: Possible engine issue\n  Example: Drops from 60% to 28% = Check for problems\n\n【Reference Line】\n• 95% dashed line = Full throttle threshold',
                'ja': '【ライン色 - チーム公式】\n• Williams (ALB/SAR)：ライトブルーライン\n• Haas (MAG/HUL)：白/赤ライン\n• Sauber (BOT/ZHO)：グリーンライン\n\n【数字の色の意味】\n• 緑の数字 = 高効率ラップ（>60%フルスロットル）\n• オレンジの数字 = 中効率\n• 赤の数字 = 低効率または問題ラップ\n\n【値の解釈例】\n• 65%：通常のフルプッシュ、高い攻撃性\n  例：VER 5周目 = 67% = フルアタック\n• 55%：軽い燃費節約またはトラフィック\n  例：HAM 30周目 = 54% = エンジン保護\n• 40%：明らかな燃費節約または機械的問題\n  例：ALO 45周目 = 42% = 燃費節約モード\n• 30%への急降下：エンジン問題の可能性\n  例：60%から28%に急降下 = 問題をチェック\n\n【参照線】\n• 95% 破線 = フルスロットル閾値'
            },
            
            # Sector Comparison Help / 分段比較說明
            'help_sector_comparison_title': {'zh': '分段比較', 'en': 'Sector Comparison', 'ja': 'セクター比較'},
            'help_sector_comparison_desc': {
                'zh': '比較車手在各分段的表現，識別強項和弱項區域。',
                'en': 'Compares driver performance across sectors, identifying strengths and weaknesses.',
                'ja': '各セクターでのドライバーパフォーマンスを比較し、強みと弱みを識別します。'
            },
            'help_sector_comparison_features': {
                'zh': '- 三個分段獨立比較\n- 視覺化差距大小\n- 追蹤分段時間趨勢',
                'en': '- Three sectors compared independently\n- Visualize gap magnitude\n- Track sector time trends',
                'ja': '- 3つのセクターを独立して比較\n- ギャップの大きさを視覚化\n- セクタータイムのトレンドを追跡'
            },
            'help_sector_comparison_colors': {
                'zh': '【背景說明】\n• 深灰背景 = 圖表整體底色\n• 分段分割線 = 深色垂直線區分 S1/S2/S3\n\n【時間顯示顏色】\n• 紫色數字 = 該分段全場最快\n  範例：S1 = 28.123 (紫) = 此車手在第一段最快\n• 綠色數字 = 個人該分段最佳\n  範例：S2 = 35.456 (綠) = 個人在 S2 最佳時間\n• 黃色數字 = 一般分段時間\n• 紅色數字 = 慢於平均\n\n【數據條顏色】\n• 數據條顏色 = 車隊官方色\n  範例：Ferrari 紅色條 = Leclerc 的分段時間\n         Mercedes 青綠條 = Hamilton 的分段時間\n         McLaren 橙色條 = Norris 的分段時間\n\n【分析範例】\n• VER: S1(紫) S2(黃) S3(綠)\n  解讀：第一段最強、第三段個人最佳\n• 理論最快圈 = S1 紫 + S2 紫 + S3 紫\n  解讀：各分段最快時間組合',
                'en': '【Background】\n• Dark gray background = Chart overall base color\n• Sector dividers = Dark vertical lines separating S1/S2/S3\n\n【Time Display Colors】\n• Purple number = Overall fastest in that sector\n  Example: S1 = 28.123 (purple) = Fastest in sector 1\n• Green number = Personal best in that sector\n  Example: S2 = 35.456 (green) = Personal best in S2\n• Yellow number = Normal sector time\n• Red number = Slower than average\n\n【Bar Colors】\n• Bar color = Team official color\n  Example: Ferrari red bar = Leclerc\'s sector time\n           Mercedes teal bar = Hamilton\'s sector time\n           McLaren orange bar = Norris\'s sector time\n\n【Analysis Examples】\n• VER: S1(purple) S2(yellow) S3(green)\n  Reading: Strongest in S1, personal best in S3\n• Theoretical fastest = S1 purple + S2 purple + S3 purple\n  Reading: Best sectors combined',
                'ja': '【背景】\n• ダークグレー背景 = チャートの基本背景色\n• セクター分割線 = S1/S2/S3を分ける暗い垂直線\n\n【タイム表示色】\n• 紫の数字 = そのセクターで全体最速\n  例：S1 = 28.123 (紫) = セクター1で最速\n• 緑の数字 = そのセクターで個人ベスト\n  例：S2 = 35.456 (緑) = S2での個人ベスト\n• 黄の数字 = 通常のセクタータイム\n• 赤の数字 = 平均より遅い\n\n【バー色】\n• バー色 = チーム公式カラー\n  例：Ferrari赤バー = Leclercのセクタータイム\n      Mercedesティールバー = Hamiltonのセクタータイム\n      McLarenオレンジバー = Norrisのセクタータイム\n\n【分析例】\n• VER: S1(紫) S2(黄) S3(緑)\n  読み取り：S1が最強、S3は個人ベスト\n• 理論最速 = S1紫 + S2紫 + S3紫\n  読み取り：各セクターのベスト組み合わせ'
            },
            
            # Default Help / 預設說明
            'help_default_title': {'zh': 'F1T 模組', 'en': 'F1T Module', 'ja': 'F1Tモジュール'},
            'help_default_desc': {
                'zh': '這是一個 F1 遙測分析模組，提供即時數據視覺化功能。',
                'en': 'This is an F1 telemetry analysis module providing real-time data visualization.',
                'ja': 'これはリアルタイムデータ可視化を提供するF1テレメトリ分析モジュールです。'
            },
            'help_default_features': {
                'zh': '- 即時數據更新\n- 可自訂視窗大小\n- 支援多視窗同步',
                'en': '- Real-time data updates\n- Customizable window size\n- Multi-window synchronization support',
                'ja': '- リアルタイムデータ更新\n- カスタマイズ可能なウィンドウサイズ\n- マルチウィンドウ同期対応'
            },
            'help_default_colors': {
                'zh': '- 顏色通常基於 F1 車隊官方配色\n- 特殊狀態使用標準顏色標示',
                'en': '- Colors typically based on official F1 team colors\n- Special states use standard color indicators',
                'ja': '- カラーは通常F1チームの公式カラーに基づく\n- 特別な状態は標準的な色で表示'
            },
            
            # ========== Speed Trace Help / 速度追蹤說明 ==========
            'help_speed_trace_title': {'zh': '速度追蹤', 'en': 'Speed Trace', 'ja': '速度トレース'},
            'help_speed_trace_desc': {
                'zh': '速度追蹤模組提供車手在單圈中的即時速度曲線，資料來自 OpenF1 API 的 car_data 端點。\n\n演算法邏輯：\n1. 資料採集：以約 3.7Hz 頻率接收車輛遙測資料\n2. 距離插值：將時間序列資料轉換為距離序列（0-100% 賽道位置）\n3. 平滑處理：使用滑動平均濾波器降低感測器雜訊\n4. 比較計算：多車手模式下計算速度差異絕對值',
                'en': 'Speed Trace module provides real-time speed curves for drivers during a lap, data sourced from OpenF1 API car_data endpoint.\n\nAlgorithm Logic:\n1. Data Collection: Receives vehicle telemetry at ~3.7Hz\n2. Distance Interpolation: Converts time-series to distance-series (0-100% track position)\n3. Smoothing: Applies moving average filter to reduce sensor noise\n4. Comparison: Calculates absolute speed differences in multi-driver mode',
                'ja': '速度トレースモジュールはOpenF1 APIのcar_dataエンドポイントからドライバーのリアルタイム速度曲線を提供します。\n\nアルゴリズムロジック：\n1. データ収集：約3.7Hzで車両テレメトリを受信\n2. 距離補間：時系列を距離系列（0-100%トラック位置）に変換\n3. スムージング：移動平均フィルタでセンサーノイズを低減\n4. 比較：マルチドライバーモードで速度差を計算'
            },
            'help_speed_trace_features': {
                'zh': '- X 軸：賽道距離（公尺）或位置百分比\n- Y 軸：瞬時速度（km/h）\n- 支援多車手疊加比較\n- 可識別 DRS 啟用區段（速度突增）\n- 標示最高速點和最低速彎角',
                'en': '- X-axis: Track distance (meters) or position percentage\n- Y-axis: Instantaneous speed (km/h)\n- Supports multi-driver overlay comparison\n- Identifies DRS activation zones (speed spikes)\n- Marks top speed points and slowest corners',
                'ja': '- X軸：トラック距離（メートル）または位置パーセンテージ\n- Y軸：瞬間速度（km/h）\n- マルチドライバーオーバーレイ比較をサポート\n- DRS有効化ゾーン（速度スパイク）を識別\n- 最高速ポイントと最も遅いコーナーをマーク'
            },
            'help_speed_trace_colors': {
                'zh': '- 各車手使用其車隊官方顏色\n- 選中車手線條較粗（2px vs 1px）\n- 速度差異區域使用半透明填充\n- 灰色虛線：分段邊界（S1/S2/S3）',
                'en': '- Each driver uses their team official color\n- Selected driver lines are thicker (2px vs 1px)\n- Speed difference areas use semi-transparent fill\n- Gray dashed lines: Sector boundaries (S1/S2/S3)',
                'ja': '- 各ドライバーはチーム公式カラーを使用\n- 選択されたドライバーの線は太い（2px vs 1px）\n- 速度差領域は半透明フィルを使用\n- グレー破線：セクター境界（S1/S2/S3）'
            },
            
            # ========== Throttle Trace Help / 油門追蹤說明 ==========
            'help_throttle_trace_title': {'zh': '油門追蹤', 'en': 'Throttle Trace', 'ja': 'スロットルトレース'},
            'help_throttle_trace_desc': {
                'zh': '油門追蹤模組顯示車手的油門踏板輸入百分比（0-100%）。\n\n演算法邏輯：\n1. 原始資料：來自車輛 ECU 的油門位置感測器（0-100 整數）\n2. 時間對齊：與其他遙測資料同步（基於 UTC 時間戳）\n3. 全油門判定：95% 以上視為全油門狀態\n4. 節油模式識別：低於預期的油門開度可能表示 Lift & Coast 策略',
                'en': 'Throttle Trace module displays driver throttle pedal input percentage (0-100%).\n\nAlgorithm Logic:\n1. Raw Data: From vehicle ECU throttle position sensor (0-100 integer)\n2. Time Alignment: Synchronized with other telemetry (based on UTC timestamp)\n3. Full Throttle Detection: Above 95% considered full throttle\n4. Fuel Save Detection: Lower than expected throttle may indicate Lift & Coast strategy',
                'ja': 'スロットルトレースモジュールはドライバーのスロットルペダル入力パーセンテージ（0-100%）を表示します。\n\nアルゴリズムロジック：\n1. 生データ：車両ECUからのスロットル位置センサー（0-100整数）\n2. 時間同期：他のテレメトリと同期（UTCタイムスタンプ基準）\n3. フルスロットル検出：95%以上をフルスロットルと判定\n4. 燃費節約検出：予想より低いスロットルはリフト&コースト戦略を示す可能性'
            },
            'help_throttle_trace_features': {
                'zh': '- 即時油門位置追蹤\n- 識別節油駕駛模式\n- 與速度曲線對照可分析動力輸出效率\n- 標示急加速和緩加速區段',
                'en': '- Real-time throttle position tracking\n- Identify fuel-saving driving patterns\n- Compare with speed trace to analyze power output efficiency\n- Mark rapid and gradual acceleration zones',
                'ja': '- リアルタイムスロットル位置追跡\n- 燃費節約走行パターンを識別\n- 速度トレースと比較してパワー出力効率を分析\n- 急加速とゆるやかな加速ゾーンをマーク'
            },
            'help_throttle_trace_colors': {
                'zh': '- 車隊顏色區分不同車手\n- 高於 95% 區域可特別標示\n- 0% 油門區域表示滑行或煞車中',
                'en': '- Team colors distinguish drivers\n- Above 95% areas can be specially marked\n- 0% throttle areas indicate coasting or braking',
                'ja': '- チームカラーでドライバーを区別\n- 95%以上の領域は特別にマーク可能\n- 0%スロットル領域はコースティングまたはブレーキングを示す'
            },
            
            # ========== Brake Trace Help / 煞車追蹤說明 ==========
            'help_brake_trace_title': {'zh': '煞車追蹤', 'en': 'Brake Trace', 'ja': 'ブレーキトレース'},
            'help_brake_trace_desc': {
                'zh': '煞車追蹤模組顯示車手的煞車踏板狀態（開/關二元值或壓力百分比）。\n\n演算法邏輯：\n1. 資料來源：車輛 brake 感測器回報\n2. 二元化處理：部分資料源僅提供 on/off 狀態\n3. 煞車點分析：計算從全油門到煞車啟動的延遲距離\n4. 煞車釋放分析：評估進彎時的煞車線性度',
                'en': 'Brake Trace module displays driver brake pedal status (on/off binary or pressure percentage).\n\nAlgorithm Logic:\n1. Data Source: Vehicle brake sensor reports\n2. Binarization: Some data sources only provide on/off status\n3. Braking Point Analysis: Calculate delay distance from full throttle to brake activation\n4. Brake Release Analysis: Evaluate braking linearity during corner entry',
                'ja': 'ブレーキトレースモジュールはドライバーのブレーキペダル状態（オン/オフバイナリまたは圧力パーセンテージ）を表示します。\n\nアルゴリズムロジック：\n1. データソース：車両ブレーキセンサーレポート\n2. 二値化：一部のデータソースはオン/オフ状態のみを提供\n3. ブレーキングポイント分析：フルスロットルからブレーキ作動までの遅延距離を計算\n4. ブレーキリリース分析：コーナー進入時のブレーキ線形性を評価'
            },
            'help_brake_trace_features': {
                'zh': '- 煞車點位置標示\n- 煞車持續時間計算\n- 與速度曲線對照分析減速 G 力\n- 識別過早或過晚煞車',
                'en': '- Braking point position marking\n- Braking duration calculation\n- Analyze deceleration G-force with speed trace\n- Identify early or late braking',
                'ja': '- ブレーキングポイント位置のマーキング\n- ブレーキ持続時間の計算\n- 速度トレースで減速G力を分析\n- 早すぎるまたは遅すぎるブレーキングを識別'
            },
            'help_brake_trace_colors': {
                'zh': '- 車隊顏色區分車手\n- 煞車啟動區域通常以填充顯示\n- 紅色強調重煞車區段',
                'en': '- Team colors distinguish drivers\n- Brake activation areas shown with fill\n- Red highlights heavy braking zones',
                'ja': '- チームカラーでドライバーを区別\n- ブレーキ作動領域はフィルで表示\n- 赤はヘビーブレーキングゾーンを強調'
            },
            
            # ========== Gear Trace Help / 檔位追蹤說明 ==========
            'help_gear_trace_title': {'zh': '檔位追蹤', 'en': 'Gear Trace', 'ja': 'ギアトレース'},
            'help_gear_trace_desc': {
                'zh': '檔位追蹤模組顯示車手的變速箱檔位選擇（1-8 檔）。\n\n演算法邏輯：\n1. 資料來源：變速箱控制單元回報的當前檔位\n2. 換檔點分析：記錄升降檔的賽道位置\n3. 最佳檔位計算：根據引擎轉速和速度推算理論最佳檔位\n4. 短換檔識別：檢測快速連續換檔（可能為策略性操作）',
                'en': 'Gear Trace module displays driver gearbox gear selection (1-8 gears).\n\nAlgorithm Logic:\n1. Data Source: Current gear reported by gearbox control unit\n2. Shift Point Analysis: Record track positions for upshifts/downshifts\n3. Optimal Gear Calculation: Compute theoretical optimal gear based on RPM and speed\n4. Short Shift Detection: Detect rapid consecutive shifts (possibly strategic)',
                'ja': 'ギアトレースモジュールはドライバーのギアボックスギア選択（1-8速）を表示します。\n\nアルゴリズムロジック：\n1. データソース：ギアボックス制御ユニットから報告される現在のギア\n2. シフトポイント分析：アップシフト/ダウンシフトのトラック位置を記録\n3. 最適ギア計算：RPMと速度に基づいて理論的な最適ギアを計算\n4. ショートシフト検出：急速な連続シフト（戦略的である可能性）を検出'
            },
            'help_gear_trace_features': {
                'zh': '- 顯示 1-8 檔位變化\n- 標示換檔點位置\n- 識別非典型檔位選擇（例如 8 檔降至 2 檔的急煞）\n- 與 RPM 曲線對照分析',
                'en': '- Display gear changes 1-8\n- Mark shift point positions\n- Identify atypical gear selections (e.g., 8th to 2nd hard braking)\n- Analyze with RPM trace',
                'ja': '- 1-8ギア変化を表示\n- シフトポイント位置をマーク\n- 非典型的なギア選択を識別（例：8速から2速への急ブレーキ）\n- RPMトレースと分析'
            },
            'help_gear_trace_colors': {
                'zh': '- 車隊顏色區分車手\n- 階梯圖形式顯示離散檔位\n- 可選擇填充顯示檔位區間',
                'en': '- Team colors distinguish drivers\n- Step chart format for discrete gears\n- Optional fill display for gear ranges',
                'ja': '- チームカラーでドライバーを区別\n- 離散ギアのステップチャート形式\n- ギア範囲のオプションフィル表示'
            },
            
            # ========== DRS Trace Help / DRS 追蹤說明 ==========
            'help_drs_trace_title': {'zh': 'DRS 追蹤', 'en': 'DRS Trace', 'ja': 'DRSトレース'},
            'help_drs_trace_desc': {
                'zh': 'DRS（可調式尾翼系統）追蹤模組顯示 DRS 的啟用狀態。\n\n演算法邏輯：\n1. 二元狀態：DRS 僅有開啟/關閉兩種狀態\n2. 啟用條件檢測：需在 DRS 區內且與前車差距小於 1 秒\n3. 速度增益計算：比較 DRS 開啟前後的加速度差異\n4. 使用效率分析：計算理論可用次數與實際使用次數的比例',
                'en': 'DRS (Drag Reduction System) Trace module displays DRS activation status.\n\nAlgorithm Logic:\n1. Binary State: DRS only has open/closed states\n2. Activation Condition Detection: Must be in DRS zone and within 1 second of car ahead\n3. Speed Gain Calculation: Compare acceleration difference before/after DRS activation\n4. Usage Efficiency Analysis: Calculate ratio of theoretical available uses vs actual uses',
                'ja': 'DRS（ドラッグリダクションシステム）トレースモジュールはDRS有効化状態を表示します。\n\nアルゴリズムロジック：\n1. バイナリ状態：DRSは開/閉の2つの状態のみ\n2. 有効化条件検出：DRSゾーン内で前車と1秒以内である必要\n3. 速度ゲイン計算：DRS作動前後の加速度差を比較\n4. 使用効率分析：理論的に使用可能な回数と実際の使用回数の比率を計算'
            },
            'help_drs_trace_features': {
                'zh': '- 顯示 DRS 開/關狀態\n- 標示 DRS 偵測點和啟用區\n- 計算每次 DRS 使用的速度增益\n- 識別錯過的 DRS 機會',
                'en': '- Display DRS on/off status\n- Mark DRS detection points and activation zones\n- Calculate speed gain per DRS use\n- Identify missed DRS opportunities',
                'ja': '- DRSオン/オフ状態を表示\n- DRS検出ポイントと有効化ゾーンをマーク\n- DRS使用ごとの速度ゲインを計算\n- 逃したDRS機会を識別'
            },
            'help_drs_trace_colors': {
                'zh': '- 綠色填充：DRS 啟用中\n- 灰色背景：DRS 關閉\n- 車隊顏色用於多車手比較',
                'en': '- Green fill: DRS active\n- Gray background: DRS closed\n- Team colors for multi-driver comparison',
                'ja': '- 緑フィル：DRS有効\n- グレー背景：DRS閉\n- マルチドライバー比較用チームカラー'
            },
            
            # ========== RPM Trace Help / 轉速追蹤說明 ==========
            'help_rpm_trace_title': {'zh': '轉速追蹤', 'en': 'RPM Trace', 'ja': 'RPMトレース'},
            'help_rpm_trace_desc': {
                'zh': '引擎轉速追蹤模組顯示引擎每分鐘轉數（RPM）。\n\n演算法邏輯：\n1. 資料範圍：F1 引擎轉速範圍約 8,000-15,000 RPM\n2. 紅線判定：接近最大轉速（~15,000 RPM）時觸發升檔\n3. 換檔分析：結合檔位資料判斷換檔時機的合理性\n4. 引擎模式推測：不同引擎模式會有不同的 RPM 曲線特徵',
                'en': 'Engine RPM Trace module displays engine revolutions per minute.\n\nAlgorithm Logic:\n1. Data Range: F1 engine RPM range approximately 8,000-15,000\n2. Redline Detection: Triggers upshift when approaching max RPM (~15,000)\n3. Shift Analysis: Combined with gear data to judge shift timing reasonableness\n4. Engine Mode Inference: Different engine modes have different RPM curve characteristics',
                'ja': 'エンジンRPMトレースモジュールはエンジン回転数（RPM）を表示します。\n\nアルゴリズムロジック：\n1. データ範囲：F1エンジンRPM範囲は約8,000-15,000\n2. レッドライン検出：最大RPM（〜15,000）に近づくとアップシフトをトリガー\n3. シフト分析：ギアデータと組み合わせてシフトタイミングの妥当性を判断\n4. エンジンモード推測：異なるエンジンモードは異なるRPM曲線特性を持つ'
            },
            'help_rpm_trace_features': {
                'zh': '- 引擎轉速即時監控\n- 紅線區域標示\n- 換檔點轉速記錄\n- 與檔位/油門曲線交叉分析',
                'en': '- Real-time engine RPM monitoring\n- Redline zone marking\n- Shift point RPM recording\n- Cross-analysis with gear/throttle traces',
                'ja': '- リアルタイムエンジンRPM監視\n- レッドラインゾーンのマーキング\n- シフトポイントRPM記録\n- ギア/スロットルトレースとのクロス分析'
            },
            'help_rpm_trace_colors': {
                'zh': '- 車隊顏色區分車手\n- 紅色區域：接近紅線轉速\n- 下降曲線表示升檔或滑行',
                'en': '- Team colors distinguish drivers\n- Red zone: Approaching redline RPM\n- Declining curves indicate upshift or coasting',
                'ja': '- チームカラーでドライバーを区別\n- 赤ゾーン：レッドラインRPMに接近\n- 下降曲線はアップシフトまたはコースティングを示す'
            },
            
            # ========== Circle Map Help / 圓形地圖說明 ==========
            'help_circle_map_title': {'zh': '圓形地圖', 'en': 'Circle Map', 'ja': 'サークルマップ'},
            'help_circle_map_desc': {
                'zh': '圓形地圖以環形視圖顯示所有車手的相對位置。\n\n演算法邏輯：\n1. 位置計算：將車手的賽道位置（0-100%）映射到圓周角度（0-360°）\n2. 間距計算：計算相鄰車手之間的角度差對應的秒數差距\n3. 即時更新：約每秒更新一次所有車手位置\n4. 衝突預測：當兩車手角度差小於閾值時標示為接近戰鬥',
                'en': 'Circle Map displays all driver relative positions in a circular view.\n\nAlgorithm Logic:\n1. Position Calculation: Maps driver track position (0-100%) to circular angle (0-360 degrees)\n2. Gap Calculation: Computes seconds gap from angle difference between adjacent drivers\n3. Real-time Update: Updates all driver positions approximately once per second\n4. Battle Detection: Marks as close battle when two drivers angle difference below threshold',
                'ja': 'サークルマップはすべてのドライバーの相対位置を円形ビューで表示します。\n\nアルゴリズムロジック：\n1. 位置計算：ドライバーのトラック位置（0-100%）を円周角度（0-360度）にマッピング\n2. ギャップ計算：隣接ドライバー間の角度差から秒数ギャップを計算\n3. リアルタイム更新：約1秒ごとにすべてのドライバー位置を更新\n4. バトル検出：2ドライバーの角度差が閾値以下の場合、接近バトルとしてマーク'
            },
            'help_circle_map_features': {
                'zh': '- 直觀顯示場上車手分布\n- 識別車群和單獨跑車手\n- 標示 DRS 範圍內的車手\n- 進站車手特殊標示',
                'en': '- Intuitive display of driver distribution on track\n- Identify groups and isolated drivers\n- Mark drivers within DRS range\n- Special marking for pit lane drivers',
                'ja': '- トラック上のドライバー分布を直感的に表示\n- グループと孤立したドライバーを識別\n- DRS範囲内のドライバーをマーク\n- ピットレーンのドライバーを特別にマーク'
            },
            'help_circle_map_colors': {
                'zh': '- 車手使用車隊顏色\n- 黃色弧線：黃旗區域\n- 紅色弧線：紅旗或危險區域\n- 綠色弧線：DRS 啟用區',
                'en': '- Drivers use team colors\n- Yellow arcs: Yellow flag zones\n- Red arcs: Red flag or danger zones\n- Green arcs: DRS activation zones',
                'ja': '- ドライバーはチームカラーを使用\n- 黄色アーク：イエローフラッグゾーン\n- 赤アーク：レッドフラッグまたは危険ゾーン\n- 緑アーク：DRS有効化ゾーン'
            },
            
            # ========== Pit Window Help / 進站窗口說明 ==========
            'help_pit_window_title': {'zh': '進站窗口', 'en': 'Pit Window', 'ja': 'ピットウィンドウ'},
            'help_pit_window_desc': {
                'zh': '進站窗口模組顯示車手的預測進站時機和策略選項。\n\n演算法邏輯：\n1. 輪胎衰退模型：根據圈數和輪胎類型預測剩餘壽命\n2. Undercut 窗口：計算提前進站可獲得的位置優勢\n3. Overcut 窗口：計算延後進站在新胎上的速度優勢\n4. 最佳策略推薦：綜合輪胎狀態、賽道位置、與對手差距給出建議',
                'en': 'Pit Window module displays predicted pit timing and strategy options for drivers.\n\nAlgorithm Logic:\n1. Tire Degradation Model: Predicts remaining life based on laps and tire type\n2. Undercut Window: Calculates position advantage from early pit stop\n3. Overcut Window: Calculates speed advantage from delayed pit on fresh tires\n4. Optimal Strategy Recommendation: Combines tire state, track position, gaps to give suggestions',
                'ja': 'ピットウィンドウモジュールはドライバーの予測ピットタイミングと戦略オプションを表示します。\n\nアルゴリズムロジック：\n1. タイヤ劣化モデル：ラップ数とタイヤタイプに基づいて残り寿命を予測\n2. アンダーカットウィンドウ：早期ピットストップからの位置優位性を計算\n3. オーバーカットウィンドウ：フレッシュタイヤでの遅延ピットからの速度優位性を計算\n4. 最適戦略推奨：タイヤ状態、トラック位置、ギャップを組み合わせて提案'
            },
            'help_pit_window_features': {
                'zh': '- 預測進站圈數範圍\n- Undercut/Overcut 分析\n- 與對手策略比較\n- 考慮安全車可能性',
                'en': '- Predict pit stop lap range\n- Undercut/Overcut analysis\n- Compare with opponent strategies\n- Consider safety car probability',
                'ja': '- ピットストップラップ範囲を予測\n- アンダーカット/オーバーカット分析\n- 対戦相手の戦略と比較\n- セーフティカーの可能性を考慮'
            },
            'help_pit_window_colors': {
                'zh': '- 綠色：建議進站窗口\n- 黃色：可選進站窗口\n- 紅色：不建議進站\n- 灰色：已完成進站',
                'en': '- Green: Recommended pit window\n- Yellow: Optional pit window\n- Red: Not recommended to pit\n- Gray: Pit completed',
                'ja': '- 緑：推奨ピットウィンドウ\n- 黄：オプションピットウィンドウ\n- 赤：ピット非推奨\n- グレー：ピット完了'
            },
            
            # ========== Tyre Strategy Help / 輪胎策略說明 ==========
            'help_tyre_strategy_title': {'zh': '輪胎策略', 'en': 'Tyre Strategy', 'ja': 'タイヤ戦略'},
            'help_tyre_strategy_desc': {
                'zh': '輪胎策略模組顯示各車手的輪胎使用歷史和預測。\n\n演算法邏輯：\n1. Stint 記錄：追蹤每套輪胎的使用圈數\n2. 衰退曲線：根據歷史數據建立各輪胎的衰退模型\n3. 剩餘圈數預測：基於衰退模型預測輪胎的有效壽命\n4. 策略比較：分析不同策略（1停/2停/3停）的預期完賽時間',
                'en': 'Tyre Strategy module displays tire usage history and predictions for each driver.\n\nAlgorithm Logic:\n1. Stint Recording: Track laps completed on each tire set\n2. Degradation Curve: Build degradation model for each tire based on historical data\n3. Remaining Lap Prediction: Predict effective tire life based on degradation model\n4. Strategy Comparison: Analyze expected race time for different strategies (1-stop/2-stop/3-stop)',
                'ja': 'タイヤ戦略モジュールは各ドライバーのタイヤ使用履歴と予測を表示します。\n\nアルゴリズムロジック：\n1. スティント記録：各タイヤセットでの完走ラップを追跡\n2. 劣化曲線：履歴データに基づいて各タイヤの劣化モデルを構築\n3. 残りラップ予測：劣化モデルに基づいてタイヤの有効寿命を予測\n4. 戦略比較：異なる戦略（1ストップ/2ストップ/3ストップ）の予想レースタイムを分析'
            },
            'help_tyre_strategy_features': {
                'zh': '- 可視化輪胎使用時間軸\n- 輪胎衰退監控\n- 最佳策略推薦\n- 歷史數據比較',
                'en': '- Visualize tire usage timeline\n- Tire degradation monitoring\n- Optimal strategy recommendation\n- Historical data comparison',
                'ja': '- タイヤ使用タイムラインを可視化\n- タイヤ劣化監視\n- 最適戦略推奨\n- 履歴データ比較'
            },
            'help_tyre_strategy_colors': {
                'zh': '- 紅色：軟胎 (SOFT)\n- 黃色：中性胎 (MEDIUM)\n- 白色：硬胎 (HARD)\n- 綠色：中雨胎 (INTERMEDIATE)\n- 藍色：全雨胎 (WET)',
                'en': '- Red: Soft tire (SOFT)\n- Yellow: Medium tire (MEDIUM)\n- White: Hard tire (HARD)\n- Green: Intermediate tire (INTERMEDIATE)\n- Blue: Wet tire (WET)',
                'ja': '- 赤：ソフトタイヤ (SOFT)\n- 黄：ミディアムタイヤ (MEDIUM)\n- 白：ハードタイヤ (HARD)\n- 緑：インターミディエイトタイヤ (INTERMEDIATE)\n- 青：ウェットタイヤ (WET)'
            },
            
            # ========== Battle Insight Help / 戰鬥分析說明 ==========
            'help_battle_insight_title': {'zh': '戰鬥分析', 'en': 'Battle Insight', 'ja': 'バトル分析'},
            'help_battle_insight_desc': {
                'zh': '戰鬥分析模組識別並追蹤賽道上的車手對決。\n\n演算法邏輯：\n1. 戰鬥識別：當兩車手差距小於 1.5 秒時判定為戰鬥\n2. 攻防評分：根據相對速度、DRS 使用、位置變化計算\n3. 超車預測：基於歷史數據和當前條件預測超車可能性\n4. 戰鬥強度：衡量雙方的攻守轉換頻率',
                'en': 'Battle Insight module identifies and tracks driver duels on track.\n\nAlgorithm Logic:\n1. Battle Identification: Determined as battle when gap less than 1.5 seconds\n2. Attack/Defense Scoring: Calculated based on relative speed, DRS usage, position changes\n3. Overtake Prediction: Predict overtake probability based on historical data and current conditions\n4. Battle Intensity: Measures attack/defense transition frequency',
                'ja': 'バトル分析モジュールはトラック上のドライバーデュエルを識別し追跡します。\n\nアルゴリズムロジック：\n1. バトル識別：ギャップが1.5秒未満の場合バトルと判定\n2. 攻守スコアリング：相対速度、DRS使用、位置変化に基づいて計算\n3. オーバーテイク予測：履歴データと現在の状況に基づいてオーバーテイク確率を予測\n4. バトル強度：攻守転換頻度を測定'
            },
            'help_battle_insight_features': {
                'zh': '- 即時戰鬥識別\n- 攻防優勢分析\n- 歷史對決記錄\n- 超車熱點標示',
                'en': '- Real-time battle identification\n- Attack/defense advantage analysis\n- Historical duel records\n- Overtake hotspot marking',
                'ja': '- リアルタイムバトル識別\n- 攻守優位性分析\n- 過去のデュエル記録\n- オーバーテイクホットスポットのマーキング'
            },
            'help_battle_insight_colors': {
                'zh': '- 紅色：攻擊方（追趕中）\n- 藍色：防守方（被追趕）\n- 黃色：僵持狀態\n- 綠色：成功超車',
                'en': '- Red: Attacking driver (chasing)\n- Blue: Defending driver (being chased)\n- Yellow: Stalemate state\n- Green: Successful overtake',
                'ja': '- 赤：攻撃側（追跡中）\n- 青：防御側（追われている）\n- 黄：膠着状態\n- 緑：オーバーテイク成功'
            },
            
            # ========== Chase Strategy Help / 追趕策略說明 ==========
            'help_chase_strategy_title': {'zh': '追趕策略', 'en': 'Chase Strategy', 'ja': '追跡戦略'},
            'help_chase_strategy_desc': {
                'zh': '追趕策略模組分析車手追趕前車所需的條件和預測。\n\n演算法邏輯：\n1. 追趕時間計算：基於單圈速度差異計算追上所需圈數\n2. 輪胎效應：考慮雙方輪胎的相對衰退率\n3. DRS 效應：評估 DRS 對縮小差距的貢獻\n4. 進站影響：預測對手進站後的相對位置變化',
                'en': 'Chase Strategy module analyzes conditions and predictions for catching the car ahead.\n\nAlgorithm Logic:\n1. Chase Time Calculation: Calculate laps needed based on lap time difference\n2. Tire Effect: Consider relative degradation rates of both drivers tires\n3. DRS Effect: Evaluate DRS contribution to gap reduction\n4. Pit Stop Impact: Predict relative position change after opponent pits',
                'ja': '追跡戦略モジュールは前車に追いつくための条件と予測を分析します。\n\nアルゴリズムロジック：\n1. 追跡時間計算：ラップタイム差に基づいて必要なラップ数を計算\n2. タイヤ効果：両ドライバーのタイヤの相対劣化率を考慮\n3. DRS効果：ギャップ縮小へのDRSの貢献を評価\n4. ピットストップ影響：対戦相手のピット後の相対位置変化を予測'
            },
            'help_chase_strategy_features': {
                'zh': '- 追趕進度可視化\n- 所需圈數預測\n- 最佳追趕策略建議\n- 風險評估（輪胎過度磨損）',
                'en': '- Chase progress visualization\n- Required laps prediction\n- Optimal chase strategy suggestion\n- Risk assessment (tire over-degradation)',
                'ja': '- 追跡進捗の可視化\n- 必要ラップ数予測\n- 最適追跡戦略の提案\n- リスク評価（タイヤ過劣化）'
            },
            'help_chase_strategy_colors': {
                'zh': '- 綠色箭頭：正在縮小差距\n- 紅色箭頭：差距擴大中\n- 黃色：差距穩定\n- 車隊顏色標示目標車手',
                'en': '- Green arrow: Gap reducing\n- Red arrow: Gap increasing\n- Yellow: Gap stable\n- Team colors mark target drivers',
                'ja': '- 緑矢印：ギャップ縮小中\n- 赤矢印：ギャップ拡大中\n- 黄：ギャップ安定\n- チームカラーでターゲットドライバーをマーク'
            },
            
            # ========== Track & Weather Help / 賽道與天氣說明 ==========
            'help_track_weather_title': {'zh': '賽道與天氣', 'en': 'Track & Weather', 'ja': 'トラック＆天気'},
            'help_track_weather_desc': {
                'zh': '賽道與天氣模組顯示即時賽道狀態和氣象資訊。\n\n演算法邏輯：\n1. 氣溫追蹤：監控空氣溫度和賽道溫度變化\n2. 降雨預測：整合氣象資料預測降雨時機\n3. 賽道演化：追蹤 Rubber-in 狀態對抓地力的影響\n4. 風向分析：評估風向對不同賽道區段的影響',
                'en': 'Track & Weather module displays real-time track conditions and meteorological information.\n\nAlgorithm Logic:\n1. Temperature Tracking: Monitor air and track temperature changes\n2. Rain Prediction: Integrate weather data to predict rain timing\n3. Track Evolution: Track rubber-in state effect on grip\n4. Wind Analysis: Evaluate wind direction impact on different track sectors',
                'ja': 'トラック＆天気モジュールはリアルタイムのトラック状況と気象情報を表示します。\n\nアルゴリズムロジック：\n1. 温度追跡：気温とトラック温度の変化を監視\n2. 雨予測：気象データを統合して雨のタイミングを予測\n3. トラック進化：ラバーイン状態がグリップに与える影響を追跡\n4. 風向分析：風向きが異なるトラックセクターに与える影響を評価'
            },
            'help_track_weather_features': {
                'zh': '- 即時溫度監控\n- 降雨機率和時間預測\n- 賽道抓地力變化\n- 風速風向顯示',
                'en': '- Real-time temperature monitoring\n- Rain probability and timing prediction\n- Track grip changes\n- Wind speed and direction display',
                'ja': '- リアルタイム温度監視\n- 雨の確率とタイミング予測\n- トラックグリップ変化\n- 風速と風向表示'
            },
            'help_track_weather_colors': {
                'zh': '- 藍色：濕潤/降雨區域\n- 黃色/橙色：高溫警告\n- 綠色：理想條件\n- 灰色：乾燥賽道',
                'en': '- Blue: Wet/rain areas\n- Yellow/Orange: High temperature warning\n- Green: Ideal conditions\n- Gray: Dry track',
                'ja': '- 青：ウェット/雨エリア\n- 黄/オレンジ：高温警告\n- 緑：理想的な条件\n- グレー：ドライトラック'
            },
            
            # ========== Traffic Timeline Help / 車流時間軸說明 ==========
            'help_traffic_timeline_title': {'zh': '車流時間軸', 'en': 'Traffic Timeline', 'ja': 'トラフィックタイムライン'},
            'help_traffic_timeline_desc': {
                'zh': '車流時間軸模組顯示各車手之間的相對間距隨時間的變化。\n\n演算法邏輯：\n1. 時間序列記錄：每圈記錄所有車手的相對位置和差距\n2. 趨勢分析：計算差距變化的斜率判斷追趕/拉開\n3. 交叉檢測：識別差距曲線交叉點（超車時刻）\n4. 群組識別：將相近的車手歸類為同一戰鬥群組',
                'en': 'Traffic Timeline module displays relative gaps between drivers over time.\n\nAlgorithm Logic:\n1. Time Series Recording: Record relative positions and gaps each lap\n2. Trend Analysis: Calculate gap change slope to determine chase/gap\n3. Crossover Detection: Identify gap curve crossover points (overtake moments)\n4. Group Identification: Classify close drivers into same battle groups',
                'ja': 'トラフィックタイムラインモジュールは時間経過に伴うドライバー間の相対ギャップを表示します。\n\nアルゴリズムロジック：\n1. 時系列記録：各ラップですべてのドライバーの相対位置とギャップを記録\n2. トレンド分析：ギャップ変化の傾きを計算して追跡/ギャップを判断\n3. クロスオーバー検出：ギャップ曲線の交差点（オーバーテイクの瞬間）を識別\n4. グループ識別：接近したドライバーを同じバトルグループに分類'
            },
            'help_traffic_timeline_features': {
                'zh': '- 差距歷史趨勢圖\n- 超車時刻標記\n- 戰鬥群組可視化\n- 預測交會時間',
                'en': '- Gap history trend chart\n- Overtake moment marking\n- Battle group visualization\n- Predicted crossover time',
                'ja': '- ギャップ履歴トレンドチャート\n- オーバーテイク瞬間のマーキング\n- バトルグループの可視化\n- 予測交差時間'
            },
            'help_traffic_timeline_colors': {
                'zh': '- 車隊顏色區分車手\n- 線條斜率表示追趕/拉開趨勢\n- 交叉點用圓圈標示',
                'en': '- Team colors distinguish drivers\n- Line slope indicates chase/gap trend\n- Crossover points marked with circles',
                'ja': '- チームカラーでドライバーを区別\n- 線の傾きは追跡/ギャップの傾向を示す\n- 交差点は円でマーク'
            },
            
            # ========== Race Control Help / 比賽控制說明 ==========
            'help_race_control_title': {'zh': '比賽控制訊息', 'en': 'Race Control Messages', 'ja': 'レースコントロールメッセージ'},
            'help_race_control_desc': {
                'zh': '比賽控制訊息模組顯示 FIA 發出的官方比賽通知。\n\n演算法邏輯：\n1. 訊息分類：將訊息分為旗號、處罰、調查、資訊等類別\n2. 嚴重性評估：根據訊息內容評估對比賽的影響程度\n3. 車手關聯：解析訊息內容識別相關車手\n4. 時間排序：按時間順序顯示所有訊息',
                'en': 'Race Control Messages module displays official FIA race notifications.\n\nAlgorithm Logic:\n1. Message Classification: Categorize into flags, penalties, investigations, info\n2. Severity Assessment: Evaluate race impact based on message content\n3. Driver Association: Parse message content to identify related drivers\n4. Time Ordering: Display all messages in chronological order',
                'ja': 'レースコントロールメッセージモジュールはFIAの公式レース通知を表示します。\n\nアルゴリズムロジック：\n1. メッセージ分類：フラッグ、ペナルティ、調査、情報にカテゴリ分け\n2. 重大度評価：メッセージ内容に基づいてレースへの影響を評価\n3. ドライバー関連：メッセージ内容を解析して関連ドライバーを識別\n4. 時間順序：すべてのメッセージを時系列順に表示'
            },
            'help_race_control_features': {
                'zh': '- 即時訊息通知\n- 按類別篩選\n- 車手相關訊息高亮\n- 歷史訊息查詢',
                'en': '- Real-time message notifications\n- Filter by category\n- Highlight driver-related messages\n- Historical message query',
                'ja': '- リアルタイムメッセージ通知\n- カテゴリでフィルター\n- ドライバー関連メッセージをハイライト\n- 過去のメッセージ検索'
            },
            'help_race_control_colors': {
                'zh': '- 紅色：紅旗/嚴重訊息\n- 黃色：黃旗/警告\n- 藍色：藍旗\n- 白色：一般資訊',
                'en': '- Red: Red flag/serious messages\n- Yellow: Yellow flag/warnings\n- Blue: Blue flag\n- White: General information',
                'ja': '- 赤：レッドフラッグ/重大メッセージ\n- 黄：イエローフラッグ/警告\n- 青：ブルーフラッグ\n- 白：一般情報'
            },
            
            # ========== Lap Time Distribution Help / 圈速分布說明 ==========
            'help_lap_distribution_title': {'zh': '圈速分布', 'en': 'Lap Time Distribution', 'ja': 'ラップタイム分布'},
            'help_lap_distribution_desc': {
                'zh': '圈速分布模組以直方圖或小提琴圖顯示車手圈速的統計分布。\n\n演算法邏輯：\n1. 資料清洗：排除進站圈、慢車圈、黃旗圈等異常資料\n2. 分布計算：計算平均值、中位數、標準差\n3. 一致性評分：標準差越小表示越穩定\n4. 尾部分析：識別異常快圈或慢圈',
                'en': 'Lap Time Distribution module displays statistical distribution of lap times as histogram or violin plot.\n\nAlgorithm Logic:\n1. Data Cleaning: Exclude pit laps, slow laps, yellow flag laps\n2. Distribution Calculation: Calculate mean, median, standard deviation\n3. Consistency Scoring: Lower standard deviation indicates more stable\n4. Tail Analysis: Identify outlier fast or slow laps',
                'ja': 'ラップタイム分布モジュールはヒストグラムまたはバイオリンプロットでラップタイムの統計分布を表示します。\n\nアルゴリズムロジック：\n1. データクリーニング：ピットラップ、スローラップ、イエローフラッグラップを除外\n2. 分布計算：平均値、中央値、標準偏差を計算\n3. 一貫性スコアリング：標準偏差が低いほど安定\n4. テール分析：外れ値の速いまたは遅いラップを識別'
            },
            'help_lap_distribution_features': {
                'zh': '- 直方圖/箱線圖/小提琴圖視圖\n- 多車手比較\n- 一致性排名\n- 最佳/最差圈標示',
                'en': '- Histogram/Box plot/Violin plot views\n- Multi-driver comparison\n- Consistency ranking\n- Best/worst lap marking',
                'ja': '- ヒストグラム/ボックスプロット/バイオリンプロットビュー\n- マルチドライバー比較\n- 一貫性ランキング\n- ベスト/ワーストラップのマーキング'
            },
            'help_lap_distribution_colors': {
                'zh': '- 車隊顏色區分車手\n- 紫色標示最快圈\n- 紅色標示異常慢圈\n- 透明度表示資料密度',
                'en': '- Team colors distinguish drivers\n- Purple marks fastest laps\n- Red marks abnormally slow laps\n- Transparency indicates data density',
                'ja': '- チームカラーでドライバーを区別\n- 紫は最速ラップをマーク\n- 赤は異常に遅いラップをマーク\n- 透明度はデータ密度を示す'
            },
            
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
            
            # Season Progress Widget - Future Season Messages
            'future_season_not_started': {'zh': '賽季尚未開始，敬請期待', 'en': 'Season Not Started Yet, Stay Tuned', 'ja': 'シーズン未開始、お楽しみに'},
            'future_season_first_race': {'zh': '首場賽事：{name}', 'en': 'First Race: {name}', 'ja': '初戦：{name}'},
            'future_season_race_time': {'zh': '比賽時間：{date}', 'en': 'Race Time: {date}', 'ja': 'レース時間：{date}'},
            'future_season_countdown': {'zh': '距離開賽還有 {days} 天', 'en': '{days} Days Until Season Start', 'ja': '開幕まであと {days} 日'},
            'future_season_total_races': {'zh': '本賽季共 {total} 場大獎賽', 'en': '{total} Races This Season', 'ja': '今シーズン {total} 戦'},
            'future_season_no_data': {'zh': '賽季數據尚未發布', 'en': 'Season data not yet available', 'ja': 'シーズンデータはまだ公開されていません'},
            
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
            'live_timing_tree': {'zh': '即時計時', 'en': 'Live Timing', 'ja': 'ライブタイミング'},
            
            # === Live Timing 主項目翻譯 ===
            'track_map': {'zh': '賽道地圖', 'en': 'Track Map', 'ja': 'トラックマップ'},
            'circle_map': {'zh': '圓形地圖', 'en': 'Circle Map', 'ja': 'サークルマップ'},
            'live_ranking': {'zh': '即時排名', 'en': 'Live Ranking', 'ja': 'ライブランキング'},
            'pit_window': {'zh': '進站窗口', 'en': 'Pit Window', 'ja': 'ピットウィンドウ'},
            'tyre_strategy': {'zh': '輪胎策略', 'en': 'Tyre Strategy', 'ja': 'タイヤ戦略'},
            'driver_strategy': {'zh': '車手策略', 'en': 'Driver Strategy', 'ja': 'ドライバー戦略'},
            'lap_time_distribution': {'zh': '圈速分布', 'en': 'Lap Time Distribution', 'ja': 'ラップタイム分布'},
            'race_control_messages': {'zh': '比賽控制訊息', 'en': 'Race Control Messages', 'ja': 'レースコントロールメッセージ'},
            'speed_trace': {'zh': '速度追蹤', 'en': 'Speed Trace', 'ja': 'スピードトレース'},
            'throttle_trace': {'zh': '油門追蹤', 'en': 'Throttle Trace', 'ja': 'スロットルトレース'},
            'brake_trace': {'zh': '煞車追蹤', 'en': 'Brake Trace', 'ja': 'ブレーキトレース'},
            'gear_trace': {'zh': '檔位追蹤', 'en': 'Gear Trace', 'ja': 'ギアトレース'},
            'drs_trace': {'zh': 'DRS 追蹤', 'en': 'DRS Trace', 'ja': 'DRS トレース'},
            'rpm_trace': {'zh': '轉速追蹤', 'en': 'RPM Trace', 'ja': 'RPM トレース'},
            'chase_strategy': {'zh': '追逐策略', 'en': 'Chase Strategy', 'ja': '追撃戦略'},
            'track_weather': {'zh': '賽道與天氣', 'en': 'Track & Weather', 'ja': 'トラック＆天気'},
            
            # === Lap History 子群組翻譯 ===
            'lap_history_group': {'zh': '圈速歷史', 'en': 'Lap History', 'ja': 'ラップヒストリー'},
            'lap_history_lap_time': {'zh': '圈速歷史 - 完整圈速', 'en': 'Lap History - Lap Time', 'ja': 'ラップヒストリー - ラップタイム'},
            'lap_history_s1': {'zh': '圈速歷史 - 第一段', 'en': 'Lap History - S1', 'ja': 'ラップヒストリー - S1'},
            'lap_history_s2': {'zh': '圈速歷史 - 第二段', 'en': 'Lap History - S2', 'ja': 'ラップヒストリー - S2'},
            'lap_history_s3': {'zh': '圈速歷史 - 第三段', 'en': 'Lap History - S3', 'ja': 'ラップヒストリー - S3'},
            'throttle_95_history': {'zh': '油門 95% 歷史', 'en': 'Throttle 95%', 'ja': 'スロットル 95%'},
            'sf_percentage_history': {'zh': 'SF% 歷史', 'en': 'SF% History', 'ja': 'SF% ヒストリー'},
            'top_speed_history': {'zh': '最高速歷史', 'en': 'Top Speed History', 'ja': '最高速ヒストリー'},
            
            # === Trace 追蹤子群組翻譯 ===
            'trace_group': {'zh': '遙測追蹤', 'en': 'Trace', 'ja': 'トレース'},
            
            # === Sector Comparison 子群組翻譯 ===
            'sector_comparison_group': {'zh': '分段比較', 'en': 'Sector Comparison', 'ja': 'セクター比較'},
            's1_comparison': {'zh': '第一段比較', 'en': 'S1 Comparison', 'ja': 'S1 比較'},
            's2_comparison': {'zh': '第二段比較', 'en': 'S2 Comparison', 'ja': 'S2 比較'},
            's3_comparison': {'zh': '第三段比較', 'en': 'S3 Comparison', 'ja': 'S3 比較'},
            
            # === 向後兼容的舊 key（保留） ===
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
            'Actual': {'zh': '實際', 'en': 'Actual', 'ja': '実際'},
            'Delta': {'zh': '差距', 'en': 'Delta', 'ja': 'デルタ'},
            'Tyre': {'zh': '輪胎', 'en': 'Tyre', 'ja': 'タイヤ'},
            'Lap': {'zh': '圈', 'en': 'Lap', 'ja': 'ラップ'},
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
            
            # ===== FP2 -> Q Prediction & Blocking Analysis =====
            'FP2_PREDICTION_TITLE': {'zh': 'FP2 -> Q 預測', 'en': 'FP2 -> Q Prediction', 'ja': 'FP2 -> Q 予測'},
            'BLOCKING_ANALYSIS': {'zh': '阻擋分析', 'en': 'Blocking Analysis', 'ja': 'ブロッキング分析'},
            'PREDICTION_INFO': {'zh': '預測資訊', 'en': 'Prediction Info', 'ja': '予測情報'},
            'APPLY_DRIVER_TO_SIM': {'zh': '套用選定車手至模擬', 'en': 'Apply Selected Driver to Simulation', 'ja': '選択したドライバーをシミュレーションに適用'},
            
            # Table headers
            'RANK': {'zh': '排名', 'en': 'Rank', 'ja': '順位'},
            'DRIVER': {'zh': '車手', 'en': 'Driver', 'ja': 'ドライバー'},
            'TEAM': {'zh': '車隊', 'en': 'Team', 'ja': 'チーム'},
            'FP2_TIME': {'zh': 'FP2 時間', 'en': 'FP2 Time', 'ja': 'FP2タイム'},
            'PREDICTED_Q': {'zh': '預測 Q', 'en': 'Predicted Q', 'ja': '予測Q'},
            'DELTA': {'zh': '差距', 'en': 'Delta', 'ja': 'デルタ'},
            
            # Info labels
            'TRACK': {'zh': '賽道', 'en': 'Track', 'ja': 'サーキット'},
            'MODEL': {'zh': '模型', 'en': 'Model', 'ja': 'モデル'},
            'SELECTED': {'zh': '已選擇', 'en': 'Selected', 'ja': '選択'},
            'NONE': {'zh': '無', 'en': 'None', 'ja': 'なし'},
            'NO_DATA_AVAILABLE': {'zh': '無可用數據', 'en': 'No data available', 'ja': 'データがありません'},
            
            # Blocking Analysis content
            'SELECT_DRIVER_FOR_BLOCKING': {'zh': '從表格選擇車手以查看阻擋分析。', 'en': 'Select a driver from the table to see blocking analysis.', 'ja': 'テーブルからドライバーを選択してブロッキング分析を表示'},
            'ANALYSIS_INCLUDES': {'zh': '分析包含', 'en': 'Analysis includes', 'ja': '分析内容'},
            'DRIVERS_AHEAD_SLOWER': {'zh': '前方較慢的車手', 'en': 'Drivers ahead with slower pace', 'ja': '前方のペースが遅いドライバー'},
            'ESTIMATED_TIME_LOSS': {'zh': '每圈預計損失時間', 'en': 'Estimated time loss per lap', 'ja': '1周あたりの推定タイムロス'},
            'STRATEGY_RECOMMENDATIONS': {'zh': '策略建議', 'en': 'Strategy recommendations', 'ja': '戦略提案'},
            'POSITION_IMPROVEMENT_POTENTIAL': {'zh': '位置提升潛力', 'en': 'Position improvement potential', 'ja': 'ポジション改善の可能性'},
            
            # Blocking analysis data
            'STARTING_POSITION': {'zh': '起始位置', 'en': 'Starting Position', 'ja': 'スタートポジション'},
            'DRIVERS_AHEAD': {'zh': '前方車手數', 'en': 'Drivers Ahead', 'ja': '前方ドライバー数'},
            'TOTAL_BLOCKING_TIME': {'zh': '總阻擋時間', 'en': 'Total Blocking Time', 'ja': '総ブロッキングタイム'},
            'PER_LAP_LOSS': {'zh': '每圈損失', 'en': 'Per Lap Loss', 'ja': '1周あたりのロス'},
            'STUCK_PROBABILITY': {'zh': '被困機率', 'en': 'Stuck Probability', 'ja': 'スタック確率'},
            'RECOMMENDED_STOP': {'zh': '建議進站', 'en': 'Recommended Stop', 'ja': '推奨ピットストップ'},
            'LAP': {'zh': '第', 'en': 'Lap', 'ja': 'ラップ'},
            'UNDERCUT_POTENTIAL': {'zh': 'Undercut 潛力', 'en': 'Undercut Potential', 'ja': 'アンダーカット可能性'},
            'POSITION_IMPROVEMENT': {'zh': '位置提升', 'en': 'Position Improvement', 'ja': 'ポジション改善'},
            'PLACES': {'zh': '位', 'en': 'places', 'ja': 'ポジション'},
            'POSITION_FORECAST': {'zh': '位置預測', 'en': 'Position Forecast', 'ja': 'ポジション予測'},
            'STRATEGY': {'zh': '策略', 'en': 'Strategy', 'ja': '戦略'},
            'EXPECTED': {'zh': '預期', 'en': 'Expected', 'ja': '予想'},
            'BEST_WORST': {'zh': '最佳/最差', 'en': 'Best/Worst', 'ja': '最良/最悪'},
            'AGGRESSIVE': {'zh': '激進', 'en': 'Aggressive', 'ja': 'アグレッシブ'},
            'CONSERVATIVE': {'zh': '保守', 'en': 'Conservative', 'ja': 'コンサバティブ'},
            'CRITICAL_BLOCKING': {'zh': '關鍵阻擋', 'en': 'Critical Blocking', 'ja': '重大ブロッキング'},
            'BLOCKING_NOT_AVAILABLE': {'zh': '此車手無法進行阻擋分析。', 'en': 'Blocking analysis not available for this driver.', 'ja': 'このドライバーのブロッキング分析は利用できません'},
            'POSSIBLE_REASONS': {'zh': '可能原因', 'en': 'Possible reasons', 'ja': '考えられる理由'},
            'NO_FP2_DATA': {'zh': '無 FP2 數據', 'en': 'No FP2 data loaded', 'ja': 'FP2データなし'},
            'DRIVER_NOT_FOUND': {'zh': '預測中找不到車手', 'en': 'Driver not found in predictions', 'ja': 'ドライバーが予測にありません'},
            
            # Strategy Comparison
            'STRATEGY_RANKING': {'zh': '策略排名', 'en': 'Strategy Ranking', 'ja': '戦略ランキング'},
            'STRATEGY_DETAILS': {'zh': '策略詳情', 'en': 'Strategy Details', 'ja': '戦略詳細'},
            'MC_POSITION_ANALYSIS': {'zh': 'Monte Carlo 位置分析', 'en': 'Monte Carlo Position Analysis', 'ja': 'モンテカルロポジション分析'},
            'PLAN': {'zh': '方案', 'en': 'Plan', 'ja': 'プラン'},
            'STOPS': {'zh': '進站', 'en': 'Stops', 'ja': 'ストップ'},
            'TOTAL_TIME': {'zh': '總時間', 'en': 'Total Time', 'ja': '総タイム'},
            'GAP': {'zh': '差距', 'en': 'Gap', 'ja': 'ギャップ'},
            'PIT_LOSS': {'zh': '進站損失', 'en': 'Pit Loss', 'ja': 'ピットロス'},
            'BEST': {'zh': '最佳', 'en': 'Best', 'ja': '最良'},
            'WIN_PCT': {'zh': '勝率', 'en': 'Win%', 'ja': '勝率'},
            'MEAN_TIME': {'zh': '平均時間', 'en': 'Mean Time', 'ja': '平均タイム'},
            'STD_DEV': {'zh': '標準差', 'en': 'Std Dev', 'ja': '標準偏差'},
            'NO_SC': {'zh': '無 SC', 'en': 'No SC', 'ja': 'SC無し'},
            'WITH_SC': {'zh': '有 SC', 'en': 'With SC', 'ja': 'SC有り'},
            'POS_GAIN': {'zh': '位置增益', 'en': 'Pos Gain', 'ja': 'ポジションゲイン'},
            'RISK': {'zh': '風險', 'en': 'Risk', 'ja': 'リスク'},
            'SC_BENEFITS': {'zh': 'SC 有利', 'en': 'SC benefits this strategy', 'ja': 'SCがこの戦略に有利'},
            'SC_HURTS': {'zh': 'SC 不利', 'en': 'SC hurts this strategy', 'ja': 'SCがこの戦略に不利'},
            'SC_NEUTRAL': {'zh': 'SC 中性', 'en': 'SC neutral', 'ja': 'SC中立'},
            'EXPECTED_POS_IMPROVEMENT': {'zh': '預期位置提升', 'en': 'Expected position improvement', 'ja': '予想ポジション改善'},
            'EXPECTED_POS_DROP': {'zh': '預期位置下降', 'en': 'Expected position drop', 'ja': '予想ポジション低下'},
            'ITERATIONS': {'zh': '迭代次數', 'en': 'Iterations', 'ja': '反復回数'},
            'SC_RATE': {'zh': 'SC 機率', 'en': 'SC Rate', 'ja': 'SC確率'},
            'MEAN_SC_COUNT': {'zh': '平均 SC 次數', 'en': 'Mean SC Count', 'ja': '平均SC回数'},
            
            # ===== Opponent Tab - Undercut/Overcut Analysis =====
            'OPPONENT_STRATEGIES': {'zh': '對手策略', 'en': 'Opponent Strategies', 'ja': '対戦相手戦略'},
            'UNDERCUT_OVERCUT': {'zh': 'Undercut/Overcut', 'en': 'Undercut/Overcut', 'ja': 'アンダーカット/オーバーカット'},
            'OPPONENT_CONFIG': {'zh': '對手設定', 'en': 'Opponent Configuration', 'ja': '対戦相手設定'},
            'OUR_STRATEGY': {'zh': '我方策略', 'en': 'Our Strategy', 'ja': '自分の戦略'},
            'OPPONENT': {'zh': '對手', 'en': 'Opponent', 'ja': '対戦相手'},
            'CURRENT_GAP': {'zh': '當前差距', 'en': 'Current Gap', 'ja': '現在のギャップ'},
            'SECONDS_ABBREV': {'zh': '秒', 'en': 's', 'ja': '秒'},
            'CALCULATE': {'zh': '計算', 'en': 'Calculate', 'ja': '計算'},
            'UNDERCUT_WINDOW': {'zh': 'Undercut 窗口', 'en': 'Undercut Window', 'ja': 'アンダーカットウィンドウ'},
            'OVERCUT_WINDOW': {'zh': 'Overcut 窗口', 'en': 'Overcut Window', 'ja': 'オーバーカットウィンドウ'},
            'OPP_PIT': {'zh': '對手進站', 'en': 'Opponent Pit', 'ja': '対戦相手ピット'},
            'WINDOW': {'zh': '窗口', 'en': 'Window', 'ja': 'ウィンドウ'},
            'ESTIMATED_GAIN': {'zh': '預估增益', 'en': 'Est. Gain', 'ja': '推定ゲイン'},
            'RECOMMENDATION': {'zh': '建議', 'en': 'Recommendation', 'ja': '推奨'},
            'GAP_TIMELINE': {'zh': '差距時間線預測', 'en': 'Gap Timeline Prediction', 'ja': 'ギャップタイムライン予測'},
            'PYQTGRAPH_NOT_INSTALLED': {'zh': 'pyqtgraph 未安裝', 'en': 'pyqtgraph not installed', 'ja': 'pyqtgraphがインストールされていません'},
            'STRONG': {'zh': '強烈', 'en': 'Strong', 'ja': '強力'},
            'MODERATE': {'zh': '適中', 'en': 'Moderate', 'ja': '中程度'},
            'WEAK': {'zh': '弱', 'en': 'Weak', 'ja': '弱い'},
            'GAP_TO_OPPONENT': {'zh': '與對手差距', 'en': 'Gap to Opponent', 'ja': '対戦相手とのギャップ'},
            'GAP_EVOLUTION_TITLE': {'zh': '差距變化 (正值 = 落後)', 'en': 'Gap Evolution (positive = behind)', 'ja': 'ギャップ推移 (正=後方)'},
            
            # ===== Strategy Comparison - Blocking Analysis =====
            'PIT_EXIT_BLOCKING': {'zh': '出站阻擋分析', 'en': 'Pit Exit Blocking Analysis', 'ja': 'ピット出口ブロッキング分析'},
            'PIT_LAP': {'zh': '進站圈', 'en': 'Pit Lap', 'ja': 'ピットラップ'},
            'BLOCKING_DRIVERS': {'zh': '阻擋車手', 'en': 'Blocking Drivers', 'ja': 'ブロッキングドライバー'},
            'TIME_LOSS': {'zh': '時間損失', 'en': 'Time Loss', 'ja': 'タイムロス'},
            'ADVICE': {'zh': '建議', 'en': 'Advice', 'ja': 'アドバイス'},
            'SET_OPPONENT_STRATEGIES': {'zh': '在對手頁籤設定對手策略以查看阻擋分析', 'en': 'Set opponent strategies in Opponents tab to see blocking analysis', 'ja': '対戦相手タブで戦略を設定してブロッキング分析を表示'},
            'NO_OPPONENT_PITS': {'zh': '無對手進站數據', 'en': 'No opponent pit data available', 'ja': '対戦相手のピットデータがありません'},
            'AVOID_PIT': {'zh': '考慮不同進站窗口', 'en': 'Consider different pit window', 'ja': '別のピットウィンドウを検討'},
            'POSSIBLE_TRAFFIC': {'zh': '可能遇到車流', 'en': 'Possible traffic', 'ja': 'トラフィックの可能性'},
            'CLEAR_AIR': {'zh': '預期淨空', 'en': 'Clear air expected', 'ja': 'クリアエア予想'},
            'BLOCKING_SUMMARY': {'zh': '潛在進站衝突', 'en': 'Potential pit conflicts', 'ja': '潜在的なピットコンフリクト'},
            'BLOCKING_HINT': {'zh': '設定後可查看進站時間窗口衝突分析', 'en': 'After setting, view pit window conflict analysis', 'ja': '設定後、ピットウィンドウの競合分析を表示'},
            'RUN_SIMULATION_FIRST': {'zh': '請先執行模擬以查看阻擋分析', 'en': 'Run simulation first to see blocking analysis', 'ja': 'ブロッキング分析を表示するには、まずシミュレーションを実行してください'},
            
            # ===== Opponent Strategy Panel =====
            'GLOBAL_STRATEGY_SETTINGS': {'zh': '全局策略設定', 'en': 'Global Strategy Settings', 'ja': 'グローバル戦略設定'},
            'DRIVER_STRATEGY_SETTINGS': {'zh': '車手策略設定', 'en': 'Driver Strategy Settings', 'ja': 'ドライバー戦略設定'},
            'STOP': {'zh': '停', 'en': 'Stop', 'ja': '停止'},
            'STOPS': {'zh': '停', 'en': 'Stops', 'ja': '停止'},
            'DEFAULT_STOPS': {'zh': '預設進站次數', 'en': 'Default Stops', 'ja': 'デフォルト停止'},
            'DEFAULT_TIRES': {'zh': '預設輪胎策略', 'en': 'Default Tire Strategy', 'ja': 'デフォルトタイヤ戦略'},
            'USE_FP2_PREDICTION': {'zh': '使用 FP2 Long Run 數據預測', 'en': 'Use FP2 Long Run Data for Prediction', 'ja': 'FP2ロングランデータを使用して予測'},
            'APPLY_TO_ALL': {'zh': '套用至所有車手', 'en': 'Apply to All Drivers', 'ja': '全ドライバーに適用'},
            'POSITION': {'zh': '位置', 'en': 'Pos', 'ja': '位置'},
            'DRIVER': {'zh': '車手', 'en': 'Driver', 'ja': 'ドライバー'},
            'TIRES': {'zh': '輪胎', 'en': 'Tires', 'ja': 'タイヤ'},
            'ACTION': {'zh': '操作', 'en': 'Action', 'ja': 'アクション'},
            'RESET': {'zh': '重置', 'en': 'Reset', 'ja': 'リセット'},
            
            # ===== Position Analysis Tab (NEW) =====
            'POSITION_SUMMARY': {'zh': '位置分析摘要', 'en': 'Position Analysis Summary', 'ja': 'ポジション分析サマリー'},
            'PODIUM_PROB': {'zh': '頒獎台機率', 'en': 'Podium Probability', 'ja': '表彰台確率'},
            'TOP5_PROB': {'zh': 'Top 5 機率', 'en': 'Top 5 Probability', 'ja': 'トップ5確率'},
            'POINTS_PROB': {'zh': '積分區機率', 'en': 'Points Probability', 'ja': 'ポイント圏確率'},
            'EXPECTED_GAIN': {'zh': '預期位置變化', 'en': 'Expected Position Gain', 'ja': '予想ポジション変化'},
            'STRATEGY_POSITION_COMPARISON': {'zh': '策略位置比較', 'en': 'Strategy Position Comparison', 'ja': '戦略ポジション比較'},
            'START_POS': {'zh': '起跑', 'en': 'Start', 'ja': 'スタート'},
            'EXPECTED_POS': {'zh': '預期', 'en': 'Expected', 'ja': '予想'},
            'BEST_CASE': {'zh': '最佳', 'en': 'Best', 'ja': '最良'},
            'WORST_CASE': {'zh': '最差', 'en': 'Worst', 'ja': '最悪'},
            'GAIN': {'zh': '增減', 'en': 'Gain', 'ja': 'ゲイン'},
            'PODIUM': {'zh': '頒獎台', 'en': 'Podium', 'ja': '表彰台'},
            'TOP5': {'zh': 'Top 5', 'en': 'Top 5', 'ja': 'トップ5'},
            'POINTS': {'zh': '積分', 'en': 'Points', 'ja': 'ポイント'},
            'POSITION_DISTRIBUTION': {'zh': '完賽位置分佈', 'en': 'Finish Position Distribution', 'ja': '完走ポジション分布'},
            'VIEW_STRATEGY': {'zh': '檢視策略', 'en': 'View Strategy', 'ja': '戦略を表示'},
            'POINTS_ZONE': {'zh': '積分區', 'en': 'Points', 'ja': 'ポイント圏'},
            'NO_POINTS': {'zh': '無積分', 'en': 'No Points', 'ja': 'ノーポイント'},
            'RUN_MC_FOR_POSITION': {'zh': '執行 Monte Carlo 模擬以查看位置預測', 'en': 'Run Monte Carlo simulation with position tracking to see predictions.', 'ja': 'ポジション追跡付きのモンテカルロシミュレーションを実行して予測を表示'},
            'MC_ITERATIONS': {'zh': 'Monte Carlo 迭代次數', 'en': 'Iterations', 'ja': '反復回数'},
            'FRONT_RUNNER_ADVICE': {'zh': '前排策略', 'en': 'Front Runner Strategy', 'ja': 'フロントランナー戦略'},
            'MIDFIELD_ADVICE': {'zh': '中場策略', 'en': 'Midfield Strategy', 'ja': 'ミッドフィールド戦略'},
            'BACKMARKER_ADVICE': {'zh': '後排策略', 'en': 'Back Grid Strategy', 'ja': 'バックグリッド戦略'},
            'BEST_FOR_PODIUM': {'zh': '最佳頒獎台策略', 'en': 'Best for podium', 'ja': '表彰台に最適'},
            'BEST_FOR_POINTS': {'zh': '最佳積分策略', 'en': 'Best for points', 'ja': 'ポイント獲得に最適'},
            'BEST_FOR_GAINING': {'zh': '最佳超車策略', 'en': 'Best for gaining positions', 'ja': 'ポジションアップに最適'},
            'MOST_CONSISTENT': {'zh': '最穩定策略', 'en': 'Most consistent', 'ja': '最も安定'},
            'POINTS_CHANCE': {'zh': '積分機會', 'en': 'Points chance', 'ja': 'ポイント獲得チャンス'},
            'NO_DATA': {'zh': '無資料', 'en': 'No data available', 'ja': 'データなし'},
            
            # ===== Position Battle Tab (NEW) =====
            'POSITION_BATTLE': {'zh': '位置戰況', 'en': 'Position Battle', 'ja': 'ポジションバトル'},
            'POSITION_BATTLE_INFO': {'zh': '此頁籤顯示基於 Monte Carlo 預測的附近對手位置戰況分析', 'en': 'This tab shows position battles with nearby opponents based on Monte Carlo predictions.', 'ja': 'このタブはモンテカルロ予測に基づく近くの対戦相手とのポジションバトルを表示'},
            'NEARBY_OPPONENTS': {'zh': '附近對手', 'en': 'Nearby Opponents', 'ja': '近くの対戦相手'},
            'THREAT_LEVEL': {'zh': '威脅程度', 'en': 'Threat', 'ja': '脅威'},
            'UNDERCUT_RISK': {'zh': 'Undercut 風險', 'en': 'Undercut Risk', 'ja': 'アンダーカットリスク'},
            'OVERCUT_RISK': {'zh': 'Overcut 風險', 'en': 'Overcut Risk', 'ja': 'オーバーカットリスク'},
            'TARGET': {'zh': '目標', 'en': 'Target', 'ja': 'ターゲット'},
            'THREAT': {'zh': '威脅', 'en': 'Threat', 'ja': '脅威'},
            'ATTACK_UNDERCUT': {'zh': 'Undercut 進攻', 'en': 'Attack via undercut', 'ja': 'アンダーカットで攻撃'},
            'ATTACK_OVERCUT': {'zh': 'Overcut 嘗試', 'en': 'Try overcut', 'ja': 'オーバーカットを試す'},
            'DEFEND_UNDERCUT': {'zh': '防守 Undercut', 'en': 'Defend undercut', 'ja': 'アンダーカット防御'},
            'MAINTAIN_PACE': {'zh': '維持節奏', 'en': 'Maintain pace', 'ja': 'ペース維持'},
            'POSITION_PREDICTION_SUMMARY': {'zh': '位置預測摘要', 'en': 'Position Prediction', 'ja': 'ポジション予測'},
            'OUR_POSITION': {'zh': '我方位置', 'en': 'Our Position', 'ja': '自分のポジション'},
            'ANALYZING_OPPONENTS': {'zh': '正在分析附近對手...', 'en': 'Analyzing nearby opponents...', 'ja': '近くの対戦相手を分析中...'},
            'RUN_MC_FOR_BATTLE': {'zh': '執行 Monte Carlo 模擬以查看位置戰況分析', 'en': 'Run Monte Carlo simulation to see position battle analysis.', 'ja': 'ポジションバトル分析を表示するにはモンテカルロシミュレーションを実行'},
            'RECOMMENDED_STRATEGY': {'zh': '建議策略', 'en': 'Recommended Strategy', 'ja': '推奨戦略'},
            'EXPECTED_RESULT': {'zh': '預期結果', 'en': 'Expected Result', 'ja': '予想結果'},
            'POSITIONS': {'zh': '位', 'en': 'positions', 'ja': 'ポジション'},
            'NO_CHANGE': {'zh': '無變化', 'en': 'no change', 'ja': '変化なし'},
            'PODIUM_PROBABILITY': {'zh': '頒獎台機率', 'en': 'Podium Probability', 'ja': '表彰台確率'},
            'POINTS_PROBABILITY': {'zh': '積分區機率', 'en': 'Points Probability', 'ja': 'ポイント圏確率'},
            'POSITION_RANGE': {'zh': '位置範圍', 'en': 'Position Range', 'ja': 'ポジション範囲'},
            'NO_PREDICTIONS': {'zh': '無位置預測資料', 'en': 'No position predictions available.', 'ja': 'ポジション予測データがありません'},
            'HIGH': {'zh': '高', 'en': 'HIGH', 'ja': '高'},
            'MEDIUM': {'zh': '中', 'en': 'MEDIUM', 'ja': '中'},
            'LOW': {'zh': '低', 'en': 'LOW', 'ja': '低'},
            
            # ===== Full Race Tab - Auto MC Display (NEW 2026-01-05) =====
            'RUN_FULL_RACE': {'zh': '執行完整賽事', 'en': 'Run Full Race', 'ja': 'フルレース実行'},
            'RUN_FULL_RACE_TOOLTIP': {'zh': '使用 MC 策略分配執行 20 車完整模擬', 'en': 'Run 20-driver simulation using MC strategy assignments', 'ja': 'MC戦略割り当てを使用して20台のフルシミュレーションを実行'},
            'FULL_RACE_SMART_TITLE': {'zh': '完整賽事 - 智能策略分配', 'en': 'Full Race - Smart Strategy Assignment', 'ja': 'フルレース - スマート戦略割り当て'},
            'FULL_RACE_SMART_EXPLANATION': {'zh': '此標籤頁使用主畫面 MC 分析的最佳策略分配，執行 20 車詳細模擬。', 'en': 'This tab uses optimal strategy assignments from main window MC analysis to run detailed 20-driver simulation.', 'ja': 'このタブはメインウィンドウのMC分析から最適な戦略割り当てを使用して、詳細な20台シミュレーションを実行します。'},
            'FULL_RACE_SMART_BENEFIT': {'zh': '優勢：對手使用最佳策略，模擬更真實；無需重新策略分析，節省時間。', 'en': 'Benefits: Opponents use optimal strategies for realistic simulation; No re-analysis needed, saves time.', 'ja': '利点：対戦相手が最適な戦略を使用してリアルなシミュレーション；再分析不要で時間を節約。'},
            'CLICK_RUN_FULL_RACE': {'zh': '點擊「執行完整賽事」運行 20 車模擬', 'en': 'Click "Run Full Race" to execute 20-driver simulation', 'ja': '「フルレース実行」をクリックして20台シミュレーションを実行'},
            'UPDATE_VIEW': {'zh': '更新檢視', 'en': 'Update View', 'ja': 'ビューを更新'},
            'UPDATE_VIEW_TOOLTIP': {'zh': '從 Monte Carlo 結果中提取並顯示選定策略的數據', 'en': 'Extract and display data for selected strategy from Monte Carlo results', 'ja': 'モンテカルロ結果から選択した戦略のデータを抽出して表示'},
            'FULL_RACE_AUTO_TITLE': {'zh': '完整賽事 - 自動使用 MC 結果', 'en': 'Full Race - Auto MC Results', 'ja': 'フルレース - 自動MC結果'},
            'FULL_RACE_AUTO_EXPLANATION': {'zh': '此標籤頁自動重用主畫面的 Monte Carlo 結果，無需重新模擬。', 'en': 'This tab automatically reuses Monte Carlo results from main window without re-simulation.', 'ja': 'このタブはメインウィンドウのモンテカルロ結果を自動的に再利用し、再シミュレーションは不要です。'},
            'FULL_RACE_AUTO_USAGE': {'zh': '只需選擇策略和 SC 場景，即可查看該策略在不同場景下的統計表現（位置分佈、勝率等）。', 'en': 'Simply select a strategy and SC scenario to view its statistical performance (position distribution, win rate, etc.)', 'ja': '戦略とSCシナリオを選択するだけで、統計的パフォーマンス（ポジション分布、勝率など）を表示できます。'},
            'MC_RESULTS_READY': {'zh': 'Monte Carlo 結果已載入', 'en': 'Monte Carlo results loaded', 'ja': 'モンテカルロ結果がロードされました'},
            'STRATEGIES': {'zh': '策略', 'en': 'strategies', 'ja': '戦略'},
            'CLICK_UPDATE_TO_VIEW': {'zh': '點擊「更新檢視」查看選定策略的表現', 'en': 'Click "Update View" to see selected strategy performance', 'ja': '「ビューを更新」をクリックして選択した戦略のパフォーマンスを表示'},
            'NO_MC_RESULTS': {'zh': '請先在主畫面執行 Monte Carlo 模擬', 'en': 'Please run Monte Carlo simulation in main window first', 'ja': 'まずメインウィンドウでモンテカルロシミュレーションを実行してください'},
            'INVALID_PLAN': {'zh': '無效的策略選擇', 'en': 'Invalid strategy selection', 'ja': '無効な戦略選択'},
            'DISPLAYING': {'zh': '正在顯示', 'en': 'Displaying', 'ja': '表示中'},
            'MC_STATS_ONLY': {'zh': 'Monte Carlo 統計結果\n(無詳細逐圈數據)\n\n顯示策略的統計表現\n而非單次完整比賽模擬', 'en': 'Monte Carlo Statistics\n(No detailed lap data)\n\nShowing statistical performance\nnot single race simulation', 'ja': 'モンテカルロ統計\n(詳細なラップデータなし)\n\n統計的パフォーマンスを表示\n単一レースシミュレーションではありません'},
            'FREQUENCY': {'zh': '頻率 (%)', 'en': 'Frequency (%)', 'ja': '頻度 (%)'},
            'FINISH_POSITION': {'zh': '完賽位置', 'en': 'Finish Position', 'ja': '完走ポジション'},
            'POSITION_DISTRIBUTION': {'zh': '位置分佈', 'en': 'Position Distribution', 'ja': 'ポジション分布'},
            'AVG_POSITION': {'zh': '平均位置', 'en': 'Average Position', 'ja': '平均ポジション'},
            'PODIUM_POINTS': {'zh': '頒獎台/積分', 'en': 'Podium/Points', 'ja': '表彰台/ポイント'},
            
            # =================================================================
            # Module Help System - Live Timing Modules (Phase 1)
            # =================================================================
            
            # --- 通用 ---
            'module_help_title': {'zh': '模組說明', 'en': 'Module Help', 'ja': 'モジュールヘルプ'},
            'help_section_description': {'zh': '功能說明', 'en': 'Description', 'ja': '機能説明'},
            'help_section_features': {'zh': '功能特點', 'en': 'Features', 'ja': '機能'},
            'help_section_colors': {'zh': '顏色圖例', 'en': 'Color Legend', 'ja': 'カラー凡例'},
            
            # --- Default ---
            'help_default_title': {'zh': '模組說明', 'en': 'Module Help', 'ja': 'モジュールヘルプ'},
            'help_default_desc': {'zh': '此模組的說明尚未建立。', 'en': 'Help content for this module is not yet available.', 'ja': 'このモジュールのヘルプは準備中です。'},
            'help_default_features': {'zh': '', 'en': '', 'ja': ''},
            'help_default_colors': {'zh': '', 'en': '', 'ja': ''},
            
            # --- Chase Strategy ⭐ 含演算法 ---
            'help_chase_strategy_title': {'zh': '追趕策略', 'en': 'Chase Strategy', 'ja': '追跡戦略'},
            'help_chase_strategy_desc': {'zh': 'P2 追趕 P1 策略分析。顯示 5 種策略的追上機率和預計圈數。', 'en': 'P2 chasing P1 strategy analysis with 5 strategy scenarios.', 'ja': 'P2がP1を追跡する戦略分析（5つの戦略シナリオ）。'},
            'help_chase_strategy_features': {'zh': '• 策略 1: 繼續當前輪胎\n• 策略 2: P2 Undercut\n• 策略 3: P2 Overcut\n• 策略 4: SC 進站\n• 策略 5: P1 先進站', 'en': '• Strategy 1: Continue tyres\n• Strategy 2: P2 Undercut\n• Strategy 3: P2 Overcut\n• Strategy 4: SC pit\n• Strategy 5: P1 pits first', 'ja': '• 戦略1: タイヤ継続\n• 戦略2: P2 アンダーカット\n• 戦略3: P2 オーバーカット\n• 戦略4: SC ピット\n• 戦略5: P1先行ピット'},
            'help_chase_strategy_colors': {'zh': '【演算法】\nweighted_advantage = W_trend × Trend + W_theory × Theory\n\n【權重】\n• |Trend| ≥ 0.5 → 90% (>>>)\n• |Trend| ≥ 0.3 → 70% (>>)\n• |Trend| ≥ 0.1 → 50% (>)\n• |Trend| < 0.1 → 20% (-)\n\n追趕圈數 = Gap ÷ weighted_advantage + 1', 'en': '【Algorithm】\nweighted_advantage = W_trend × Trend + W_theory × Theory\n\n【Weights】\n• |Trend| ≥ 0.5 → 90% (>>>)\n• |Trend| ≥ 0.3 → 70% (>>)\n• |Trend| ≥ 0.1 → 50% (>)\n• |Trend| < 0.1 → 20% (-)\n\nLaps to catch = Gap ÷ weighted_advantage + 1', 'ja': '【アルゴリズム】\nweighted_advantage = W_trend × Trend + W_theory × Theory\n\n【重み】\n• |Trend| ≥ 0.5 → 90%（>>>）\n• |Trend| ≥ 0.3 → 70%（>>）\n• |Trend| ≥ 0.1 → 50%（>）\n• |Trend| < 0.1 → 20%（-）\n\n追い付きラップ = Gap ÷ weighted_advantage + 1'},
            
            # --- SF% History ⭐ 含演算法 ---
            'help_sf_percentage_title': {'zh': 'SF% 歷史', 'en': 'SF% History', 'ja': 'SF%履歴'},
            'help_sf_percentage_desc': {'zh': '顯示車手 SF% (Stint Fuel Saving) 歷史曲線。', 'en': 'Displays driver SF% history curve.', 'ja': 'ドライバーSF%履歴曲線を表示。'},
            'help_sf_percentage_features': {'zh': '• SF% 曲線\n• 閾值區域 (-3% 黃, -5% 紅)\n• SC 區域標記\n• 進站標記', 'en': '• SF% curve\n• Threshold zones (-3% yellow, -5% red)\n• SC zone marking\n• PIT markers', 'ja': '• SF%曲線\n• 閾値ゾーン（-3%黄、-5%赤）\n• SCゾーンマーキング\n• PITマーカー'},
            'help_sf_percentage_colors': {'zh': '【演算法】\nSF% = ((Throttle - Baseline) / Baseline) × 100\n\n【解讀】\n• SF% > 0 → 推進模式\n• SF% < 0 → 省油模式\n• SF% < -3% → 黃色警告\n• SF% < -5% → 紅色警告', 'en': '【Algorithm】\nSF% = ((Throttle - Baseline) / Baseline) × 100\n\n【Interpretation】\n• SF% > 0 → Pushing mode\n• SF% < 0 → Fuel saving\n• SF% < -3% → Yellow warning\n• SF% < -5% → Red warning', 'ja': '【アルゴリズム】\nSF% = ((Throttle - Baseline) / Baseline) × 100\n\n【解釈】\n• SF% > 0 → プッシュモード\n• SF% < 0 → 燃料節約\n• SF% < -3% → 黄色警告\n• SF% < -5% → 赤色警告'},
            
            # --- Battle Insight ⭐ 含演算法 ---
            'help_battle_insight_title': {'zh': '戰鬥分析', 'en': 'Battle Insight', 'ja': 'バトル分析'},
            'help_battle_insight_desc': {
                'zh': '即時顯示可能發生超車的車手配對。使用 F83 超車預測 + F84 規則引擎解說。\n\n【核心功能】\n• OT% 超車機率預測 (F83 模型)\n• 連續追近計數器 (容錯機制)\n• DRS 狀態判斷 (gap < 1s)\n• 輪胎差異分析',
                'en': 'Real-time display of driver pairs likely to battle. Uses F83 overtake prediction + F84 rule engine.\n\n【Core Functions】\n• OT% overtake probability (F83 model)\n• Consecutive catching counter (with tolerance)\n• DRS status detection (gap < 1s)\n• Tyre difference analysis',
                'ja': 'バトル可能性のあるドライバーペアをリアルタイム表示。F83オーバーテイク予測 + F84ルールエンジンを使用。\n\n【コア機能】\n• OT%オーバーテイク確率（F83モデル）\n• 連続追跡カウンター（容錯付き）\n• DRSステータス検出（gap < 1s）\n• タイヤ差分析'
            },
            'help_battle_insight_features': {
                'zh': '【閾值設定】\n• BATTLE_THRESHOLD: 40% (OT% >= 40%才顯示)\n• CATCHING_THRESHOLD: -0.04 s/圈 (追近判斷)\n• CATCHING_RESET_TOLERANCE: 3 (連續3次未追近才重置)\n• HISTORY_RETENTION: 10s (超車後保留顯示)\n\n【表格欄位】\n• Battle: P{x} TLA vs P{y} TLA\n• OT%: 超車機率 (≥ 80% 黃色警示)\n• Status: DRS/Closing/Hunting\n• Insight: 間距 + 輪胎 + 追近計數',
                'en': '【Thresholds】\n• BATTLE_THRESHOLD: 40% (show if OT% >= 40%)\n• CATCHING_THRESHOLD: -0.04 s/lap\n• CATCHING_RESET_TOLERANCE: 3 (reset after 3 non-catching)\n• HISTORY_RETENTION: 10s\n\n【Table Columns】\n• Battle: P{x} TLA vs P{y} TLA\n• OT%: Overtake probability (≥ 80% yellow)\n• Status: DRS/Closing/Hunting\n• Insight: Gap + Tyre + Catching count',
                'ja': '【閾値設定】\n• BATTLE_THRESHOLD: 40%（OT% >= 40%で表示）\n• CATCHING_THRESHOLD: -0.04 s/ラップ\n• CATCHING_RESET_TOLERANCE: 3（3回連続非追跡でリセット）\n• HISTORY_RETENTION: 10s\n\n【テーブルカラム】\n• Battle: P{x} TLA vs P{y} TLA\n• OT%: オーバーテイク確率（≥ 80%黃色）\n• Status: DRS/Closing/Hunting\n• Insight: ギャップ + タイヤ + 追跡カウント'
            },
            'help_battle_insight_colors': {
                'zh': '【連續追近演算法】\nif gap_trend < CATCHING_THRESHOLD:\n    consecutive_catching += 1\n    not_catching_count = 0\nelse:\n    not_catching_count += 1\n    if not_catching_count >= 3:\n        consecutive_catching = 0  # 重置\n\n【追近標記】\n• >>> x3: 連續 3-4 次追近 (深綠)\n• >>>>> x5+: 連續 5+ 次追近 (亮綠)\n\n【狀態顏色】\n• 綠色 DRS: gap < 1.0s\n• 黃色 Closing: gap < 1.5s\n• 白色 Hunting: 其他',
                'en': '【Consecutive Catching Algorithm】\nif gap_trend < CATCHING_THRESHOLD:\n    consecutive_catching += 1\n    not_catching_count = 0\nelse:\n    not_catching_count += 1\n    if not_catching_count >= 3:\n        consecutive_catching = 0  # reset\n\n【Catching Markers】\n• >>> x3: 3-4 consecutive catching (dark green)\n• >>>>> x5+: 5+ consecutive catching (bright green)\n\n【Status Colors】\n• Green DRS: gap < 1.0s\n• Yellow Closing: gap < 1.5s\n• White Hunting: other',
                'ja': '【連続追跡アルゴリズム】\nif gap_trend < CATCHING_THRESHOLD:\n    consecutive_catching += 1\n    not_catching_count = 0\nelse:\n    not_catching_count += 1\n    if not_catching_count >= 3:\n        consecutive_catching = 0  # リセット\n\n【追跡マーカー】\n• >>> x3: 3-4回連続追跡（濃緑）\n• >>>>> x5+: 5+回連続追跡（鮮緑）\n\n【ステータスカラー】\n• 緑 DRS: gap < 1.0s\n• 黄 Closing: gap < 1.5s\n• 白 Hunting: その他'
            },
            
            # --- Driver Strategy ---
            'help_driver_strategy_title': {'zh': '車手策略', 'en': 'Driver Strategy', 'ja': 'ドライバー戦略'},
            'help_driver_strategy_desc': {
                'zh': '即時車手策略分析圖表。顯示實際圈速/預測圈速曲線、輪胎衰退模型、進站預測、省胎評估(F87)、賽道演進等功能。支援同時追蹤全場 20 位車手，可即時切換無延遲。',
                'en': 'Real-time driver strategy analysis chart. Shows actual vs predicted lap times, tyre degradation model, pit prediction, fuel saving assessment (F87), track evolution. Tracks all 20 drivers simultaneously with instant switching.',
                'ja': 'リアルタイムドライバー戦略分析チャート。実際のラップタイム対予測、タイヤ劣化モデル、ピット予測、燃料節約評価（F87）、トラック進化を表示。20ドライバー同時追跡、即時切替対応。'
            },
            'help_driver_strategy_features': {
                'zh': '【核心功能】\n• 實際圈速曲線 (青色實線+圓點)\n• 預測圈速曲線 (紫色虛線)\n• 預測範圍區域 (半透明紫色填充)\n• 三配方預測線 (S/M/H)\n\n【進階功能】\n• SC/VSC 區域標記 (金色)\n• 進站標記 + PIT Est 預估\n• 省胎評估 (F87 演算法)\n• 賽道演進效應 (20車統計)\n• 燃油效率修正\n\n【操作】\n• 右鍵選單切換車手\n• 懸停顯示 Tooltip',
                'en': '【Core Features】\n• Actual lap curve (cyan solid + circles)\n• Predicted lap curve (purple dashed)\n• Prediction range fill (semi-transparent)\n• 3-compound prediction lines (S/M/H)\n\n【Advanced】\n• SC/VSC zone marking (gold)\n• Pit markers + PIT Est prediction\n• Fuel saving assessment (F87)\n• Track evolution effect (20-car stats)\n• Fuel efficiency correction\n\n【Controls】\n• Right-click to switch driver\n• Hover for tooltip',
                'ja': '【コア機能】\n• 実際のラップ曲線（シアン実線+円）\n• 予測ラップ曲線（紫破線）\n• 予測範囲塗り（半透明）\n• 3コンパウンド予測線（S/M/H）\n\n【高度な機能】\n• SC/VSCゾーンマーキング（金）\n• ピットマーカー + PIT Est予測\n• 燃料節約評価（F87）\n• トラック進化効果（20車統計）\n• 燃料効率補正\n\n【操作】\n• 右クリックでドライバー切替\n• ホバーでツールチップ'
            },
            'help_driver_strategy_colors': {
                'zh': '【演算法】\n預測圈速 = Base + 衰退 + 燃油 + 演進 – 修正\n\n• Base: 前3圈鎖定的基準圈速\n• 衰退: 二次方程式模型 (a·n² + b·n + c)\n• 燃油: 每圈減重約 0.035s\n• 演進: 全場中位數賽道演進\n• 修正: 自適應校正因子\n\n【省胎 F87】\nSF% = (Baseline - Current) / Baseline × 100\n• NONE: SF < 5%\n• LIGHT: 5-15% (+8%)\n• MODERATE: 15-30% (+15%)\n• HEAVY: > 30% (+25%)\n\n【顏色】\n• 青線 = 實際圈速\n• 紫線 = 預測圈速\n• 金區 = SC/VSC\n• 紅/黃/白 = S/M/H 預測線',
                'en': '【Algorithm】\nPredicted = Base + Degradation + Fuel + Evolution – Correction\n\n• Base: Locked base lap time from laps 2-3\n• Degradation: Quadratic model (a·n² + b·n + c)\n• Fuel: ~0.035s per lap weight reduction\n• Evolution: Median track evolution\n• Correction: Adaptive correction factor\n\n【F87 Fuel Saving】\nSF% = (Baseline - Current) / Baseline × 100\n• NONE: SF < 5%\n• LIGHT: 5-15% (+8%)\n• MODERATE: 15-30% (+15%)\n• HEAVY: > 30% (+25%)\n\n【Colors】\n• Cyan = Actual lap times\n• Purple = Predicted lap times\n• Gold = SC/VSC zones\n• Red/Yellow/White = S/M/H predictions',
                'ja': '【アルゴリズム】\n予測 = Base + 劣化 + 燃料 + 進化 – 補正\n\n• Base: ラップ2-3からロックされたベースタイム\n• 劣化: 二次方程式モデル（a·n² + b·n + c）\n• 燃料: ラップ毎約0.035s軽量化\n• 進化: 中央値トラック進化\n• 補正: 適応補正係数\n\n【F87燃料節約】\nSF% = (Baseline - Current) / Baseline × 100\n• NONE: SF < 5%\n• LIGHT: 5-15%（+8%）\n• MODERATE: 15-30%（+15%）\n• HEAVY: > 30%（+25%）\n\n【カラー】\n• シアン = 実際のラップタイム\n• 紫 = 予測ラップタイム\n• 金 = SC/VSCゾーン\n• 赤/黃/白 = S/M/H予測線'
            },
            
            # --- Throttle 95% History ---
            'help_throttle_history_title': {'zh': '油門 95% 歷史', 'en': 'Throttle 95% History', 'ja': 'スロットル95%履歴'},
            'help_throttle_history_desc': {'zh': '顯示所有車手每圈油門 95%+ 使用率。', 'en': 'Shows throttle 95%+ usage per lap for all drivers.', 'ja': '全ドライバーの各ラップのスロットル95%+使用率を表示。'},
            'help_throttle_history_features': {'zh': '• 每圈油門使用率\n• 歷史趨勢曲線', 'en': '• Per-lap throttle usage\n• Historical trend curve', 'ja': '• ラップ毎スロットル使用率\n• 履歴トレンド曲線'},
            'help_throttle_history_colors': {'zh': '• 綠 = 高使用率\n• 紅 = 低使用率', 'en': '• Green = High usage\n• Red = Low usage', 'ja': '• 緑 = 高使用率\n• 赤 = 低使用率'},
            
            # --- Top Speed History ---
            'help_top_speed_history_title': {'zh': '最高速歷史', 'en': 'Top Speed History', 'ja': '最高速度履歴'},
            'help_top_speed_history_desc': {'zh': '顯示所有車手每圈最高速度。', 'en': 'Shows top speed per lap for all drivers.', 'ja': '全ドライバーの各ラップの最高速度を表示。'},
            'help_top_speed_history_features': {'zh': '• 每圈最高速\n• 個人最佳標記', 'en': '• Per-lap top speed\n• Personal best marking', 'ja': '• ラップ毎最高速度\n• パーソナルベストマーキング'},
            'help_top_speed_history_colors': {'zh': '• 紫色背景 = 個人最佳', 'en': '• Purple background = Personal best', 'ja': '• 紫背景 = パーソナルベスト'},
            
            # --- Track Map ---
            'help_track_map_title': {'zh': '賽道地圖', 'en': 'Track Map', 'ja': 'トラックマップ'},
            'help_track_map_desc': {'zh': '即時顯示車手在賽道上的位置。', 'en': 'Real-time driver positions on track.', 'ja': 'トラック上のドライバー位置をリアルタイム表示。'},
            'help_track_map_features': {'zh': '• 即時位置追蹤\n• 車隊顏色標記', 'en': '• Real-time position tracking\n• Team color markers', 'ja': '• リアルタイムポジション追跡\n• チームカラーマーカー'},
            'help_track_map_colors': {'zh': '車隊顏色圓點 = 車手位置', 'en': 'Team color dot = Driver position', 'ja': 'チームカラードット = ドライバー位置'},
            
            # --- Ranking Tower ---
            # --- Ranking Tower ⭐ 含演算法 ---
            'help_ranking_tower_title': {'zh': '即時排名', 'en': 'Live Ranking', 'ja': 'ライブランキング'},
            'help_ranking_tower_desc': {
                'zh': '即時車手排名塔。顯示位置、差距變化趨勢、輪胎狀態和進站次數。\n\n【差距趨勢分析】\n使用 gap_trend 判斷車手間的距離變化，顯示 >>, >, <, << 等箭頭指示。',
                'en': 'Real-time driver ranking tower. Shows position, gap trends, tyre status and pit counts.\n\n【Gap Trend Analysis】\nUses gap_trend to determine distance changes between drivers, showing >>, >, <, << arrows.',
                'ja': 'リアルタイムドライバーランキングタワー。ポジション、ギャップトレンド、タイヤステータス、ピット回数を表示。\n\n【ギャップトレンド分析】\ngap_trendでドライバー間の距離変化を判断、>>, >, <, << 矢印を表示。'
            },
            'help_ranking_tower_features': {
                'zh': '【欄位說明】\n• P: 位置 (帶車隊色條)\n• Driver: 車手代號 (TLA)\n• Tyres: 輪胎配方 + 圈數 (S12/M8/H5)\n• Gap: 與前車差距 + 趨勢箭頭\n• Int: 與領先車差距\n• Last: 最後一圈圈速\n• PIT: 進站次數',
                'en': '【Column Description】\n• P: Position (with team color bar)\n• Driver: Driver code (TLA)\n• Tyres: Compound + Age (S12/M8/H5)\n• Gap: Gap to ahead + trend arrow\n• Int: Gap to leader\n• Last: Last lap time\n• PIT: Pit stop count',
                'ja': '【カラム説明】\n• P: ポジション（チームカラーバー付き）\n• Driver: ドライバーコード（TLA）\n• Tyres: コンパウンド + 周回数（S12/M8/H5）\n• Gap: 前車とのギャップ + トレンド矢印\n• Int: リーダーとのギャップ\n• Last: 最後のラップタイム\n• PIT: ピットストップ回数'
            },
            'help_ranking_tower_colors': {
                'zh': '【差距趨勢演算法】\nif gap_trend < -0.3: "綠>>> "  # 強勢追近\nif gap_trend < -0.1: "綠>> "   # 追近\nif gap_trend < -0.03: "綠> "  # 輕微追近\nif gap_trend > 0.03: " <紅"   # 輕微拉開\nif gap_trend > 0.1: " <<紅"  # 拉開\nif gap_trend > 0.3: " <<<紅" # 強勢拉開\n\n【輪胎顏色】\n• 紅圓 = SOFT\n• 黃圓 = MEDIUM\n• 白圓 = HARD\n• 綠圓 = INTER\n• 藍圓 = WET\n\n【特殊狀態】\n• 紅底線 = OUT車\n• 紫紅底 = 全場最快圈\n• 黃底 = PIT 狀態',
                'en': '【Gap Trend Algorithm】\nif gap_trend < -0.3: "green>>> "  # Strong closing\nif gap_trend < -0.1: "green>> "   # Closing\nif gap_trend < -0.03: "green> "  # Slight closing\nif gap_trend > 0.03: " <red"   # Slight increasing\nif gap_trend > 0.1: " <<red"  # Increasing\nif gap_trend > 0.3: " <<<red" # Strong increasing\n\n【Tyre Colors】\n• Red circle = SOFT\n• Yellow circle = MEDIUM\n• White circle = HARD\n• Green circle = INTER\n• Blue circle = WET\n\n【Special Status】\n• Red underline = OUT\n• Purple bg = Session fastest\n• Yellow bg = PIT status',
                'ja': '【ギャップトレンドアルゴリズム】\nif gap_trend < -0.3: "緑>>> "  # 強い接近\nif gap_trend < -0.1: "緑>> "   # 接近\nif gap_trend < -0.03: "緑> "  # 微小接近\nif gap_trend > 0.03: " <赤"   # 微小拡大\nif gap_trend > 0.1: " <<赤"  # 拡大\nif gap_trend > 0.3: " <<<赤" # 強い拡大\n\n【タイヤカラー】\n• 赤円 = SOFT\n• 黄円 = MEDIUM\n• 白円 = HARD\n• 緑円 = INTER\n• 青円 = WET\n\n【特殊ステータス】\n• 赤下線 = OUT\n• 紫背景 = セッション最速\n• 黄背景 = PITステータス'
            },
            
            # --- Lap History ---
            'help_lap_history_title': {'zh': '圈速歷史', 'en': 'Lap History', 'ja': 'ラップ履歴'},
            'help_lap_history_desc': {'zh': '顯示所有車手圈速歷史。', 'en': 'Shows lap time history for all drivers.', 'ja': '全ドライバーのラップタイム履歴を表示。'},
            'help_lap_history_features': {'zh': '• 圈速表格\n• 最快圈標記\n• 個人最佳標記', 'en': '• Lap time table\n• Fastest lap marking\n• Personal best marking', 'ja': '• ラップタイムテーブル\n• 最速ラップマーキング\n• パーソナルベストマーキング'},
            'help_lap_history_colors': {'zh': '• 紫色 = 全場最快\n• 綠色 = 個人最佳', 'en': '• Purple = Session fastest\n• Green = Personal best', 'ja': '• 紫 = セッション最速\n• 緑 = パーソナルベスト'},
            
            # --- Sector Comparison ---
            'help_sector_comparison_title': {'zh': '扇區比較', 'en': 'Sector Comparison', 'ja': 'セクター比較'},
            'help_sector_comparison_desc': {'zh': '比較兩位車手扇區時間。', 'en': 'Compares sector times between drivers.', 'ja': '2人のドライバーのセクタータイムを比較。'},
            'help_sector_comparison_features': {'zh': '• 雙車手比較\n• 扇區時間差', 'en': '• Two-driver comparison\n• Sector time difference', 'ja': '• 2ドライバー比較\n• セクタータイム差'},
            'help_sector_comparison_colors': {'zh': '• 綠色 = 領先\n• 紅色 = 落後', 'en': '• Green = Ahead\n• Red = Behind', 'ja': '• 緑 = 先行\n• 赤 = 遅れ'},
            
            # --- Speed/Telemetry Traces ---
            'help_speed_trace_title': {'zh': '速度追蹤', 'en': 'Speed Trace', 'ja': '速度トレース'},
            'help_speed_trace_desc': {'zh': '速度 vs 距離曲線。', 'en': 'Speed vs distance trace.', 'ja': '速度対距離トレース。'},
            'help_speed_trace_features': {'zh': '• 速度曲線\n• 雙車手比較', 'en': '• Speed curve\n• Dual driver comparison', 'ja': '• 速度曲線\n• 2ドライバー比較'},
            'help_speed_trace_colors': {'zh': '車隊顏色 = 速度曲線', 'en': 'Team color = Speed curve', 'ja': 'チームカラー = 速度曲線'},
            
            'help_throttle_trace_title': {'zh': '油門追蹤', 'en': 'Throttle Trace', 'ja': 'スロットルトレース'},
            'help_throttle_trace_desc': {'zh': '油門 vs 距離曲線。', 'en': 'Throttle vs distance trace.', 'ja': 'スロットル対距離トレース。'},
            'help_throttle_trace_features': {'zh': '• 油門百分比曲線', 'en': '• Throttle percentage curve', 'ja': '• スロットル%曲線'},
            'help_throttle_trace_colors': {'zh': '綠色 = 全油門', 'en': 'Green = Full throttle', 'ja': '緑 = フルスロットル'},
            
            'help_brake_trace_title': {'zh': '煞車追蹤', 'en': 'Brake Trace', 'ja': 'ブレーキトレース'},
            'help_brake_trace_desc': {'zh': '煞車 vs 距離曲線。', 'en': 'Brake vs distance trace.', 'ja': 'ブレーキ対距離トレース。'},
            'help_brake_trace_features': {'zh': '• 煞車區域標記', 'en': '• Brake zone marking', 'ja': '• ブレーキゾーンマーキング'},
            'help_brake_trace_colors': {'zh': '紅色 = 煞車中', 'en': 'Red = Braking', 'ja': '赤 = ブレーキ中'},
            
            'help_gear_trace_title': {'zh': '檔位追蹤', 'en': 'Gear Trace', 'ja': 'ギアトレース'},
            'help_gear_trace_desc': {'zh': '檔位 vs 距離曲線 (1-8)。', 'en': 'Gear vs distance trace (1-8).', 'ja': 'ギア対距離トレース（1-8）。'},
            'help_gear_trace_features': {'zh': '• 檔位變化曲線', 'en': '• Gear change curve', 'ja': '• ギア変更曲線'},
            'help_gear_trace_colors': {'zh': '漸層色 = 檔位 1-8', 'en': 'Gradient = Gear 1-8', 'ja': 'グラデーション = ギア1-8'},
            
            'help_drs_trace_title': {'zh': 'DRS 追蹤', 'en': 'DRS Trace', 'ja': 'DRSトレース'},
            'help_drs_trace_desc': {'zh': 'DRS 狀態 vs 距離。', 'en': 'DRS status vs distance.', 'ja': 'DRSステータス対距離。'},
            'help_drs_trace_features': {'zh': '• DRS 開啟區域', 'en': '• DRS open zones', 'ja': '• DRSオープンゾーン'},
            'help_drs_trace_colors': {'zh': '綠色 = DRS 開啟', 'en': 'Green = DRS open', 'ja': '緑 = DRSオープン'},
            
            'help_rpm_trace_title': {'zh': '轉速追蹤', 'en': 'RPM Trace', 'ja': 'RPMトレース'},
            'help_rpm_trace_desc': {'zh': 'RPM vs 距離曲線。', 'en': 'RPM vs distance trace.', 'ja': 'RPM対距離トレース。'},
            'help_rpm_trace_features': {'zh': '• RPM 曲線', 'en': '• RPM curve', 'ja': '• RPM曲線'},
            'help_rpm_trace_colors': {'zh': '紅色 = 高轉速', 'en': 'Red = High RPM', 'ja': '赤 = 高回転'},
            
            # --- Other Live Timing Modules ---
            'help_circle_map_title': {'zh': '圓形地圖', 'en': 'Circle Map', 'ja': 'サークルマップ'},
            'help_circle_map_desc': {'zh': '圓形賽道位置可視化。', 'en': 'Circular track position visualization.', 'ja': '円形トラックポジション可視化。'},
            'help_circle_map_features': {'zh': '• 圓形賽道顯示', 'en': '• Circular track display', 'ja': '• 円形トラック表示'},
            'help_circle_map_colors': {'zh': '車隊顏色 = 位置', 'en': 'Team color = Position', 'ja': 'チームカラー = 位置'},
            
            'help_pit_window_title': {'zh': '進站窗口', 'en': 'Pit Window', 'ja': 'ピットウィンドウ'},
            'help_pit_window_desc': {'zh': '進站窗口分析。', 'en': 'Pit stop window analysis.', 'ja': 'ピットストップウィンドウ分析。'},
            'help_pit_window_features': {'zh': '• Undercut/Overcut 窗口', 'en': '• Undercut/Overcut window', 'ja': '• アンダー/オーバーカットウィンドウ'},
            'help_pit_window_colors': {'zh': '綠色 = Undercut\n藍色 = Overcut', 'en': 'Green = Undercut\nBlue = Overcut', 'ja': '緑 = アンダーカット\n青 = オーバーカット'},
            
            'help_tyre_strategy_title': {'zh': '輪胎策略', 'en': 'Tyre Strategy', 'ja': 'タイヤ戦略'},
            'help_tyre_strategy_desc': {'zh': '即時輪胎策略。', 'en': 'Real-time tyre strategy.', 'ja': 'リアルタイムタイヤ戦略。'},
            'help_tyre_strategy_features': {'zh': '• 輪胎 Stint 顯示', 'en': '• Tyre stint display', 'ja': '• タイヤスティント表示'},
            'help_tyre_strategy_colors': {'zh': '紅=SOFT 黃=MEDIUM 白=HARD', 'en': 'Red=SOFT Yellow=MEDIUM White=HARD', 'ja': '赤=SOFT 黃=MEDIUM 白=HARD'},
            
            'help_track_weather_title': {'zh': '賽道與天氣', 'en': 'Track & Weather', 'ja': 'トラック＆天気'},
            'help_track_weather_desc': {'zh': '即時賽道和天氣狀態。', 'en': 'Real-time track and weather status.', 'ja': 'リアルタイムトラック・天候ステータス。'},
            'help_track_weather_features': {'zh': '• 賽道溫度\n• 天氣條件', 'en': '• Track temperature\n• Weather conditions', 'ja': '• トラック温度\n• 天候条件'},
            'help_track_weather_colors': {'zh': '藍=低溫 紅=高溫', 'en': 'Blue=Low temp Red=High temp', 'ja': '青=低温 赤=高温'},
            
            'help_traffic_timeline_title': {'zh': '車流時間線', 'en': 'Traffic Timeline', 'ja': 'トラフィックタイムライン'},
            'help_traffic_timeline_desc': {'zh': '車流熱力圖。', 'en': 'Traffic heatmap.', 'ja': 'トラフィックヒートマップ。'},
            'help_traffic_timeline_features': {'zh': '• 乾淨/髒空氣顯示', 'en': '• Clean/Dirty air display', 'ja': '• クリーン/ダーティエア表示'},
            'help_traffic_timeline_colors': {'zh': '綠=乾淨 紅=髒空氣', 'en': 'Green=Clean Red=Dirty', 'ja': '緑=クリーン 赤=ダーティ'},
            
            'help_race_control_title': {'zh': '比賽控制訊息', 'en': 'Race Control', 'ja': 'レースコントロール'},
            'help_race_control_desc': {'zh': '比賽控制訊息。', 'en': 'Race control messages.', 'ja': 'レースコントロールメッセージ。'},
            'help_race_control_features': {'zh': '• 旗幟、處罰、調查', 'en': '• Flags, penalties, investigations', 'ja': '• フラグ、ペナルティ、調査'},
            'help_race_control_colors': {'zh': '黃=黃旗 紅=紅旗 綠=綠旗', 'en': 'Yellow=Yellow Red=Red Green=Green', 'ja': '黃=黃旗 赤=赤旗 緑=緑旗'},
            
            'help_lap_distribution_title': {'zh': '圈速分布', 'en': 'Lap Distribution', 'ja': 'ラップ分布'},
            'help_lap_distribution_desc': {'zh': '圈速分布可視化。', 'en': 'Lap time distribution visualization.', 'ja': 'ラップタイム分布可視化。'},
            'help_lap_distribution_features': {'zh': '• 分布圖表', 'en': '• Distribution chart', 'ja': '• 分布チャート'},
            'help_lap_distribution_colors': {'zh': '車隊顏色 = 各車手', 'en': 'Team color = Each driver', 'ja': 'チームカラー = 各ドライバー'},
            
            'help_control_panel_title': {'zh': '控制面板', 'en': 'Control Panel', 'ja': 'コントロールパネル'},
            'help_control_panel_desc': {'zh': 'Live Timing 控制。', 'en': 'Live Timing control.', 'ja': 'ライブタイミングコントロール。'},
            'help_control_panel_features': {'zh': '• 模式切換\n• 回放控制', 'en': '• Mode switch\n• Playback control', 'ja': '• モード切替\n• 再生コントロール'},
            'help_control_panel_colors': {'zh': '綠=已連接 紅=未連接', 'en': 'Green=Connected Red=Disconnected', 'ja': '緑=接続済 赤=未接続'},
            
            # =================================================================
            # Module Help System - Phase 2: Telemetry Analysis Modules
            # =================================================================
            
            'help_speed_analysis_title': {'zh': '速度分析', 'en': 'Speed Analysis', 'ja': '速度分析'},
            'help_speed_analysis_desc': {'zh': 'F1 賽車速度分析，支援雙車手圈速對比。', 'en': 'F1 speed analysis with dual driver comparison.', 'ja': 'F1速度分析、2ドライバー比較対応。'},
            'help_speed_analysis_features': {'zh': '• 速度曲線對比\n• 距離/時間軸切換\n• 最高速標記', 'en': '• Speed curve comparison\n• Distance/Time axis toggle\n• Top speed marking', 'ja': '• 速度曲線比較\n• 距離/時間軸切替\n• 最高速度マーキング'},
            'help_speed_analysis_colors': {'zh': '車隊顏色 = 各車手', 'en': 'Team color = Each driver', 'ja': 'チームカラー = 各ドライバー'},
            
            'help_throttle_analysis_title': {'zh': '油門分析', 'en': 'Throttle Analysis', 'ja': 'スロットル分析'},
            'help_throttle_analysis_desc': {'zh': 'F1 賽車油門分析，對比駕駛風格。', 'en': 'F1 throttle analysis comparing driving styles.', 'ja': 'F1スロットル分析、ドライビングスタイル比較。'},
            'help_throttle_analysis_features': {'zh': '• 油門曲線對比\n• 全油門時間統計', 'en': '• Throttle curve comparison\n• Full throttle time stats', 'ja': '• スロットル曲線比較\n• フルスロットル時間統計'},
            'help_throttle_analysis_colors': {'zh': '綠=高油門 灰=低油門', 'en': 'Green=High throttle Gray=Low throttle', 'ja': '緑=高スロットル グレー=低スロットル'},
            
            'help_brake_analysis_title': {'zh': '煞車分析', 'en': 'Brake Analysis', 'ja': 'ブレーキ分析'},
            'help_brake_analysis_desc': {'zh': 'F1 賽車煞車分析，識別煞車點和煞車強度。', 'en': 'F1 brake analysis identifying brake points and intensity.', 'ja': 'F1ブレーキ分析、ブレーキポイントと強度を識別。'},
            'help_brake_analysis_features': {'zh': '• 煞車曲線對比\n• 煞車點識別\n• 煞車距離比較', 'en': '• Brake curve comparison\n• Brake point identification\n• Braking distance comparison', 'ja': '• ブレーキ曲線比較\n• ブレーキポイント識別\n• ブレーキ距離比較'},
            'help_brake_analysis_colors': {'zh': '紅=煞車中 白=釋放', 'en': 'Red=Braking White=Released', 'ja': '赤=ブレーキ中 白=リリース'},
            
            'help_gear_analysis_title': {'zh': '檔位分析', 'en': 'Gear Analysis', 'ja': 'ギア分析'},
            'help_gear_analysis_desc': {'zh': 'F1 賽車檔位分析，對比換檔時機。', 'en': 'F1 gear analysis comparing shift timing.', 'ja': 'F1ギア分析、シフトタイミングを比較。'},
            'help_gear_analysis_features': {'zh': '• 檔位曲線 (1-8)\n• 換檔點比較', 'en': '• Gear curve (1-8)\n• Shift point comparison', 'ja': '• ギア曲線（1-8）\n• シフトポイント比較'},
            'help_gear_analysis_colors': {'zh': '漸層色 = 檔位 1-8', 'en': 'Gradient = Gear 1-8', 'ja': 'グラデーション = ギア1-8'},
            
            'help_rpm_analysis_title': {'zh': 'RPM 分析', 'en': 'RPM Analysis', 'ja': 'RPM分析'},
            'help_rpm_analysis_desc': {'zh': 'F1 賽車 RPM 轉速對比分析。', 'en': 'F1 RPM comparison analysis.', 'ja': 'F1 RPM比較分析。'},
            'help_rpm_analysis_features': {'zh': '• RPM 曲線對比\n• 紅線區域標記', 'en': '• RPM curve comparison\n• Redline zone marking', 'ja': '• RPM曲線比較\n• レッドラインゾーンマーキング'},
            'help_rpm_analysis_colors': {'zh': '紅=高轉速 藍=低轉速', 'en': 'Red=High RPM Blue=Low RPM', 'ja': '赤=高回転 青=低回転'},
            
            'help_telemetry_comparison_title': {'zh': '遙測比較', 'en': 'Telemetry Comparison', 'ja': 'テレメトリー比較'},
            'help_telemetry_comparison_desc': {'zh': '多車手遙測疊加對比分析。', 'en': 'Multi-driver telemetry overlay comparison.', 'ja': 'マルチドライバーテレメトリーオーバーレイ比較。'},
            'help_telemetry_comparison_features': {'zh': '• 多遙測通道對比\n• 跨賽段比較\n• Delta 時間計算', 'en': '• Multi-channel comparison\n• Cross-session comparison\n• Delta time calculation', 'ja': '• マルチチャンネル比較\n• クロスセッション比較\n• デルタタイム計算'},
            'help_telemetry_comparison_colors': {'zh': '車隊顏色 = 各車手曲線', 'en': 'Team color = Each driver curve', 'ja': 'チームカラー = 各ドライバー曲線'},
            
            # =================================================================
            # Module Help System - Phase 3: Advanced Analysis Modules
            # =================================================================
            
            'help_long_run_title': {'zh': 'Long Run 分析', 'en': 'Long Run Analysis', 'ja': 'ロングラン分析'},
            'help_long_run_desc': {
                'zh': '長距離配速分析和輪胎衰退預測。支援自動識別 Long Run stint、燃油修正、賽道演進、真實衰退率計算。\n\n【自動識別條件】\n• 連續 8+ 圈有效圈速\n• 排除 PIT IN/OUT 圈\n• 可選擇 stint 進行分析',
                'en': 'Long distance pace analysis and tyre degradation prediction. Supports auto-detection of Long Run stints, fuel correction, track evolution, true degradation calculation.\n\n【Auto Detection Criteria】\n• 8+ consecutive valid laps\n• Excludes PIT IN/OUT laps\n• Selectable stints for analysis',
                'ja': 'ロングランペース分析とタイヤ劣化予測。ロングランスティント自動検出、燃料補正、トラックエボリューション、真の劣化率計算対応。\n\n【自動検出条件】\n• 8+連続有効ラップ\n• PIT IN/OUTラップ除外\n• 分析用スティント選択可能'
            },
            'help_long_run_features': {
                'zh': '【計算項目】\n• Raw Degradation: 原始衰退率\n• Fuel Adjustment: 燃油修正量\n• Track Evolution: 賽道演進量\n• True Degradation: 真實衰退率\n\n【燃油參數】\n• start_fuel_kg: 85 kg (預設)\n• fuel_kg_per_lap: 1.70 kg/圈\n• fuel_effect: 0.030 s/kg',
                'en': '【Calculations】\n• Raw Degradation: original degradation rate\n• Fuel Adjustment: fuel correction amount\n• Track Evolution: track evolution amount\n• True Degradation: actual degradation rate\n\n【Fuel Parameters】\n• start_fuel_kg: 85 kg (default)\n• fuel_kg_per_lap: 1.70 kg/lap\n• fuel_effect: 0.030 s/kg',
                'ja': '【計算項目】\n• Raw Degradation: 元の劣化率\n• Fuel Adjustment: 燃料補正量\n• Track Evolution: トラックエボリューション量\n• True Degradation: 実際の劣化率\n\n【燃料パラメータ】\n• start_fuel_kg: 85 kg（デフォルト）\n• fuel_kg_per_lap: 1.70 kg/ラップ\n• fuel_effect: 0.030 s/kg'
            },
            'help_long_run_colors': {
                'zh': '【衰退計算演算法】\n1. Fuel Corrected Time:\n   corrected = lap_time - (remaining_fuel x fuel_effect)\n\n2. Track Evolution:\n   統計方法: 全場中位數趨勢\n   參考方法: 指定車手基準\n   混合方法: 兩者加權\n\n3. True Degradation:\n   true_deg = raw - track_evo + fuel_adj\n\n【曲線擬合】\n• 線性迴歸: y = ax + b\n• 二次迴歸: y = ax2 + bx + c',
                'en': '【Degradation Algorithm】\n1. Fuel Corrected Time:\n   corrected = lap_time - (remaining_fuel x fuel_effect)\n\n2. Track Evolution:\n   Statistical: Full field median trend\n   Reference: Specified driver baseline\n   Hybrid: Weighted combination\n\n3. True Degradation:\n   true_deg = raw - track_evo + fuel_adj\n\n【Curve Fitting】\n• Linear: y = ax + b\n• Quadratic: y = ax2 + bx + c',
                'ja': '【劣化アルゴリズム】\n1. 燃料補正タイム:\n   corrected = lap_time - (remaining_fuel x fuel_effect)\n\n2. トラックエボリューション:\n   統計: 全場中央値トレンド\n   参照: 指定ドライバー基準\n   ハイブリッド: 加重組み合わせ\n\n3. 真の劣化:\n   true_deg = raw - track_evo + fuel_adj\n\n【曲線フィッティング】\n• 線形: y = ax + b\n• 二次: y = ax2 + bx + c'
            },
            
            'help_ideal_lap_title': {'zh': '理想圈速', 'en': 'Ideal Lap', 'ja': '理想ラップ'},
            'help_ideal_lap_desc': {'zh': '計算理想圈速（最佳扇區組合）。', 'en': 'Calculates ideal lap time (best sector combination).', 'ja': '理想ラップタイム（最適セクター組み合わせ）を計算。'},
            'help_ideal_lap_features': {'zh': '• 最佳扇區組合\n• 理論最快圈\n• 扇區熱力圖', 'en': '• Best sector combination\n• Theoretical fastest lap\n• Sector heatmap', 'ja': '• 最適セクター組み合わせ\n• 理論最速ラップ\n• セクターヒートマップ'},
            'help_ideal_lap_colors': {'zh': '【演算法】\nIdeal Lap = min(S1) + min(S2) + min(S3)\n\n各車手取各扇區最佳時間組合', 'en': '【Algorithm】\nIdeal Lap = min(S1) + min(S2) + min(S3)\n\nCombines best sector times for each driver', 'ja': '【アルゴリズム】\nIdeal Lap = min(S1) + min(S2) + min(S3)\n\n各ドライバーの各セクター最適タイムを組み合わせ'},
            
            'help_pitstop_analysis_title': {'zh': '進站分析', 'en': 'Pitstop Analysis', 'ja': 'ピットストップ分析'},
            'help_pitstop_analysis_desc': {'zh': '進站時間分析和策略評估。', 'en': 'Pit stop time analysis and strategy evaluation.', 'ja': 'ピットストップ時間分析と戦略評価。'},
            'help_pitstop_analysis_features': {'zh': '• 靜止時間分析\n• 進站損失計算\n• 策略比較', 'en': '• Stationary time analysis\n• Pit loss calculation\n• Strategy comparison', 'ja': '• 静止時間分析\n• ピットロス計算\n• 戦略比較'},
            'help_pitstop_analysis_colors': {'zh': '【演算法】\n進站損失 = 靜止時間 + 進出站時間損失\n\nUndercut = 新胎優勢 - 進站損失', 'en': '【Algorithm】\nPit loss = Stationary time + In/Out lap time loss\n\nUndercut = Fresh tyre advantage - Pit loss', 'ja': '【アルゴリズム】\nピットロス = 静止時間 + イン/アウトラップタイムロス\n\nアンダーカット = 新タイヤアドバンテージ - ピットロス'},
            
            'help_lap_box_plot_title': {'zh': '圈速箱型圖', 'en': 'Lap Box Plot', 'ja': 'ラップ箱ひげ図'},
            'help_lap_box_plot_desc': {'zh': '圈速分布統計可視化。', 'en': 'Lap time distribution statistics visualization.', 'ja': 'ラップタイム分布統計可視化。'},
            'help_lap_box_plot_features': {'zh': '• 箱型圖統計\n• 中位數/四分位\n• 異常值標記', 'en': '• Box plot statistics\n• Median/Quartiles\n• Outlier marking', 'ja': '• 箱ひげ図統計\n• 中央値/四分位\n• 外れ値マーキング'},
            'help_lap_box_plot_colors': {'zh': '車隊顏色 = 各車手分布', 'en': 'Team color = Each driver distribution', 'ja': 'チームカラー = 各ドライバー分布'},
            
            # =================================================================
            # Module Help System - Phase 4: Prediction Modules
            # =================================================================
            
            'help_fp2_prediction_title': {'zh': 'FP2 排位預測', 'en': 'FP2 Qualifying Prediction', 'ja': 'FP2予選予測'},
            'help_fp2_prediction_desc': {
                'zh': 'Function 76 集成學習排位賽預測模組。使用 FP2/FP3 階段數據，透過 XGBoost 機器學習模型預測排位賽結果。\n\n【模型性能】\n• MAE: 0.766s (平均絕對誤差)\n• R²: 0.939 (決定係數)\n• 訓練數據: 2018-2024 共 1,433 樣本',
                'en': 'Function 76 ensemble learning qualifying prediction module. Uses FP2/FP3 session data with XGBoost ML model to predict qualifying results.\n\n【Model Performance】\n• MAE: 0.766s (mean absolute error)\n• R²: 0.939 (coefficient of determination)\n• Training data: 2018-2024, 1,433 samples',
                'ja': 'Function 76 アンサンブル学習予選予測モジュール。FP2/FP3セッションデータとXGBoost MLモデルを使用して予選結果を予測。\n\n【モデル性能】\n• MAE: 0.766s（平均絶対誤差）\n• R²: 0.939（決定係数）\n• 訓練データ: 2018-2024、1,433サンプル'
            },
            'help_fp2_prediction_features': {
                'zh': '【15 個核心特徵】\n\n📊 FP3 基礎特徵 (8 個):\n• fp3_best_lap: FP3 最佳圈速\n• fp3_avg_lap: FP3 平均圈速\n• fp3_lap_std: 圈速標準差\n• fp3_sector1/2/3: 扇區時間\n• fp3_speed_trap: 速度陷阱\n• fp3_valid_laps: 有效圈數\n\n📊 參考特徵 (2 個):\n• fp1_best_lap, fp2_best_lap\n\n📊 進步幅度 (2 個):\n• improvement_fp3_fp1/fp2\n\n📊 車手表現 (2 個):\n• fp3_consistency, sector_balance\n\n📊 賽道分類 (1 個):\n• track_cluster (0=高速街道, 1=標準高速, 2=技術型)',
                'en': '【15 Core Features】\n\n📊 FP3 Base Features (8):\n• fp3_best_lap: FP3 best lap time\n• fp3_avg_lap: FP3 average lap time\n• fp3_lap_std: Lap time std dev\n• fp3_sector1/2/3: Sector times\n• fp3_speed_trap: Speed trap\n• fp3_valid_laps: Valid laps count\n\n📊 Reference Features (2):\n• fp1_best_lap, fp2_best_lap\n\n📊 Improvement Features (2):\n• improvement_fp3_fp1/fp2\n\n📊 Driver Performance (2):\n• fp3_consistency, sector_balance\n\n📊 Track Classification (1):\n• track_cluster (0=street, 1=high-speed, 2=technical)',
                'ja': '【15コア特徴量】\n\n📊 FP3基本特徴（8個）:\n• fp3_best_lap: FP3ベストラップ\n• fp3_avg_lap: FP3平均ラップ\n• fp3_lap_std: ラップ標準偏差\n• fp3_sector1/2/3: セクタータイム\n• fp3_speed_trap: スピードトラップ\n• fp3_valid_laps: 有効ラップ数\n\n📊 参照特徴（2個）:\n• fp1_best_lap, fp2_best_lap\n\n📊 改善特徴（2個）:\n• improvement_fp3_fp1/fp2\n\n📊 ドライバー性能（2個）:\n• fp3_consistency, sector_balance\n\n📊 トラック分類（1個）:\n• track_cluster（0=ストリート, 1=高速, 2=テクニカル）'
            },
            'help_fp2_prediction_colors': {
                'zh': '【XGBoost 演算法】\n\n• 模型類型: Gradient Boosting (GBDT)\n• n_estimators: 200 棵樹\n• max_depth: 7 層\n• learning_rate: 0.05\n• subsample: 0.8\n• colsample_bytree: 0.8\n\n【集成策略】\n• 加權平均: w_i = (1/MAE_i) / Σ(1/MAE_j)\n• Stacking: Ridge 元模型組合\n\n【預測流程】\nFP3 數據 → 特徵提取 → XGBoost → Q3 預測時間\n\n【誤差分佈】\n• 0-0.5s: ~40% 車手\n• 0.5-1.0s: ~30% 車手\n• 1.0-2.0s: ~20% 車手\n• >2.0s: ~10% 車手 (異常場景)',
                'en': '【XGBoost Algorithm】\n\n• Model type: Gradient Boosting (GBDT)\n• n_estimators: 200 trees\n• max_depth: 7 layers\n• learning_rate: 0.05\n• subsample: 0.8\n• colsample_bytree: 0.8\n\n【Ensemble Strategy】\n• Weighted avg: w_i = (1/MAE_i) / Σ(1/MAE_j)\n• Stacking: Ridge meta-model\n\n【Prediction Flow】\nFP3 data → Feature extraction → XGBoost → Q3 predicted time\n\n【Error Distribution】\n• 0-0.5s: ~40% drivers\n• 0.5-1.0s: ~30% drivers\n• 1.0-2.0s: ~20% drivers\n• >2.0s: ~10% drivers (anomaly)',
                'ja': '【XGBoostアルゴリズム】\n\n• モデルタイプ: 勾配ブースティング（GBDT）\n• n_estimators: 200ツリー\n• max_depth: 7レイヤー\n• learning_rate: 0.05\n• subsample: 0.8\n• colsample_bytree: 0.8\n\n【アンサンブル戦略】\n• 加重平均: w_i = (1/MAE_i) / Σ(1/MAE_j)\n• スタッキング: Ridgeメタモデル\n\n【予測フロー】\nFP3データ → 特徴抽出 → XGBoost → Q3予測タイム\n\n【誤差分布】\n• 0-0.5s: ~40%ドライバー\n• 0.5-1.0s: ~30%ドライバー\n• 1.0-2.0s: ~20%ドライバー\n• >2.0s: ~10%ドライバー（異常）'
            },
            
            'help_qualifying_prediction_title': {'zh': '排位預測', 'en': 'Qualifying Prediction', 'ja': '予選予測'},
            'help_qualifying_prediction_desc': {'zh': '排位賽結果預測。', 'en': 'Qualifying result prediction.', 'ja': '予選結果予測。'},
            'help_qualifying_prediction_features': {'zh': '• 排位時間預測\n• Q1/Q2/Q3 分析', 'en': '• Qualifying time prediction\n• Q1/Q2/Q3 analysis', 'ja': '• 予選タイム予測\n• Q1/Q2/Q3分析'},
            'help_qualifying_prediction_colors': {'zh': '綠=可能晉級 紅=可能淘汰', 'en': 'Green=Likely advance Red=Likely eliminated', 'ja': '緑=進出可能 赤=敗退可能'},
            
            'help_race_prediction_title': {'zh': '正賽預測', 'en': 'Race Prediction', 'ja': 'レース予測'},
            'help_race_prediction_desc': {
                'zh': '正賽結果預測模組。使用 Monte Carlo 模擬預測各車手完賽位置分布。\n\n【模擬參數】\n• 模擬次數: 10,000+ 次\n• 考慮因素: 起跑、策略、事故、天氣',
                'en': 'Race result prediction module. Uses Monte Carlo simulation to predict position distribution.\n\n【Simulation Parameters】\n• Iterations: 10,000+\n• Factors: Start, Strategy, Incidents, Weather',
                'ja': 'レース結果予測モジュール。モンテカルロシミュレーションでポジション分布を予測。\n\n【シミュレーションパラメータ】\n• 反復回数: 10,000+\n• 考慮要素: スタート、戦略、インシデント、天候'
            },
            'help_race_prediction_features': {
                'zh': '【Monte Carlo 流程】\n1. 初始化排位賽結果\n2. 迴圈模擬各圈位置變化:\n   - 圈速差異 (車輛性能 + 車手技術)\n   - 超車機率 (DRS, 輪胎差)\n   - 進站策略 (Undercut/Overcut)\n   - 隨機事件 (SC, DNF)\n3. 統計位置分布',
                'en': '【Monte Carlo Flow】\n1. Initialize from quali results\n2. Simulate each lap position changes:\n   - Pace difference (car + driver skill)\n   - Overtake probability (DRS, tyre diff)\n   - Pit strategy (Undercut/Overcut)\n   - Random events (SC, DNF)\n3. Statistical position distribution',
                'ja': '【モンテカルロフロー】\n1. 予選結果から初期化\n2. 各ラップポジション変化シミュレーション:\n   - ペース差（マシン + ドライバースキル）\n   - オーバーテイク確率（DRS、タイヤ差）\n   - ピット戦略（アンダーカット/オーバーカット）\n   - ランダムイベント（SC、DNF）\n3. 統計的ポジション分布'
            },
            'help_race_prediction_colors': {
                'zh': '【位置機率計算】\nP_position(i) = count(sim_position == i) / total_simulations\n\n【預期位置】\nE[position] = Sum(i x P_position(i))\n\n【顏色指示】\n• 金色 P1: 第1名\n• 銀色 P2: 第2名\n• 銅色 P3: 第3名\n• 綠色 P4-10: 積分區',
                'en': '【Position Probability】\nP_position(i) = count(sim_position == i) / total_simulations\n\n【Expected Position】\nE[position] = Sum(i x P_position(i))\n\n【Color Indicators】\n• Gold P1: 1st place\n• Silver P2: 2nd place\n• Bronze P3: 3rd place\n• Green P4-10: Points zone',
                'ja': '【ポジション確率】\nP_position(i) = count(sim_position == i) / total_simulations\n\n【期待ポジション】\nE[position] = Sum(i x P_position(i))\n\n【カラーインジケーター】\n• 金 P1: 1位\n• 銀 P2: 2位\n• 銅 P3: 3位\n• 緑 P4-10: ポイント圏'
            },
            
            # =================================================================
            # Module Help System - Phase 5: Multi-Season/Historical Modules
            # =================================================================
            
            'help_pole_defense_title': {'zh': '桿位防守', 'en': 'Pole Defense', 'ja': 'ポールポジション防御'},
            'help_pole_defense_desc': {'zh': '桿位車手第一圈防守率統計。', 'en': 'Pole position first lap defense rate statistics.', 'ja': 'ポールポジションドライバーの第1ラップ防御率統計。'},
            'help_pole_defense_features': {'zh': '• 桿位防守率\n• 歷年趨勢\n• 賽道比較', 'en': '• Pole defense rate\n• Historical trend\n• Track comparison', 'ja': '• ポール防御率\n• 履歴トレンド\n• トラック比較'},
            'help_pole_defense_colors': {'zh': '綠=成功防守 紅=失去領先', 'en': 'Green=Defended Red=Lost lead', 'ja': '緑=防御成功 赤=リード喪失'},
            
            'help_pit_loss_table_title': {'zh': '進站時間損失表', 'en': 'Pit Loss Table', 'ja': 'ピットタイムロス表'},
            'help_pit_loss_table_desc': {
                'zh': '各賽道進站時間損失總覽。顯示 Green Flag、VSC 和 Safety Car 狀態下的進站時間損失，幫助策略分析。',
                'en': 'Circuit pit time loss overview. Displays pit time loss under Green Flag, VSC and Safety Car conditions for strategy analysis.',
                'ja': '各サーキットのピットタイムロス概要。グリーンフラッグ、VSC、セーフティカー状態でのピットタイムロスを表示し、戦略分析を支援。'
            },
            'help_pit_loss_table_features': {
                'zh': '【顯示資訊】\n• Green Flag: 正常進站時間損失\n• VSC: 虛擬安全車進站損失\n• SC: 安全車進站損失\n• 樣本數: 訓練數據量\n• 來源: 數據來源類型',
                'en': '【Display Information】\n• Green Flag: Normal pit time loss\n• VSC: Virtual safety car pit loss\n• SC: Safety car pit loss\n• Samples: Training data count\n• Source: Data source type',
                'ja': '【表示情報】\n• グリーンフラッグ: 通常ピットタイムロス\n• VSC: バーチャルセーフティカーピットロス\n• SC: セーフティカーピットロス\n• サンプル数: トレーニングデータ数\n• ソース: データソースタイプ'
            },
            'help_pit_loss_table_colors': {
                'zh': '【顏色含義】\n• 綠色: 較快 (< 20秒)\n• 黃色: 中等 (20-24秒)\n• 紅色: 較慢 (> 24秒)\n\n【應用建議】\n• 使用 VSC/SC 損失規劃最佳進站時機\n• 比較不同賽道的進站成本差異',
                'en': '【Color Meaning】\n• Green: Fast (< 20s)\n• Yellow: Medium (20-24s)\n• Red: Slow (> 24s)\n\n【Application Tips】\n• Use VSC/SC loss for optimal pit timing\n• Compare pit costs across circuits',
                'ja': '【カラーの意味】\n• 緑: 速い (< 20秒)\n• 黄: 中程度 (20-24秒)\n• 赤: 遅い (> 24秒)\n\n【活用のヒント】\n• VSC/SCロスで最適ピットタイミングを計画\n• サーキット間のピットコストを比較'
            },
            
            'help_start_reaction_title': {'zh': '起跑反應', 'en': 'Start Reaction', 'ja': 'スタート反応'},
            'help_start_reaction_desc': {
                'zh': '起跑反應時間分析。分析車手從燈滅到首次移動的反應時間，以及 0-50 km/h 加速表現。',
                'en': 'Start reaction time analysis. Analyzes reaction time from lights out to first movement, and 0-50 km/h acceleration.',
                'ja': 'スタート反応時間分析。ライトアウトから最初の動きまでの反応時間、0-50 km/h加速を分析。'
            },
            'help_start_reaction_features': {
                'zh': '【分析指標】\n• Reaction Time: 燈滅到動作時間\n• 0-50 km/h: 加速時間\n• 0-100 km/h: 加速時間\n• 位置變化: T1 進入前後差異',
                'en': '【Analysis Metrics】\n• Reaction Time: Lights out to movement\n• 0-50 km/h: Acceleration time\n• 0-100 km/h: Acceleration time\n• Position Change: Before/after T1',
                'ja': '【分析指標】\n• 反応時間: ライトアウトから動作まで\n• 0-50 km/h: 加速時間\n• 0-100 km/h: 加速時間\n• ポジション変化: T1前後の差'
            },
            'help_start_reaction_colors': {
                'zh': '【計算演算法】\nReaction = T_first_move - T_lights_out\n\n【參考值】\n• 優秀: < 0.25s\n• 良好: 0.25-0.35s\n• 平均: 0.35-0.45s\n• 較慢: > 0.45s\n\n【顏色】\n• 綠 = 快速反應 (< 0.30s)\n• 黃 = 一般 (0.30-0.40s)\n• 紅 = 慢反應 (> 0.40s)',
                'en': '【Algorithm】\nReaction = T_first_move - T_lights_out\n\n【Reference Values】\n• Excellent: < 0.25s\n• Good: 0.25-0.35s\n• Average: 0.35-0.45s\n• Slow: > 0.45s\n\n【Colors】\n• Green = Fast (< 0.30s)\n• Yellow = Average (0.30-0.40s)\n• Red = Slow (> 0.40s)',
                'ja': '【アルゴリズム】\nReaction = T_first_move - T_lights_out\n\n【参考値】\n• 優秀: < 0.25s\n• 良好: 0.25-0.35s\n• 平均: 0.35-0.45s\n• 遅い: > 0.45s\n\n【カラー】\n• 緑 = 高速（< 0.30s）\n• 黄 = 平均（0.30-0.40s）\n• 赤 = 遅い（> 0.40s）'
            },
            
            'help_season_progress_title': {'zh': '賽季進度', 'en': 'Season Progress', 'ja': 'シーズン進捗'},
            'help_season_progress_desc': {'zh': '賽季積分進度可視化。', 'en': 'Season points progress visualization.', 'ja': 'シーズンポイント進捗可視化。'},
            'help_season_progress_features': {'zh': '• 積分趨勢圖\n• 排名變化\n• 冠軍爭奪分析', 'en': '• Points trend chart\n• Ranking changes\n• Championship battle analysis', 'ja': '• ポイントトレンドチャート\n• ランキング変化\n• チャンピオンシップバトル分析'},
            'help_season_progress_colors': {'zh': '車隊顏色 = 各車手/車隊', 'en': 'Team color = Each driver/team', 'ja': 'チームカラー = 各ドライバー/チーム'},
            
            'help_driver_standings_title': {'zh': '車手積分榜', 'en': 'Driver Standings', 'ja': 'ドライバースタンディング'},
            'help_driver_standings_desc': {'zh': '車手積分排名。', 'en': 'Driver points standings.', 'ja': 'ドライバーポイントスタンディング。'},
            'help_driver_standings_features': {'zh': '• 積分排名\n• 賽事積分\n• 差距計算', 'en': '• Points ranking\n• Race points\n• Gap calculation', 'ja': '• ポイントランキング\n• レースポイント\n• ギャップ計算'},
            'help_driver_standings_colors': {'zh': '車隊顏色 = 各車手', 'en': 'Team color = Each driver', 'ja': 'チームカラー = 各ドライバー'},
            
            'help_constructor_standings_title': {'zh': '車隊積分榜', 'en': 'Constructor Standings', 'ja': 'コンストラクタースタンディング'},
            'help_constructor_standings_desc': {'zh': '車隊積分排名。', 'en': 'Constructor points standings.', 'ja': 'コンストラクターポイントスタンディング。'},
            'help_constructor_standings_features': {'zh': '• 車隊積分\n• 賽事統計\n• 趨勢分析', 'en': '• Team points\n• Race statistics\n• Trend analysis', 'ja': '• チームポイント\n• レース統計\n• トレンド分析'},
            'help_constructor_standings_colors': {'zh': '車隊顏色 = 各車隊', 'en': 'Team color = Each team', 'ja': 'チームカラー = 各チーム'},
            
            # =================================================================
            # Module Help System - Additional Analysis Modules
            # =================================================================
            
            'help_tire_analysis_title': {'zh': '輪胎分析', 'en': 'Tire Analysis', 'ja': 'タイヤ分析'},
            'help_tire_analysis_desc': {'zh': '輪胎策略和衰退分析。', 'en': 'Tyre strategy and degradation analysis.', 'ja': 'タイヤ戦略と劣化分析。'},
            'help_tire_analysis_features': {'zh': '• 輪胎配方比較\n• 衰退曲線\n• 最佳進站圈', 'en': '• Compound comparison\n• Degradation curve\n• Optimal pit lap', 'ja': '• コンパウンド比較\n• 劣化曲線\n• 最適ピットラップ'},
            'help_tire_analysis_colors': {'zh': '紅=SOFT 黃=MEDIUM 白=HARD', 'en': 'Red=SOFT Yellow=MEDIUM White=HARD', 'ja': '赤=SOFT 黃=MEDIUM 白=HARD'},
            
            'help_accident_analysis_title': {'zh': '事故分析', 'en': 'Accident Analysis', 'ja': '事故分析'},
            'help_accident_analysis_desc': {'zh': 'F1 事故統計和分析。', 'en': 'F1 accident statistics and analysis.', 'ja': 'F1事故統計と分析。'},
            'help_accident_analysis_features': {'zh': '• 事故類型統計\n• 旗幟分佈\n• 車手涉入', 'en': '• Incident type statistics\n• Flag distribution\n• Driver involvement', 'ja': '• インシデントタイプ統計\n• フラグ分布\n• ドライバー関与'},
            'help_accident_analysis_colors': {'zh': '黃=黃旗 紅=紅旗 橙=SC', 'en': 'Yellow=Yellow flag Red=Red flag Orange=SC', 'ja': '黃=黃旗 赤=赤旗 オレンジ=SC'},
            
            'help_weather_timeline_title': {'zh': '天氣時間線', 'en': 'Weather Timeline', 'ja': '天気タイムライン'},
            'help_weather_timeline_desc': {'zh': '賽事天氣變化時間線。', 'en': 'Race weather change timeline.', 'ja': 'レース天候変化タイムライン。'},
            'help_weather_timeline_features': {'zh': '• 溫度變化\n• 降雨機率\n• 賽道狀態', 'en': '• Temperature changes\n• Rain probability\n• Track status', 'ja': '• 温度変化\n• 降雨確率\n• トラック状態'},
            'help_weather_timeline_colors': {'zh': '藍=雨 綠=乾', 'en': 'Blue=Rain Green=Dry', 'ja': '青=雨 緑=ドライ'},
            
            'help_position_analysis_title': {'zh': '位置變化分析', 'en': 'Position Analysis', 'ja': 'ポジション分析'},
            'help_position_analysis_desc': {'zh': '車手位置變化追蹤。', 'en': 'Driver position change tracking.', 'ja': 'ドライバーポジション変化追跡。'},
            'help_position_analysis_features': {'zh': '• 位置變化圖\n• 超車統計\n• 關鍵時刻', 'en': '• Position change chart\n• Overtake statistics\n• Key moments', 'ja': '• ポジション変化チャート\n• オーバーテイク統計\n• キーモーメント'},
            'help_position_analysis_colors': {'zh': '綠=超車 紅=被超', 'en': 'Green=Overtake Red=Overtaken', 'ja': '緑=オーバーテイク 赤=オーバーテイクされた'},
            
            # =================================================================
            # Home Page Modules - Weather Timeline & Standings
            # =================================================================
            
            # Weather Timeline 天氣時間軸
            'weather_timeline_title': {'zh': '比賽週末天氣時間軸', 'en': 'Race Weekend Weather Timeline', 'ja': 'レースウィークエンド天気タイムライン'},
            'weather_history_title': {'zh': '歷史天氣對比', 'en': 'Historical Weather Comparison', 'ja': '過去の天気比較'},
            'weather_no_data': {'zh': '暫無天氣數據', 'en': 'No weather data available', 'ja': '天気データがありません'},
            'weather_future_event': {'zh': '賽季尚未開始，天氣數據暫不可用', 'en': 'Season not started yet, weather data unavailable', 'ja': 'シーズン未開始、天気データなし'},
            'weather_api_error': {'zh': '無法連接氣象服務', 'en': 'Cannot connect to weather service', 'ja': '天気サービスに接続できません'},
            'weather_no_event_data': {'zh': '此賽事暫無天氣數據', 'en': 'No weather data for this event', 'ja': 'このイベントの天気データはありません'},
            'weather_history_unavailable': {'zh': '歷史數據不可用', 'en': 'Historical data unavailable', 'ja': '過去データ利用不可'},
            'weather_day_minus_2': {'zh': '前2天\n{date}', 'en': 'Day -2\n{date}', 'ja': '2日前\n{date}'},
            'weather_day_minus_1': {'zh': '前1天\n{date}', 'en': 'Day -1\n{date}', 'ja': '1日前\n{date}'},
            'weather_race_day': {'zh': '比賽日\n{date}', 'en': 'Race Day\n{date}', 'ja': 'レース当日\n{date}'},
            'weather_temp_loading': {'zh': '--', 'en': '--', 'ja': '--'},
            'weather_icon_loading': {'zh': '...', 'en': '...', 'ja': '...'},
            'weather_rain_loading': {'zh': '--', 'en': '--', 'ja': '--'},
            'weather_wind_loading': {'zh': '--', 'en': '--', 'ja': '--'},
            'weather_temp_celsius': {'zh': '{temp:.1f}°C', 'en': '{temp:.1f}°C', 'ja': '{temp:.1f}°C'},
            'weather_rain_mm': {'zh': '{precip:.1f}mm', 'en': '{precip:.1f}mm', 'ja': '{precip:.1f}mm'},
            'weather_wind_kmh': {'zh': '{arrow} {speed:.0f}km/h', 'en': '{arrow} {speed:.0f}km/h', 'ja': '{arrow} {speed:.0f}km/h'},
            'weather_wind_speed': {'zh': '，風速 {speed:.0f}km/h', 'en': ', Wind {speed:.0f}km/h', 'ja': '、風速 {speed:.0f}km/h'},
            'weather_history_2024': {'zh': '2024 年 ({date}): {icon} {temp_min:.1f}°C ~ {temp_max:.1f}°C, 降雨 {precip:.1f}mm', 'en': '2024 ({date}): {icon} {temp_min:.1f}°C ~ {temp_max:.1f}°C, Rain {precip:.1f}mm', 'ja': '2024年 ({date}): {icon} {temp_min:.1f}°C ~ {temp_max:.1f}°C, 降雨 {precip:.1f}mm'},
            'weather_history_2023': {'zh': '2023 年 ({date}): {icon} {temp_min:.1f}°C ~ {temp_max:.1f}°C, 降雨 {precip:.1f}mm', 'en': '2023 ({date}): {icon} {temp_min:.1f}°C ~ {temp_max:.1f}°C, Rain {precip:.1f}mm', 'ja': '2023年 ({date}): {icon} {temp_min:.1f}°C ~ {temp_max:.1f}°C, 降雨 {precip:.1f}mm'},
            
            # Season Progress 賽季進度
            'season_progress_title': {'zh': '賽季進度 - {year}', 'en': 'Season Progress - {year}', 'ja': 'シーズン進捗 - {year}'},
            'future_season_not_started': {'zh': '賽季尚未開始，敬請期待', 'en': 'Season Not Started Yet, Stay Tuned', 'ja': 'シーズン未開始、お楽しみに'},
            
            # Standings 積分榜
            'constructor_standings_window_title': {'zh': '車隊積分榜 - {year}', 'en': 'Constructor Standings - {year}', 'ja': 'コンストラクターズランキング - {year}'},
            'driver_standings_window_title': {'zh': '車手積分榜 - {year}', 'en': 'Driver Standings - {year}', 'ja': 'ドライバーズランキング - {year}'},
            'constructor_standings_title': {'zh': '車隊積分榜', 'en': 'Constructor Standings', 'ja': 'コンストラクターズ'},
            'driver_standings_title': {'zh': '車手積分榜', 'en': 'Driver Standings', 'ja': 'ドライバーズ'},
            'constructor_standings_title_with_round': {'zh': '車隊積分榜 - {year} 第 {round} 站', 'en': 'Constructor Standings - {year} Round {round}', 'ja': 'コンストラクター - {year} 第{round}戦'},
            'driver_standings_title_with_round': {'zh': '車手積分榜 - {year} 第 {round} 站', 'en': 'Driver Standings - {year} Round {round}', 'ja': 'ドライバー - {year} 第{round}戦'},
            'constructor_standings': {'zh': '🏆 {year} 車隊積分榜', 'en': '🏆 {year} Constructor Standings', 'ja': '🏆 {year} コンストラクターズ'},
            'driver_standings': {'zh': '🏁 {year} 車手積分榜', 'en': '🏁 {year} Driver Standings', 'ja': '🏁 {year} ドライバーズ'},
            
            # Standings Table Columns 積分榜表格欄位
            'standings_col_position': {'zh': '名次', 'en': 'Pos', 'ja': '順位'},
            'standings_col_driver_code': {'zh': '代碼', 'en': 'Code', 'ja': 'コード'},
            'standings_col_driver': {'zh': '車手', 'en': 'Driver', 'ja': 'ドライバー'},
            'standings_col_team': {'zh': '車隊', 'en': 'Team', 'ja': 'チーム'},
            'standings_col_constructor': {'zh': '車隊', 'en': 'Constructor', 'ja': 'コンストラクター'},
            'standings_col_points': {'zh': '積分', 'en': 'Points', 'ja': 'ポイント'},
            'standings_col_wins': {'zh': '勝場', 'en': 'Wins', 'ja': '勝利数'},
            'standings_col_delta': {'zh': '落後差', 'en': 'Gap', 'ja': '差'},
            'future_season_no_data': {'zh': '賽季數據尚未發布', 'en': 'Season data not yet available', 'ja': 'シーズンデータ未発表'},
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
