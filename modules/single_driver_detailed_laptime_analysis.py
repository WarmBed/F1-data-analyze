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
        
    def analyze_every_lap(self, driver, show_detailed_output=True, **kwargs):
        """Function 27: 分析車手的每一圈詳細數據
        
        Args:
            driver: 車手代碼
            show_detailed_output: 是否顯示詳細輸出，即使使用緩存也顯示完整表格
        """
        try:
            print(f"⏱️ 開始執行 {driver} 的每圈圈速詳細分析...")
            
            # 生成緩存鍵值
            cache_key = f"detailed_laptime_analysis_{self.year}_{self.race}_{self.session}_{driver}"
            
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
                    self._display_cached_detailed_output(cached_result, driver)
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
            
            # 獲取車手數據
            driver_laps = laps[laps['Driver'] == driver].copy()
            
            if driver_laps.empty:
                print(f"❌ 找不到車手 {driver} 的數據")
                return None
            
            # 執行詳細分析
            result = self._perform_detailed_analysis(driver, driver_laps, session, weather_data, results)
            
            # 結果驗證和反饋
            if not self._report_analysis_results(result, "車手每圈圈速詳細分析"):
                return None
            
            # 保存緩存
            if self.cache_enabled and result:
                self._save_cache(result, cache_key)
                print("💾 分析結果已緩存")
            
            # 保存JSON輸出
            self._save_json_output(result, driver)
            
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
            # 簡化的天氣判斷
            if 'TrackTemp' in weather_data.columns:
                avg_temp = weather_data['TrackTemp'].mean()
                if avg_temp > 40:
                    return "🌡️熱"
                elif avg_temp < 25:
                    return "❄️涼"
                else:
                    return "🌤️適中"
            return "☀️乾"
        except:
            return "N/A"
    
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
        json_dir = "json"
        os.makedirs(json_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"detailed_laptime_analysis_{driver}_{self.year}_{timestamp}.json"
        json_path = os.path.join(json_dir, json_filename)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"📄 JSON 分析報告已保存: {json_path}")
    
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
