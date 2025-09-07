#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
單一車手輪胎策略分析模組
提供車手輪胎使用策略和表現分析
"""

import os
import json
import pickle
from datetime import datetime
from typing import Dict, Any, Optional, List
from prettytable import PrettyTable

class SingleDriverTireAnalysis:
    """單一車手輪胎策略分析器"""
    
    def __init__(self, data_loader, year: int, race: str, session: str):
        self.data_loader = data_loader
        self.year = year
        self.race = race
        self.session = session
        self.cache_dir = "cache"
        
        # 確保緩存目錄存在
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def analyze_tire_strategy(self, driver: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """分析車手輪胎策略
        
        Args:
            driver: 車手代碼 (如 'VER', 'LEC')，如果為 None 則分析全部車手
            
        Returns:
            Dict: 包含輪胎策略分析結果的字典
        """
        if driver:
            print(f"🛞 開始分析車手 {driver} 的輪胎策略...")
            analysis_mode = "single"
        else:
            print("🛞 開始分析全部車手的輪胎策略...")
            analysis_mode = "all"
        
        try:
            # 生成緩存鍵
            if analysis_mode == "single":
                cache_key = f"tire_strategy_{self.year}_{self.race}_{self.session}_{driver}"
            else:
                cache_key = f"tire_strategy_{self.year}_{self.race}_{self.session}_all_drivers"
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
            
            # 檢查緩存
            if os.path.exists(cache_file):
                print("📦 從緩存載入輪胎策略數據...")
                with open(cache_file, 'rb') as f:
                    cached_result = pickle.load(f)
                
                # 顯示對應的 JSON 檔案路徑
                json_file = cache_file.replace('.pkl', '.json')
                if os.path.exists(json_file):
                    print(f"📄 對應 JSON 檔案: {json_file}")
                
                # 顯示輪胎策略表格
                self._display_tire_strategy_table(cached_result, driver)
                
                print("✅ 輪胎策略分析完成 (使用緩存)")
                return cached_result
            
            # 載入賽事數據
            session_data = self.data_loader.get_loaded_data()
            
            if session_data is None:
                raise ValueError("無法載入賽事數據")
            
            # 從數據字典中獲取圈速數據
            if isinstance(session_data, dict):
                laps_data = session_data.get('laps')
                if laps_data is None:
                    # 嘗試直接使用 session_data 作為 laps_data
                    laps_data = session_data
            else:
                laps_data = getattr(session_data, 'laps', None)
                if laps_data is None:
                    # 嘗試直接使用 session_data 作為 laps_data
                    laps_data = session_data
            
            # 根據分析模式獲取車手數據
            if analysis_mode == "single":
                # 單一車手分析
                driver_data = laps_data.pick_driver(driver)
                if driver_data.empty:
                    raise ValueError(f"找不到車手 {driver} 的數據")
                drivers_to_analyze = [driver]
                driver_data_dict = {driver: driver_data}
            else:
                # 全部車手分析
                all_drivers = laps_data['Driver'].unique().tolist()
                drivers_to_analyze = [d for d in all_drivers if d]
                driver_data_dict = {}
                for drv in drivers_to_analyze:
                    drv_data = laps_data.pick_driver(drv)
                    if not drv_data.empty:
                        driver_data_dict[drv] = drv_data
                
                if not driver_data_dict:
                    raise ValueError("找不到任何車手的數據")
                
                print(f"📊 將分析 {len(drivers_to_analyze)} 位車手的輪胎策略")
            
            # 分析輪胎策略
            if analysis_mode == "single":
                # 單一車手分析
                tire_strategy_data = {
                    "tire_compounds_used": self._get_tire_compounds_used(driver_data_dict[driver]),
                    "pit_stops": self._analyze_pit_stops(driver_data_dict[driver]),
                    "tire_performance": self._analyze_tire_performance(driver_data_dict[driver]),
                    "stint_analysis": self._analyze_stints(driver_data_dict[driver]),
                    "tire_degradation": self._analyze_tire_degradation(driver_data_dict[driver]),
                    "strategy_effectiveness": self._evaluate_strategy(driver_data_dict[driver])
                }
                
                result = {
                    "success": True,
                    "driver": driver,
                    "year": self.year,
                    "race": self.race,
                    "session": self.session,
                    "analysis_mode": "single",
                    "analysis_timestamp": datetime.now().isoformat(),
                    "tire_strategy": tire_strategy_data
                }
            else:
                # 全部車手分析
                all_drivers_tire_data = {}
                for drv, drv_data in driver_data_dict.items():
                    all_drivers_tire_data[drv] = {
                        "tire_compounds_used": self._get_tire_compounds_used(drv_data),
                        "pit_stops": self._analyze_pit_stops(drv_data),
                        "tire_performance": self._analyze_tire_performance(drv_data),
                        "stint_analysis": self._analyze_stints(drv_data),
                        "tire_degradation": self._analyze_tire_degradation(drv_data),
                        "strategy_effectiveness": self._evaluate_strategy(drv_data)
                    }
                
                result = {
                    "success": True,
                    "drivers_analyzed": list(driver_data_dict.keys()),
                    "year": self.year,
                    "race": self.race,
                    "session": self.session,
                    "analysis_mode": "all",
                    "analysis_timestamp": datetime.now().isoformat(),
                    "all_drivers_tire_strategy": all_drivers_tire_data
                }
            
            # 保存到緩存
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
            
            # 同時保存為 JSON
            json_file = cache_file.replace('.pkl', '.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"💾 JSON 分析結果已保存: {json_file}")
            
            # 顯示輪胎策略表格
            if analysis_mode == "single":
                self._display_tire_strategy_table(result, driver)
                print("✅ 單一車手輪胎策略分析完成")
            else:
                self._display_all_drivers_tire_strategy_table(result)
                print("✅ 全部車手輪胎策略分析完成")
            return result
            
        except Exception as e:
            print(f"❌ 輪胎策略分析失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "driver": driver,
                "analysis_timestamp": datetime.now().isoformat()
            }
    
    def _get_tire_compounds_used(self, driver_data) -> List[str]:
        """獲取使用的輪胎配方"""
        try:
            if 'Compound' in driver_data.columns:
                compounds = driver_data['Compound'].dropna().unique().tolist()
                return [c for c in compounds if c]
            return []
        except:
            return []
    
    def _analyze_pit_stops(self, driver_data) -> Dict[str, Any]:
        """分析進站策略"""
        try:
            # 檢測進站 (輪胎年齡重置為1的圈數)
            pit_stops = []
            if 'TyreLife' in driver_data.columns:
                tyre_life = driver_data['TyreLife'].fillna(0)
                for i in range(1, len(tyre_life)):
                    if tyre_life.iloc[i] == 1 and tyre_life.iloc[i-1] > 1:
                        pit_stops.append({
                            "lap": int(driver_data.iloc[i]['LapNumber']),
                            "from_compound": driver_data.iloc[i-1].get('Compound', 'Unknown'),
                            "to_compound": driver_data.iloc[i].get('Compound', 'Unknown')
                        })
            
            return {
                "total_pit_stops": len(pit_stops),
                "pit_stop_details": pit_stops,
                "average_pit_window": self._calculate_average_pit_window(pit_stops)
            }
        except:
            return {"error": "無法分析進站策略"}
    
    def _analyze_tire_performance(self, driver_data) -> Dict[str, Any]:
        """分析各輪胎配方表現"""
        try:
            performance_by_compound = {}
            
            if 'Compound' in driver_data.columns and 'LapTime' in driver_data.columns:
                for compound in driver_data['Compound'].dropna().unique():
                    compound_data = driver_data[driver_data['Compound'] == compound]
                    
                    # 只考慮有效圈速 (排除進出站等)
                    valid_times = compound_data['LapTime'].dropna()
                    if not valid_times.empty:
                        performance_by_compound[compound] = {
                            "laps_used": len(compound_data),
                            "average_lap_time": float(valid_times.mean().total_seconds()),
                            "best_lap_time": float(valid_times.min().total_seconds()),
                            "lap_time_range": float(valid_times.max().total_seconds() - valid_times.min().total_seconds())
                        }
            
            return performance_by_compound
        except:
            return {"error": "無法分析輪胎表現"}
    
    def _analyze_stints(self, driver_data) -> List[Dict[str, Any]]:
        """分析每個 stint (進站間的段落)"""
        try:
            stints = []
            current_stint = []
            
            if 'TyreLife' in driver_data.columns:
                for _, lap in driver_data.iterrows():
                    tyre_life = lap.get('TyreLife', 0)
                    
                    if tyre_life == 1 and current_stint:
                        # 新 stint 開始，結束上一個
                        stints.append(self._analyze_stint(current_stint))
                        current_stint = [lap]
                    else:
                        current_stint.append(lap)
                
                # 處理最後一個 stint
                if current_stint:
                    stints.append(self._analyze_stint(current_stint))
            
            return stints
        except:
            return []
    
    def _analyze_stint(self, stint_data: List) -> Dict[str, Any]:
        """分析單個 stint"""
        try:
            if not stint_data:
                return {}
            
            first_lap = stint_data[0]
            last_lap = stint_data[-1]
            
            return {
                "start_lap": int(first_lap.get('LapNumber', 0)),
                "end_lap": int(last_lap.get('LapNumber', 0)),
                "stint_length": len(stint_data),
                "compound": first_lap.get('Compound', 'Unknown'),
                "average_lap_time": self._calculate_average_stint_time(stint_data),
                "positions_gained": int(first_lap.get('Position', 0)) - int(last_lap.get('Position', 0))
            }
        except:
            return {"error": "無法分析 stint"}
    
    def _calculate_average_stint_time(self, stint_data: List) -> Optional[float]:
        """計算 stint 平均圈速"""
        try:
            valid_times = []
            for lap in stint_data:
                lap_time = lap.get('LapTime')
                if lap_time and hasattr(lap_time, 'total_seconds'):
                    valid_times.append(lap_time.total_seconds())
            
            if valid_times:
                return sum(valid_times) / len(valid_times)
        except:
            pass
        return None
    
    def _analyze_tire_degradation(self, driver_data) -> Dict[str, Any]:
        """分析輪胎衰退"""
        try:
            degradation_data = {}
            
            if 'Compound' in driver_data.columns and 'TyreLife' in driver_data.columns:
                for compound in driver_data['Compound'].dropna().unique():
                    compound_data = driver_data[driver_data['Compound'] == compound]
                    
                    if len(compound_data) > 5:  # 至少5圈數據
                        degradation_data[compound] = self._calculate_degradation_rate(compound_data)
            
            return degradation_data
        except:
            return {"error": "無法分析輪胎衰退"}
    
    def _calculate_degradation_rate(self, compound_data) -> Dict[str, Any]:
        """計算特定配方的衰退率"""
        try:
            # 簡化的衰退分析 - 比較前5圈和後5圈
            if len(compound_data) >= 10:
                first_5 = compound_data.head(5)['LapTime'].dropna().mean()
                last_5 = compound_data.tail(5)['LapTime'].dropna().mean()
                
                if first_5 and last_5:
                    degradation = (last_5 - first_5).total_seconds()
                    return {
                        "degradation_seconds": degradation,
                        "degradation_percentage": (degradation / first_5.total_seconds()) * 100
                    }
            
            return {"insufficient_data": True}
        except:
            return {"error": "計算失敗"}
    
    def _calculate_average_pit_window(self, pit_stops: List) -> Optional[float]:
        """計算平均進站間隔"""
        try:
            if len(pit_stops) > 1:
                intervals = []
                for i in range(1, len(pit_stops)):
                    interval = pit_stops[i]["lap"] - pit_stops[i-1]["lap"]
                    intervals.append(interval)
                return sum(intervals) / len(intervals)
        except:
            pass
        return None
    
    def _evaluate_strategy(self, driver_data) -> Dict[str, Any]:
        """評估策略效果"""
        try:
            start_pos = driver_data.iloc[0].get('Position', 0) if not driver_data.empty else 0
            end_pos = driver_data.iloc[-1].get('Position', 0) if not driver_data.empty else 0
            
            return {
                "starting_position": int(start_pos),
                "finishing_position": int(end_pos),
                "positions_gained": int(start_pos) - int(end_pos),
                "strategy_rating": self._rate_strategy(start_pos, end_pos)
            }
        except:
            return {"error": "無法評估策略"}
    
    def _rate_strategy(self, start_pos: int, end_pos: int) -> str:
        """評估策略等級"""
        try:
            gain = start_pos - end_pos
            if gain >= 5:
                return "Excellent"
            elif gain >= 2:
                return "Good"
            elif gain >= 0:
                return "Average"
            elif gain >= -2:
                return "Below Average"
            else:
                return "Poor"
        except:
            return "Unknown"
    
    def _display_tire_strategy_table(self, result: Dict[str, Any], driver: str):
        """顯示輪胎策略分析結果表格"""
        try:
            tire_data = result.get('tire_strategy', {})
            
            print(f"\n🛞 車手 {driver} 輪胎策略分析結果")
            print("=" * 80)
            
            # 輪胎配方使用表格
            compounds_used = tire_data.get('tire_compounds_used', [])
            if compounds_used:
                compound_table = PrettyTable()
                compound_table.field_names = ["輪胎配方", "狀態"]
                compound_table.align["輪胎配方"] = "l"
                
                for compound in compounds_used:
                    compound_table.add_row([compound, "✅ 已使用"])
                
                print(f"\n🔧 使用的輪胎配方:")
                print(compound_table)
            
            # 進站策略表格
            pit_stops = tire_data.get('pit_stops', {})
            if pit_stops and not pit_stops.get('error'):
                pit_table = PrettyTable()
                pit_table.field_names = ["進站次序", "圈數", "從配方", "到配方"]
                pit_table.align["從配方"] = "c"
                pit_table.align["到配方"] = "c"
                
                pit_details = pit_stops.get('pit_stop_details', [])
                total_stops = pit_stops.get('total_pit_stops', 0)
                
                if pit_details:
                    for i, stop in enumerate(pit_details, 1):
                        lap_num = stop.get('lap', 'N/A')
                        from_compound = stop.get('from_compound', 'Unknown')
                        to_compound = stop.get('to_compound', 'Unknown')
                        pit_table.add_row([f"第 {i} 次", f"第 {lap_num} 圈", from_compound, to_compound])
                else:
                    pit_table.add_row(["無進站", "整場比賽", "同一配方", "同一配方"])
                
                avg_window = pit_stops.get('average_pit_window')
                avg_info = f" (平均間隔: {avg_window:.1f} 圈)" if avg_window else ""
                
                print(f"\n🔄 進站策略 (總計 {total_stops} 次{avg_info}):")
                print(pit_table)
            
            # 各配方表現表格
            performance = tire_data.get('tire_performance', {})
            if performance and not performance.get('error'):
                perf_table = PrettyTable()
                perf_table.field_names = ["輪胎配方", "使用圈數", "平均圈速", "最快圈速", "圈速差距"]
                perf_table.align["輪胎配方"] = "c"
                
                for compound, data in performance.items():
                    laps_used = data.get('laps_used', 0)
                    avg_time = data.get('average_lap_time', 0)
                    best_time = data.get('best_lap_time', 0)
                    time_range = data.get('lap_time_range', 0)
                    
                    avg_str = f"{avg_time//60:.0f}:{avg_time%60:06.3f}" if avg_time > 0 else "N/A"
                    best_str = f"{best_time//60:.0f}:{best_time%60:06.3f}" if best_time > 0 else "N/A"
                    range_str = f"{time_range:.3f}s" if time_range > 0 else "N/A"
                    
                    perf_table.add_row([compound, f"{laps_used} 圈", avg_str, best_str, range_str])
                
                print(f"\n📊 各配方表現分析:")
                print(perf_table)
            
            # Stint 分析表格
            stints = tire_data.get('stint_analysis', [])
            if stints:
                stint_table = PrettyTable()
                stint_table.field_names = ["Stint", "起始圈", "結束圈", "長度", "配方", "平均圈速", "位置變化"]
                stint_table.align["配方"] = "c"
                stint_table.align["位置變化"] = "c"
                
                for i, stint in enumerate(stints, 1):
                    if not stint.get('error'):
                        start_lap = stint.get('start_lap', 0)
                        end_lap = stint.get('end_lap', 0)
                        length = stint.get('stint_length', 0)
                        compound = stint.get('compound', 'Unknown')
                        avg_time = stint.get('average_lap_time')
                        pos_change = stint.get('positions_gained', 0)
                        
                        avg_str = f"{avg_time//60:.0f}:{avg_time%60:06.3f}" if avg_time and avg_time > 0 else "N/A"
                        pos_str = f"+{pos_change}" if pos_change > 0 else str(pos_change) if pos_change < 0 else "0"
                        
                        stint_table.add_row([f"Stint {i}", start_lap, end_lap, f"{length} 圈", compound, avg_str, pos_str])
                
                print(f"\n⏱️ Stint 分析:")
                print(stint_table)
            
            # 策略效果評估
            strategy_eval = tire_data.get('strategy_effectiveness', {})
            if strategy_eval and not strategy_eval.get('error'):
                eval_table = PrettyTable()
                eval_table.field_names = ["評估項目", "數值", "說明"]
                eval_table.align["評估項目"] = "l"
                eval_table.align["說明"] = "l"
                
                start_pos = strategy_eval.get('starting_position', 0)
                finish_pos = strategy_eval.get('finishing_position', 0)
                positions_gained = strategy_eval.get('positions_gained', 0)
                rating = strategy_eval.get('strategy_rating', 'Unknown')
                
                eval_table.add_row(["起始位置", start_pos, "比賽開始時的位置"])
                eval_table.add_row(["完賽位置", finish_pos, "比賽結束時的位置"])
                eval_table.add_row(["位置變化", f"{positions_gained:+d}", "正數為進步，負數為退步"])
                eval_table.add_row(["策略評級", rating, "策略整體效果評級"])
                
                print(f"\n🎯 策略效果評估:")
                print(eval_table)
            
            print("=" * 80)
            
        except Exception as e:
            print(f"❌ 顯示輪胎策略表格失敗: {e}")
            # 顯示基本信息作為備用
            print(f"\n🛞 車手 {driver} 輪胎策略分析結果 (簡化版)")
            print(f"分析時間: {result.get('analysis_timestamp', 'Unknown')}")
            print(f"分析狀態: {'成功' if result.get('success') else '失敗'}")
    
    def _display_all_drivers_tire_strategy_table(self, result: Dict[str, Any]):
        """顯示全部車手輪胎策略分析結果表格"""
        try:
            all_drivers_data = result.get('all_drivers_tire_strategy', {})
            drivers_analyzed = result.get('drivers_analyzed', [])
            
            print(f"\n🛞 全部車手輪胎策略分析結果")
            print("=" * 100)
            print(f"📊 共分析 {len(drivers_analyzed)} 位車手")
            
            # 創建總覽表格
            overview_table = PrettyTable()
            overview_table.field_names = ["車手", "輪胎配方", "進站次數", "主要策略"]
            overview_table.align = "c"
            
            for driver in drivers_analyzed:
                driver_data = all_drivers_data.get(driver, {})
                tire_compounds = driver_data.get('tire_compounds_used', [])
                pit_stops = driver_data.get('pit_stops', {})
                
                compounds_str = ", ".join(tire_compounds) if tire_compounds else "未知"
                pit_count = pit_stops.get('total_pit_stops', 0) if isinstance(pit_stops, dict) else 0
                
                # 判斷主要策略
                if pit_count == 0:
                    strategy = "一停策略"
                elif pit_count == 1:
                    strategy = "兩停策略"
                elif pit_count == 2:
                    strategy = "三停策略"
                else:
                    strategy = f"{pit_count+1}停策略"
                
                overview_table.add_row([driver, compounds_str, pit_count, strategy])
            
            print(f"\n📋 車手輪胎策略總覽:")
            print(overview_table)
            
            # 顯示每個車手的詳細信息
            for driver in drivers_analyzed:
                driver_data = all_drivers_data.get(driver, {})
                print(f"\n{'='*50}")
                print(f"🏎️ 車手 {driver} 詳細分析")
                print(f"{'='*50}")
                
                # 輪胎配方
                compounds = driver_data.get('tire_compounds_used', [])
                if compounds:
                    print(f"🔧 使用的輪胎配方: {', '.join(compounds)}")
                
                # 進站信息
                pit_stops = driver_data.get('pit_stops', {})
                if isinstance(pit_stops, dict) and not pit_stops.get('error'):
                    pit_count = pit_stops.get('total_pit_stops', 0)
                    print(f"🔄 進站次數: {pit_count}")
                    
                    pit_details = pit_stops.get('pit_stop_details', [])
                    if pit_details:
                        print("   進站詳情:")
                        for i, stop in enumerate(pit_details, 1):
                            lap = stop.get('lap', 'N/A')
                            from_compound = stop.get('from_compound', 'Unknown')
                            to_compound = stop.get('to_compound', 'Unknown')
                            print(f"   {i}. 第{lap}圈: {from_compound} → {to_compound}")
                
                # 輪胎表現
                performance = driver_data.get('tire_performance', {})
                if isinstance(performance, dict) and not performance.get('error'):
                    print("📊 輪胎表現:")
                    for compound, data in performance.items():
                        laps_used = data.get('laps_used', 0)
                        avg_time = data.get('average_lap_time', 0)
                        best_time = data.get('best_lap_time', 0)
                        
                        if avg_time > 0:
                            avg_str = f"{avg_time//60:.0f}:{avg_time%60:06.3f}"
                            best_str = f"{best_time//60:.0f}:{best_time%60:06.3f}" if best_time > 0 else "N/A"
                            print(f"   {compound}: {laps_used}圈, 平均{best_str}, 最快{best_str}")
            
            print(f"\n{'='*100}")
            print("✅ 全部車手輪胎策略分析完成")
            
        except Exception as e:
            print(f"❌ 顯示全部車手輪胎策略表格失敗: {e}")
            # 顯示基本信息作為備用
            drivers_analyzed = result.get('drivers_analyzed', [])
            print(f"\n🛞 全部車手輪胎策略分析結果 (簡化版)")
            print(f"分析車手數量: {len(drivers_analyzed)}")
            print(f"車手列表: {', '.join(drivers_analyzed)}")
            print(f"分析時間: {result.get('analysis_timestamp', 'Unknown')}")
            print(f"分析狀態: {'成功' if result.get('success') else '失敗'}")
