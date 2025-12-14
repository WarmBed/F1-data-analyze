#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1 車隊進站時間排行榜模組 (功能4)
Team Pitstop Ranking Module

分析各車隊的進站表現，提供統計分析和排名
優先使用 OpenF1 API 獲取準確的進站時間數據
符合 copilot-instructions 開發核心要求

版本: 1.0
作者: F1 Analysis Team
"""

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import os
import pickle
import json
import statistics
from datetime import datetime
from prettytable import PrettyTable

# 導入 OpenF1 分析器
try:
    from ..core.openf1_data_analyzer import F1OpenDataAnalyzer
except ImportError:
    try:
        from CLI_modules.cli.core.openf1_data_analyzer import F1OpenDataAnalyzer
    except ImportError:
        print("[WARNING] 無法導入 OpenF1 數據分析器")
        F1OpenDataAnalyzer = None


def check_cache(cache_key):
    """檢查緩存是否存在"""
    cache_dir = "cache"
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"{cache_key}.pkl")
    
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"[WARNING] 緩存載入失敗: {e}")
            return None
    return None


def save_cache(data, cache_key):
    """保存數據到緩存"""
    cache_dir = "cache"
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"{cache_key}.pkl")
    
    try:
        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)
    except Exception as e:
        print(f"[WARNING] 緩存保存失敗: {e}")


def report_analysis_results(data, analysis_type="analysis"):
    """報告分析結果狀態"""
    if not data:
        print(f"❌ {analysis_type}失敗：無可用數據")
        return False
    
    data_count = len(data) if isinstance(data, list) else 0
    print(f"📊 {analysis_type}結果摘要：")
    print(f"   • 車隊數量: {data_count}")
    print(f"   • 數據完整性: {'✅ 良好' if data_count > 0 else '❌ 不足'}")
    
    if data_count > 0:
        print(f"   • 最快車隊: {data[0]['team']}")
        print(f"   • 最快時間: {data[0]['fastest_time']:.1f}秒")
    
    print(f"✅ {analysis_type}分析完成！")
    return True


def standardize_race_name(event_name: str) -> str:
    """統一賽事名稱以匹配 OpenF1 API 搜尋格式"""
    if not event_name:
        return "unknown"

    race_name_mapping = {
        "bahrain grand prix": "bahrain",
        "bahrain": "bahrain",
        "saudi arabian grand prix": "saudi arabia",
        "saudi arabia": "saudi arabia",
        "australian grand prix": "australia",
        "australia": "australia",
        "japanese grand prix": "japan",
        "japan": "japan",
        "chinese grand prix": "china",
        "china": "china",
        "monaco grand prix": "monaco",
        "monaco": "monaco",
        "spanish grand prix": "spain",
        "spain": "spain",
        "canadian grand prix": "canada",
        "canada": "canada",
        "austrian grand prix": "austria",
        "austria": "austria",
        "french grand prix": "france",
        "france": "france",
        "hungarian grand prix": "hungary",
        "hungary": "hungary",
        "belgian grand prix": "belgium",
        "belgium": "belgium",
        "italian grand prix": "italy",
        "italy": "italy",
        "singapore grand prix": "singapore",
        "singapore": "singapore",
        "russian grand prix": "russia",
        "russia": "russia",
        "turkish grand prix": "turkey",
        "turkey": "turkey",
        "united states grand prix": "austin",  # 🔧 修復: Austin COTA 使用 'austin'
        "united states": "austin",             # 🔧 修復: United States → austin
        "miami grand prix": "miami",           # 新增: 區分 Miami 大獎賽
        "miami": "miami",                      # 新增: Miami 簡稱
        "mexican grand prix": "mexico",
        "mexico": "mexico",
        "brazilian grand prix": "brazil",
        "brazil": "brazil",
        "abu dhabi grand prix": "abu dhabi",
        "abu dhabi": "abu dhabi",
    }

    normalized = event_name.strip().lower()

    if normalized in race_name_mapping:
        return race_name_mapping[normalized]

    if normalized.endswith("grand prix"):
        base_name = normalized.replace("grand prix", "").strip()
        if base_name in race_name_mapping:
            return race_name_mapping[base_name]
        return base_name

    return normalized


def run_team_pitstop_ranking(data_loader, show_detailed_output=True):
    """執行車隊進站時間排行榜分析 - 功能4 (Function 15 標準)
    
    Args:
        data_loader: 數據載入器
        show_detailed_output: 是否顯示詳細輸出（即使使用緩存也顯示完整表格）
    
    Returns:
        dict: 包含成功狀態、數據、緩存狀態和緩存鍵的標準化返回格式
    """
    print("🚀 開始執行車隊進站時間排行榜分析...")
    print("🏁 車隊進站時間排行榜 (功能4)")
    print("=" * 60)
    
    try:
        # 獲取基本賽事資訊
        session_info = get_session_info(data_loader)
        cache_key = f"team_pitstop_{session_info.get('year')}_{session_info.get('event_name', 'Unknown').replace(' ', '_')}"
        
        # 檢查緩存 - Function 15 標準實現
        cached_data = check_cache(cache_key)
        cache_used = cached_data is not None
        
        if cached_data and not show_detailed_output:
            print("📦 使用緩存數據")
            ranking_data = cached_data
            
            # 結果驗證和反饋
            if not report_analysis_results(ranking_data, "車隊進站時間排行榜"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "4"}
            
            # 保存 JSON 結果 - 即使使用緩存也要保存
            save_json_results(ranking_data, session_info, "team_pitstop_ranking")
            
            print("\n✅ 車隊進站時間排行榜分析完成！")
            return {
                "success": True,
                "data": ranking_data,
                "cache_used": cache_used,
                "cache_key": cache_key,
                "function_id": "4"
            }
            
        elif cached_data and show_detailed_output:
            print("� 使用緩存數據 + 📊 顯示詳細分析結果")
            ranking_data = cached_data
            
            # 結果驗證和反饋
            if not report_analysis_results(ranking_data, "車隊進站時間排行榜"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "4"}
                
            # 顯示詳細輸出 - 即使使用緩存
            _display_cached_detailed_output(ranking_data, session_info)
            
            # 保存 JSON 結果 - 即使使用緩存也要保存
            save_json_results(ranking_data, session_info, "team_pitstop_ranking")
            
            print("\n✅ 車隊進站時間排行榜分析完成！")
            return {
                "success": True,
                "data": ranking_data,
                "cache_used": cache_used,
                "cache_key": cache_key,
                "function_id": "4"
            }
        else:
            print("�🔄 重新計算 - 開始數據分析...")
            ranking_data = analyze_team_pitstop_performance(data_loader, session_info)
            
            if not ranking_data:
                print("❌ 車隊進站時間排行榜分析失敗：無可用數據")
                return {"success": False, "message": "無可用數據", "function_id": "4"}
            
            # 保存緩存
            save_cache(ranking_data, cache_key)
            print("💾 分析結果已緩存")
            
            # 結果驗證和反饋
            if not report_analysis_results(ranking_data, "車隊進站時間排行榜"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "4"}
            
            # 顯示排行榜
            display_team_pitstop_rankings(ranking_data)
            
            # 保存 JSON 結果
            save_json_results(ranking_data, session_info, "team_pitstop_ranking")
            
            print("\n✅ 車隊進站時間排行榜分析完成！")
            return {
                "success": True,
                "data": ranking_data,
                "cache_used": cache_used,
                "cache_key": cache_key,
                "function_id": "4"
            }
        
    except Exception as e:
        print(f"❌ 車隊進站時間排行榜分析失敗: {e}")
        return {"success": False, "message": f"分析失敗: {str(e)}", "function_id": "4"}


def get_session_info(data_loader):
    """獲取賽事基本信息"""
    from datetime import datetime
    current_year = datetime.now().year
    
    session_info = {}
    if hasattr(data_loader, 'session') and data_loader.session is not None:
        event = data_loader.session.event if hasattr(data_loader.session, 'event') else {}
        session_info = {
            "event_name": getattr(event, 'EventName', 'Unknown'),
            "circuit_name": getattr(event, 'Location', 'Unknown'),
            "session_type": getattr(data_loader.session, 'session_info', {}).get('Type', 'Unknown'),
            "year": getattr(event, 'year', current_year)  # 使用當前年份作為預設值
        }
        
        # 調試信息：檢查獲取的年份是否正確
        print(f"[DEBUG] Session info: year={session_info['year']}, event_name={session_info['event_name']}")
    
    return session_info


def analyze_team_pitstop_performance(data_loader, session_info):
    """分析車隊進站時間數據"""
    if F1OpenDataAnalyzer is None:
        print("[ERROR] OpenF1 數據分析器未可用")
        return None
    
    try:
        # 創建 OpenF1 分析器
        openf1_analyzer = F1OpenDataAnalyzer()
        
        # 根據年份和比賽名稱找到對應的 session_key
        raw_event_name = session_info.get('event_name', 'Unknown')
        normalized_race_name = standardize_race_name(raw_event_name)

        print(f"[DEBUG] Race name標準化: '{raw_event_name}' -> '{normalized_race_name}'")

        race_session = openf1_analyzer.find_race_session_by_name(
            session_info.get('year'), normalized_race_name
        )
        
        if not race_session:
            print("[ERROR] 無法找到對應的比賽會話")
            return None
        
        session_key = race_session.get('session_key')
        print(f"📡 從 OpenF1 API 獲取進站數據 (session_key: {session_key})...")
        
        # 獲取 OpenF1 進站數據
        enhanced_pitstops = openf1_analyzer.get_enhanced_pit_stops(session_key)
        
        if not enhanced_pitstops:
            print("[ERROR] OpenF1 API 未返回進站數據")
            return None
        
        print(f"[SUCCESS] 成功獲取 {len(enhanced_pitstops)} 個進站記錄")
        
        # 分析車隊進站表現
        team_stats = {}
        
        for stop in enhanced_pitstops:
            # 正確提取車手和車隊信息 (從 driver_info 字段中)
            driver_info = stop.get('driver_info', {})
            team = driver_info.get('team_name', 'Unknown Team')
            pit_duration = stop.get('pit_duration')
            
            # 只處理有效的進站時間（通常在 20-50 秒之間）
            if pit_duration is not None and 15.0 <= pit_duration <= 60.0:
                if team not in team_stats:
                    team_stats[team] = []
                team_stats[team].append(float(pit_duration))
        
        # 計算車隊統計數據
        team_rankings = []
        for team, times in team_stats.items():
            if not times:  # 跳過沒有有效進站的車隊
                continue
                
            team_data = {
                'team': team,
                'fastest_time': min(times),
                'average_time': statistics.mean(times),
                'median_time': statistics.median(times),
                'pitstop_count': len(times),
                'std_deviation': statistics.stdev(times) if len(times) > 1 else 0.0,
                'consistency_score': max(0, 100 - (statistics.stdev(times) if len(times) > 1 else 0) * 20)
            }
            team_rankings.append(team_data)
        
        # 按最快時間排序
        team_rankings.sort(key=lambda x: x['fastest_time'])
        
        return team_rankings
        
    except Exception as e:
        print(f"[ERROR] 車隊進站時間分析失敗: {e}")
        return None


def display_team_pitstop_rankings(ranking_data):
    """顯示車隊進站時間排行榜"""
    if not ranking_data:
        print("[ERROR] 沒有排行榜數據可顯示")
        return
    
    print(f"\n🏁 車隊進站時間排行榜:")
    print(f"⚡ 最快車隊: {ranking_data[0]['team']} ({ranking_data[0]['fastest_time']:.1f}秒)")
    print(f"🐌 最慢車隊: {ranking_data[-1]['team']} ({ranking_data[-1]['fastest_time']:.1f}秒)")
    
    # 基本排行榜
    basic_table = PrettyTable()
    basic_table.field_names = ["排名", "車隊", "最快時間", "平均時間", "進站次數"]
    
    for i, team_data in enumerate(ranking_data, 1):
        basic_table.add_row([
            i,
            team_data['team'][:20],
            f"{team_data['fastest_time']:.1f}秒",
            f"{team_data['average_time']:.1f}秒",
            team_data['pitstop_count']
        ])
    
    print(basic_table)


def _display_cached_detailed_output(ranking_data, session_info):
    """顯示緩存數據的詳細輸出 - Function 15 標準
    
    Args:
        ranking_data: 車隊進站時間排行榜數據
        session_info: 賽事基本信息
    """
    print("\n📊 詳細車隊進站時間排行榜 (緩存數據)")
    print("=" * 80)
    
    # 基本信息
    total_teams = len(ranking_data)
    print(f"🏆 總車隊數量: {total_teams}")
    
    if ranking_data:
        fastest_team = ranking_data[0]
        slowest_team = ranking_data[-1]
        print(f"🏎️ 最快車隊: {fastest_team['team']} ({fastest_team['fastest_time']:.1f}秒)")
        print(f"🐌 最慢車隊: {slowest_team['team']} ({slowest_team['fastest_time']:.1f}秒)")
    
    # 詳細排行榜表格
    detailed_table = PrettyTable()
    detailed_table.field_names = [
        "排名", "車隊", "最快時間", "平均時間", "總進站次數", 
        "時間標準差", "最快/平均差", "表現評級"
    ]
    
    for i, team_data in enumerate(ranking_data, 1):
        # 計算表現評級
        fastest_time = team_data.get('fastest_time', 0)
        average_time = team_data.get('average_time', 0)
        time_diff = abs(average_time - fastest_time)
        
        if time_diff <= 1.0:
            performance = "優秀"
        elif time_diff <= 2.0:
            performance = "良好"
        elif time_diff <= 3.0:
            performance = "一般"
        else:
            performance = "不穩定"
        
        detailed_table.add_row([
            i,
            team_data['team'][:15],
            f"{fastest_time:.2f}秒",
            f"{average_time:.2f}秒",
            team_data.get('pitstop_count', 0),
            f"{team_data.get('time_variance', 0):.2f}秒",
            f"{time_diff:.2f}秒",
            performance
        ])
    
    print(detailed_table)
    
    # 統計摘要
    print("\n📈 統計摘要:")
    if ranking_data:
        all_fastest_times = [team['fastest_time'] for team in ranking_data]
        all_average_times = [team['average_time'] for team in ranking_data]
        total_pitstops = sum(team.get('pitstop_count', 0) for team in ranking_data)
        
        print(f"   • 最快時間範圍: {min(all_fastest_times):.2f}秒 - {max(all_fastest_times):.2f}秒")
        print(f"   • 平均時間範圍: {min(all_average_times):.2f}秒 - {max(all_average_times):.2f}秒") 
        print(f"   • 總進站次數: {total_pitstops}")
        print(f"   • 平均每隊進站: {total_pitstops/total_teams:.1f}次")
    
    print("\n💾 數據來源: 緩存檔案")
    print(f"📅 賽事: {session_info.get('year', 'Unknown')} {session_info.get('event_name', 'Unknown')}")
    print(f"🏁 賽段: {session_info.get('session', 'Unknown')}")
    print("✅ 緩存數據詳細輸出完成")
    
    # 詳細統計表
    print(f"\n📊 車隊進站詳細統計:")
    detail_table = PrettyTable()
    detail_table.field_names = ["車隊", "最快", "平均", "中位數", "標準差", "一致性", "進站數"]
    
    for team_data in ranking_data:
        detail_table.add_row([
            team_data['team'][:15],
            f"{team_data['fastest_time']:.1f}s",
            f"{team_data['average_time']:.1f}s",
            f"{team_data['median_time']:.1f}s",
            f"{team_data['std_deviation']:.2f}s",
            f"{team_data['consistency_score']:.0f}%",
            team_data['pitstop_count']
        ])
    
    print(detail_table)


def save_json_results(ranking_data, session_info, analysis_type):
    """保存 JSON 結果"""
    json_dir = "json"
    os.makedirs(json_dir, exist_ok=True)
    
    result_data = {
        "function_id": 4,
        "function_name": "Team Pitstop Ranking",
        "analysis_type": analysis_type,
        "session_info": session_info,
        "timestamp": datetime.now().isoformat(),
        "data": ranking_data
    }
    
    # 修正檔名格式：team_pitstop_ranking_YYYY_賽事.json
    event_name = session_info.get('event_name', 'Unknown').replace(' ', '_')
    filename = f"{analysis_type}_{session_info.get('year')}_{event_name}.json"
    filepath = os.path.join(json_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        print(f"💾 JSON結果已保存到: file:///{os.path.abspath(filepath)}")
    except Exception as e:
        print(f"[WARNING] JSON保存失敗: {e}")


if __name__ == "__main__":
    print("車隊進站時間排行榜模組 - 獨立測試模式")
