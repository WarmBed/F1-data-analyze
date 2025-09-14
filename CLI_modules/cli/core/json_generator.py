#!/usr/bin/env python3
"""
F1 Analysis Universal JSON Generator
F1 分析通用 JSON 生成器

提供統一的 JSON 格式化、清理和輸出功能
確保所有分析模組使用一致的 JSON 格式和標準

作者: F1 Analysis Team
版本: 1.0
"""

import os
import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Any, Union, Optional
import pandas as pd
import numpy as np


class F1AnalysisJSONGenerator:
    """F1 分析通用 JSON 生成器"""
    
    def __init__(self, output_dir: str = "json"):
        """
        初始化 JSON 生成器
        
        Args:
            output_dir: JSON 輸出目錄
        """
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
    
    def clean_for_json(self, obj: Any) -> Any:
        """
        清理數據使其可以序列化為 JSON
        處理 NumPy、Pandas、datetime 等特殊類型
        
        Args:
            obj: 要清理的對象
            
        Returns:
            可序列化的對象
        """
        if obj is None:
            return None
        elif isinstance(obj, bool):
            return bool(obj)
        elif isinstance(obj, (str, int, float)):
            return obj
        elif isinstance(obj, (list, tuple)):
            return [self.clean_for_json(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self.clean_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, timedelta):
            return str(obj)
        elif hasattr(obj, '__module__') and 'numpy' in str(obj.__module__):
            # 處理 NumPy 類型
            if hasattr(obj, 'item'):
                return obj.item()
            elif hasattr(obj, 'tolist'):
                return obj.tolist()
            else:
                return float(obj) if hasattr(obj, '__float__') else str(obj)
        elif hasattr(obj, '__module__') and 'pandas' in str(obj.__module__):
            # 處理 Pandas 類型
            if hasattr(obj, 'to_dict'):
                return self.clean_for_json(obj.to_dict())
            elif hasattr(obj, 'tolist'):
                return obj.tolist()
            else:
                return str(obj)
        else:
            # 其他類型轉為字符串
            return str(obj)
    
    def generate_standard_metadata(self, analysis_type: str, function_id: str, 
                                 session_info: Dict = None, **kwargs) -> Dict[str, Any]:
        """
        生成標準元數據
        
        Args:
            analysis_type: 分析類型
            function_id: 功能編號
            session_info: 賽事信息
            **kwargs: 其他元數據
            
        Returns:
            標準元數據字典
        """
        metadata = {
            "analysis_type": analysis_type,
            "function_id": function_id,
            "generated_at": datetime.now().isoformat(),
            "generator_version": "1.0",
            "format_version": "F1T_JSON_v1.0"
        }
        
        # 添加賽事信息
        if session_info:
            metadata.update({
                "year": session_info.get('year'),
                "race": session_info.get('race', session_info.get('event_name')),
                "race_short": session_info.get('race_short', session_info.get('race')),
                "session": session_info.get('session', session_info.get('session_name')),
                "session_type": session_info.get('session_type')
            })
        
        # 添加額外元數據
        metadata.update(kwargs)
        
        return self.clean_for_json(metadata)
    
    def generate_filename(self, analysis_type: str, session_info: Dict = None, 
                         driver: str = None, suffix: str = None) -> str:
        """
        生成標準 JSON 檔案名稱
        
        Args:
            analysis_type: 分析類型
            session_info: 賽事信息
            driver: 車手代碼（可選）
            suffix: 額外後綴（可選）
            
        Returns:
            檔案名稱
        """
        parts = [analysis_type]
        
        if session_info:
            year = session_info.get('year', '2025')
            race = session_info.get('race_short', session_info.get('race', 'Unknown'))
            session = session_info.get('session_type', 'R')
            
            parts.extend([str(year), race, session])
        
        if driver:
            parts.append(driver)
        
        if suffix:
            parts.append(suffix)
        
        filename = "_".join(parts) + ".json"
        return filename
    
    def save_analysis_result(self, data: Dict[str, Any], analysis_type: str, 
                           function_id: str, session_info: Dict = None,
                           driver: str = None, suffix: str = None,
                           include_metadata: bool = True) -> Dict[str, str]:
        """
        保存分析結果為 JSON 檔案
        
        Args:
            data: 要保存的數據
            analysis_type: 分析類型
            function_id: 功能編號
            session_info: 賽事信息
            driver: 車手代碼（可選）
            suffix: 檔案名後綴（可選）
            include_metadata: 是否包含元數據
            
        Returns:
            保存信息字典
        """
        try:
            # 清理數據
            clean_data = self.clean_for_json(data)
            
            # 添加標準元數據
            if include_metadata:
                if not isinstance(clean_data, dict):
                    clean_data = {"data": clean_data}
                
                if "metadata" not in clean_data:
                    clean_data["metadata"] = self.generate_standard_metadata(
                        analysis_type, function_id, session_info
                    )
            
            # 生成檔案名
            filename = self.generate_filename(analysis_type, session_info, driver, suffix)
            filepath = os.path.join(self.output_dir, filename)
            
            # 保存檔案
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(clean_data, f, ensure_ascii=False, indent=2)
            
            file_size = os.path.getsize(filepath)
            
            print(f"💾 JSON 已保存: {filepath} ({file_size:,} bytes)")
            
            return {
                "success": True,
                "filename": filename,
                "filepath": filepath,
                "size": file_size
            }
            
        except Exception as e:
            error_msg = f"JSON 保存失敗: {e}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    
    def save_raw_data(self, data: Dict[str, Any], analysis_type: str, 
                     session_info: Dict = None) -> Dict[str, str]:
        """
        保存原始數據（Raw Data）
        
        Args:
            data: 原始數據
            analysis_type: 分析類型
            session_info: 賽事信息
            
        Returns:
            保存信息字典
        """
        try:
            # 構建原始數據格式
            raw_data = {
                "data_type": "raw_data",
                "analysis_type": analysis_type,
                "timestamp": datetime.now().strftime("%Y%m%d"),
                "session_info": self.clean_for_json(session_info) if session_info else {},
                "raw_data": self.clean_for_json(data)
            }
            
            # 生成檔案名
            if session_info:
                year = session_info.get('year', '2025')
                race = session_info.get('race', 'Unknown')
                filename = f"raw_data_{analysis_type}_{year}_{race}.json"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"raw_data_{analysis_type}_{timestamp}.json"
            
            filepath = os.path.join(self.output_dir, filename)
            
            # 保存檔案
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, ensure_ascii=False, indent=2)
            
            file_size = os.path.getsize(filepath)
            
            print(f"💾 Raw Data 已保存: {filepath} ({file_size:,} bytes)")
            
            return {
                "success": True,
                "filename": filename,
                "filepath": filepath,
                "size": file_size
            }
            
        except Exception as e:
            error_msg = f"Raw Data 保存失敗: {e}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    
    def load_analysis_result(self, filepath: str) -> Dict[str, Any]:
        """
        載入分析結果 JSON 檔案
        
        Args:
            filepath: JSON 檔案路徑
            
        Returns:
            載入的數據
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"✅ JSON 載入成功: {filepath}")
            return data
            
        except Exception as e:
            print(f"❌ JSON 載入失敗: {e}")
            return {}
    
    def validate_json_structure(self, data: Dict[str, Any], 
                              required_fields: List[str] = None) -> bool:
        """
        驗證 JSON 結構
        
        Args:
            data: 要驗證的數據
            required_fields: 必需的欄位
            
        Returns:
            驗證結果
        """
        try:
            if not isinstance(data, dict):
                print("❌ JSON 結構驗證失敗: 根節點必須是字典")
                return False
            
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    print(f"❌ JSON 結構驗證失敗: 缺少必需欄位 {missing_fields}")
                    return False
            
            # 驗證元數據（如果存在）
            if "metadata" in data:
                metadata = data["metadata"]
                required_metadata = ["analysis_type", "generated_at", "format_version"]
                missing_metadata = [field for field in required_metadata if field not in metadata]
                if missing_metadata:
                    print(f"⚠️ 元數據不完整: 缺少 {missing_metadata}")
            
            print("✅ JSON 結構驗證通過")
            return True
            
        except Exception as e:
            print(f"❌ JSON 結構驗證錯誤: {e}")
            return False


class F1SessionInfoExtractor:
    """F1 賽事信息提取器"""
    
    @staticmethod
    def extract_from_data_loader(data_loader) -> Dict[str, Any]:
        """
        從數據載入器提取賽事信息
        
        Args:
            data_loader: 數據載入器
            
        Returns:
            賽事信息字典
        """
        try:
            session_info = {
                'year': getattr(data_loader, 'year', 2025),
                'race': getattr(data_loader, 'race_name', 'Unknown'),
                'race_short': getattr(data_loader, 'race_name', 'Unknown'),
                'session_type': getattr(data_loader, 'session_type', 'R'),
                'session_name': 'Race' if getattr(data_loader, 'session_type', 'R') == 'R' else getattr(data_loader, 'session_type', 'R')
            }
            
            # 賽事全名映射
            race_full_name_mapping = {
                'Bahrain': 'Bahrain Grand Prix',
                'Saudi': 'Saudi Arabian Grand Prix', 
                'Australia': 'Australian Grand Prix',
                'Azerbaijan': 'Azerbaijan Grand Prix',
                'Miami': 'Miami Grand Prix',
                'Monaco': 'Monaco Grand Prix',
                'Spain': 'Spanish Grand Prix',
                'Canada': 'Canadian Grand Prix',
                'Austria': 'Austrian Grand Prix',
                'Britain': 'British Grand Prix',
                'Great Britain': 'British Grand Prix',
                'Hungary': 'Hungarian Grand Prix',
                'Belgium': 'Belgian Grand Prix',
                'Netherlands': 'Dutch Grand Prix',
                'Italy': 'Italian Grand Prix',
                'Singapore': 'Singapore Grand Prix',
                'Japan': 'Japanese Grand Prix',
                'Qatar': 'Qatar Grand Prix',
                'United States': 'United States Grand Prix',
                'Mexico': 'Mexico City Grand Prix',
                'Brazil': 'Brazilian Grand Prix',
                'Las Vegas': 'Las Vegas Grand Prix',
                'Abu Dhabi': 'Abu Dhabi Grand Prix'
            }
            
            # 設定完整賽事名稱
            race_name = session_info['race']
            session_info['event_name'] = race_full_name_mapping.get(race_name, f"{race_name} Grand Prix")
            
            return session_info
            
        except Exception as e:
            print(f"[WARNING] 賽事信息提取失敗: {e}")
            return {
                'year': 2025,
                'race': 'Unknown',
                'race_short': 'Unknown',
                'event_name': 'Unknown Grand Prix',
                'session_type': 'R',
                'session_name': 'Race'
            }


# 便利函數
def create_json_generator(output_dir: str = "json") -> F1AnalysisJSONGenerator:
    """創建 JSON 生成器實例"""
    return F1AnalysisJSONGenerator(output_dir)

def save_f1_analysis_json(data: Dict[str, Any], analysis_type: str, function_id: str,
                         data_loader=None, **kwargs) -> Dict[str, str]:
    """
    便利函數：保存 F1 分析結果為 JSON
    
    Args:
        data: 分析數據
        analysis_type: 分析類型
        function_id: 功能編號
        data_loader: 數據載入器（用於提取賽事信息）
        **kwargs: 其他參數
        
    Returns:
        保存結果
    """
    generator = create_json_generator()
    
    # 提取賽事信息
    session_info = None
    if data_loader:
        session_info = F1SessionInfoExtractor.extract_from_data_loader(data_loader)
    
    return generator.save_analysis_result(
        data, analysis_type, function_id, session_info, **kwargs
    )

def clean_data_for_json(data: Any) -> Any:
    """便利函數：清理數據使其可序列化"""
    generator = F1AnalysisJSONGenerator()
    return generator.clean_for_json(data)


if __name__ == "__main__":
    # 測試用途
    print("F1 Analysis Universal JSON Generator")
    print("F1 分析通用 JSON 生成器")
    
    # 測試數據清理
    test_data = {
        "test": "example",
        "number": 123,
        "float": 45.67,
        "datetime": datetime.now(),
        "numpy_array": np.array([1, 2, 3]) if 'numpy' in globals() else [1, 2, 3]
    }
    
    generator = create_json_generator()
    cleaned = generator.clean_for_json(test_data)
    print(f"清理後的數據: {cleaned}")
