# -*- coding: utf-8 -*-
"""
車手每圈圈速詳細分析模組 - Function 27
提供單一車手的詳細每圈分析功能，包含圈速、輪胎、胎齡、進站、天氣、速度、特殊事件等
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from prettytable import PrettyTable
import os
import json
import pickle
from datetime import datetime

class SingleDriverDetailedLaptimeAnalysis:
    """車手每圈圈速詳細分析類"""
    
    def __init__(self, data_loader=None, year=None, race=None, session='R'):
        self.data_loader = data_loader
        self.year = year
        self.race = race
        self.session = session
        self.cache_enabled = True
        
    def analyze_every_lap(self, driver=None, show_detailed_output=True, **kwargs):
        """Function 28: 分析車手的每一圈詳細數據
        
        Args:
            driver: 車手代碼 (如 'VER', 'LEC')，如果為 None 則分析全部車手
            show_detailed_output: 是否顯示詳細輸出，即使使用緩存也顯示完整表格
        """
        try:
            if driver:
                print(f"⏱️ 開始執行 {driver} 的每圈圈速詳細分析...")
                analysis_mode = "single"
            else:
                print("⏱️ 開始執行全部車手的每圈圈速詳細分析...")
                analysis_mode = "all"
            
            # 生成緩存鍵值
            if analysis_mode == "single":
                cache_key = f"detailed_laptime_analysis_{self.year}_{self.race}_{self.session}_{driver}"
            else:
                cache_key = f"detailed_laptime_analysis_{self.year}_{self.race}_{self.session}_all_drivers"
            
            # 檢查緩存
            if self.cache_enabled:
                cached_result = self._check_cache(cache_key)
                if cached_result and not show_detailed_output:
                    print("📦 使用緩存數據")
                    self._report_analysis_results(cached_result, "車手每圈圈速詳細分析")
                    return cached_result
                elif cached_result and show_detailed_output:
                    print("📦 使用緩存數據 + 📊 顯示詳細分析結果")
                    # 重新顯示詳細輸出
                    if analysis_mode == "single":
                        self._display_cached_detailed_output(cached_result, driver)
                    else:
                        self._display_cached_all_drivers_output(cached_result)
                    return cached_result
            
            print("🔄 重新計算 - 開始數據分析...")
            
            # 獲取數據
            data = self.data_loader.get_loaded_data()
            if not data:
                print("❌ 無可用數據")
                return None
            
            laps = data['laps']
            session = data['session']
            weather_data = data.get('weather_data')
            results = data['results']
            
            # 根據分析模式獲取車手數據
            if analysis_mode == "single":
                # 單一車手分析
                driver_laps = laps[laps['Driver'] == driver].copy()
                
                if driver_laps.empty:
                    print(f"❌ 找不到車手 {driver} 的數據")
                    return None
                
                # 執行詳細分析
                result = self._perform_detailed_analysis(driver, driver_laps, session, weather_data, results)
                
            else:
                # 全部車手分析
                all_drivers = laps['Driver'].unique().tolist()
                drivers_to_analyze = [d for d in all_drivers if d]
                
                if not drivers_to_analyze:
                    print("❌ 找不到任何車手的數據")
                    return None
                
                print(f"📊 將分析 {len(drivers_to_analyze)} 位車手的每圈圈速")
                
                # 執行全部車手分析
                result = self._perform_all_drivers_detailed_analysis(drivers_to_analyze, laps, session, weather_data, results)
            
            # 結果驗證和反饋
            if not self._report_analysis_results(result, "車手每圈圈速詳細分析"):
                return None
            
            # 保存緩存
            if self.cache_enabled and result:
                self._save_cache(result, cache_key)
                print("💾 分析結果已緩存")
            
            # 保存JSON輸出
            if analysis_mode == "single":
                self._save_json_output(result, driver)
            else:
                self._save_json_output_all_drivers(result)
            
            return result
            
        except Exception as e:
            print(f"❌ 車手每圈圈速詳細分析失敗：{str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _perform_detailed_analysis(self, driver, driver_laps, session, weather_data, results):
        """執行詳細的每圈分析"""
        
        # 排序圈數
        driver_laps = driver_laps.sort_values('LapNumber').reset_index(drop=True)
        
        # 創建詳細分析表格
        table = PrettyTable()
        table.field_names = ["圈數", "圈速", "輪胎", "胎齡", "進站", "天氣", "I1速度", "I2速度", "終點速", "備註"]
        table.align = "l"
        
        detailed_data = []
        
        for _, lap in driver_laps.iterrows():
            lap_number = int(lap['LapNumber'])
            
            # 圈速時間
            lap_time = self._format_lap_time(lap.get('LapTime'))
            
            # 輪胎信息
            tire_compound = lap.get('Compound', 'N/A')
            tire_life = lap.get('TyreLife', 'N/A')
            
            # 進站檢查
            pit_status = ""
            if pd.notna(lap.get('PitOutTime')) or pd.notna(lap.get('PitInTime')):
                pit_status = "🔧進站"
            
            # 天氣信息
            weather = self._get_weather_for_lap(lap_number, weather_data)
            
            # 速度信息 (如果有遙測數據)
            speeds = self._get_speed_data(lap)
            i1_speed = speeds.get('i1_speed', 'N/A')
            i2_speed = speeds.get('i2_speed', 'N/A')
            finish_speed = speeds.get('finish_speed', 'N/A')
            
            # 特殊事件備註
            remarks = self._get_lap_remarks_enhanced(lap, lap_number, driver_laps)
            
            # 添加到表格
            table.add_row([
                lap_number,
                lap_time,
                tire_compound,
                tire_life if tire_life != 'N/A' else '',
                pit_status,
                weather,
                i1_speed,
                i2_speed,
                finish_speed,
                remarks
            ])
            
            # 添加到詳細數據
            detailed_data.append({
                "lap_number": lap_number,
                "lap_time": lap_time,
                "lap_time_seconds": lap.get('LapTime').total_seconds() if pd.notna(lap.get('LapTime')) else None,
                "tire_compound": tire_compound,
                "tire_life": tire_life,
                "pit_status": pit_status,
                "weather": weather,
                "i1_speed": i1_speed,
                "i2_speed": i2_speed,
                "finish_speed": finish_speed,
                "remarks": remarks,
                "sector_1": self._format_time(lap.get('Sector1Time')),
                "sector_2": self._format_time(lap.get('Sector2Time')),
                "sector_3": self._format_time(lap.get('Sector3Time'))
            })
        
        # 顯示表格
        print(f"\n📊 {driver} 每圈詳細分析表:")
        print("=" * 120)
        print(table)
        
        # 統計摘要
        self._print_summary_statistics(driver_laps, driver)
        
        # 創建分析結果
        result = {
            "success": True,
            "driver": driver,
            "total_laps": len(driver_laps),
            "detailed_lap_data": detailed_data,
            "summary_statistics": self._calculate_summary_stats(driver_laps),
            "analysis_metadata": {
                "year": self.year,
                "race": self.race,
                "session": self.session,
                "analysis_type": "detailed_laptime_analysis",
                "generated_at": datetime.now().isoformat()
            }
        }
        
        return result
    
    def _format_lap_time(self, lap_time):
        """格式化圈速時間"""
        if pd.isna(lap_time):
            return "N/A"
        
        total_seconds = lap_time.total_seconds()
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:06.3f}"
    
    def _format_time(self, time_obj):
        """格式化時間對象"""
        if pd.isna(time_obj):
            return "N/A"
        
        if hasattr(time_obj, 'total_seconds'):
            seconds = time_obj.total_seconds()
            return f"{seconds:.3f}s"
        return str(time_obj)
    
    def _get_weather_for_lap(self, lap_number, weather_data):
        """獲取特定圈數的天氣信息"""
        if weather_data is None or weather_data.empty:
            return "N/A"
        
        try:
            # 嘗試獲取特定圈數的天氣數據
            lap_weather = None
            
            # 方法1: 直接查找對應圈數的天氣數據
            if hasattr(weather_data, 'index') and hasattr(weather_data.index, 'get_level_values'):
                # 如果是多層索引，嘗試根據圈數查找
                try:
                    lap_weather = weather_data[weather_data.index.get_level_values('LapNumber') == lap_number]
                except:
                    pass
            
            # 方法2: 如果有 LapNumber 欄位，直接篩選
            if lap_weather is None or lap_weather.empty:
                if 'LapNumber' in weather_data.columns:
                    lap_weather = weather_data[weather_data['LapNumber'] == lap_number]
            
            # 方法3: 根據時間順序估算（如果weather_data按時間排序）
            if lap_weather is None or lap_weather.empty:
                # 假設weather_data按時間排序，根據圈數比例估算位置
                total_laps_estimated = 60  # 假設大約60圈
                weather_index = min(int((lap_number / total_laps_estimated) * len(weather_data)), len(weather_data) - 1)
                lap_weather = weather_data.iloc[weather_index:weather_index+1]
            
            # 如果找到對應的天氣數據，進行詳細分析
            if lap_weather is not None and not lap_weather.empty:
                # 獲取賽道溫度
                track_temp = None
                air_temp = None
                humidity = None
                rainfall = None
                
                # 賽道溫度
                if 'TrackTemp' in lap_weather.columns:
                    track_temp = lap_weather['TrackTemp'].iloc[0]
                
                # 空氣溫度
                if 'AirTemp' in lap_weather.columns:
                    air_temp = lap_weather['AirTemp'].iloc[0]
                
                # 濕度
                if 'Humidity' in lap_weather.columns:
                    humidity = lap_weather['Humidity'].iloc[0]
                
                # 降雨
                if 'Rainfall' in lap_weather.columns:
                    rainfall = lap_weather['Rainfall'].iloc[0]
                
                # 基於實際數據生成天氣描述
                return self._generate_weather_description(track_temp, air_temp, humidity, rainfall)
            
            # 如果無法找到特定圈數數據，使用整體平均值作為備選
            if 'TrackTemp' in weather_data.columns:
                avg_temp = weather_data['TrackTemp'].mean()
                return self._generate_simple_weather_description(avg_temp)
            
            return "☀️乾"
            
        except Exception as e:
            print(f"⚠️ 天氣數據處理錯誤: {e}")
            return "N/A"
    
    def _generate_weather_description(self, track_temp, air_temp, humidity, rainfall):
        """基於真實數據生成詳細天氣描述"""
        try:
            # 檢查降雨
            if rainfall is not None and pd.notna(rainfall) and rainfall > 0:
                if rainfall > 0.5:
                    return "🌧️大雨"
                else:
                    return "🌦️小雨"
            
            # 檢查濕度（高濕度可能表示潮濕條件）
            if humidity is not None and pd.notna(humidity) and humidity > 85:
                return "�️潮濕"
            
            # 主要基於溫度判斷
            temp_to_use = track_temp if pd.notna(track_temp) else air_temp
            
            if pd.notna(temp_to_use):
                if temp_to_use > 45:
                    return f"🔥極熱({temp_to_use:.1f}°C)"
                elif temp_to_use > 35:
                    return f"🌡️熱({temp_to_use:.1f}°C)"
                elif temp_to_use > 25:
                    return f"🌤️適中({temp_to_use:.1f}°C)"
                elif temp_to_use > 15:
                    return f"❄️涼({temp_to_use:.1f}°C)"
                else:
                    return f"🧊冷({temp_to_use:.1f}°C)"
            
            return "☀️乾燥"
            
        except Exception as e:
            return "N/A"
    
    def _generate_simple_weather_description(self, avg_temp):
        """基於平均溫度生成簡單天氣描述"""
        if pd.notna(avg_temp):
            if avg_temp > 40:
                return f"🌡️熱(~{avg_temp:.1f}°C)"
            elif avg_temp < 25:
                return f"❄️涼(~{avg_temp:.1f}°C)"
            else:
                return f"🌤️適中(~{avg_temp:.1f}°C)"
        return "☀️乾"
    
    def _get_speed_data(self, lap):
        """獲取速度數據"""
        try:
            speeds = {}
            
            # 從實際數據中獲取速度
            speeds['i1_speed'] = f"{int(lap.get('SpeedI1', 0))} km/h" if pd.notna(lap.get('SpeedI1')) else "N/A"
            speeds['i2_speed'] = f"{int(lap.get('SpeedI2', 0))} km/h" if pd.notna(lap.get('SpeedI2')) else "N/A"
            speeds['finish_speed'] = f"{int(lap.get('SpeedFL', 0))} km/h" if pd.notna(lap.get('SpeedFL')) else "N/A"
            
            return speeds
        except Exception as e:
            return {
                'i1_speed': 'N/A',
                'i2_speed': 'N/A', 
                'finish_speed': 'N/A'
            }
    
    def _get_lap_remarks_enhanced(self, lap, lap_number, driver_laps):
        """獲取增強的圈數備註"""
        remarks = []
        
        # 檢查進站
        if pd.notna(lap.get('PitOutTime')) or pd.notna(lap.get('PitInTime')):
            remarks.append("🔧進站")
        
        # 檢查是否為全場最快圈（而非個人最快）
        if self._is_fastest_lap_of_driver(lap, driver_laps):
            remarks.append("⚡最快圈")
        
        # 檢查軌道狀況
        if lap_number == 1:
            remarks.append("🏁起跑")
        
        # 檢查輪胎更換（基於輪胎配方變化和胎齡重置）
        if self._is_tire_change_lap(lap, lap_number, driver_laps):
            remarks.append("🛞換胎")
        
        # 檢查事故（基於 TrackStatus 和賽事控制信息）
        if self._is_accident_lap(lap, lap_number):
            remarks.append("⚠️事故")
        
        return " | ".join(remarks) if remarks else ""
    
    def _is_fastest_lap_of_driver(self, lap, driver_laps):
        """檢查是否為車手的最快圈（真正的最快圈，不是每次刷新）"""
        current_lap_time = lap.get('LapTime')
        if pd.isna(current_lap_time):
            return False
        
        # 找出車手的絕對最快圈
        valid_laps = driver_laps[driver_laps['LapTime'].notna()]
        if valid_laps.empty:
            return False
        
        fastest_time = valid_laps['LapTime'].min()
        return current_lap_time == fastest_time
    
    def _is_tire_change_lap(self, lap, lap_number, driver_laps):
        """檢查是否為換胎圈"""
        if lap_number <= 1:
            return False
        
        try:
            # 檢查胎齡是否重置為 1
            current_tire_life = lap.get('TyreLife')
            if pd.notna(current_tire_life) and current_tire_life == 1:
                # 確認不是第一圈
                if lap_number > 1:
                    return True
            
            # 檢查輪胎配方是否改變
            current_compound = lap.get('Compound')
            if pd.notna(current_compound) and lap_number > 1:
                prev_lap_idx = lap.name - 1
                if prev_lap_idx >= 0:
                    prev_compound = driver_laps.iloc[prev_lap_idx].get('Compound')
                    if pd.notna(prev_compound) and current_compound != prev_compound:
                        return True
            
            return False
        except:
            return False
    
    def _is_accident_lap(self, lap, lap_number):
        """檢查是否為事故圈（基於 TrackStatus）"""
        try:
            track_status = lap.get('TrackStatus')
            if pd.notna(track_status):
                # TrackStatus: 1=綠旗, 2=黃旗, 4=安全車, 5=紅旗, 6=虛擬安全車
                if str(track_status) in ['2', '4', '5', '6']:
                    return True
            return False
        except:
            return False
    
    def _get_accident_laps(self, session, driver):
        """獲取事故相關圈數（預留給未來事故模組整合）"""
        # 這個方法預留給 Function 6-10 事故模組的整合
        # 目前返回空列表，待事故模組提供 API
        return []

    def _get_lap_remarks(self, lap, lap_number):
        """獲取圈數備註"""
        remarks = []
        
        # 檢查進站
        if pd.notna(lap.get('PitOutTime')) or pd.notna(lap.get('PitInTime')):
            remarks.append("🔧進站")
        
        # 檢查個人最快圈
        if lap.get('IsPersonalBest', False):
            remarks.append("⚡個人最快")
        
        # 檢查軌道狀況 (簡化版)
        if lap_number == 1:
            remarks.append("🏁起跑")
        
        # 檢查輪胎更換
        if pd.notna(lap.get('Compound')):
            if lap_number > 1:
                remarks.append("🛞新胎")
        
        return " | ".join(remarks) if remarks else ""
    
    def _print_summary_statistics(self, driver_laps, driver):
        """顯示統計摘要"""
        valid_laps = driver_laps[driver_laps['LapTime'].notna()]
        
        if valid_laps.empty:
            return
        
        print(f"\n📈 {driver} 圈速統計摘要:")
        print("=" * 60)
        
        lap_times_seconds = valid_laps['LapTime'].dt.total_seconds()
        
        stats_table = PrettyTable()
        stats_table.field_names = ["統計項目", "數值"]
        stats_table.align = "l"
        
        stats_table.add_row(["總圈數", len(driver_laps)])
        stats_table.add_row(["有效圈數", len(valid_laps)])
        stats_table.add_row(["最快圈時間", self._format_lap_time(valid_laps['LapTime'].min())])
        stats_table.add_row(["最慢圈時間", self._format_lap_time(valid_laps['LapTime'].max())])
        stats_table.add_row(["平均圈速", f"{lap_times_seconds.mean():.3f}s"])
        stats_table.add_row(["圈速標準差", f"{lap_times_seconds.std():.3f}s"])
        
        # 進站統計
        pit_laps = driver_laps[driver_laps['PitOutTime'].notna() | driver_laps['PitInTime'].notna()]
        stats_table.add_row(["進站次數", len(pit_laps)])
        
        # 輪胎使用統計
        tire_compounds = driver_laps['Compound'].dropna().unique()
        if len(tire_compounds) > 0:
            stats_table.add_row(["使用輪胎", " | ".join(tire_compounds)])
        
        print(stats_table)
    
    def _calculate_summary_stats(self, driver_laps):
        """計算統計摘要"""
        valid_laps = driver_laps[driver_laps['LapTime'].notna()]
        
        if valid_laps.empty:
            return {}
        
        lap_times_seconds = valid_laps['LapTime'].dt.total_seconds()
        
        return {
            "total_laps": len(driver_laps),
            "valid_laps": len(valid_laps),
            "fastest_lap_time": self._format_lap_time(valid_laps['LapTime'].min()),
            "slowest_lap_time": self._format_lap_time(valid_laps['LapTime'].max()),
            "average_lap_time": f"{lap_times_seconds.mean():.3f}s",
            "lap_time_std": f"{lap_times_seconds.std():.3f}s",
            "pit_stops": len(driver_laps[driver_laps['PitOutTime'].notna() | driver_laps['PitInTime'].notna()]),
            "tire_compounds_used": list(driver_laps['Compound'].dropna().unique())
        }
    
    def _check_cache(self, cache_key):
        """檢查緩存"""
        cache_path = os.path.join("cache", f"{cache_key}.pkl")
        if os.path.exists(cache_path):
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        return None
    
    def _save_cache(self, data, cache_key):
        """保存緩存"""
        os.makedirs("cache", exist_ok=True)
        cache_path = os.path.join("cache", f"{cache_key}.pkl")
        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)
    
    def _save_json_output(self, result, driver):
        """保存JSON輸出"""
        json_dir = "json_exports"
        os.makedirs(json_dir, exist_ok=True)
        
        # 修正檔名格式：detailed_laptime_analysis_YYYY_賽事_賽段_車手.json
        json_filename = f"detailed_laptime_analysis_{self.year}_{self.race}_{self.session}_{driver}.json"
        json_path = os.path.join(json_dir, json_filename)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"📄 JSON 分析報告已保存: {json_path}")
    
    def _save_json_output_all_drivers(self, result):
        """保存全部車手的JSON輸出"""
        json_dir = "json_exports"
        os.makedirs(json_dir, exist_ok=True)
        
        # 修正檔名格式：detailed_laptime_analysis_YYYY_賽事_賽段_all_drivers.json
        json_filename = f"detailed_laptime_analysis_{self.year}_{self.race}_{self.session}_all_drivers.json"
        json_path = os.path.join(json_dir, json_filename)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"📄 全部車手 JSON 分析報告已保存: {json_path}")
    
    def _report_analysis_results(self, data, analysis_type="analysis"):
        """報告分析結果狀態"""
        if not data:
            print(f"❌ {analysis_type}失敗：無可用數據")
            return False
        
        lap_count = data.get('total_laps', 0) if isinstance(data, dict) else len(data) if hasattr(data, '__len__') else 1
        print(f"📊 {analysis_type}結果摘要：")
        print(f"   • 分析圈數: {lap_count}")
        print(f"   • 數據完整性: {'✅ 良好' if lap_count > 0 else '❌ 不足'}")
        
        print(f"✅ {analysis_type}分析完成！")
        return True
    
    def _perform_all_drivers_detailed_analysis(self, drivers_to_analyze, laps, session, weather_data, results):
        """執行全部車手的詳細每圈分析"""
        
        all_drivers_data = {}
        
        for driver in drivers_to_analyze:
            print(f"🔄 分析車手 {driver}...")
            
            driver_laps = laps[laps['Driver'] == driver].copy()
            
            if driver_laps.empty:
                print(f"⚠️ 車手 {driver} 無數據，跳過")
                continue
            
            # 執行單一車手的詳細分析
            driver_result = self._perform_detailed_analysis(driver, driver_laps, session, weather_data, results)
            
            if driver_result:
                all_drivers_data[driver] = driver_result
        
        if not all_drivers_data:
            print("❌ 沒有任何車手的有效數據")
            return None
        
        # 構建全部車手分析結果
        result = {
            "success": True,
            "drivers_analyzed": list(all_drivers_data.keys()),
            "year": self.year,
            "race": self.race,
            "session": self.session,
            "analysis_mode": "all",
            "analysis_timestamp": pd.Timestamp.now().isoformat(),
            "all_drivers_detailed_laptime": all_drivers_data
        }
        
        print(f"✅ 完成 {len(all_drivers_data)} 位車手的詳細圈速分析")
        return result
    
    def _display_cached_detailed_output(self, cached_result, driver):
        """顯示緩存數據的詳細輸出"""
        try:
            detailed_data = cached_result.get('detailed_lap_data', [])
            
            if not detailed_data:
                print("⚠️ 緩存數據中無詳細圈速資料")
                return
            
            # 創建詳細分析表格
            table = PrettyTable()
            table.field_names = ["圈數", "圈速", "輪胎", "胎齡", "進站", "天氣", "I1速度", "I2速度", "終點速", "備註"]
            table.align = "l"
            
            for lap_data in detailed_data:
                table.add_row([
                    lap_data.get('lap_number', 'N/A'),
                    lap_data.get('lap_time', 'N/A'),
                    lap_data.get('compound', 'N/A'),
                    lap_data.get('tire_age', 'N/A'),
                    lap_data.get('pit_info', ''),
                    lap_data.get('weather', 'N/A'),
                    lap_data.get('speed_i1', 'N/A'),
                    lap_data.get('speed_i2', 'N/A'),
                    lap_data.get('speed_fl', 'N/A'),
                    lap_data.get('remarks', '')
                ])
            
            # 顯示表格
            print(f"\n📊 {driver} 每圈詳細分析表:")
            print("=" * 120)
            print(table)
            
            # 顯示統計摘要
            summary_stats = cached_result.get('summary_statistics', {})
            if summary_stats:
                print(f"\n📈 {driver} 圈速統計摘要:")
                print(f"   • 最快圈速: {summary_stats.get('fastest_lap_time', 'N/A')}")
                print(f"   • 最慢圈速: {summary_stats.get('slowest_lap_time', 'N/A')}")
                print(f"   • 平均圈速: {summary_stats.get('average_lap_time', 'N/A')}")
                print(f"   • 圈速標準差: {summary_stats.get('lap_time_std', 'N/A')}")
                print(f"   • 進站次數: {summary_stats.get('pit_stops', 0)}")
                print(f"   • 使用輪胎: {', '.join(summary_stats.get('tire_compounds_used', []))}")
            
            print("=" * 120)
            
        except Exception as e:
            print(f"❌ 顯示緩存詳細輸出失敗: {e}")
    
    def _display_cached_all_drivers_output(self, cached_result):
        """顯示全部車手的緩存詳細輸出"""
        try:
            all_drivers_data = cached_result.get('all_drivers_detailed_laptime', {})
            
            if not all_drivers_data:
                print("⚠️ 緩存數據中無全部車手詳細圈速資料")
                return
            
            for driver, driver_data in all_drivers_data.items():
                print(f"\n{'='*60}")
                print(f"🏁 車手 {driver} 詳細圈速分析")
                print(f"{'='*60}")
                
                detailed_data = driver_data.get('detailed_lap_data', [])
                
                if not detailed_data:
                    print(f"⚠️ 車手 {driver} 無詳細圈速資料")
                    continue
                
                # 創建詳細分析表格
                table = PrettyTable()
                table.field_names = ["圈數", "圈速", "輪胎", "胎齡", "進站", "天氣", "I1速度", "I2速度", "終點速", "備註"]
                table.align = "l"
                
                for lap_data in detailed_data:
                    table.add_row([
                        lap_data.get('lap_number', 'N/A'),
                        lap_data.get('lap_time', 'N/A'),
                        lap_data.get('compound', 'N/A'),
                        lap_data.get('tire_age', 'N/A'),
                        lap_data.get('pit_info', ''),
                        lap_data.get('weather', 'N/A'),
                        lap_data.get('speed_i1', 'N/A'),
                        lap_data.get('speed_i2', 'N/A'),
                        lap_data.get('speed_fl', 'N/A'),
                        lap_data.get('remarks', '')
                    ])
                
                # 顯示表格
                print(table)
                
                # 顯示統計摘要
                summary_stats = driver_data.get('summary_statistics', {})
                if summary_stats:
                    print(f"\n📈 {driver} 圈速統計摘要:")
                    print(f"   • 最快圈速: {summary_stats.get('fastest_lap_time', 'N/A')}")
                    print(f"   • 最慢圈速: {summary_stats.get('slowest_lap_time', 'N/A')}")
                    print(f"   • 平均圈速: {summary_stats.get('average_lap_time', 'N/A')}")
                    print(f"   • 圈速標準差: {summary_stats.get('lap_time_std', 'N/A')}")
                    print(f"   • 進站次數: {summary_stats.get('pit_stops', 0)}")
                    print(f"   • 使用輪胎: {', '.join(summary_stats.get('tire_compounds_used', []))}")
            
            print(f"\n{'='*60}")
            print(f"✅ 全部車手詳細圈速分析顯示完成")
            print(f"{'='*60}")
            
        except Exception as e:
            print(f"❌ 顯示全部車手緩存詳細輸出失敗: {e}")
