#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
單一車手比賽位置分析模組
提供車手在比賽中的位置變化分析
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from prettytable import PrettyTable
import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')


class SingleDriverPositionAnalysis:
    """單一車手比賽位置分析器"""
    
    def __init__(self, data_loader, year: int, race: str, session: str):
        self.data_loader = data_loader
        self.year = year
        self.race = race
        self.session = session
        self.cache_dir = "json"
        
        # 確保輸出目錄存在
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def analyze_position_changes(self, driver: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """分析車手位置變化
        
        Args:
            driver: 車手代碼 (如 'VER', 'LEC')，如果為 None 則分析全部車手
            
        Returns:
            Dict: 包含位置分析結果的字典
        """
        if driver:
            print(f"🏁 開始分析車手 {driver} 的比賽位置變化...")
            analysis_mode = "single"
        else:
            print("🏁 開始分析全部車手的比賽位置變化...")
            analysis_mode = "all"
        
        try:
            # 生成檔案名稱（符合 API 搜索模式）
            if analysis_mode == "single":
                cache_key = f"driver_race_position_{self.year}_{self.race}_{self.session}_{driver}"
            else:
                cache_key = f"driver_race_position_{self.year}_{self.race}_{self.session}"
            
            # ✅ 改為僅使用 JSON 檔案
            json_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            
            # 檢查 JSON 緩存
            if os.path.exists(json_file):
                print("📦 從 JSON 緩存載入位置分析數據...")
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        cached_result = json.load(f)
                    
                    # ✅ 驗證數據有效性
                    if not cached_result.get("success"):
                        print("⚠️  緩存數據標記為失敗，重新生成...")
                    elif analysis_mode == "all" and not cached_result.get("all_drivers_position_analysis"):
                        print("⚠️  緩存數據缺少車手分析，重新生成...")
                    elif analysis_mode == "single" and not cached_result.get("position_analysis"):
                        print("⚠️  緩存數據缺少位置分析，重新生成...")
                    else:
                        print(f"📄 使用 JSON 檔案: {json_file}")
                        
                        # 顯示位置變化表格
                        self._display_position_analysis_table(cached_result, driver)
                        
                        print("✅ 位置分析完成 (使用 JSON 緩存)")
                        return cached_result
                except Exception as e:
                    print(f"⚠️  讀取 JSON 緩存失敗: {e}，重新生成...")
            
            # 載入賽事數據
            session_data = self.data_loader.get_loaded_data()
            
            if session_data is None:
                raise ValueError("無法載入賽事數據")
            
            # 從數據字典中獲取圈速數據和結果數據
            if isinstance(session_data, dict):
                laps_data = session_data.get('laps')
                results_data = session_data.get('results')
                if laps_data is None:
                    raise ValueError("無法找到圈速數據")
            else:
                laps_data = getattr(session_data, 'laps', None)
                results_data = getattr(session_data, 'results', None)
                if laps_data is None:
                    raise ValueError("無法找到圈速數據")
            
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
                
                print(f"📊 將分析 {len(drivers_to_analyze)} 位車手的比賽位置變化")
            
            # 分析位置變化
            if analysis_mode == "single":
                # 單一車手分析
                result = {
                    "success": True,
                    "driver": driver,
                    "year": self.year,
                    "race": self.race,
                    "session": self.session,
                    "analysis_mode": "single",
                    "analysis_timestamp": datetime.now().isoformat(),
                    "position_analysis": {
                        "starting_position": self._get_starting_position(driver_data_dict[driver]),
                        "finishing_position": self._get_finishing_position(driver_data_dict[driver], results_data, driver),
                        "position_changes": self._analyze_position_changes(driver_data_dict[driver]),
                        "best_position": self._get_best_position(driver_data_dict[driver]),
                        "worst_position": self._get_worst_position(driver_data_dict[driver]),
                        "total_laps": len(driver_data_dict[driver]),
                        "position_statistics": self._calculate_position_statistics(driver_data_dict[driver])
                    }
                }
            else:
                # 全部車手分析
                all_drivers_position_data = {}
                for drv, drv_data in driver_data_dict.items():
                    # 從 results 中獲取車隊資訊
                    team_name = "Unknown"
                    if results_data is not None:
                        try:
                            driver_result = results_data[results_data['Abbreviation'] == drv]
                            if not driver_result.empty:
                                team_name = driver_result.iloc[0]['TeamName']
                        except Exception as e:
                            print(f"⚠️ 無法獲取車手 {drv} 的車隊資訊: {e}")
                    
                    all_drivers_position_data[drv] = {
                        "team": team_name,
                        "starting_position": self._get_starting_position(drv_data),
                        "finishing_position": self._get_finishing_position(drv_data, results_data, drv),
                        "position_changes": self._analyze_position_changes(drv_data),
                        "best_position": self._get_best_position(drv_data),
                        "worst_position": self._get_worst_position(drv_data),
                        "total_laps": len(drv_data),
                        "position_statistics": self._calculate_position_statistics(drv_data)
                    }
                
                result = {
                    "success": True,
                    "drivers_analyzed": list(driver_data_dict.keys()),
                    "year": self.year,
                    "race": self.race,
                    "session": self.session,
                    "analysis_mode": "all",
                    "analysis_timestamp": datetime.now().isoformat(),
                    "all_drivers_position_analysis": all_drivers_position_data
                }
            
            # ✅ 僅保存為 JSON（移除 .pkl）
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"💾 JSON 分析結果已保存: {json_file}")
            
            # 顯示位置變化表格
            if analysis_mode == "single":
                self._display_position_analysis_table(result, driver)
                print("✅ 單一車手比賽位置分析完成")
            else:
                self._display_all_drivers_position_analysis_table(result)
                print("✅ 全部車手比賽位置分析完成")
            return result
            
        except Exception as e:
            print(f"❌ 位置分析失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "driver": driver,
                "analysis_timestamp": datetime.now().isoformat()
            }
    
    def _get_starting_position(self, driver_data) -> Optional[int]:
        """獲取起始位置"""
        try:
            if not driver_data.empty:
                return int(driver_data.iloc[0]['Position'])
        except:
            pass
        return None
    
    def _get_finishing_position(self, driver_data, results_data=None, driver_abbr=None):
        """
        獲取完賽位置
        
        返回:
            - int: 完賽位置 (1-20)
            - str: "DNF" (退賽)
            - None: 無數據
        """
        try:
            if not driver_data.empty:
                # 檢查 DNF 狀態 (從 session.results 獲取)
                if results_data is not None and driver_abbr is not None:
                    try:
                        driver_result = results_data[results_data['Abbreviation'] == driver_abbr]
                        if not driver_result.empty:
                            status = driver_result.iloc[0]['Status']
                            if status == 'Retired':
                                return "DNF"
                    except Exception as e:
                        print(f"⚠️ 無法檢查車手 {driver_abbr} 的 Status: {e}")
                
                # 正常完賽：返回位置
                return int(driver_data.iloc[-1]['Position'])
        except:
            pass
        return None
    
    def _get_best_position(self, driver_data) -> Optional[int]:
        """獲取最佳位置"""
        try:
            if not driver_data.empty:
                return int(driver_data['Position'].min())
        except:
            pass
        return None
    
    def _get_worst_position(self, driver_data) -> Optional[int]:
        """獲取最差位置"""
        try:
            if not driver_data.empty:
                return int(driver_data['Position'].max())
        except:
            pass
        return None
    
    def _analyze_position_changes(self, driver_data) -> Dict[str, Any]:
        """分析位置變化詳細"""
        try:
            positions = driver_data['Position'].tolist()
            changes = []
            
            for i in range(1, len(positions)):
                change = positions[i-1] - positions[i]  # 正數為進步，負數為退步
                changes.append({
                    "lap": i + 1,
                    "from_position": positions[i-1],
                    "to_position": positions[i],
                    "change": change
                })
            
            return {
                "lap_by_lap_changes": changes,
                "total_changes": len([c for c in changes if c['change'] != 0]),
                "positions_gained": sum([c['change'] for c in changes if c['change'] > 0]),
                "positions_lost": abs(sum([c['change'] for c in changes if c['change'] < 0]))
            }
        except:
            return {"error": "無法分析位置變化"}
    
    def _calculate_position_statistics(self, driver_data) -> Dict[str, Any]:
        """計算位置統計"""
        try:
            positions = driver_data['Position']
            return {
                "average_position": float(positions.mean()),
                "median_position": float(positions.median()),
                "position_variance": float(positions.var()),
                "time_in_top_5": len(positions[positions <= 5]),
                "time_in_top_10": len(positions[positions <= 10]),
                "time_in_points": len(positions[positions <= 10])  # 前10名得分
            }
        except:
            return {"error": "無法計算位置統計"}
    
    def _display_position_analysis_table(self, result: Dict[str, Any], driver: str):
        """顯示位置分析結果表格"""
        try:
            position_data = result.get('position_analysis', {})
            
            print(f"\n🏁 車手 {driver} 比賽位置分析結果")
            print("=" * 80)
            
            # 基本位置信息表格
            basic_table = PrettyTable()
            basic_table.field_names = ["項目", "位置", "說明"]
            basic_table.align["項目"] = "l"
            basic_table.align["說明"] = "l"
            
            start_pos = position_data.get('starting_position', 'N/A')
            finish_pos = position_data.get('finishing_position', 'N/A')
            best_pos = position_data.get('best_position', 'N/A')
            worst_pos = position_data.get('worst_position', 'N/A')
            total_laps = position_data.get('total_laps', 0)
            
            basic_table.add_row(["起始位置", start_pos, "比賽開始時的位置"])
            basic_table.add_row(["完賽位置", finish_pos, "比賽結束時的位置"])
            basic_table.add_row(["最佳位置", best_pos, "比賽中達到的最高位置"])
            basic_table.add_row(["最差位置", worst_pos, "比賽中的最低位置"])
            basic_table.add_row(["總圈數", total_laps, "完成的總圈數"])
            
            if start_pos != 'N/A' and finish_pos != 'N/A':
                position_change = start_pos - finish_pos
                change_desc = f"進步 {position_change} 位" if position_change > 0 else f"退步 {abs(position_change)} 位" if position_change < 0 else "位置無變化"
                basic_table.add_row(["總位置變化", f"{position_change:+d}", change_desc])
            
            print("\n📊 基本位置統計:")
            print(basic_table)
            
            # 位置變化詳細表格 (顯示前 20 圈的變化)
            position_changes = position_data.get('position_changes', {})
            lap_changes = position_changes.get('lap_by_lap_changes', [])
            
            if lap_changes:
                change_table = PrettyTable()
                change_table.field_names = ["圈數", "從位置", "到位置", "變化", "說明"]
                change_table.align["說明"] = "l"
                
                # 只顯示前 20 圈或有變化的圈數
                display_changes = [c for c in lap_changes[:20] if c.get('change', 0) != 0][:15]
                
                for change in display_changes:
                    lap_num = change.get('lap', 0)
                    from_pos = change.get('from_position', 0)
                    to_pos = change.get('to_position', 0)
                    pos_change = change.get('change', 0)
                    
                    if pos_change > 0:
                        change_desc = f"超越 {pos_change} 位"
                        change_str = f"+{pos_change}"
                    elif pos_change < 0:
                        change_desc = f"被超 {abs(pos_change)} 位"
                        change_str = str(pos_change)
                    else:
                        change_desc = "位置保持"
                        change_str = "0"
                    
                    change_table.add_row([lap_num, from_pos, to_pos, change_str, change_desc])
                
                if display_changes:
                    print(f"\n📈 位置變化詳細 (顯示前 {len(display_changes)} 個變化):")
                    print(change_table)
                else:
                    print("\n📈 位置變化: 比賽中位置保持穩定，無重大位置變化")
            
            # 位置統計摘要
            stats = position_data.get('position_statistics', {})
            if stats and not stats.get('error'):
                stats_table = PrettyTable()
                stats_table.field_names = ["統計項目", "數值", "說明"]
                stats_table.align["統計項目"] = "l"
                stats_table.align["說明"] = "l"
                
                avg_pos = stats.get('average_position', 0)
                median_pos = stats.get('median_position', 0)
                top5_time = stats.get('time_in_top_5', 0)
                top10_time = stats.get('time_in_top_10', 0)
                points_time = stats.get('time_in_points', 0)
                
                stats_table.add_row(["平均位置", f"{avg_pos:.1f}", "整場比賽的平均位置"])
                stats_table.add_row(["中位數位置", f"{median_pos:.1f}", "位置分布的中位數"])
                stats_table.add_row(["前5位圈數", f"{top5_time} 圈", f"在前5位的圈數 ({top5_time/total_laps*100:.1f}%)" if total_laps > 0 else "在前5位的圈數"])
                stats_table.add_row(["前10位圈數", f"{top10_time} 圈", f"在前10位的圈數 ({top10_time/total_laps*100:.1f}%)" if total_laps > 0 else "在前10位的圈數"])
                stats_table.add_row(["得分區圈數", f"{points_time} 圈", f"在得分區的圈數 ({points_time/total_laps*100:.1f}%)" if total_laps > 0 else "在得分區的圈數"])
                
                print(f"\n📊 位置統計摘要:")
                print(stats_table)
            
            # 位置變化總結
            if position_changes:
                total_changes = position_changes.get('total_changes', 0)
                positions_gained = position_changes.get('positions_gained', 0)
                positions_lost = position_changes.get('positions_lost', 0)
                
                print(f"\n📋 位置變化總結:")
                print(f"   • 總位置變化次數: {total_changes} 次")
                print(f"   • 累積進步位置: {positions_gained} 位")
                print(f"   • 累積退步位置: {positions_lost} 位")
                print(f"   • 淨位置變化: {int(positions_gained - positions_lost):+d} 位")
            
            print("=" * 80)
            
        except Exception as e:
            print(f"❌ 顯示位置分析表格失敗: {e}")
            # 顯示基本信息作為備用
            print(f"\n🏁 車手 {driver} 比賽位置分析結果 (簡化版)")
            print(f"分析時間: {result.get('analysis_timestamp', 'Unknown')}")
            print(f"分析狀態: {'成功' if result.get('success') else '失敗'}")
    
    def _display_all_drivers_position_analysis_table(self, result: Dict[str, Any]):
        """顯示全部車手比賽位置分析結果表格"""
        try:
            all_drivers_data = result.get('all_drivers_position_analysis', {})
            drivers_analyzed = result.get('drivers_analyzed', [])
            
            print(f"\n🏁 全部車手比賽位置分析結果")
            print("=" * 100)
            print(f"📊 共分析 {len(drivers_analyzed)} 位車手")
            
            # 創建總覽表格
            overview_table = PrettyTable()
            overview_table.field_names = ["車手", "起跑位置", "終點位置", "最佳位置", "最差位置", "位置變化"]
            overview_table.align = "c"
            
            for driver in drivers_analyzed:
                driver_data = all_drivers_data.get(driver, {})
                starting_pos = driver_data.get('starting_position', 'N/A')
                finishing_pos = driver_data.get('finishing_position', 'N/A')
                best_pos = driver_data.get('best_position', 'N/A')
                worst_pos = driver_data.get('worst_position', 'N/A')
                
                # 計算總位置變化
                position_changes_data = driver_data.get('position_changes', {})
                if isinstance(position_changes_data, dict):
                    lap_changes = position_changes_data.get('lap_by_lap_changes', [])
                else:
                    lap_changes = position_changes_data if isinstance(position_changes_data, list) else []
                
                if lap_changes:
                    total_change = sum(change.get('change', 0) for change in lap_changes)
                    change_str = f"{total_change:+d}"
                else:
                    change_str = "N/A"
                
                overview_table.add_row([driver, starting_pos, finishing_pos, best_pos, worst_pos, change_str])
            
            print(f"\n📋 車手位置變化總覽:")
            print(overview_table)
            
            # 顯示每個車手的詳細信息
            for driver in drivers_analyzed:
                driver_data = all_drivers_data.get(driver, {})
                print(f"\n{'='*60}")
                print(f"🏎️ 車手 {driver} 詳細分析")
                print(f"{'='*60}")
                
                starting_pos = driver_data.get('starting_position', 'N/A')
                finishing_pos = driver_data.get('finishing_position', 'N/A')
                best_pos = driver_data.get('best_position', 'N/A')
                worst_pos = driver_data.get('worst_position', 'N/A')
                
                print(f"🏁 起跑位置: {starting_pos}")
                print(f"🏆 終點位置: {finishing_pos}")
                print(f"📈 最佳位置: {best_pos}")
                print(f"📉 最差位置: {worst_pos}")
                
                # 位置變化統計
                position_changes_data = driver_data.get('position_changes', {})
                if isinstance(position_changes_data, dict):
                    lap_changes = position_changes_data.get('lap_by_lap_changes', [])
                else:
                    lap_changes = position_changes_data if isinstance(position_changes_data, list) else []
                
                if lap_changes:
                    positions_gained = sum(1 for change in lap_changes if change.get('change', 0) > 0)
                    positions_lost = sum(1 for change in lap_changes if change.get('change', 0) < 0)
                    total_change = sum(change.get('change', 0) for change in lap_changes)
                    
                    print(f"📊 位置變化統計:")
                    print(f"   • 總圈數: {len(lap_changes)}")
                    print(f"   • 超越次數: {positions_gained}")
                    print(f"   • 被超次數: {positions_lost}")
                    print(f"   • 淨位置變化: {total_change:+d} 位")
                
                # 位置穩定性
                stability = driver_data.get('position_stability', {})
                if stability and not stability.get('error'):
                    avg_pos = stability.get('average_position', 'N/A')
                    pos_std = stability.get('position_std', 'N/A')
                    if avg_pos != 'N/A' and pos_std != 'N/A':
                        print(f"📈 位置穩定性:")
                        print(f"   • 平均位置: {avg_pos:.1f}")
                        print(f"   • 位置標準差: {pos_std:.2f}")
            
            print(f"\n{'='*100}")
            print("✅ 全部車手比賽位置分析完成")
            
        except Exception as e:
            print(f"❌ 顯示全部車手位置分析表格失敗: {e}")
            # 顯示基本信息作為備用
            drivers_analyzed = result.get('drivers_analyzed', [])
            print(f"\n🏁 全部車手比賽位置分析結果 (簡化版)")
            print(f"分析車手數量: {len(drivers_analyzed)}")
            print(f"車手列表: {', '.join(drivers_analyzed)}")
            print(f"分析時間: {result.get('analysis_timestamp', 'Unknown')}")
            print(f"分析狀態: {'成功' if result.get('success') else '失敗'}")
