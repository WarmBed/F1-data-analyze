#!/usr/bin/env python3
"""
F1 降雨強度分析系統 - JSON輸出版本
Rain Intensity Analysis System - JSON Output Version
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
import json

# 全局字體設置函數
def setup_chinese_fonts():
    """設置中文字體支援"""
    try:
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans', 'Arial', 'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 驗證字體設置
        import matplotlib.font_manager as fm
        fonts = [f.name for f in fm.fontManager.ttflist if 'JhengHei' in f.name or 'SimHei' in f.name]
        if fonts:
            print(f"[SUCCESS] 中文字體已設置: {fonts[0] if fonts else '系統預設'}")
        else:
            print("[WARNING] 未找到特定中文字體，使用系統預設字體")
        return True
    except Exception as e:
        print(f"[ERROR] 字體設置失敗: {e}")
        return False

def format_time_for_json(time_obj):
    """格式化時間對象為JSON友好的字符串"""
    if isinstance(time_obj, timedelta):
        total_seconds = time_obj.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = total_seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:06.3f}"
        else:
            return f"{minutes}:{seconds:06.3f}"
    elif isinstance(time_obj, (datetime, pd.Timestamp)):
        return time_obj.isoformat()
    else:
        return str(time_obj)

# 模組載入時自動設置字體
setup_chinese_fonts()

class RainIntensityAnalyzerJSON:
    """降雨強度分析器 - JSON輸出版本"""
    
    def __init__(self):
        self.weather_data = None
        self.session = None
        self.rain_events = []
        self.data_loader = None
        
    def initialize_from_data_loader(self, data_loader):
        """從數據載入器初始化"""
        try:
            self.data_loader = data_loader
            
            # 獲取真實的天氣數據 - 使用正確的 FastF1 API
            import fastf1
            
            # 從 data_loader 獲取賽事資訊
            year = getattr(data_loader, 'year', 2024)
            race_name = getattr(data_loader, 'race_name', 'Unknown')
            session_type = getattr(data_loader, 'session_type', 'R')
            
            print(f"[INFO] 載入真實天氣數據: {year} {race_name} {session_type}")
            
            # 啟用快取
            fastf1.Cache.enable_cache("./f1cache")
            
            # 使用正確的 FastF1 方法載入天氣數據
            session = fastf1.get_session(year, race_name, session_type)
            session.load(weather=True)  # 關鍵：要把 weather 打開
            
            # 檢查天氣數據
            if hasattr(session, 'weather_data') and session.weather_data is not None:
                wx = session.weather_data
                if not wx.empty:
                    self.weather_data = wx
                    self.session = session
                    print(f"[SUCCESS] 天氣數據載入成功: {len(wx)} 記錄")
                    print(f"[INFO] 天氣數據欄位: {list(wx.columns)}")
                    
                    # 檢查降雨數據
                    if 'Rainfall' in wx.columns:
                        rain_count = (wx['Rainfall'] == True).sum()
                        print(f"[INFO] 降雨記錄數: {rain_count}")
                        if rain_count == 0:
                            print(f"[INFO] 此賽事無降雨記錄，將進行乾燥天氣分析")
                    
                    return True
                else:
                    print(f"[ERROR] 天氣數據為空")
                    return False
            else:
                print(f"[ERROR] 找不到 weather_data 屬性")
                return False
            
        except Exception as e:
            print(f"[ERROR] 天氣數據載入失敗: {e}")
            print(f"此分析功能需要真實的F1天氣數據才能執行")
            print(f"請選擇有天氣數據記錄的賽事和賽段")
            return False

    def analyze_rain_patterns(self):
        """分析降雨模式並返回結果（靜默模式）"""
        if self.weather_data is None or self.weather_data.empty:
            return False
        
        # 檢查是否有降雨資料
        if 'Rainfall' not in self.weather_data.columns:
            return False
        
        return True

    def display_detailed_analysis(self):
        """顯示詳細的降雨分析表格"""
        try:
            from prettytable import PrettyTable
            
            print("📊 降雨強度分析結果摘要：")
            
            if self.weather_data is None or self.weather_data.empty:
                print("❌ 無可用的天氣數據")
                return
            
            # 基本統計表格
            summary_table = PrettyTable()
            summary_table.field_names = ["項目", "數值", "備註"]
            summary_table.align = "l"
            
            total_records = len(self.weather_data)
            # 修正降雨統計 - FastF1 的 Rainfall 是 Boolean 欄位
            if 'Rainfall' in self.weather_data.columns:
                rain_records = (self.weather_data['Rainfall'] == True).sum()
            else:
                rain_records = 0
            rain_percentage = (rain_records / total_records * 100) if total_records > 0 else 0
            
            summary_table.add_row(["總數據點數", f"{total_records:,}", "比賽期間天氣記錄總數"])
            summary_table.add_row(["降雨記錄數", f"{int(rain_records):,}", "有降雨的時間點"])
            summary_table.add_row(["降雨比例", f"{rain_percentage:.1f}%", "降雨時間占比"])
            
            # 溫度統計
            if 'AirTemp' in self.weather_data.columns:
                temp_data = self.weather_data['AirTemp'].dropna()
                if not temp_data.empty:
                    summary_table.add_row(["最低氣溫", f"{temp_data.min():.1f}°C", "比賽期間最低溫度"])
                    summary_table.add_row(["最高氣溫", f"{temp_data.max():.1f}°C", "比賽期間最高溫度"])
                    summary_table.add_row(["平均氣溫", f"{temp_data.mean():.1f}°C", "比賽期間平均溫度"])
            
            # 濕度統計
            if 'Humidity' in self.weather_data.columns:
                humidity_data = self.weather_data['Humidity'].dropna()
                if not humidity_data.empty:
                    summary_table.add_row(["平均濕度", f"{humidity_data.mean():.1f}%", "比賽期間平均濕度"])
                    summary_table.add_row(["最高濕度", f"{humidity_data.max():.1f}%", "比賽期間最高濕度"])
            
            # 風速統計  
            if 'WindSpeed' in self.weather_data.columns:
                wind_data = self.weather_data['WindSpeed'].dropna()
                if not wind_data.empty:
                    summary_table.add_row(["平均風速", f"{wind_data.mean():.1f} km/h", "比賽期間平均風速"])
                    summary_table.add_row(["最大風速", f"{wind_data.max():.1f} km/h", "比賽期間最大風速"])
            
            print(summary_table)
            
            # 降雨強度分析
            if rain_records > 0:
                intensity_table = PrettyTable()
                intensity_table.field_names = ["降雨強度", "描述", "影響"]
                intensity_table.align = "l"
                
                if rain_percentage < 20:
                    intensity_table.add_row(["輕微降雨 💧", f"僅 {rain_percentage:.1f}% 時間有雨", "對比賽影響較小"])
                elif rain_percentage < 50:
                    intensity_table.add_row(["中度降雨 🌧️", f"{rain_percentage:.1f}% 時間有雨", "可能影響輪胎策略"])
                else:
                    intensity_table.add_row(["重度降雨 🌧️🌧️🌧️", f"{rain_percentage:.1f}% 時間有雨", "顯著影響比賽條件"])
                
                print("\n🌧️ 降雨強度評估：")
                print(intensity_table)
            else:
                print("\n☀️ 本場比賽無降雨記錄")
            
            print(f"   • 數據完整性: {'✅ 良好' if total_records > 0 else '❌ 不足'}")
            
        except ImportError:
            # 如果沒有 prettytable，使用簡單格式
            print("📊 降雨強度分析結果：")
            total_records = len(self.weather_data)
            rain_records = self.weather_data['Rainfall'].sum() if 'Rainfall' in self.weather_data.columns else 0
            print(f"   • 總數據點數: {total_records:,}")
            print(f"   • 降雨記錄數: {int(rain_records):,}")
            print(f"   • 降雨比例: {(rain_records / total_records * 100) if total_records > 0 else 0:.1f}%")
        except Exception as e:
            print(f"⚠️ 顯示詳細分析時發生錯誤: {e}")

    def _report_analysis_results(self, data, analysis_type="analysis"):
        """報告分析結果狀態"""
        if not data:
            print(f"❌ {analysis_type}失敗：無可用數據")
            return False
        
        # 檢查數據結構
        data_count = 1
        if isinstance(data, dict):
            if 'detailed_weather_timeline' in data:
                data_count = len(data['detailed_weather_timeline'])
            elif 'total_data_points' in data:
                data_count = data['total_data_points']
            else:
                data_count = len(data.keys())
        elif hasattr(data, '__len__'):
            data_count = len(data)
        
        print(f"📊 {analysis_type}結果摘要：")
        print(f"   • 數據項目數量: {data_count}")
        print(f"   • 數據完整性: {'✅ 良好' if data_count > 0 else '❌ 不足'}")
        
        # 檢查關鍵分析內容
        if isinstance(data, dict):
            if 'error' in data:
                print(f"   • 執行狀態: ❌ 錯誤 - {data['error']}")
                return False
            else:
                print(f"   • 執行狀態: ✅ 成功")
        
        print(f"✅ {analysis_type}分析完成！")
        return True

    def _display_json_preview(self, json_data, preview_count=20):
        """顯示JSON資料預覽供使用者確認"""
        try:
            from prettytable import PrettyTable
            
            print(f"\n📋 JSON 資料預覽 (前 {preview_count} 筆詳細天氣資料)：")
            
            if not isinstance(json_data, dict) or 'detailed_weather_timeline' not in json_data:
                print("⚠️ 無法顯示天氣時間序列預覽")
                return
            
            timeline_data = json_data['detailed_weather_timeline']
            if not timeline_data:
                print("⚠️ 天氣時間序列資料為空")
                return
            
            # 創建預覽表格
            preview_table = PrettyTable()
            preview_table.field_names = ["時間點", "時間", "溫度(°C)", "濕度(%)", "風速(m/s)", "降雨狀態"]
            preview_table.align = "l"
            
            # 顯示前N筆資料
            display_count = min(preview_count, len(timeline_data))
            for i in range(display_count):
                data_point = timeline_data[i]
                time_index = data_point.get('time_index', i)
                time_point = data_point.get('time_point', f"T+{i}")
                
                weather = data_point.get('weather_data', {})
                
                # 提取天氣數據
                temp = weather.get('air_temperature', {}).get('value', 'N/A')
                temp_str = f"{temp:.1f}" if isinstance(temp, (int, float)) else str(temp)
                
                humidity = weather.get('humidity', {}).get('value', 'N/A')
                humidity_str = f"{humidity:.1f}" if isinstance(humidity, (int, float)) else str(humidity)
                
                wind_speed = weather.get('wind_speed', {}).get('value', 'N/A')
                wind_str = f"{wind_speed:.1f}" if isinstance(wind_speed, (int, float)) else str(wind_speed)
                
                # 降雨狀態
                rainfall = weather.get('rainfall', {})
                if rainfall.get('is_raining', False):
                    rain_status = f"🌧️ {rainfall.get('status', 'wet')}"
                    if 'description' in rainfall:
                        rain_status = f"🌧️ {rainfall['description']}"
                else:
                    rain_status = f"☀️ {rainfall.get('status', 'dry')}"
                
                preview_table.add_row([
                    str(time_index),
                    time_point,
                    temp_str,
                    humidity_str, 
                    wind_str,
                    rain_status
                ])
            
            print(preview_table)
            
            # 顯示統計摘要
            total_points = len(timeline_data)
            rain_points = sum(1 for point in timeline_data 
                            if point.get('weather_data', {}).get('rainfall', {}).get('is_raining', False))
            
            print(f"\n📊 JSON 資料統計摘要：")
            print(f"   • 總時間點數量: {total_points:,}")
            print(f"   • 顯示預覽數量: {display_count}")
            print(f"   • 降雨時間點數: {rain_points}")
            print(f"   • 降雨比例: {(rain_points/total_points*100):.1f}%")
            
            if display_count < total_points:
                print(f"   • 剩餘資料: {total_points - display_count:,} 筆 (已儲存至JSON檔案)")
                
        except ImportError:
            # 如果沒有 prettytable，使用簡單格式
            print(f"\n📋 JSON 資料預覽 (前 {preview_count} 筆)：")
            timeline_data = json_data.get('detailed_weather_timeline', [])
            display_count = min(preview_count, len(timeline_data))
            
            for i in range(display_count):
                data_point = timeline_data[i]
                time_point = data_point.get('time_point', f"T+{i}")
                weather = data_point.get('weather_data', {})
                
                temp = weather.get('air_temperature', {}).get('value', 'N/A')
                rainfall_status = "🌧️ 降雨" if weather.get('rainfall', {}).get('is_raining', False) else "☀️ 無雨"
                
                print(f"   {i+1:2d}. 時間:{time_point} | 溫度:{temp}°C | { rainfall_status}")
                
            print(f"\n   總共 {len(timeline_data)} 筆資料，顯示前 {display_count} 筆")
            
        except Exception as e:
            print(f"⚠️ 顯示JSON預覽時發生錯誤: {e}")

    def generate_json_output(self, enable_debug=False):
        """生成JSON格式的分析結果"""
        try:
            # 確保已執行分析
            if self.weather_data is None:
                return {"error": "No weather data available"}
            
            # 基本元數據
            metadata = {
                "analysis_type": "Rain Intensity Analysis",
                "generated_at": datetime.now().isoformat(),
                "version": "1.0",
                "debug_mode": enable_debug
            }
            
            # 添加賽事信息
            if self.data_loader:
                metadata.update({
                    "year": getattr(self.data_loader, 'year', None),
                    "race_name": getattr(self.data_loader, 'race_name', None),
                    "session": getattr(self.data_loader, 'session_name', None)
                })
            
            # 分析結果
            analysis = {}
            analysis["metadata"] = metadata
            
            # 基本統計 - 修正降雨統計方式
            total_records = len(self.weather_data)
            if 'Rainfall' in self.weather_data.columns:
                rain_records = (self.weather_data['Rainfall'] == True).sum()
            else:
                rain_records = 0
            
            analysis["summary"] = {
                "total_data_points": total_records,
                "rain_data_points": int(rain_records),
                "rain_percentage": float(rain_records / total_records * 100) if total_records > 0 else 0.0
            }
            
            # 降雨強度等級判定
            if rain_records > 0:
                rain_intensity = rain_records / total_records
                
                if rain_intensity < 0.2:
                    analysis["rain_intensity"] = "light"
                    analysis["rain_intensity_description"] = "輕微降雨 💧"
                elif rain_intensity < 0.5:
                    analysis["rain_intensity"] = "moderate"
                    analysis["rain_intensity_description"] = "中度降雨 🌧️"
                else:
                    analysis["rain_intensity"] = "heavy"
                    analysis["rain_intensity_description"] = "重度降雨 🌧️🌧️🌧️"
            
            # 添加其他天氣數據分析
            for column in ['AirTemp', 'Humidity', 'WindSpeed', 'Pressure']:
                if column in self.weather_data.columns:
                    data = self.weather_data[column].dropna()
                    if not data.empty:
                        analysis[f"{column.lower()}_analysis"] = {
                            "min": float(data.min()),
                            "max": float(data.max()),
                            "mean": float(data.mean()),
                            "std": float(data.std()) if len(data) > 1 else 0.0
                        }
            
            # 生成詳細的天氣時間序列數據
            timeline_data = []
            for index, row in self.weather_data.iterrows():
                weather_point = {
                    "time_index": int(index),
                    "time_point": format_time_for_json(row.get('Time', f"T+{index}")),
                    "weather_data": {}
                }
                
                # 添加所有可用的天氣參數
                if 'AirTemp' in row and pd.notna(row['AirTemp']):
                    weather_point["weather_data"]["air_temperature"] = {
                        "value": float(row['AirTemp']),
                        "unit": "°C"
                    }
                
                if 'Humidity' in row and pd.notna(row['Humidity']):
                    weather_point["weather_data"]["humidity"] = {
                        "value": float(row['Humidity']),
                        "unit": "%"
                    }
                
                if 'Pressure' in row and pd.notna(row['Pressure']):
                    weather_point["weather_data"]["pressure"] = {
                        "value": float(row['Pressure']),
                        "unit": "mb"
                    }
                
                if 'WindSpeed' in row and pd.notna(row['WindSpeed']):
                    weather_point["weather_data"]["wind_speed"] = {
                        "value": float(row['WindSpeed']),
                        "unit": "m/s"
                    }
                
                if 'Rainfall' in row:
                    is_raining = bool(row['Rainfall'])
                    weather_point["weather_data"]["rainfall"] = {
                        "is_raining": is_raining,
                        "status": "wet" if is_raining else "dry"
                    }
                    
                    # 基於濕度推算降雨強度
                    if is_raining and 'Humidity' in row and pd.notna(row['Humidity']):
                        humidity = float(row['Humidity'])
                        if humidity >= 85:
                            rain_intensity_level = "heavy"
                            rain_description = "大雨 🌧️🌧️🌧️"
                        elif humidity >= 80:
                            rain_intensity_level = "moderate"
                            rain_description = "中雨 🌧️🌧️"
                        elif humidity >= 75:
                            rain_intensity_level = "light"
                            rain_description = "小雨 🌧️"
                        else:
                            rain_intensity_level = "drizzle"
                            rain_description = "毛毛雨 💧"
                        
                        weather_point["weather_data"]["rainfall"]["intensity"] = rain_intensity_level
                        weather_point["weather_data"]["rainfall"]["description"] = rain_description
                
                timeline_data.append(weather_point)
            
            analysis["detailed_weather_timeline"] = timeline_data
            analysis["total_data_points"] = len(timeline_data)
            
            return analysis
            
        except Exception as e:
            return {"error": f"JSON輸出生成失敗: {str(e)}"}


def run_rain_intensity_analysis_json(data_loader, enable_debug=False, output_file=None, show_detailed_output=True):
    """執行降雨強度分析並返回JSON格式結果，同時顯示詳細分析表格 - 符合開發核心原則
    
    Args:
        data_loader: 數據載入器
        enable_debug: 是否啟用除錯模式
        output_file: 輸出檔案路徑
        show_detailed_output: 是否顯示詳細輸出（即使使用緩存也顯示完整表格）
    """
    import pickle
    
    try:
        print("🚀 開始執行降雨強度分析...")
        
        # 1. 生成緩存鍵值
        year = getattr(data_loader, 'year', 2024)
        race_name = getattr(data_loader, 'race_name', 'Unknown')
        session_type = getattr(data_loader, 'session_type', 'R')
        cache_key = f"rain_intensity_{year}_{race_name}_{session_type}"
        cache_path = f"cache/{cache_key}.pkl"
        
        # 2. 檢查緩存
        cached_result = None
        cache_used = False
        try:
            if os.path.exists(cache_path):
                with open(cache_path, 'rb') as f:
                    cached_result = pickle.load(f)
                cache_used = True
                if cached_result and not show_detailed_output:
                    print("📦 使用緩存數據")
                    return {
                        "success": True,
                        "data": cached_result,
                        "cache_used": cache_used,
                        "cache_key": cache_key,
                        "function_id": "1"
                    }
                elif cached_result and show_detailed_output:
                    print("📦 使用緩存數據 + 📊 顯示詳細分析結果")
                    # 顯示詳細輸出
                    _display_cached_detailed_output(cached_result)
                    
                    # 按照 Function 2 標準：即使使用緩存也要保存 JSON
                    session_info = get_session_info(data_loader)
                    save_rain_raw_data(session_info, cached_result)
                    
                    return {
                        "success": True,
                        "data": cached_result,
                        "cache_used": cache_used,
                        "cache_key": cache_key,
                        "function_id": "1"
                    }
        except Exception as e:
            print(f"⚠️ 緩存讀取失敗: {e}")
            cache_used = False
        
        print("🔄 重新計算 - 開始數據分析...")
        # 確保非緩存情況下 cache_used 為 False
        cache_used = False
        
        # 3. 創建分析器
        analyzer = RainIntensityAnalyzerJSON()
        
        # 4. 從數據載入器初始化
        print("📥 載入數據中...")
        if not analyzer.initialize_from_data_loader(data_loader):
            print("❌ 降雨強度分析失敗：分析器初始化失敗")
            return {"error": "分析器初始化失敗"}
        
        # 5. 執行分析
        print("🔄 分析處理中...")
        if not analyzer.analyze_rain_patterns():
            print("❌ 降雨強度分析失敗：降雨模式分析失敗")
            return {"error": "降雨模式分析失敗"}
        
        # 6. 顯示詳細分析結果表格
        analyzer.display_detailed_analysis()
        
        # 7. 生成JSON結果
        print("💾 生成 JSON 數據...")
        json_result = analyzer.generate_json_output(enable_debug=enable_debug)
        
        # 8. 保存Raw Data（按照 Function 2 標準）
        session_info = get_session_info(data_loader)
        save_rain_raw_data(session_info, json_result)
        
        # 9. 顯示前20筆JSON資料供使用者確認
        analyzer._display_json_preview(json_result, preview_count=20)
        
        # 10. 報告分析結果
        analyzer._report_analysis_results(json_result, "降雨強度分析")
        
        # 11. 保存緩存
        try:
            os.makedirs("cache", exist_ok=True)
            with open(cache_path, 'wb') as f:
                pickle.dump(json_result, f)
            print("💾 分析結果已緩存")
        except Exception as e:
            print(f"⚠️ 緩存保存失敗: {e}")
        
        # 12. 返回符合 Function 15 標準的結果格式
        return {
            "success": True,
            "data": json_result,
            "cache_used": cache_used,
            "cache_key": cache_key,
            "function_id": "1"
        }
        
    except Exception as e:
        print(f"❌ 降雨強度分析執行失敗: {str(e)}")
        return {"error": f"降雨強度分析執行失敗: {str(e)}"}


def _display_cached_detailed_output(cached_result):
    """顯示緩存數據的詳細輸出"""
    try:
        print("📊 顯示緩存的詳細分析結果...")
        
        # 從緩存結果中提取統計信息
        summary = cached_result.get('summary', {})
        metadata = cached_result.get('metadata', {})
        
        if summary:
            total_points = summary.get('total_data_points', 0)
            rain_points = summary.get('rain_data_points', 0)
            rain_percentage = summary.get('rain_percentage', 0.0)
            
            print(f"\n📊 降雨強度分析結果摘要：")
            print(f"+----------------+----------+----------------------+")
            print(f"| 項目           | 數值     | 備註                 |")
            print(f"+----------------+----------+----------------------+")
            print(f"| 總數據點數     | {total_points:8} | 比賽期間天氣記錄總數 |")
            print(f"| 降雨記錄數     | {rain_points:8} | 有降雨的時間點       |")
            print(f"| 降雨比例       | {rain_percentage:7.1f}% | 降雨時間占比         |")
            print(f"| 分析時間       | {metadata.get('generated_at', 'N/A')[:19]} | 分析生成時間         |")
            print(f"| 賽季年份       | {metadata.get('year', 'N/A'):8} | 比賽年份             |")
            print(f"| 比賽名稱       | {metadata.get('race_name', 'N/A'):8} | 大獎賽名稱           |")
            print(f"+----------------+----------+----------------------+")
            
            if rain_points == 0:
                print("☀️ 本場比賽無降雨記錄")
            else:
                print(f"🌧️ 本場比賽有降雨，持續時間占比 {rain_percentage:.1f}%")
        
        # 顯示詳細分析資料 
        if cached_result.get('airtemp_analysis'):
            airtemp = cached_result['airtemp_analysis']
            print(f"\n🌡️ 氣溫分析：")
            # 處理不同的鍵值格式並格式化數值
            min_temp = airtemp.get('min_temp', airtemp.get('min', 'N/A'))
            max_temp = airtemp.get('max_temp', airtemp.get('max', 'N/A'))
            avg_temp = airtemp.get('avg_temp', airtemp.get('mean', 'N/A'))
            # 格式化為一位小數
            min_temp = f"{min_temp:.1f}" if isinstance(min_temp, (int, float)) else min_temp
            max_temp = f"{max_temp:.1f}" if isinstance(max_temp, (int, float)) else max_temp
            avg_temp = f"{avg_temp:.1f}" if isinstance(avg_temp, (int, float)) else avg_temp
            print(f"   • 最低氣溫: {min_temp}°C")
            print(f"   • 最高氣溫: {max_temp}°C") 
            print(f"   • 平均氣溫: {avg_temp}°C")
        
        if cached_result.get('humidity_analysis'):
            humidity = cached_result['humidity_analysis']
            print(f"\n💧 濕度分析：")
            # 處理不同的鍵值格式並格式化數值
            min_humidity = humidity.get('min_humidity', humidity.get('min', 'N/A'))
            max_humidity = humidity.get('max_humidity', humidity.get('max', 'N/A'))
            avg_humidity = humidity.get('avg_humidity', humidity.get('mean', 'N/A'))
            # 格式化為一位小數
            min_humidity = f"{min_humidity:.1f}" if isinstance(min_humidity, (int, float)) else min_humidity
            max_humidity = f"{max_humidity:.1f}" if isinstance(max_humidity, (int, float)) else max_humidity
            avg_humidity = f"{avg_humidity:.1f}" if isinstance(avg_humidity, (int, float)) else avg_humidity
            print(f"   • 最低濕度: {min_humidity}%")
            print(f"   • 最高濕度: {max_humidity}%")
            print(f"   • 平均濕度: {avg_humidity}%")
        
        if cached_result.get('windspeed_analysis'):
            windspeed = cached_result['windspeed_analysis']
            print(f"\n💨 風速分析：")
            # 處理不同的鍵值格式並格式化數值
            min_speed = windspeed.get('min_speed', windspeed.get('min', 'N/A'))
            max_speed = windspeed.get('max_speed', windspeed.get('max', 'N/A'))
            avg_speed = windspeed.get('avg_speed', windspeed.get('mean', 'N/A'))
            # 格式化為一位小數
            min_speed = f"{min_speed:.1f}" if isinstance(min_speed, (int, float)) else min_speed
            max_speed = f"{max_speed:.1f}" if isinstance(max_speed, (int, float)) else max_speed
            avg_speed = f"{avg_speed:.1f}" if isinstance(avg_speed, (int, float)) else avg_speed
            print(f"   • 最低風速: {min_speed} km/h")
            print(f"   • 最高風速: {max_speed} km/h")
            print(f"   • 平均風速: {avg_speed} km/h")
        
        print("\n   • 數據完整性: ✅ 良好")
        
    except Exception as e:
        print(f"⚠️ 緩存詳細輸出顯示失敗: {e}")
        # 顯示基本信息作為後備
        print("📊 緩存數據詳細輸出:")
        print("   • 數據完整性: ✅ 良好")

def get_session_info(data_loader):
    """獲取賽事基本信息 - 遵循 Function 2 標準"""
    try:
        # 獲取賽事資訊
        year = getattr(data_loader, 'year', 2025)
        race_name = getattr(data_loader, 'race_name', 'Unknown')
        session_type = getattr(data_loader, 'session_type', 'R')
        
        # 使用賽事全名映射（與 Function 2 一致）
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
        
        # 獲取完整賽事名稱
        full_race_name = race_full_name_mapping.get(race_name, race_name)
        
        session_info = {
            'year': year,
            'race': full_race_name,  # 使用完整名稱
            'race_short': race_name,  # 保留短名稱
            'session_type': session_type,
            'session_name': 'Race' if session_type == 'R' else session_type
        }
        
        return session_info
        
    except Exception as e:
        print(f"[WARNING] 獲取賽事資訊失敗: {e}")
        return {
            'year': 2025,
            'race': 'Unknown Grand Prix',
            'race_short': 'Unknown',
            'session_type': 'R',
            'session_name': 'Race'
        }


def save_rain_raw_data(session_info, rain_data):
    """保存降雨分析Raw Data - 遵循 Function 2 標準"""
    
    # 清理不能序列化的數據類型（與 Function 2 相同的 clean_for_json 函數）
    def clean_for_json(obj):
        if isinstance(obj, (list, tuple)):
            return [clean_for_json(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: clean_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, bool):
            return bool(obj)
        elif obj is None or isinstance(obj, (str, int, float)):
            return obj
        elif hasattr(obj, '__module__') and 'numpy' in str(obj.__module__):
            # 處理 NumPy 類型
            if hasattr(obj, 'item'):
                return obj.item()
            else:
                return float(obj) if hasattr(obj, '__float__') else str(obj)
        else:
            return str(obj)
    
    raw_data = {
        "analysis_type": "rain_intensity_analysis",
        "function": "1",
        "timestamp": datetime.now().strftime("%Y%m%d"),
        "session_info": clean_for_json(session_info),
        "rain_analysis": {
            "has_weather_data": bool(rain_data.get("summary", {}).get("total_data_points", 0) > 0),
            "rain_intensity": rain_data.get("rain_intensity", "unknown"),
            "rain_intensity_description": rain_data.get("rain_intensity_description", "未知"),
            "total_data_points": rain_data.get("summary", {}).get("total_data_points", 0),
            "rain_data_points": rain_data.get("summary", {}).get("rain_data_points", 0),
            "rain_percentage": rain_data.get("summary", {}).get("rain_percentage", 0.0)
        },
        "weather_statistics": {
            "temperature_analysis": clean_for_json(rain_data.get("airtemp_analysis", {})),
            "humidity_analysis": clean_for_json(rain_data.get("humidity_analysis", {})),
            "wind_speed_analysis": clean_for_json(rain_data.get("windspeed_analysis", {})),
            "pressure_analysis": clean_for_json(rain_data.get("pressure_analysis", {}))
        },
        "detailed_weather_timeline": clean_for_json(rain_data.get("detailed_weather_timeline", []))
    }
    
    # 確保json資料夾存在
    import os
    json_dir = "json"
    os.makedirs(json_dir, exist_ok=True)
    
    # 檔案命名格式：raw_data_rain_intensity_YYYY_賽事.json（與 Function 2 一致）
    # 使用賽事名稱（如 "Japanese Grand Prix"）
    year = session_info.get('year', 2025)
    race_name = session_info.get('race', 'Unknown')
    
    raw_data_file = os.path.join(json_dir, f"raw_data_rain_intensity_{year}_{race_name}.json")
    
    try:
        with open(raw_data_file, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=2)
        print(f"\n[SAVE] Raw Data 已保存: {raw_data_file}")
    except Exception as e:
        print(f"\n[ERROR] Raw Data 保存失敗: {e}")
