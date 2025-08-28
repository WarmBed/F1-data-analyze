"""
賽道數據模型
Track Data Model

負責載入、驗證和管理賽道 JSON 數據
"""

import json
import logging
from typing import Dict, List, Optional, Tuple


class TrackDataModel:
    """賽道數據模型類別"""
    
    def __init__(self, track_data: Optional[Dict] = None):
        """
        初始化賽道數據模型
        
        Args:
            track_data: 賽道 JSON 數據字典
        """
        self.track_data = track_data or {}
        self.logger = logging.getLogger(__name__)
        
    def load_json_data(self, json_file_path: str) -> bool:
        """
        從 JSON 文件載入賽道數據
        
        Args:
            json_file_path: JSON 文件路徑
            
        Returns:
            bool: 載入成功返回 True，失敗返回 False
        """
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                self.track_data = json.load(file)
            
            self.logger.info(f"成功載入賽道數據: {json_file_path}")
            return self.validate_data()
            
        except FileNotFoundError:
            self.logger.error(f"找不到 JSON 文件: {json_file_path}")
            return False
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON 解析錯誤: {e}")
            return False
        except Exception as e:
            self.logger.error(f"載入數據時發生錯誤: {e}")
            return False
    
    def validate_data(self) -> bool:
        """
        驗證賽道數據的完整性
        
        Returns:
            bool: 數據有效返回 True，無效返回 False
        """
        if not self.track_data:
            self.logger.warning("賽道數據為空")
            return False
        
        # 檢查必要欄位
        required_fields = [
            'analysis_type',
            'session_info',
            'position_analysis',
            'detailed_position_records'
        ]
        
        for field in required_fields:
            if field not in self.track_data:
                self.logger.error(f"缺少必要欄位: {field}")
                return False
        
        # 檢查位置記錄
        positions = self.track_data.get('detailed_position_records', [])
        if not positions:
            self.logger.error("沒有位置記錄數據")
            return False
        
        # 檢查第一個位置記錄的格式
        first_position = positions[0]
        required_position_fields = ['point_index', 'distance_m', 'position_x', 'position_y']
        
        for field in required_position_fields:
            if field not in first_position:
                self.logger.error(f"位置記錄缺少欄位: {field}")
                return False
        
        self.logger.info("賽道數據驗證通過")
        return True
    
    def get_track_bounds(self) -> Tuple[float, float, float, float]:
        """
        獲取賽道邊界
        
        Returns:
            Tuple: (x_min, x_max, y_min, y_max)
        """
        bounds = self.track_data.get('position_analysis', {}).get('track_bounds', {})
        return (
            bounds.get('x_min', 0.0),
            bounds.get('x_max', 0.0),
            bounds.get('y_min', 0.0),
            bounds.get('y_max', 0.0)
        )
    
    def get_position_records(self) -> List[Dict]:
        """
        獲取位置記錄列表
        
        Returns:
            List[Dict]: 位置記錄列表
        """
        return self.track_data.get('detailed_position_records', [])
    
    def get_session_info(self) -> Dict:
        """
        獲取賽段信息
        
        Returns:
            Dict: 賽段信息字典
        """
        return self.track_data.get('session_info', {})
    
    def get_race_name(self) -> str:
        """
        獲取賽事名稱
        
        Returns:
            str: 賽事名稱
        """
        session_info = self.get_session_info()
        return session_info.get('race', 'Unknown Race')
    
    def get_origin_point(self) -> Optional[Dict]:
        """
        獲取原點 (第一個位置記錄)
        
        Returns:
            Optional[Dict]: 原點數據，如果沒有數據則返回 None
        """
        positions = self.get_position_records()
        return positions[0] if positions else None
    
    def get_coordinates(self) -> Tuple[List[float], List[float]]:
        """
        獲取所有座標點
        
        Returns:
            Tuple: (x_coordinates, y_coordinates)
        """
        positions = self.get_position_records()
        x_coords = [pos['position_x'] for pos in positions]
        y_coords = [pos['position_y'] for pos in positions]
        return x_coords, y_coords
    
    def get_total_distance(self) -> float:
        """
        獲取總距離
        
        Returns:
            float: 總距離 (米)
        """
        analysis = self.track_data.get('position_analysis', {})
        return analysis.get('distance_covered_m', 0.0)
    
    def get_total_points(self) -> int:
        """
        獲取總位置點數
        
        Returns:
            int: 位置點總數
        """
        analysis = self.track_data.get('position_analysis', {})
        return analysis.get('total_position_records', 0)


# 創建子模組 __init__.py
