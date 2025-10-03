#!/usr/bin/env python3
"""
降雨分析數據載入器
基於 UniversalDataLoader 的降雨分析專門接口
"""

import sys
import os
import json
from typing import Dict, List, Optional, Any
from PyQt5.QtCore import QObject, pyqtSignal

# 添加項目根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from modules.gui.base import UniversalDataLoader

class RainUniversalDataLoader(UniversalDataLoader):
    """降雨分析專門的通用數據載入器實現"""
    
    def __init__(self):
        super().__init__('rain')
    
    def _validate_load_parameters(self, params: Dict[str, Any]) -> bool:
        """驗證載入參數"""
        required_params = ['year', 'race']
        return all(param in params for param in required_params)
    
    def _build_filename_patterns(self, **kwargs) -> List[str]:
        """構建降雨分析檔案名稱搜尋模式"""
        year = kwargs.get('year', '*')
        race = kwargs.get('race', '*')
        session = kwargs.get('session', 'R')
        
        patterns = [
            f"enhanced_rain_analysis_{year}_{race}_{session}.json",
            f"rain_analysis_{year}_{race}_{session}.json",
            f"weather_data_{year}_{race}_{session}.json"
        ]
        return patterns
    
    def _generate_data_via_cli(self, **kwargs) -> bool:
        """透過 CLI 工具生成降雨數據"""
        # 這裡可以調用 CLI 工具生成降雨分析數據
        # 暫時返回 False，表示不支援 CLI 生成
        return False
    
    def _validate_data_format(self, raw_data: Any) -> bool:
        """驗證降雨數據格式"""
        if not isinstance(raw_data, dict):
            return False
        
        # 檢查必要的降雨數據欄位
        required_fields = ['weather_data', 'session_info']
        return any(field in raw_data for field in required_fields)
    
    def _process_data(self, raw_data: Any) -> Dict[str, Any]:
        """處理降雨數據為標準格式"""
        if isinstance(raw_data, dict):
            return {
                'metadata': raw_data.get('metadata', {}),
                'session_info': raw_data.get('session_info', {}),
                'weather_data': raw_data.get('weather_data', {}),
                'rain_analysis': raw_data.get('rain_analysis', {}),
                'raw_data': raw_data
            }
        return {'raw_data': raw_data}

class RainDataLoader(QObject):
    """降雨分析專門數據載入器"""
    
    # 信號定義
    data_loaded = pyqtSignal(dict)  # 數據載入完成
    load_error = pyqtSignal(str)    # 載入錯誤
    status_changed = pyqtSignal(str) # 狀態變化
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 創建專門的通用數據載入器實例
        self.universal_loader = RainUniversalDataLoader()
        
        # 連接通用載入器的信號
        self._connect_universal_loader_signals()
        
        # 降雨分析特定配置
        self.analysis_config = {
            'rain': {
                'required_data': ['weather', 'lap_times', 'telemetry'],
                'optional_data': ['track_status', 'safety_car'],
                'analysis_types': ['rain_impact', 'wet_performance', 'tire_strategy']
            }
        }
    
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
            print(f"📥 [RAIN_DATA] 接收到通用載入器數據")
            print(f"   - 數據類型: {type(data)}")
            print(f"   - 數據鍵: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            # 對降雨分析數據進行後處理
            processed_data = self._process_rain_data(data)
            
            print(f"📤 [RAIN_DATA] 發射 data_loaded 信號")
            print(f"   - 處理後數據類型: {type(processed_data)}")
            print(f"   - 處理後數據鍵: {list(processed_data.keys()) if isinstance(processed_data, dict) else 'Not a dict'}")
            
            self.data_loaded.emit(processed_data)
        except Exception as e:
            print(f"❌ [RAIN_DATA] 數據後處理錯誤: {str(e)}")
            import traceback
            traceback.print_exc()
            self.load_error.emit(f"數據後處理錯誤: {str(e)}")
    
    def _on_universal_load_error(self, error_message):
        """處理通用載入器的錯誤"""
        self.load_error.emit(f"降雨數據載入錯誤: {error_message}")
    
    def _on_universal_status_changed(self, status):
        """處理通用載入器的狀態變化"""
        self.status_changed.emit(f"降雨分析 - {status}")
    
    def _process_rain_data(self, data: Dict) -> Dict:
        """
        處理降雨分析特定的數據格式
        
        Args:
            data: 原始數據字典
            
        Returns:
            Dict: 處理後的降雨分析數據
        """
        processed_data = {
            'metadata': data.get('metadata', {}),
            'session_info': data.get('session_info', {}),
            'rain_analysis': {},
            'raw_data': data
        }
        
        # 提取降雨相關信息
        if 'weather_data' in data:
            processed_data['rain_analysis']['weather'] = self._extract_rain_weather_data(data['weather_data'])
        
        if 'track_status' in data:
            processed_data['rain_analysis']['track_conditions'] = self._extract_track_conditions(data['track_status'])
        
        if 'lap_times' in data:
            processed_data['rain_analysis']['lap_performance'] = self._analyze_rain_lap_performance(data['lap_times'])
        
        if 'tire_data' in data:
            processed_data['rain_analysis']['tire_strategy'] = self._analyze_wet_tire_strategy(data['tire_data'])
        
        return processed_data
    
    def _extract_rain_weather_data(self, weather_data: Dict) -> Dict:
        """提取降雨天氣數據"""
        rain_data = {
            'rainfall': weather_data.get('Rainfall', False),
            'humidity': weather_data.get('Humidity', 0),
            'air_temp': weather_data.get('AirTemp', 0),
            'track_temp': weather_data.get('TrackTemp', 0),
            'wind_speed': weather_data.get('WindSpeed', 0),
            'wind_direction': weather_data.get('WindDirection', 0)
        }
        return rain_data
    
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
    
    def _analyze_rain_lap_performance(self, lap_times: Dict) -> Dict:
        """分析降雨對圈速的影響"""
        performance_analysis = {
            'wet_lap_times': [],
            'dry_lap_times': [],
            'performance_difference': {},
            'adaptation_analysis': {}
        }
        
        # 這裡可以添加更詳細的圈速分析邏輯
        return performance_analysis
    
    def _analyze_wet_tire_strategy(self, tire_data: Dict) -> Dict:
        """分析濕地輪胎策略"""
        tire_analysis = {
            'compound_usage': {},
            'pit_stop_timing': [],
            'tire_performance': {},
            'strategy_effectiveness': {}
        }
        
        # 這裡可以添加更詳細的輪胎策略分析邏輯
        return tire_analysis
    
    def load_rain_analysis_data(self, year: int, race: str, session: str = 'R') -> bool:
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
    
    def load_from_json(self, json_file_path: str) -> bool:
        """
        從 JSON 文件載入降雨分析數據
        
        Args:
            json_file_path: JSON 文件路徑
            
        Returns:
            bool: 是否成功載入
        """
        try:
            self.status_changed.emit(f"從 JSON 文件載入數據: {json_file_path}")
            
            with open(json_file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # 處理並發射數據
            processed_data = self._process_rain_data(json_data)
            self.data_loaded.emit(processed_data)
            
            self.status_changed.emit("JSON 數據載入完成")
            return True
            
        except FileNotFoundError:
            self.load_error.emit(f"找不到 JSON 文件: {json_file_path}")
            return False
        except json.JSONDecodeError as e:
            self.load_error.emit(f"JSON 文件格式錯誤: {str(e)}")
            return False
        except Exception as e:
            self.load_error.emit(f"載入 JSON 文件失敗: {str(e)}")
            return False
    
    def get_available_analyses(self) -> List[str]:
        """獲取可用的降雨分析類型"""
        return self.analysis_config['rain']['analysis_types']
    
    def get_required_data(self) -> List[str]:
        """獲取必需的數據類型"""
        return self.analysis_config['rain']['required_data']
    
    def is_data_complete(self, data: Dict) -> bool:
        """檢查數據是否完整"""
        required_data = self.get_required_data()
        return all(key in data for key in required_data)


def create_rain_data_loader(parent=None) -> RainDataLoader:
    """
    工廠函數：創建降雨數據載入器實例
    
    Args:
        parent: 父對象
        
    Returns:
        RainDataLoader: 降雨數據載入器實例
    """
    return RainDataLoader(parent)


if __name__ == "__main__":
    """測試用例"""
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 創建載入器實例
    loader = create_rain_data_loader()
    
    # 連接測試信號
    def on_data_loaded(data):
        print("數據載入完成:")
        print(f"  - 元數據: {data.get('metadata', {})}")
        print(f"  - 降雨分析: {list(data.get('rain_analysis', {}).keys())}")
    
    def on_error(error):
        print(f"載入錯誤: {error}")
    
    def on_status(status):
        print(f"狀態: {status}")
    
    loader.data_loaded.connect(on_data_loaded)
    loader.load_error.connect(on_error)
    loader.status_changed.connect(on_status)
    
    # 測試載入 JSON 文件
    json_path = "json/enhanced_rain_analysis_2025_Belgium_R.json"
    if os.path.exists(json_path):
        print(f"測試載入 JSON 文件: {json_path}")
        loader.load_from_json(json_path)
    else:
        print("找不到測試 JSON 文件")
    
    print("降雨數據載入器測試完成")
