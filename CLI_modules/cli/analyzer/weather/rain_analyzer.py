#!/usr/bin/env python3
"""
增強版降雨分析模組
Enhanced Rain Analyzer Module
基於FastF1直接數據，輸出簡化JSON格式
"""

import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional

# 導入現有的基礎模組
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'core'))

from analysis_module_manager import AnalysisModuleBase
from compatible_data_loader import CompatibleF1DataLoader

class EnhancedRainAnalyzer(AnalysisModuleBase):
    """增強版降雨分析器 - 簡化版只顯示有雨/無雨"""
    
    def __init__(self):
        super().__init__(
            name="降雨狀況分析",
            description="基於FastF1數據的圈數vs天氣分析，簡化降雨為有雨/無雨狀態",
            module_id=1
        )
        self.data_loader = CompatibleF1DataLoader()
    
    def validate_parameters(self, **kwargs) -> bool:
        """驗證參數"""
        required = ['year', 'race', 'session']
        return all(param in kwargs for param in required)
    
    def analyze(self, year: int, race: str, session: str = 'R', **kwargs) -> Dict[str, Any]:
        """
        執行降雨狀況分析 (簡化版：有雨/無雨)
        
        Args:
            year: 年份 (如 2025)
            race: 比賽名稱 (如 'Japan')
            session: 賽段類型 (如 'R')
            
        Returns:
            Dict: 包含簡化JSON結構的分析結果
        """
        try:
            print(f"🌧️ 開始降雨狀況分析 (有雨/無雨): {year} {race} {session}")
            
            # 直接從已載入的數據載入器獲取天氣數據
            weather_data = None
            if hasattr(self.data_loader, 'weather_data') and self.data_loader.weather_data is not None:
                weather_data = self.data_loader.weather_data
            elif hasattr(self.data_loader, 'get_loaded_data'):
                # 嘗試從 get_loaded_data 獲取
                loaded_data = self.data_loader.get_loaded_data()
                if loaded_data and hasattr(loaded_data, 'weather'):
                    weather_data = loaded_data.weather
            
            # 如果還是沒有數據，返回錯誤
            if weather_data is None:
                return {
                    "success": False,
                    "error": "無法獲取天氣數據，請確保數據已正確載入",
                    "cache_used": False
                }
            if weather_data is None or weather_data.empty:
                return {
                    "success": False,
                    "error": "沒有可用的天氣數據",
                    "cache_used": True
                }
            
            print(f"✅ 成功載入 {len(weather_data)} 筆天氣數據")
            print(f"📋 可用欄位: {list(weather_data.columns)}")
            
            # 第3步：生成簡化降雨分析JSON
            enhanced_json = self._generate_enhanced_json(
                weather_data, year, race, session
            )
            
            # 第4步：保存JSON檔案
            json_filename = self._save_enhanced_json(enhanced_json, year, race, session)
            
            # 輸出降雨狀態總結 - 考慮比賽前降雨
            rain_laps = enhanced_json["summary"].get("rain_laps", 0)
            original_rain_points = enhanced_json["summary"].get("original_rain_points", 0)
            rain_timing = enhanced_json["summary"].get("rain_timing_analysis", {})
            
            if rain_laps > 0:
                rain_status = f"比賽中有降雨 ({rain_laps} 圈)"
            elif original_rain_points > 0:
                # 有原始降雨數據但沒有比賽中降雨
                before_race = rain_timing.get("rain_before_race", 0)
                if before_race > 0:
                    rain_status = f"比賽前有降雨 ({before_race} 個時間點)，比賽中無降雨"
                else:
                    rain_status = "其他時間有降雨，比賽中無降雨"
            else:
                rain_status = "無降雨"
                
            print(f"🎯 降雨結論: {year} {race} {session} - {rain_status}")
            
            return {
                "success": True,
                "data": enhanced_json,
                "json_file": json_filename,
                "cache_used": hasattr(self.data_loader, 'loaded_from_cache'),
                "data_points": len(weather_data),
                "analysis_type": "simplified_rain_analysis",
                "rain_status": rain_status,
                "race_rain_laps": rain_laps,
                "total_rain_points": original_rain_points
            }
            
        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "cache_used": False
            }
    
    def _generate_enhanced_json(self, weather_data: pd.DataFrame, 
                               year: int, race: str, session: str) -> Dict[str, Any]:
        """
        生成簡化版JSON結構 - 圈數對應時間、溫度、天氣、濕度、風速
        輸出格式: 圈數 -> {時間, 溫度, 天氣, 濕度, 風速}
        """
        
        # 檢查可用的FastF1欄位
        available_columns = list(weather_data.columns)
        print(f"📊 可用的天氣數據欄位: {available_columns}")
        
        # 獲取圈數數據來建立時間-圈數對應
        laps_data = self.data_loader.laps if hasattr(self.data_loader, 'laps') and self.data_loader.laps is not None else None
        
        # 基礎metadata - 簡化降雨分析版本
        enhanced_json = {
            "metadata": {
                "analysis_type": "Simplified Rain Status Analysis",
                "generated_at": datetime.now().isoformat(),
                "version": "4.0_rain_simplified",
                "year": year,
                "race_name": race,
                "session_type": session,
                "data_points": len(weather_data),
                "description": "圈數對應天氣的簡化降雨分析 - 只顯示有雨/無雨狀態"
            },
            "lap_weather_data": {}
        }
        
        # 建立圈數-天氣數據對應
        if laps_data is not None and not laps_data.empty and 'Time' in weather_data.columns:
            # 有圈數數據時，建立精確的時間對應
            enhanced_json["lap_weather_data"] = self._create_lap_weather_mapping(weather_data, laps_data)
            total_laps = len(enhanced_json["lap_weather_data"])
        else:
            # 沒有圈數數據時，使用序號模擬圈數
            print("⚠️ 沒有圈數數據，使用序號模擬圈數")
            enhanced_json["lap_weather_data"] = self._create_simulated_lap_mapping(weather_data)
            total_laps = len(enhanced_json["lap_weather_data"])
        
        # 添加統計摘要
        enhanced_json["summary"] = {
            "total_laps": total_laps,
            "weather_data_points": len(weather_data),
            "has_rain_data": 'Rainfall' in weather_data.columns,
            "has_temperature_data": 'AirTemp' in weather_data.columns or 'TrackTemp' in weather_data.columns,
            "has_humidity_data": 'Humidity' in weather_data.columns,
            "has_wind_data": 'WindSpeed' in weather_data.columns
        }
        
        # 計算降雨統計 - 直接從原始天氣數據計算，簡化為有雨/無雨
        if 'Rainfall' in weather_data.columns:
            # 直接計算原始數據中的降雨點數
            original_rain_points = weather_data['Rainfall'].sum()
            total_weather_points = len(weather_data)
            
            print(f"🌧️ 降雨統計: {original_rain_points}/{total_weather_points} 個天氣點有降雨")
            
            # 計算處理後的圈數數據中有多少圈有雨
            rain_laps_count = len([lap for lap in enhanced_json["lap_weather_data"].values() 
                                  if lap.get("weather", {}).get("rainfall", False)])
            
            # 使用處理後的圈數統計（確保與JSON輸出一致）
            enhanced_json["summary"]["rain_laps"] = rain_laps_count
            enhanced_json["summary"]["rain_percentage"] = round((rain_laps_count / total_laps * 100), 1) if total_laps > 0 else 0.0
            
            # 添加原始降雨數據統計供參考
            enhanced_json["summary"]["original_rain_points"] = int(original_rain_points)
            enhanced_json["summary"]["original_rain_percentage"] = round((original_rain_points / total_weather_points * 100), 1) if total_weather_points > 0 else 0.0
            
            # 添加降雨時間分析
            rain_timing = self._analyze_rain_timing(weather_data, laps_data)
            enhanced_json["summary"]["rain_timing_analysis"] = rain_timing
            
            # 輸出降雨時間分析結果
            if rain_timing.get("status") not in ["no_rain_data", "no_rain"]:
                print(f"⏰ 降雨時間分析:")
                print(f"   比賽前: {rain_timing.get('rain_before_race', 0)} 點 ({rain_timing.get('rain_distribution', {}).get('before_race_percentage', 0):.1f}%)")
                print(f"   比賽中: {rain_timing.get('rain_during_race', 0)} 點 ({rain_timing.get('rain_distribution', {}).get('during_race_percentage', 0):.1f}%)")
                print(f"   比賽後: {rain_timing.get('rain_after_race', 0)} 點 ({rain_timing.get('rain_distribution', {}).get('after_race_percentage', 0):.1f}%)")
        
        return enhanced_json
    
    def _create_lap_weather_mapping(self, weather_data: pd.DataFrame, laps_data: pd.DataFrame) -> Dict[str, Any]:
        """
        建立圈數-天氣數據的精確對應 (基於累積時間匹配)
        """
        lap_weather_map = {}
        
        try:
            # 檢查是否有有效的圈數和天氣時間數據
            if 'Time' in laps_data.columns and 'Time' in weather_data.columns:
                # 使用圈數的累積時間作為基準 (從比賽開始算起)
                race_start = laps_data['Time'].min() if 'Time' in laps_data.columns else None
                
                for i, (_, lap_row) in enumerate(laps_data.iterrows()):
                    lap_num = str(int(lap_row['LapNumber']))
                    lap_time = lap_row.get('Time')  # 改用累積時間而非單圈時間
                    
                    if pd.isna(lap_time):
                        continue
                    
                    # 找到最接近的天氣數據點 (使用累積時間)
                    closest_weather = self._find_closest_weather(weather_data, lap_time)
                    
                    if closest_weather is not None:
                        lap_weather_map[lap_num] = self._format_weather_data(closest_weather, lap_time)
            
            # 如果沒有成功映射任何數據，使用模擬方法
            if not lap_weather_map:
                print("⚠️ 時間匹配失敗，使用模擬圈數映射")
                return self._create_simulated_lap_mapping(weather_data)
                
        except Exception as e:
            print(f"⚠️ 圈數映射過程中發生錯誤: {e}")
            return self._create_simulated_lap_mapping(weather_data)
        
        return lap_weather_map
    
    def _analyze_rain_timing(self, weather_data: pd.DataFrame, laps_data: pd.DataFrame = None) -> Dict[str, Any]:
        """
        分析降雨時間分佈，區分比賽前、比賽中、比賽後的降雨
        """
        if 'Rainfall' not in weather_data.columns:
            return {"status": "no_rain_data"}
        
        rain_data = weather_data[weather_data['Rainfall'] == True]
        if len(rain_data) == 0:
            return {"status": "no_rain", "total_rain_points": 0}
        
        timing_analysis = {
            "total_rain_points": len(rain_data),
            "rain_start_time": str(rain_data['Time'].min()),
            "rain_end_time": str(rain_data['Time'].max()),
            "weather_data_start": str(weather_data['Time'].min()),
            "weather_data_end": str(weather_data['Time'].max())
        }
        
        # 如果有圈數數據，分析比賽時間內的降雨
        if laps_data is not None and 'Time' in laps_data.columns:
            valid_laps = laps_data.dropna(subset=['Time'])
            if len(valid_laps) > 0:
                race_start = valid_laps['Time'].min()
                race_end = valid_laps['Time'].max()
                
                # 分類降雨時間
                rain_before_race = rain_data[rain_data['Time'] < race_start]
                rain_during_race = rain_data[
                    (rain_data['Time'] >= race_start) & (rain_data['Time'] <= race_end)
                ]
                rain_after_race = rain_data[rain_data['Time'] > race_end]
                
                timing_analysis.update({
                    "race_start_time": str(race_start),
                    "race_end_time": str(race_end),
                    "rain_before_race": len(rain_before_race),
                    "rain_during_race": len(rain_during_race), 
                    "rain_after_race": len(rain_after_race),
                    "rain_distribution": {
                        "before_race_percentage": round(len(rain_before_race) / len(rain_data) * 100, 1),
                        "during_race_percentage": round(len(rain_during_race) / len(rain_data) * 100, 1),
                        "after_race_percentage": round(len(rain_after_race) / len(rain_data) * 100, 1)
                    }
                })
        
        return timing_analysis

    def _create_simulated_lap_mapping(self, weather_data: pd.DataFrame) -> Dict[str, Any]:
        """
        創建模擬的圈數-天氣對應 (當沒有圈數數據時)
        """
        lap_weather_map = {}
        
        # 將天氣數據按順序分配給圈數
        for i, (_, row) in enumerate(weather_data.iterrows()):
            lap_num = str(i + 1)
            lap_weather_map[lap_num] = self._format_weather_data(row)
        
        return lap_weather_map
    
    def _find_closest_weather(self, weather_data: pd.DataFrame, target_time) -> Optional[pd.Series]:
        """
        找到最接近指定時間的天氣數據
        """
        try:
            if 'Time' not in weather_data.columns:
                return None
            
            # 計算時間差並找到最小值 - 這裡可能很慢
            time_diffs = abs(weather_data['Time'] - target_time)
            closest_idx = time_diffs.idxmin()
            
            return weather_data.loc[closest_idx]
        except Exception as e:
            print(f"⚠️ 尋找最接近天氣數據時發生錯誤: {e}")
            return None
    
    def _format_weather_data(self, weather_row: pd.Series, lap_time=None) -> Dict[str, Any]:
        """
        格式化天氣數據為標準結構: 時間、溫度、天氣、濕度、風速
        """
        formatted_data = {}
        
        # 時間
        if lap_time is not None:
            formatted_data["time"] = str(lap_time)
        elif 'Time' in weather_row.index:
            formatted_data["time"] = str(weather_row['Time'])
        else:
            formatted_data["time"] = "N/A"
        
        # 溫度 (優先使用空氣溫度，其次賽道溫度)
        temperature = {}
        if 'AirTemp' in weather_row.index and not pd.isna(weather_row['AirTemp']):
            temperature["air_temp"] = float(weather_row['AirTemp'])
        if 'TrackTemp' in weather_row.index and not pd.isna(weather_row['TrackTemp']):
            temperature["track_temp"] = float(weather_row['TrackTemp'])
        formatted_data["temperature"] = temperature if temperature else "N/A"
        
        # 天氣 (降雨狀況)
        weather = {}
        if 'Rainfall' in weather_row.index:
            weather["rainfall"] = bool(weather_row['Rainfall'])
        if 'Pressure' in weather_row.index and not pd.isna(weather_row['Pressure']):
            weather["pressure"] = float(weather_row['Pressure'])
        formatted_data["weather"] = weather if weather else "N/A"
        
        # 濕度
        if 'Humidity' in weather_row.index and not pd.isna(weather_row['Humidity']):
            formatted_data["humidity"] = float(weather_row['Humidity'])
        else:
            formatted_data["humidity"] = "N/A"
        
        # 風速
        wind = {}
        if 'WindSpeed' in weather_row.index and not pd.isna(weather_row['WindSpeed']):
            wind["speed"] = float(weather_row['WindSpeed'])
        if 'WindDirection' in weather_row.index and not pd.isna(weather_row['WindDirection']):
            wind["direction"] = float(weather_row['WindDirection'])
        formatted_data["wind"] = wind if wind else "N/A"
        
        return formatted_data
    
    def _analyze_temperature_vs_lap(self, weather_data: pd.DataFrame, valid_fields: dict, laps_data=None) -> Dict[str, Any]:
        """分析溫度vs圈數 - 基於FastF1直接數據"""
        temp_analysis = {
            "description": "每圈溫度變化分析",
            "analysis_method": "fastest_lap_logic_adapted",
            "data_structure": "per_lap_weather_correlation"
        }
        
        # 取前3筆作為範例數據 (實際應該根據圈數對應)
        sample_data = []
        for i, (idx, row) in enumerate(weather_data.head(3).iterrows()):
            lap_record = {"lap_number": i + 1}
            
            if 'AirTemp' in valid_fields:
                lap_record["air_temperature"] = {
                    "value": float(row['AirTemp']),
                    "unit": "°C"
                }
            
            if 'TrackTemp' in valid_fields:
                lap_record["track_temperature"] = {
                    "value": float(row['TrackTemp']),
                    "unit": "°C"
                }
                
            sample_data.append(lap_record)
        
        temp_analysis["lap_temperature_data"] = sample_data
        
        # 統計數據
        stats = {}
        if 'AirTemp' in valid_fields:
            air_temps = weather_data['AirTemp'].dropna()
            stats["min_air_temp"] = {
                "value": float(air_temps.min()),
                "lap": 1  # 簡化，實際需要找到對應圈數
            }
            stats["max_air_temp"] = {
                "value": float(air_temps.max()),
                "lap": len(weather_data)  # 簡化
            }
            
        if 'TrackTemp' in valid_fields:
            track_temps = weather_data['TrackTemp'].dropna()
            stats["min_track_temp"] = {
                "value": float(track_temps.min()),
                "lap": 1
            }
            stats["max_track_temp"] = {
                "value": float(track_temps.max()),
                "lap": len(weather_data)
            }
            
        temp_analysis["temperature_statistics"] = stats
        return temp_analysis
    
    def _analyze_rain_vs_lap(self, weather_data: pd.DataFrame, valid_fields: dict, laps_data=None) -> Dict[str, Any]:
        """分析降雨vs圈數 - 基於FastF1直接數據"""
        rain_analysis = {
            "description": "每圈降雨狀況分析",
            "analysis_method": "fastest_lap_logic_adapted", 
            "data_structure": "per_lap_precipitation_tracking"
        }
        
        # 取前3筆作為範例數據
        sample_data = []
        for i, (idx, row) in enumerate(weather_data.head(3).iterrows()):
            lap_record = {
                "lap_number": i + 1,
                "rainfall": {
                    "value": bool(row['Rainfall']) if 'Rainfall' in valid_fields else False,
                    "unit": "boolean"
                }
            }
            
            if 'Humidity' in valid_fields:
                lap_record["humidity"] = {
                    "value": float(row['Humidity']),
                    "unit": "%"
                }
                
            sample_data.append(lap_record)
        
        rain_analysis["lap_rain_data"] = sample_data
        
        # 降雨統計
        if 'Rainfall' in valid_fields:
            rain_records = weather_data[weather_data['Rainfall'] == True]
            rain_analysis["rain_statistics"] = {
                "total_rain_laps": len(rain_records),
                "longest_rain_period": {
                    "laps": 0,  # 需要實作連續降雨檢測
                    "start_lap": None,
                    "end_lap": None
                }
            }
        
        return rain_analysis
    
    def _analyze_humidity_vs_lap(self, weather_data: pd.DataFrame, valid_fields: dict, laps_data=None) -> Dict[str, Any]:
        """分析濕度vs圈數"""
        humidity_analysis = {
            "description": "每圈濕度變化分析",
            "analysis_method": "fastest_lap_logic_adapted",
            "data_structure": "per_lap_humidity_tracking"
        }
        
        # 取前3筆作為範例數據
        sample_data = []
        for i, (idx, row) in enumerate(weather_data.head(3).iterrows()):
            lap_record = {
                "lap_number": i + 1,
                "humidity": {
                    "value": float(row['Humidity']),
                    "unit": "%"
                }
            }
            sample_data.append(lap_record)
        
        humidity_analysis["lap_humidity_data"] = sample_data
        
        # 濕度統計
        humidity_values = weather_data['Humidity'].dropna()
        humidity_analysis["humidity_statistics"] = {
            "min_humidity": {
                "value": float(humidity_values.min()),
                "lap": 1
            },
            "max_humidity": {
                "value": float(humidity_values.max()),
                "lap": len(weather_data)
            },
            "average_humidity": float(humidity_values.mean())
        }
        
        return humidity_analysis
    
    def _analyze_windspeed_vs_lap(self, weather_data: pd.DataFrame, valid_fields: dict, laps_data=None) -> Dict[str, Any]:
        """分析風速vs圈數"""
        wind_analysis = {
            "description": "每圈風速變化分析",
            "analysis_method": "fastest_lap_logic_adapted",
            "data_structure": "per_lap_wind_tracking"
        }
        
        # 取前3筆作為範例數據
        sample_data = []
        for i, (idx, row) in enumerate(weather_data.head(3).iterrows()):
            lap_record = {
                "lap_number": i + 1,
                "wind_speed": {
                    "value": float(row['WindSpeed']),
                    "unit": "m/s"
                }
            }
            sample_data.append(lap_record)
        
        wind_analysis["lap_windspeed_data"] = sample_data
        
        # 風速統計
        wind_values = weather_data['WindSpeed'].dropna()
        wind_analysis["windspeed_statistics"] = {
            "min_windspeed": {
                "value": float(wind_values.min()),
                "lap": 1
            },
            "max_windspeed": {
                "value": float(wind_values.max()),
                "lap": len(weather_data)
            },
            "average_windspeed": float(wind_values.mean())
        }
        
        return wind_analysis
    
    def _analyze_pressure_vs_lap(self, weather_data: pd.DataFrame, valid_fields: dict, laps_data=None) -> Dict[str, Any]:
        """分析氣壓vs圈數"""
        pressure_analysis = {
            "description": "每圈氣壓變化分析",
            "analysis_method": "fastest_lap_logic_adapted",
            "data_structure": "per_lap_pressure_tracking"
        }
        
        # 取前3筆作為範例數據
        sample_data = []
        for i, (idx, row) in enumerate(weather_data.head(3).iterrows()):
            lap_record = {
                "lap_number": i + 1,
                "atmospheric_pressure": {
                    "value": float(row['Pressure']),
                    "unit": "mbar"
                }
            }
            sample_data.append(lap_record)
        
        pressure_analysis["lap_pressure_data"] = sample_data
        
        # 氣壓統計
        pressure_values = weather_data['Pressure'].dropna()
        pressure_analysis["pressure_statistics"] = {
            "min_pressure": {
                "value": float(pressure_values.min()),
                "lap": 1
            },
            "max_pressure": {
                "value": float(pressure_values.max()),
                "lap": len(weather_data)
            },
            "average_pressure": float(pressure_values.mean())
        }
        
        return pressure_analysis
    
    def _save_enhanced_json(self, enhanced_json: Dict[str, Any], 
                           year: int, race: str, session: str) -> str:
        """
        保存增強版JSON到檔案
        
        Args:
            enhanced_json: 增強版JSON數據
            year: 年份
            race: 比賽名稱  
            session: 賽段類型
            
        Returns:
            str: 保存的檔案路徑
        """
        try:
            # 創建json目錄
            json_dir = "json"
            os.makedirs(json_dir, exist_ok=True)
            
            # 生成檔案名稱 - 簡化版本，不包含時間戳
            filename = f"enhanced_rain_analysis_{year}_{race}_{session}.json"
            filepath = os.path.join(json_dir, filename)
            
            # 保存JSON檔案
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(enhanced_json, f, ensure_ascii=False, indent=2)
            
            print(f"💾 簡化降雨分析JSON已保存: {filepath}")
            file_size = os.path.getsize(filepath)
            print(f"📄 檔案大小: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            
            # 顯示降雨摘要
            if 'rain_laps' in enhanced_json.get('summary', {}):
                rain_laps = enhanced_json['summary']['rain_laps']
                total_laps = enhanced_json['summary']['total_laps']
                
                # 顯示降雨時間分析
                timing_analysis = enhanced_json['summary'].get('rain_timing_analysis', {})
                if "rain_before_race" in timing_analysis:
                    before = timing_analysis["rain_before_race"]
                    during = timing_analysis["rain_during_race"]
                    after = timing_analysis["rain_after_race"]
                    
                    print(f"🌧️ 降雨時間分析:")
                    print(f"   比賽前: {before} 點 ({timing_analysis.get('rain_distribution', {}).get('before_race_percentage', 0)}%)")
                    print(f"   比賽中: {during} 點 ({timing_analysis.get('rain_distribution', {}).get('during_race_percentage', 0)}%)")
                    print(f"   比賽後: {after} 點 ({timing_analysis.get('rain_distribution', {}).get('after_race_percentage', 0)}%)")
                
                print(f"🌧️ 降雨摘要: {rain_laps}/{total_laps} 圈有降雨 ({enhanced_json['summary'].get('rain_percentage', 0)}%)")
                
                # 更新結論輸出
                if rain_laps > 0:
                    rain_status = "比賽中有雨"
                elif timing_analysis.get("rain_before_race", 0) > 0:
                    rain_status = "比賽前有雨，比賽中無雨"
                else:
                    rain_status = "無降雨"
                print(f"🎯 降雨結論: {rain_status}")
            
            return filepath
            
        except Exception as e:
            print(f"❌ JSON檔案保存失敗: {e}")
            return ""

if __name__ == "__main__":
    # 測試模組
    print("🧪 測試增強版降雨分析模組")
    print("=" * 50)
    
    analyzer = EnhancedRainAnalyzer()
    
    # 測試參數驗證
    print("📋 測試參數驗證:")
    print(f"   有效參數: {analyzer.validate_parameters(year=2025, race='Japan', session='R')}")
    print(f"   無效參數: {analyzer.validate_parameters(year=2025)}")
    
    # 測試分析 (使用已知存在的緩存)
    print("\n🔍 測試分析執行:")
    result = analyzer.analyze(year=2025, race='Japan', session='R')
    
    if result['success']:
        print(f"✅ 分析成功")
        print(f"   數據點數: {result['data_points']}")
        print(f"   緩存使用: {result['cache_used']}")
        print(f"   JSON檔案: {result['json_file']}")
        if 'lap_weather_data' in result['data']:
            sample_laps = list(result['data']['lap_weather_data'].keys())[:3]
            print(f"   範例圈數: {sample_laps}")
    else:
        print(f"❌ 分析失敗: {result['error']}")
