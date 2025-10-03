#!/usr/bin/env python3
"""
GUI 國際化模組 - GUI Internationalization Module
專門處理 GUI 介面的語言切換，不影響 CLI print 輸出
Dedicated to GUI interface language switching, does not affect CLI print output
"""

import os
import json

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
        self._config_file = os.path.join(os.path.dirname(__file__), 'gui_language_config.json')
    
    def _load_saved_language(self):
        """從設定檔載入保存的語言設定"""
        try:
            config_file = os.path.join(os.path.dirname(__file__), 'gui_language_config.json')
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('language', 'en')
        except Exception as e:
            print(f"[GUI_I18N] 載入語言設定失敗: {e}")
        return None
    
    def _save_language(self, language):
        """保存語言設定到檔案"""
        try:
            config = {'language': language}
            config_file = os.path.join(os.path.dirname(__file__), 'gui_language_config.json')
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"[GUI_I18N] 語言設定已保存: {language}")
            return True
        except Exception as e:
            print(f"[GUI_I18N] 保存語言設定失敗: {e}")
            return False
    
    def _load_translations(self):
        """載入翻譯字典"""
        return {
            # 主視窗元素
            'main_window': {'zh': 'F1T 賽車分析工作站', 'en': 'F1T Racing Analysis Workstation', 'ja': 'F1Tレーシング分析ワークステーション'},
            
            # 遙測分析對話框
            'telemetry_options_title': {'zh': '遙測分析選項', 'en': 'Telemetry Analysis Options', 'ja': 'テレメトリー分析オプション'},
            'select_telemetry_charts': {'zh': '請選擇要顯示的遙測圖表', 'en': 'Please select telemetry charts to display', 'ja': '表示するテレメトリーチャートを選択してください'},
            'driver_lap_selection': {'zh': '車手與圈數選擇', 'en': 'Driver & Lap Selection', 'ja': 'ドライバーとラップの選択'},
            'driver1_required': {'zh': '車手1 (必選):', 'en': 'Driver 1 (Required):', 'ja': 'ドライバー1（必須）:'},
            'driver2_optional': {'zh': '車手2 (選用):', 'en': 'Driver 2 (Optional):', 'ja': 'ドライバー2（オプション）:'},
            'lap_number': {'zh': '圈數:', 'en': 'Lap:', 'ja': 'ラップ:'},
            'telemetry_options': {'zh': '遙測選項', 'en': 'Telemetry Options', 'ja': 'テレメトリーオプション'},
            
            # 按鈕
            'select_all': {'zh': '全選', 'en': 'Select All', 'ja': 'すべて選択'},
            'select_none': {'zh': '全不選', 'en': 'Clear All', 'ja': 'すべてクリア'},
            'restore_default': {'zh': '恢復預設', 'en': 'Restore Default', 'ja': 'デフォルトに戻す'},
            'ok': {'zh': '確定', 'en': 'OK', 'ja': 'OK'},
            'cancel': {'zh': '取消', 'en': 'Cancel', 'ja': 'キャンセル'},
            'reanalyze': {'zh': 'R', 'en': 'R', 'ja': 'R'},
            
            # 控制項標籤
            'year': {'zh': '年:', 'en': 'Year:', 'ja': '年:'},
            'race': {'zh': '賽事:', 'en': 'Race:', 'ja': 'レース:'},
            'session': {'zh': '賽段:', 'en': 'Session:', 'ja': 'セッション:'},

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
            'tile_windows_action': {'zh': '平鋪視窗', 'en': 'Tile Windows', 'ja': 'ウィンドウを並べて表示'},
            'cascade_windows_action': {'zh': '層疊視窗', 'en': 'Cascade Windows', 'ja': 'ウィンドウを重ねて表示'},
            'sync_checkbox_main': {'zh': '[LINK] 接收主程式同步 (年份/賽事/賽段)', 'en': '[LINK] Receive Main Window Sync (Year/Race/Session)', 'ja': '[LINK] Receive Main Window Sync (Year/Race/Session)'},
            'sync_checkbox_tooltip_main': {'zh': '勾選時接收主程式參數同步，下方分析參數將變為不可編輯', 'en': 'When checked, receive parameters from main window and lock analysis controls', 'ja': 'When checked, receive parameters from main window and lock analysis controls'},

            
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
            'brake_chart_title': {'zh': '🔄 煞車分析圖表', 'en': '🔄 Brake Analysis Chart', 'ja': '🔄 ブレーキ分析チャート'},
            'brake_chart_loading': {'zh': '煞車圖表組件正在載入中...', 'en': 'Brake chart component loading...', 'ja': 'ブレーキチャートコンポーネント読み込み中...'},
            'brake_value': {'zh': '煞車', 'en': 'brake', 'ja': 'ブレーキ'},
            
            # throttle 分析專用
            'throttle_chart_title': {'zh': '🔄 油門分析圖表', 'en': '🔄 Throttle Analysis Chart', 'ja': '🔄 スロットル分析チャート'},
            'throttle_chart_loading': {'zh': '油門圖表組件正在載入中...', 'en': 'Throttle chart component loading...', 'ja': 'スロットルチャートコンポーネント読み込み中...'},
            'throttle_value': {'zh': '油門', 'en': 'throttle', 'ja': 'スロットル'},
            
            # RPM 分析專用
            'rpm_chart_title': {'zh': '🔄 RPM分析圖表', 'en': '🔄 RPM Analysis Chart', 'ja': '🔄 RPM分析チャート'},
            'rpm_chart_loading': {'zh': 'RPM圖表組件正在載入中...', 'en': 'RPM chart component loading...', 'ja': 'RPMチャートコンポーネント読み込み中...'},
            'rpm_value': {'zh': 'RPM', 'en': 'RPM', 'ja': 'RPM'},
            
            # gear 分析專用
            'gear_chart_title': {'zh': '🔄 檔位分析圖表', 'en': '🔄 Gear Analysis Chart', 'ja': '🔄 ギア分析チャート'},
            'gear_chart_loading': {'zh': '檔位圖表組件正在載入中...', 'en': 'Gear chart component loading...', 'ja': 'ギアチャートコンポーネント読み込み中...'},
            'gear_value': {'zh': '檔位', 'en': 'gear', 'ja': 'ギア'},
            
            # acceleration 分析專用
            'acceleration_chart_title': {'zh': '🔄 加速度分析圖表', 'en': '🔄 Acceleration Analysis Chart', 'ja': '🔄 加速度分析チャート'},
            'acceleration_chart_loading': {'zh': '加速度圖表組件正在載入中...', 'en': 'Acceleration chart component loading...', 'ja': '加速度チャートコンポーネント読み込み中...'},
            'acceleration_value': {'zh': '加速度', 'en': 'acceleration', 'ja': '加速度'},
            'telemetry_acceleration': {'zh': '加速度 (m/s²)', 'en': 'Acceleration (m/s²)', 'ja': '加速度 (m/s²)'},
            
            # speeddiff 分析專用
            'speeddiff_chart_title': {'zh': '🔄 速度差分析圖表', 'en': '🔄 Speed Diff Analysis Chart', 'ja': '🔄 速度差分析チャート'},
            'speeddiff_chart_loading': {'zh': '速度差圖表組件正在載入中...', 'en': 'Speed diff chart component loading...', 'ja': '速度差チャートコンポーネント読み込み中...'},
            'speeddiff_value': {'zh': '速度差', 'en': 'speed diff', 'ja': '速度差'},
            'loading_speeddiff_data': {'zh': '開始載入速度差數據...', 'en': 'Loading speed diff data...', 'ja': '速度差データを読み込み中...'},
            
            # distancediff 分析專用
            'distancediff_chart_title': {'zh': '🔄 距離差分析圖表', 'en': '🔄 Distance Diff Analysis Chart', 'ja': '🔄 距離差分析チャート'},
            'distancediff_chart_loading': {'zh': '距離差圖表組件正在載入中...', 'en': 'Distance diff chart component loading...', 'ja': '距離差チャートコンポーネント読み込み中...'},
            'distancediff_value': {'zh': '距離差', 'en': 'distance diff', 'ja': '距離差'},
            'loading_distancediff_data': {'zh': '開始載入距離差數據...', 'en': 'Loading distance diff data...', 'ja': '距離差データを読み込み中...'},
            'loading_acceleration_data': {'zh': '開始載入加速度數據...', 'en': 'Loading acceleration data...', 'ja': '加速度データを読み込み中...'},
            
            # 通用狀態
            'cleared': {'zh': '已清除', 'en': 'Cleared', 'ja': 'クリア済み'},
            
            # === 新增：QMessageBox 對話框翻譯鍵 ===
            # 關閉確認對話框
            'confirm_exit': {'zh': '確認退出', 'en': 'Confirm Exit', 'ja': '終了確認'},
            'confirm_exit_message': {
                'zh': '確定要退出 F1T 專業賽車分析工作站嗎？\n\n所有正在執行的分析將被停止。', 
                'en': 'Are you sure you want to exit F1T Professional Racing Analysis Workstation?\n\nAll running analyses will be stopped.', 
                'ja': 'F1Tプロフェッショナルレーシング分析ワークステーションを終了してもよろしいですか？\n\n実行中のすべての分析が停止されます。'
            },
            
            # 按鈕選項
            'yes': {'zh': '是', 'en': 'Yes', 'ja': 'はい'},
            'no': {'zh': '否', 'en': 'No', 'ja': 'いいえ'},
            
            # 分析錯誤訊息
            'analysis_failed': {'zh': '分析失敗', 'en': 'Analysis Failed', 'ja': '分析失敗'},
            'cli_error': {'zh': 'CLI 分析過程中發生錯誤', 'en': 'Error occurred during CLI analysis', 'ja': 'CLI分析中にエラーが発生しました'},
            
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
            'rain_analysis': {'zh': '雨況分析', 'en': 'Rain Analysis', 'ja': '降雨分析'},
            
            # 事故分析模組
            'waiting_data_load': {'zh': '等待數據載入...', 'en': 'Waiting for data loading...', 'ja': 'データ読み込み待ち...'},
            'accident_analysis_error': {'zh': '事故分析錯誤', 'en': 'Accident Analysis Error', 'ja': '事故分析エラー'},
            'accident_comprehensive_analysis': {'zh': '事故綜合分析', 'en': 'Accident Comprehensive Analysis', 'ja': '事故総合分析'},
            'accident_module_description': {'zh': 'F1 事故統計分析與可視化', 'en': 'F1 Accident Statistics Analysis and Visualization', 'ja': 'F1 事故統計分析と可視化'},
            'invalid_load_parameters': {'zh': '載入參數不正確', 'en': 'Invalid load parameters', 'ja': 'ロードパラメータが無効'},
            'local_data_format_error': {'zh': '本地資料格式錯誤', 'en': 'Local data format error', 'ja': 'ローカルデータフォーマットエラー'},
            'data_load_complete': {'zh': '✅ 數據載入完成', 'en': '✅ Data loaded successfully', 'ja': '✅ データ読み込み完了'},
            'data_cleared': {'zh': '數據已清除', 'en': 'Data cleared', 'ja': 'データがクリアされました'},
            'incident_type': {'zh': '事故類型', 'en': 'Incident Type', 'ja': '事故タイプ'},
            'count': {'zh': '次數', 'en': 'Count', 'ja': '回数'},
            'accident_comprehensive_analysis': {'zh': '🔥 事故綜合分析', 'en': '🔥 Accident Comprehensive Analysis', 'ja': '🔥 事故総合分析'},
            
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
            'load_failed': {'zh': '載入失敗', 'en': 'Load failed', 'ja': '読み込み失敗'},
            'all_categories': {'zh': '全部類別', 'en': 'All Categories', 'ja': 'すべてのカテゴリー'},
            'all_severities': {'zh': '全部嚴重程度', 'en': 'All Severities', 'ja': 'すべての重大度'},
            'all_impacts': {'zh': '全部影響程度', 'en': 'All Impacts', 'ja': 'すべての影響度'},
            'refresh': {'zh': '刷新', 'en': 'Refresh', 'ja': '更新'},
            'loading': {'zh': '載入中...', 'en': 'Loading...', 'ja': '読み込み中...'},
            'no_incident_data': {'zh': '無事件數據', 'en': 'No incident data', 'ja': 'イベントデータなし'},
            'loading_incident_data': {'zh': '載入事件數據中...', 'en': 'Loading incident data...', 'ja': 'イベントデータ読み込み中...'},
            
            # 事故分析分頁和搜尋
            'accident_statistics': {'zh': '事故統計', 'en': 'Accident Statistics', 'ja': '事故統計'},
            'detailed_records': {'zh': '詳細記錄', 'en': 'Detailed Records', 'ja': '詳細記録'},
            'search_event_description': {'zh': '搜尋事件描述或關鍵字...', 'en': 'Search event description or keywords...', 'ja': 'イベント説明またはキーワードを検索...'},
            'total_events': {'zh': '總事件', 'en': 'Total Events', 'ja': '総イベント'},
            'pit_related': {'zh': 'PIT相關', 'en': 'PIT Related', 'ja': 'PIT関連'},
            'track_limits': {'zh': '賽道限制', 'en': 'Track Limits', 'ja': 'トラックリミット'},
            'investigation': {'zh': '調查', 'en': 'Investigation', 'ja': '調査'},
            'penalty_cat': {'zh': '處罰', 'en': 'Penalty', 'ja': 'ペナルティ'},
            'other': {'zh': '其他', 'en': 'Other', 'ja': 'その他'},
            
            # 事故統計卡片
            'track_limit_violations': {'zh': '⚠️ Track Limit', 'en': '⚠️ Track Limit', 'ja': '⚠️ トラックリミット'},
            'violations_count': {'zh': '(違規次數)', 'en': '(Violations)', 'ja': '(違反回数)'},
            'double_yellow_flag': {'zh': '🟡🟡 雙黃旗', 'en': '🟡🟡 Double Yellow', 'ja': '🟡🟡 ダブルイエロー'},
            'yellow_flag': {'zh': '🟡 黃旗', 'en': '🟡 Yellow Flag', 'ja': '🟡 イエローフラッグ'},
            'red_flag': {'zh': '🔴 紅旗', 'en': '🔴 Red Flag', 'ja': '🔴 レッドフラッグ'},
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
            'speeddiff_analysis': {'zh': '速度差異分析', 'en': 'Speed Diff Analysis', 'ja': '速度差分析'},
            'speeddiff_analysis_description': {
                'zh': 'F1賽車速度差異對比分析工具',
                'en': 'F1 racing speed difference analysis tool',
                'ja': 'F1レーシング速度差分析ツール'
            },
            'distancediff_analysis': {'zh': '距離差異分析', 'en': 'Distance Diff Analysis', 'ja': '距離差分析'},
            'distancediff_analysis_description': {
                'zh': 'F1賽車距離差異對比分析工具',
                'en': 'F1 racing distance difference analysis tool',
                'ja': 'F1レーシング距離差分析ツール'
            },
            'acceleration_analysis': {'zh': '加速度分析', 'en': 'Acceleration Analysis', 'ja': '加速度分析'},
            'acceleration_analysis_description': {
                'zh': 'F1賽車加速度分析模組',
                'en': 'F1 racing acceleration analysis module',
                'ja': 'F1レーシング加速度分析モジュール'
            },
            
            # 統計面板通用標籤
            'detailed_statistics': {'zh': '詳細統計信息', 'en': 'Detailed Statistics', 'ja': '詳細統計情報'},
            'lap_time': {'zh': '圈時間', 'en': 'Lap Time', 'ja': 'ラップタイム'},
            'tire_compound': {'zh': '輪胎配方', 'en': 'Tire Compound', 'ja': 'タイヤコンパウンド'},
            'lap_number_short': {'zh': '圈數', 'en': 'Lap', 'ja': 'ラップ'},
            'lap_number_label': {'zh': '🔄 圈數:', 'en': '🔄 Lap:', 'ja': '🔄 ラップ:'},
            
            # 速度差分析專用標籤
            'speed_diff_kmh': {'zh': '速度差距 (km/h)', 'en': 'Speed Diff (km/h)', 'ja': '速度差 (km/h)'},
            'leading': {'zh': '領先', 'en': 'Leading', 'ja': '先行'},
            'zero_line': {'zh': '零點線', 'en': 'Zero Line', 'ja': 'ゼロライン'},
            'speeddiff_window_title': {'zh': '⚡ 速度差分析', 'en': '⚡ Speed Diff Analysis', 'ja': '⚡ 速度差分析'},
            
            # 累積距離差分析專用標籤
            'distance_diff_m': {'zh': '距離差距 (m)', 'en': 'Distance Diff (m)', 'ja': '距離差 (m)'},
            'distancediff_window_title': {'zh': '📏 累積距離差分析', 'en': '📏 Distance Diff Analysis', 'ja': '📏 距離差分析'},
            
            # 表格標題
            'item': {'zh': '項目', 'en': 'Item', 'ja': '項目'},
            'driver1': {'zh': '車手1', 'en': 'Driver 1', 'ja': 'ドライバー1'},
            'driver2': {'zh': '車手2', 'en': 'Driver 2', 'ja': 'ドライバー2'},
            'difference': {'zh': '差值', 'en': 'Difference', 'ja': '差分'},
            
            # 軸標籤和單位
            'distance_m': {'zh': '距離 (m)', 'en': 'Distance (m)', 'ja': '距離 (m)'},
            'distance_label': {'zh': '距離', 'en': 'Distance', 'ja': '距離'},
            'linkage_distance': {'zh': '連動距離', 'en': 'Linkage Distance', 'ja': '連動距離'},
            
            # 連動系統專用翻譯
            'linkage_button': {'zh': '🔗 連動', 'en': '🔗 Link', 'ja': '🔗 連動'},
            'master_linkage_button': {'zh': '🔗 主連動', 'en': '🔗 Master Link', 'ja': '🔗 マスター連動'},
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
            'detailed_lap_analysis': {'zh': '詳細圈速分析', 'en': 'Detailed Lap Analysis', 'ja': 'Detailed Lap Analysis'},
            'driver_analysis': {'zh': '車手分析', 'en': 'Driver Analysis', 'ja': 'ドライバー分析'},
            'driver_ranking': {'zh': '車手排名', 'en': 'Driver Ranking', 'ja': 'Driver Ranking'},
            'tire_strategy_analysis': {'zh': '輪胎策略分析', 'en': 'Tire Strategy Analysis', 'ja': 'Tire Strategy Analysis'},
            
            # 視窗標題模板
            'window_title_track': {'zh': '賽道', 'en': 'Track', 'ja': 'Track'},
            'window_title_rain_analysis': {'zh': '🌧️ 降雨分析', 'en': '🌧️ Rain Analysis', 'ja': '🌧️ Rain Analysis'},
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
            'export_report': {'zh': '匯出報告...', 'en': 'Export Report...', 'ja': 'レポートをエクスポート...'},
            'exit': {'zh': '結束', 'en': 'Exit', 'ja': '終了'},
            
            # Analysis Menu 項目
            'rain_analysis': {'zh': '降雨分析', 'en': 'Rain Analysis', 'ja': '降雨分析'},
            'track_analysis': {'zh': '賽道分析', 'en': 'Track Analysis', 'ja': 'トラック分析'},
            'race_overview': {'zh': '🏎️ 賽事概覽', 'en': '🏎️ Race Overview', 'ja': '🏎️ レース概要'},
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
            'run_api_health_check': {'zh': '立即執行 API 健康檢查', 'en': 'Run an API health check immediately', 'ja': 'APIヘルスチェックを即座に実行'},
            
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
            'context_menu_maximize': {'zh': '🔳 最大化', 'en': '🔳 Maximize', 'ja': '🔳 最大化'},
            
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
            
            # 功能樹項目
            'single_race_analysis': {'zh': '單場賽事分析', 'en': 'Single Race Analysis', 'ja': '単一レース分析'},
            'single_race_driver_analysis': {'zh': '🚗 單場賽事車手分析', 'en': '🚗 Single Race Driver Analysis', 'ja': '🚗 単一レースドライバー分析'},
            'pitstop_analysis': {'zh': '進站分析', 'en': 'Pitstop Analysis', 'ja': 'ピットストップ分析'},
            'driver_ranking': {'zh': '車手排名', 'en': 'Driver Ranking', 'ja': 'ドライバーランキング'},
            'tire_strategy_analysis': {'zh': '輪胎策略分析', 'en': 'Tire Strategy Analysis', 'ja': 'タイヤ戦略分析'},
            'detailed_lap_analysis': {'zh': '詳細圈速分析', 'en': 'Detailed Lap Analysis', 'ja': '詳細ラップ分析'},
            
            # 歡迎頁面
            'main_title': {'zh': 'F1T 專業賽車分析工作站', 'en': 'F1T Professional Racing Analysis Workstation', 'ja': 'F1T Professional Racing Analysis Workstation'},
            'subtitle': {'zh': '專業級 F1 數據分析平台', 'en': 'Professional F1 Data Analysis Platform', 'ja': 'Professional F1 Data Analysis Platform'},
            'welcome_info': {'zh': '💡 左鍵選擇模組 • 右鍵執行分析 • 支援 Ctrl/Shift 多選批量分析 • Version 13.0', 'en': '💡 Left click to select module • Right click to execute analysis • Support Ctrl/Shift multi-select batch analysis • Version 13.0', 'ja': '💡 Left click to select module • Right click to execute analysis • Support Ctrl/Shift multi-select batch analysis • Version 13.0'},
            
            # 統計和數據
            'statistics_data': {'zh': '統計數據', 'en': 'Statistics Data', 'ja': 'Statistics Data'},
            'season_statistics': {'zh': '[CHART] 賽季統計數據\n• 總圈數: 1,247\n• 平均圈速: 1:18.456\n• 最快圈速: 1:16.123', 'en': '[CHART] Season Statistics\n• Total Laps: 1,247\n• Average Lap Time: 1:18.456\n• Fastest Lap: 1:16.123', 'ja': '[CHART] Season Statistics\n• Total Laps: 1,247\n• Average Lap Time: 1:18.456\n• Fastest Lap: 1:16.123'},
            'data_overview': {'zh': '[STATS] 數據總覽', 'en': '[STATS] Data Overview', 'ja': '[STATS] Data Overview'},
            
            # 統計卡片
            'track_limit_violations': {'zh': '⚠️ Track Limit', 'en': '⚠️ Track Limit', 'ja': '⚠️ Track Limit'},
            'double_yellow_flag': {'zh': '🟡🟡 雙黃旗', 'en': '🟡🟡 Double Yellow', 'ja': '🟡🟡 Double Yellow'},
            'yellow_flag': {'zh': '🟡 黃旗', 'en': '🟡 Yellow Flag', 'ja': '🟡 Yellow Flag'},
            'red_flag': {'zh': '🔴 紅旗', 'en': '🔴 Red Flag', 'ja': '🔴 Red Flag'},
            'fastest_driver': {'zh': '最快車手', 'en': 'Fastest Driver', 'ja': 'Fastest Driver'},
            'avg_laptime': {'zh': '平均圈速', 'en': 'Avg Lap Time', 'ja': 'Avg Lap Time'},
            'violations_count': {'zh': '(違規次數)', 'en': '(Violations)', 'ja': '(Violations)'},
            'display_count': {'zh': '(出示次數)', 'en': '(Displayed)', 'ja': '(Displayed)'},
            
            # 圖表軸標籤
            'lap_number_axis': {'zh': '圈數 (Lap)', 'en': 'Lap Number', 'ja': 'Lap Number'},
            'track_temperature': {'zh': '賽道溫度 (°C)', 'en': 'Track Temperature (°C)', 'ja': 'Track Temperature (°C)'},
            'air_track_temp_comparison': {'zh': '氣溫與賽道溫度對比', 'en': 'Air vs Track Temperature', 'ja': 'Air vs Track Temperature'},
            
            # 分頁標籤
            'driver_fastest_pitstop_ranking': {'zh': '🏆 車手最快進站排行榜', 'en': '🏆 Driver Fastest Pitstop Ranking', 'ja': '🏆 Driver Fastest Pitstop Ranking'},
            'team_pitstop_statistics': {'zh': '🏁 車隊進站統計', 'en': '🏁 Team Pitstop Statistics', 'ja': '🏁 Team Pitstop Statistics'},
            'detailed_records': {'zh': '📋 詳細記錄', 'en': '📋 Detailed Records', 'ja': '📋 Detailed Records'},
            
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
            'show_all_data': {'zh': '顯示所有資料', 'en': 'Show All Data', 'ja': 'Show All Data'},
            
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
            'forced_close_gui': {'zh': 'F1T GUI 已強制關閉', 'en': 'F1T GUI has been force closed', 'ja': 'F1T GUI has been force closed'},
            
            # Tooltips
            'sync_main_window_tooltip': {'zh': '接收主程式同步：啟用 (綠色) / 停用 (紅色)', 'en': 'Receive Main Window Sync: Enabled (Green) / Disabled (Red)', 'ja': 'Receive Main Window Sync: Enabled (Green) / Disabled (Red)'},
            'individual_linkage_tooltip': {'zh': '個別連動：啟用 / 停用', 'en': 'Individual Linkage: Enabled / Disabled', 'ja': 'Individual Linkage: Enabled / Disabled'},
            'restore_normal_size_tooltip': {'zh': '恢復正常大小', 'en': 'Restore to normal size', 'ja': 'Restore to normal size'},
            'window_settings_tooltip': {'zh': '視窗設定', 'en': 'Window settings', 'ja': 'Window settings'},
            'minimize_tooltip': {'zh': '最小化', 'en': 'Minimize', 'ja': 'Minimize'},
            'maximize_tooltip': {'zh': '最大化/還原', 'en': 'Maximize/Restore', 'ja': 'Maximize/Restore'},
            'popout_tooltip': {'zh': '彈出為獨立視窗', 'en': 'Pop out as independent window', 'ja': 'Pop out as independent window'},
            'close_tooltip': {'zh': '關閉', 'en': 'Close', 'ja': '閉じる'},
            
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
            'main_window_title': {'zh': 'F1T 專業賽車分析工作站 v8.0', 'en': 'F1T Professional Racing Analysis Workstation v8.0', 'ja': 'F1Tプロフェッショナルレーシング分析ワークステーション v8.0'},
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
            'driver_lap_selection': {'zh': '車手和圈數選擇', 'en': 'Driver and Lap Selection', 'ja': 'Driver and Lap Selection'},
            'driver1_required': {'zh': '車手1 (必選):', 'en': 'Driver 1 (Required):', 'ja': 'ドライバー1（必須）:'},
            'driver2_optional': {'zh': '車手2 (選用):', 'en': 'Driver 2 (Optional):', 'ja': 'ドライバー2（オプション）:'},
            'lap_number': {'zh': '圈數:', 'en': 'Lap:', 'ja': 'ラップ:'},
            'fastest_lap': {'zh': '最速圈', 'en': 'Fastest Lap', 'ja': '最速ラップ'},
            'telemetry_options': {'zh': '遙測選項', 'en': 'Telemetry Options', 'ja': 'テレメトリーオプション'},
            'select_all': {'zh': '全選', 'en': 'Select All', 'ja': 'すべて選択'},
            'select_none': {'zh': '全不選', 'en': 'Select None', 'ja': 'Select None'},
            'restore_default': {'zh': '恢復預設', 'en': 'Restore Default', 'ja': 'デフォルトに戻す'},
            'ok': {'zh': '確定', 'en': 'OK', 'ja': 'OK'},
            'lap': {'zh': '圈', 'en': 'Lap', 'ja': 'ラップ'},
            'fastest_lap_type': {'zh': '最速圈', 'en': 'Fastest Lap', 'ja': '最速ラップ'},
            'specific_lap': {'zh': '指定圈數', 'en': 'Specific Lap', 'ja': '特定ラップ'},
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
            print(f"[GUI_I18N] ✅ 語言已切換至: {language}")
            return True
        print(f"[GUI_I18N] ⚠️ 不支援的語言: {language}")
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
