#!/usr/bin/env python3
"""
詳細圈速分析數據載入器
基於 UniversalDataLoader 的 Function 28 (詳細圈速分析) 專門接口
"""

import sys
import os
import json
import subprocess
from typing import Dict, List, Optional, Any
from PyQt5.QtCore import QObject, pyqtSignal

# 添加項目根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from modules.gui.base import UniversalDataLoader

class driverLapUniversalDataLoader(UniversalDataLoader):
    """詳細圈速分析專門的通用數據載入器實現 (Function 28)"""
    
    def __init__(self):
        # 使用 laptime 類型初始化（由 driverLapDataLoader 預先註冊）
        super().__init__('laptime')
    
    def _validate_load_parameters(self, params: Dict[str, Any]) -> bool:
        """驗證載入參數"""
        required_params = ['year', 'race', 'driver']
        return all(param in params for param in required_params)
    
    def _build_filename_patterns(self, **kwargs) -> List[str]:
        """構建詳細圈速分析檔案名稱搜尋模式 (Function 28)"""
        year = kwargs.get('year', '*')
        race = kwargs.get('race', '*')
        session = kwargs.get('session', 'R')
        driver = kwargs.get('driver', '*')
        
        # 處理賽事名稱的多種格式
        race_variants = [race]
        if race == 'Japan':
            race_variants.extend(['Japanese Grand Prix', 'Japanese_Grand_Prix'])
        elif ' ' in race:
            # 如果原始名稱包含空格，也嘗試下劃線版本
            race_variants.append(race.replace(' ', '_'))
        
        # 處理 session 的多種格式 - 添加更多變體
        session_variants = [session]
        if session == 'R':
            session_variants.extend(['Race', 'None'])
        elif session is None or session == '':
            session_variants.extend(['R', 'Race', 'None'])
        
        patterns = []
        
        # Function 28 詳細圈速分析檔案格式
        file_prefixes = [
            'detailed_laptime_analysis',       # Function 28 主要格式
            'detailed_driver_laptime',         # 變體格式
            'driver_detailed_analysis',        # 備用格式
            'f28_detailed_laptime'             # 帶功能號格式
        ]
        
        for race_var in race_variants:
            for session_var in session_variants:
                for prefix in file_prefixes:
                    # Function 28 格式：detailed_laptime_analysis_{year}_{race}_{session}_all_drivers.json
                    patterns.extend([
                        f"{prefix}_{year}_{race_var}_{session_var}_all_drivers.json",
                        f"{prefix}_{year}_{race_var}_{session_var}_{driver}.json",
                        f"{prefix}_{year}_{race_var}_{session_var}.json"
                    ])
        
        # 移除重複並過濾空的 session 部分
        unique_patterns = []
        for pattern in patterns:
            # 清理連續的下劃線和空session
            cleaned = pattern.replace('__', '_').replace('_.json', '.json')
            if cleaned not in unique_patterns:
                unique_patterns.append(cleaned)
        
        # 添加調試信息
        print(f"[F28_LOADER] 生成了 {len(unique_patterns)} 個搜尋模式")
        for i, pattern in enumerate(unique_patterns[:10], 1):  # 只顯示前10個避免輸出過長
            print(f"[F28_LOADER]   模式 {i}: {pattern}")
        if len(unique_patterns) > 10:
            print(f"[F28_LOADER]   ... 還有 {len(unique_patterns) - 10} 個模式")
        
        return unique_patterns
    
    def _generate_data_via_cli(self, **kwargs) -> bool:
        """透過 CLI -f28 工具生成詳細圈速分析數據"""
        try:
            year = kwargs.get('year')
            race = kwargs.get('race')
            session = kwargs.get('session', 'R')
            driver = kwargs.get('driver')
            
            if not all([year, race]):
                print("[F28_LOADER] 缺少必要參數：year, race")
                return False
            
            # 執行 CLI -f28 詳細圈速分析
            cmd = [
                'python', 'f1_analysis_modular_main.py',
                '-y', str(year),
                '-r', str(race), 
                '-s', str(session),
                '-f', '28'
            ]
            
            # 如果指定了車手，添加車手參數
            if driver and driver != 'all_drivers':
                cmd.extend(['-d', str(driver)])
            
            print(f"[F28_LOADER] 執行 CLI 命令: {' '.join(cmd)}")
            
            # 切換到專案根目錄執行
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            result = subprocess.run(cmd, cwd=project_root, 
                                  capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("[F28_LOADER] CLI -f28 執行成功")
                return True
            else:
                print(f"[F28_LOADER] CLI -f28 執行失敗: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"[F28_LOADER] CLI 執行異常: {e}")
            return False
            return False
    
    def _validate_data_format(self, raw_data: Any) -> bool:
        """驗證詳細圈速分析數據格式 (Function 28)"""
        if not isinstance(raw_data, dict):
            return False
        
        # 檢查必要的詳細圈速分析數據欄位
        required_fields = [
            'all_drivers_detailed_laptime',   # Function 28 主要數據格式
            'drivers_analyzed',               # 車手列表
            'success'                         # 基本成功標記
        ]
        return any(field in raw_data for field in required_fields)
    
    def _process_data(self, raw_data: Any) -> Dict[str, Any]:
        """處理詳細圈速分析數據為標準格式 (Function 28)"""
        if isinstance(raw_data, dict):
            # 提取分析信息 - Function 28 格式
            metadata = raw_data.get('metadata', {})
            
            # 基本元數據
            combined_metadata = {
                'year': raw_data.get('year') or metadata.get('year'),
                'race': raw_data.get('race') or metadata.get('race'), 
                'session': raw_data.get('session') or metadata.get('session'),
                'analysis_timestamp': raw_data.get('analysis_timestamp') or metadata.get('generated_at'),
                'success': raw_data.get('success', True),
                'analysis_mode': raw_data.get('analysis_mode', 'single'),
                'function_id': '28',
                'analysis_type': 'detailed_laptime_analysis'
            }
            
            # 獲取車手詳細圈速數據 - Function 28 格式
            detailed_laptime_data = {}
            drivers_analyzed = []
            
            if 'all_drivers_detailed_laptime' in raw_data:
                # Function 28 標準格式
                detailed_laptime_data = raw_data['all_drivers_detailed_laptime']
                drivers_analyzed = raw_data.get('drivers_analyzed', list(detailed_laptime_data.keys()))
                print(f"[F28_DATA] 使用 Function 28 格式，車手數量: {len(drivers_analyzed)}")
            else:
                print(f"[F28_DATA] 警告：無法找到 Function 28 支援的數據格式")
                detailed_laptime_data = {}
                drivers_analyzed = []
            
            return {
                'metadata': combined_metadata,
                'drivers_analyzed': drivers_analyzed,
                'all_drivers_detailed_laptime': detailed_laptime_data,
                'detailed_laptime_analysis': detailed_laptime_data,
                'raw_data': raw_data
            }
        return {'raw_data': raw_data}

class driverLapDataLoader(QObject):
    """詳細圈速分析專門數據載入器 (Function 28)"""
    
    # 信號定義
    data_loaded = pyqtSignal(dict)  # 數據載入完成
    load_error = pyqtSignal(str)    # 載入錯誤
    status_changed = pyqtSignal(str) # 狀態變化
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 確保 laptime 類型已註冊
        self._ensure_laptime_registered()
        
        # 創建專門的通用數據載入器實例
        self.universal_loader = driverLapUniversalDataLoader()
        
        # 連接通用載入器的信號
        self._connect_universal_loader_signals()
        
        # 詳細圈速分析特定配置 (Function 28)
        self.analysis_config = {
            'detailed_laptime': {
                'required_data': ['detailed_lap_data', 'smart_markers', 'lap_times'],
                'optional_data': ['track_status', 'weather', 'tire_data'],
                'analysis_types': ['detailed_laptime_analysis', 'intelligent_marking', 'comprehensive_analysis']
            }
        }
        
        # 詳細圈速分析特定配置 (Function 28)
        self.analysis_config = {
            'detailed_laptime': {
                'required_data': ['detailed_lap_data', 'smart_markers', 'lap_times'],
                'optional_data': ['track_status', 'weather', 'tire_data'],
                'analysis_types': ['detailed_laptime_analysis', 'intelligent_marking', 'comprehensive_analysis']
            }
        }
    
    def _ensure_laptime_registered(self):
        """確保 laptime 分析類型已註冊"""
        from modules.gui.base import UniversalDataLoader, AnalysisConfig
        
        if 'laptime' not in UniversalDataLoader.ANALYSIS_TYPES:
            UniversalDataLoader.register_analysis_type(
                'laptime',
                AnalysisConfig(
                    display_name='詳細圈速分析',
                    debug_prefix='F28_DATA',
                    data_source='json',
                    cli_function='28',  # Function 28: 詳細圈速分析
                    file_patterns=['detailed_laptime_analysis_*.json']
                )
            )
            print(f"[F28_DATA] 已註冊 laptime 分析類型")
    
    def _connect_universal_loader_signals(self):
        """連接通用載入器信號"""
        if hasattr(self.universal_loader, 'data_loaded'):
            self.universal_loader.data_loaded.connect(self._on_universal_data_loaded)
        if hasattr(self.universal_loader, 'load_error'):
            self.universal_loader.load_error.connect(self._on_universal_load_error)
        if hasattr(self.universal_loader, 'status_changed'):
            self.universal_loader.status_changed.connect(self._on_universal_status_changed)
    
    def _on_universal_data_loaded(self, data):
        """處理通用載入器的數據載入完成"""
        try:
            print(f"📥 [F28_DATA] 接收到通用載入器數據")
            print(f"   - 數據類型: {type(data)}")
            print(f"   - 數據鍵: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            # 對詳細圈速分析數據進行後處理
            processed_data = self._process_detailed_laptime_data(data)
            
            print(f"📤 [F28_DATA] 發射 data_loaded 信號")
            print(f"   - 處理後數據類型: {type(processed_data)}")
            print(f"   - 處理後數據鍵: {list(processed_data.keys()) if isinstance(processed_data, dict) else 'Not a dict'}")
            
            self.data_loaded.emit(processed_data)
        except Exception as e:
            print(f"❌ [F28_DATA] 數據後處理錯誤: {str(e)}")
            import traceback
            traceback.print_exc()
            self.load_error.emit(f"數據後處理錯誤: {str(e)}")
    
    def _on_universal_load_error(self, error_message):
        """處理通用載入器的錯誤"""
        self.load_error.emit(f"詳細圈速分析數據載入錯誤: {error_message}")
    
    def _on_universal_status_changed(self, status):
        """處理通用載入器的狀態變化"""
    def _process_detailed_laptime_data(self, data: Dict) -> Dict:
        """
        處理詳細圈速分析特定的數據格式 (Function 28)
        
        Args:
            data: 原始數據字典
            
        Returns:
            Dict: 處理後的詳細圈速分析數據
        """
        processed_data = {
            'metadata': data.get('metadata', {}),
            'raw_data': data
        }
        
        # 獲取車手詳細圈速數據 - Function 28 格式
        if 'all_drivers_detailed_laptime' in data:
            # Function 28 標準格式
            all_drivers_data = data['all_drivers_detailed_laptime']
            drivers_analyzed = data.get('drivers_analyzed', list(all_drivers_data.keys()))
            print(f"[F28_DATA] Function 28 格式：找到 {len(drivers_analyzed)} 個車手")
            
            # 處理每個車手的詳細數據
            for driver in all_drivers_data:
                driver_data = all_drivers_data[driver]
                if isinstance(driver_data, dict):
                    # 統計圈數和智能標記
                    detailed_laps = driver_data.get('detailed_lap_data', [])
                    smart_markers = driver_data.get('smart_markers_summary', {})
                    print(f"[F28_DATA] 車手 {driver}: {len(detailed_laps)} 圈，智能標記: {len(smart_markers)} 類")
        else:
            all_drivers_data = {}
            drivers_analyzed = []
            print(f"[F28_DATA] 警告：未找到 Function 28 支援的數據格式")
        
        processed_data['drivers_analyzed'] = drivers_analyzed
        processed_data['detailed_laptime_analysis'] = all_drivers_data
        
        print(f"[F28_DATA] 處理完成，車手數量: {len(all_drivers_data)}")
        
        return processed_data
        """
        處理輪胎策略分析特定的數據格式
        
        Args:
            data: 原始數據字典
            
        Returns:
            Dict: 處理後的輪胎策略分析數據
        """
        processed_data = {
            'metadata': data.get('metadata', {}),
            'raw_data': data
        }
        
        # 獲取車手分析數據和車手列表
        if 'drivers_analysis' in data:
            # 新格式 v2
            all_drivers_data = data['drivers_analysis']
            drivers_analyzed = list(all_drivers_data.keys())
            print(f"[driverLap_DATA] 新格式：找到 {len(drivers_analyzed)} 個車手")
        elif 'all_drivers_driverLap_strategy' in data:
            # 舊格式 v1
            all_drivers_data = data['all_drivers_driverLap_strategy']
            drivers_analyzed = data.get('drivers_analyzed', list(all_drivers_data.keys()))
            print(f"[driverLap_DATA] 舊格式：找到 {len(drivers_analyzed)} 個車手")
        elif 'driverLap_timing_corrected' in data:
            # 舊格式 v1
            all_drivers_data = data['driverLap_timing_corrected']
            drivers_analyzed = data.get('drivers_analyzed', list(all_drivers_data.keys()))
            print(f"[driverLap_DATA] 舊格式：找到 {len(drivers_analyzed)} 個車手")
        else:
            all_drivers_data = {}
            drivers_analyzed = []
            print(f"[driverLap_DATA] 警告：未找到支援的數據格式")
        
        processed_data['drivers_analyzed'] = drivers_analyzed
        processed_data['driverLap_analysis'] = all_drivers_data
        
        print(f"[driverLap_DATA] 處理完成，車手數量: {len(all_drivers_data)}")
        if all_drivers_data and len(all_drivers_data) > 0:
            first_driver = list(all_drivers_data.keys())[0]
            driver_data = all_drivers_data[first_driver]
            if isinstance(driver_data, dict):
                stint_count = len(driver_data.get('stint_analysis', []))
                print(f"[driverLap_DATA] 示例車手 {first_driver} 有 {stint_count} 個 Stint")
        
        return processed_data
    
    def _convert_to_stint_format(self, all_drivers_data: Dict) -> Dict:
        """將 CLI -f26 的數據格式轉換為圖表組件需要的 Stint 格式"""
        stint_analysis = {}
        
        for driver, driver_data in all_drivers_data.items():
            driver_stints = []
            
            # 從輪胎使用情況重建 Stint
            driverLap_usage = driver_data.get('driverLap_usage_by_lap', {})
            pit_stops = driver_data.get('pit_stops', {}).get('pit_stop_details', [])
            
            if driverLap_usage:
                # 按圈數排序
                sorted_laps = sorted([int(lap) for lap in driverLap_usage.keys()])
                
                current_stint = None
                stint_number = 1
                
                for lap in sorted_laps:
                    lap_data = driverLap_usage[str(lap)]
                    compound = lap_data.get('compound', 'UNKNOWN')
                    
                    # 檢查是否開始新的 Stint
                    if current_stint is None or current_stint['compound'] != compound:
                        # 結束上一個 Stint
                        if current_stint:
                            current_stint['end_lap'] = lap - 1
                            driver_stints.append(current_stint)
                        
                        # 開始新的 Stint
                        current_stint = {
                            'stint_number': stint_number,
                            'start_lap': lap,
                            'end_lap': lap,  # 暫時設定，稍後更新
                            'compound': compound,
                            'fastest_lap': lap,
                            'fastest_time': lap_data.get('lap_time', 0),
                            'avg_time': 0
                        }
                        stint_number += 1
                    else:
                        # 更新現有 Stint
                        current_stint['end_lap'] = lap
                        # 更新最快圈速
                        if lap_data.get('lap_time', float('inf')) < current_stint['fastest_time']:
                            current_stint['fastest_lap'] = lap
                            current_stint['fastest_time'] = lap_data.get('lap_time', 0)
                
                # 添加最後一個 Stint
                if current_stint:
                    driver_stints.append(current_stint)
            
            stint_analysis[driver] = {
                'stints': driver_stints,
                'pit_stops': pit_stops,
                'driverLap_performance': driver_data.get('driverLap_performance', {})
            }
        
        return stint_analysis
    
    def load_from_parameters(self, **kwargs):
        """從參數載入數據（透過通用載入器）"""
        try:
            print(f"[F28_DATA] 從參數載入數據: {kwargs}")
            
            if hasattr(self.universal_loader, 'load_from_parameters'):
                self.universal_loader.load_from_parameters(**kwargs)
            else:
                # 嘗試直接載入 JSON 文件
                year = kwargs.get('year')
                race = kwargs.get('race') 
                session = kwargs.get('session', 'R')
                driver = kwargs.get('driver', 'all_drivers')
                
                # 構建 JSON 文件路徑 - Function 28 格式
                json_filename = f"detailed_laptime_analysis_{year}_{race}_{session}_{driver}.json"
                json_path = os.path.join("json", json_filename)
                
                if os.path.exists(json_path):
                    self.load_from_json(json_path)
                else:
                    print(f"[F28_DATA] JSON 文件不存在: {json_path}")
                    self.load_error.emit(f"找不到詳細圈速分析數據文件: {json_filename}")
                    
        except Exception as e:
            print(f"[F28_DATA] 參數載入錯誤: {e}")
            self.load_error.emit(f"參數載入錯誤: {str(e)}")
    
    def load_from_json(self, json_path: str):
        """從 JSON 文件載入數據"""
        try:
            print(f"[F28_DATA] 載入 JSON 文件: {json_path}")
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 處理數據並發射信號
            processed_data = self._process_detailed_laptime_data(data)
            self.data_loaded.emit(processed_data)
            
        except Exception as e:
            print(f"[F28_DATA] JSON 載入錯誤: {e}")
            self.load_error.emit(f"JSON 載入錯誤: {str(e)}")
    
    def _extract_driverLap_weather_data(self, weather_data: Dict) -> Dict:
        """提取降雨天氣數據"""
        driverLap_data = {
            'driverLapfall': weather_data.get('driverLapfall', False),
            'humidity': weather_data.get('Humidity', 0),
            'air_temp': weather_data.get('AirTemp', 0),
            'track_temp': weather_data.get('TrackTemp', 0),
            'wind_speed': weather_data.get('WindSpeed', 0),
            'wind_direction': weather_data.get('WindDirection', 0)
        }
        return driverLap_data
    
    def _extract_track_conditions(self, track_status: Dict) -> Dict:
        """提取賽道狀況數據"""
        conditions = {
            'dry_sessions': [],
            'wet_sessions': [],
            'mixed_sessions': [],
            'safety_car_periods': []
        }
        
        # 這裡可以根據實際數據結構進行調整
        if isinstance(track_status, dict):
            conditions.update(track_status)
        
        return conditions
    
    def _analyze_driverLap_lap_performance(self, lap_times: Dict) -> Dict:
        """分析降雨對圈速的影響"""
        performance_analysis = {
            'wet_lap_times': [],
            'dry_lap_times': [],
            'performance_difference': {},
            'adaptation_analysis': {}
        }
        
        # 這裡可以添加更詳細的圈速分析邏輯
        return performance_analysis
    
    def _analyze_wet_driverLap_strategy(self, driverLap_data: Dict) -> Dict:
        """分析濕地輪胎策略"""
        driverLap_analysis = {
            'compound_usage': {},
            'pit_stop_timing': [],
            'driverLap_performance': {},
            'strategy_effectiveness': {}
        }
        
        # 這裡可以添加更詳細的輪胎策略分析邏輯
        return driverLap_analysis
    
    def load_driverLap_analysis_data(self, year: int, race: str, session: str = 'R') -> bool:
        """
        載入降雨分析數據
        
        Args:
            year: 年份
            race: 比賽名稱
            session: 節次 (R=正賽, Q=排位賽等)
            
        Returns:
            bool: 是否成功開始載入
        """
        try:
            self.status_changed.emit("開始載入降雨分析數據...")
            
            # 使用通用載入器載入數據
            if hasattr(self.universal_loader, 'load_data'):
                return self.universal_loader.load_data(year, race, session)
            else:
                # 如果沒有 load_data 方法，嘗試其他方法
                self.load_error.emit("通用載入器沒有 load_data 方法")
                return False
                
        except Exception as e:
            self.load_error.emit(f"載入降雨分析數據失敗: {str(e)}")
            return False
    
    def get_available_analyses(self) -> List[str]:
        """獲取可用的詳細圈速分析類型"""
        return self.analysis_config['detailed_laptime']['analysis_types']
    
    def get_required_data(self) -> List[str]:
        """獲取必需的數據類型"""
        return self.analysis_config['detailed_laptime']['required_data']
    
    def is_data_complete(self, data: Dict) -> bool:
        """檢查數據是否完整"""
        required_data = self.get_required_data()
        return all(key in data for key in required_data)


def create_driverLap_data_loader(parent=None) -> driverLapDataLoader:
    """
    工廠函數：創建詳細圈速分析數據載入器實例 (Function 28)
    
    Args:
        parent: 父對象
        
    Returns:
        driverLapDataLoader: 詳細圈速分析數據載入器實例
    """
    return driverLapDataLoader(parent)


if __name__ == "__main__":
    """測試用例"""
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 創建載入器實例
    loader = create_driverLap_data_loader()
    
    # 連接測試信號
    def on_data_loaded(data):
        print("數據載入完成:")
        print(f"  - 元數據: {data.get('metadata', {})}")
        print(f"  - 詳細圈速分析: {list(data.get('detailed_laptime_analysis', {}).keys())}")
    
    def on_error(error):
        print(f"載入錯誤: {error}")
    
    def on_status(status):
        print(f"狀態: {status}")
    
    loader.data_loaded.connect(on_data_loaded)
    loader.load_error.connect(on_error)
    loader.status_changed.connect(on_status)
    
    # 測試載入 JSON 文件 - 使用 CLI -f28 生成的數據
    json_path = "json/detailed_laptime_analysis_2025_Japan_R_all_drivers.json"
    if os.path.exists(json_path):
        print(f"測試載入 JSON 文件: {json_path}")
        loader.load_from_json(json_path)
    else:
        print("找不到測試 JSON 文件，嘗試透過參數載入...")
        # 測試透過參數載入生成數據
        loader.load_from_parameters(year=2025, race='Japan', session='R', driver='all_drivers')
    
    print("詳細圈速分析數據載入器測試完成")
