# -*- coding: utf-8 -*-
"""
單一車手綜合分析模組 - 完整版
提供單一車手的完整分析功能，包含輪胎分析、Pitstop分析、區間時間、超車分析及圖表生成
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from prettytable import PrettyTable

def run_single_driver_comprehensive_analysis(data_loader, open_analyzer, f1_analysis_instance=None, selected_driver=None, show_detailed_output=True):
    """執行單一車手綜合分析 - 符合開發核心要求 (Function 15 標準)
    
    Args:
        data_loader: 數據載入器
        open_analyzer: OpenF1 分析器
        f1_analysis_instance: F1分析實例
        selected_driver: 指定的車手代碼
        show_detailed_output: 是否顯示詳細輸出（即使使用緩存也顯示完整表格）
    
    Returns:
        dict: 包含成功狀態、數據、緩存狀態和緩存鍵的標準化返回格式
    """
    import os
    import json
    import pickle
    from datetime import datetime
    
    try:
        print("🚀 開始執行單一車手綜合分析...")
        
        # 參數處理 - 支援詳細輸出控制
        if show_detailed_output:
            print("📋 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
        
        # 獲取已載入的數據
        data = data_loader.get_loaded_data()
        if not data:
            print("❌ 單一車手綜合分析失敗：無可用數據")
            return {"success": False, "message": "無可用數據", "function_id": "11"}
        
        laps = data['laps']
        session = data['session']
        results = data['results']
        
        # 自動選擇車手（使用預設或第一個可用車手）
        if not selected_driver:
            drivers = sorted(laps['Driver'].unique())
            selected_driver = 'VER' if 'VER' in drivers else drivers[0]
        
        # 生成緩存鍵值 - Function 15 標準
        year = getattr(data_loader, 'year', 2025)
        race = getattr(data_loader, 'race', 'Unknown')
        session_type = getattr(data_loader, 'session', 'R')
        cache_key = f"single_driver_comprehensive_{year}_{selected_driver}_{race}_{session_type}"
        
        # Function 15 標準 - 檢查緩存
        cache_path = os.path.join("cache", f"{cache_key}.pkl")
        cached_data = None
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    cached_data = pickle.load(f)
            except Exception as e:
                print(f"[WARNING] 緩存載入失敗: {e}")
                cached_data = None
        
        cache_used = cached_data is not None
        
        if cached_data and not show_detailed_output:
            print("📦 使用緩存數據")
            # 結果驗證和反饋
            if not _report_analysis_results(cached_data, "單一車手綜合分析"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "11"}
            
            return {
                "success": True,
                "data": cached_data,
                "cache_used": cache_used,
                "cache_key": cache_key,
                "function_id": "11"
            }
            
        elif cached_data and show_detailed_output:
            print("📦 使用緩存數據 + 📊 顯示詳細分析結果")
            # 重新顯示詳細輸出
            _display_detailed_output(cached_data)
            # 結果驗證和反饋
            if not _report_analysis_results(cached_data, "單一車手綜合分析"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "11"}
                
            return {
                "success": True,
                "data": cached_data,
                "cache_used": cache_used,
                "cache_key": cache_key,
                "function_id": "11"
            }
        else:
            print("🔄 重新計算 - 開始數據分析...")
        
        # 執行分析
        result = _perform_comprehensive_analysis_enhanced(selected_driver, data, f1_analysis_instance)
        
        # 結果驗證和反饋
        if not _report_analysis_results(result, "單一車手綜合分析"):
            return {"success": False, "message": "結果驗證失敗", "function_id": "11"}
        
        # 保存緩存
        os.makedirs("cache", exist_ok=True)
        with open(cache_path, 'wb') as f:
            pickle.dump(result, f)
        print("💾 分析結果已緩存")
        
        # 保存JSON輸出
        json_dir = "json"
        os.makedirs(json_dir, exist_ok=True)
        
        # 生成安全的文件名
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"single_driver_comprehensive_{selected_driver}_{year}_{timestamp}.json"
        json_path = os.path.join(json_dir, json_filename)
        
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            print(f"📄 JSON數據已保存: {json_path}")
        except Exception as json_error:
            print(f"⚠️ JSON保存失敗: {json_error}")
            # 嘗試使用最簡化文件名
            simple_json_path = os.path.join(json_dir, f"function11_output_{timestamp}.json")
            with open(simple_json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            print(f"📄 JSON數據已保存 (簡化名稱): {simple_json_path}")
        
        # Function 15 標準返回格式
        return {
            "success": True,
            "data": result,
            "cache_used": cache_used,
            "cache_key": cache_key,
            "function_id": "11"
        }
        
    except Exception as e:
        print(f"❌ 單一車手綜合分析失敗：{str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"分析失敗: {str(e)}", "function_id": "11"}

def _perform_comprehensive_analysis_enhanced(driver, data, f1_analysis_instance):
    """執行車手的完整綜合分析 - 增強版"""
    from datetime import datetime
    
    try:
        laps = data['laps']
        session = data['session']
        results = data['results']
        
        # 篩選車手數據
        driver_laps = laps[laps['Driver'] == driver].copy()
        
        if driver_laps.empty:
            print(f"❌ 沒有找到車手 {driver} 的數據")
            return None
        
        print(f"📊 分析車手: {driver}")
        
        # 基本統計分析
        total_laps = len(driver_laps)
        valid_laps = driver_laps[driver_laps['LapTime'].notna()]
        completed_laps = len(valid_laps)
        
        if completed_laps == 0:
            print("❌ 沒有有效的圈速數據")
            return None
        
        # 圈速分析
        fastest_lap_time = valid_laps['LapTime'].min()
        average_lap_time = valid_laps['LapTime'].mean()
        
        # 最快圈詳細信息
        fastest_lap_data = valid_laps[valid_laps['LapTime'] == fastest_lap_time].iloc[0]
        fastest_lap_num = fastest_lap_data['LapNumber']
        
        # 位置分析
        try:
            driver_result = results[results['Abbreviation'] == driver].iloc[0]
            final_position = driver_result['Position']
            grid_position = driver_result['GridPosition']
            position_change = grid_position - final_position
        except:
            final_position = "N/A"
            grid_position = "N/A" 
            position_change = 0
        
        # 輪胎分析
        tire_compounds = driver_laps['Compound'].value_counts()
        most_used_tire = tire_compounds.index[0] if len(tire_compounds) > 0 else "Unknown"
        
        # 進站分析
        pit_stops = len(driver_laps[driver_laps['PitOutTime'].notna()])
        
        # 構建結果
        result = {
            "driver": driver,
            "analysis_type": "single_driver_comprehensive",
            "timestamp": datetime.now().isoformat(),
            "basic_statistics": {
                "total_laps": int(total_laps),
                "completed_laps": int(completed_laps),
                "completion_rate": round(completed_laps / total_laps * 100, 2) if total_laps > 0 else 0
            },
            "lap_time_analysis": {
                "fastest_lap_time": _format_time_enhanced(fastest_lap_time),
                "fastest_lap_number": int(fastest_lap_num),
                "average_lap_time": _format_time_enhanced(average_lap_time),
                "gap_to_average": _format_time_enhanced(average_lap_time - fastest_lap_time)
            },
            "race_position": {
                "final_position": final_position,
                "grid_position": grid_position,
                "position_change": position_change
            },
            "tire_strategy": {
                "most_used_compound": most_used_tire,
                "compounds_used": tire_compounds.to_dict(),
                "total_compounds": len(tire_compounds)
            },
            "pit_strategy": {
                "total_pit_stops": pit_stops
            },
            "metadata": {
                "year": getattr(data.get('session'), 'event', {}).get('EventName', 'Unknown'),
                "race": getattr(data.get('session'), 'event', {}).get('RoundNumber', 'Unknown'),
                "session_type": getattr(data.get('session'), 'name', 'Unknown')
            }
        }
        
        return result
        
    except Exception as e:
        print(f"❌ 綜合分析執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

def _format_time_enhanced(time_obj):
    """增強時間格式化函數 - 符合開發核心要求（禁止包含days）"""
    if time_obj is None or pd.isna(time_obj):
        return "N/A"
    
    try:
        if hasattr(time_obj, 'total_seconds'):
            total_seconds = time_obj.total_seconds()
        else:
            total_seconds = float(time_obj)
        
        if total_seconds < 0:
            return "N/A"
            
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        
        if minutes > 0:
            return f"{minutes}:{seconds:06.3f}"
        else:
            return f"{seconds:.3f}s"
    except:
        return str(time_obj)

def _display_detailed_output(cached_result):
    """顯示詳細輸出 - 當使用緩存但需要完整表格時"""
    if not cached_result:
        return
    
    print("🔄 重新顯示 - 展示詳細分析結果...")
    
    # 顯示基本統計
    basic_stats = cached_result.get('basic_statistics', {})
    if basic_stats:
        print(f"\n🏎️ 車手基本資訊:")
        print(f"   • 車手代碼: {basic_stats.get('driver', 'N/A')}")
        print(f"   • 完成圈數: {basic_stats.get('completed_laps', 'N/A')}")
        print(f"   • 最終名次: {basic_stats.get('final_position', 'N/A')}")
    
    # 顯示圈時分析
    lap_analysis = cached_result.get('lap_time_analysis', {})
    if lap_analysis:
        print(f"\n⏱️ 圈時分析:")
        print(f"   • 最快圈時間: {lap_analysis.get('fastest_lap_time', 'N/A')}")
        print(f"   • 平均圈時間: {lap_analysis.get('average_lap_time', 'N/A')}")
    
    print("📊 詳細數據已重新顯示")

def _report_analysis_results(data, analysis_type="analysis"):
    """報告分析結果狀態 - 符合開發核心要求"""
    if not data:
        print(f"❌ {analysis_type}失敗：無可用數據")
        return False
    
    # 計算數據項目數量
    if isinstance(data, dict):
        data_count = len(data.get('basic_statistics', {})) + len(data.get('lap_time_analysis', {}))
    else:
        data_count = len(data) if hasattr(data, '__len__') else 1
    
    print(f"📊 {analysis_type}結果摘要：")
    print(f"   • 數據項目數量: {data_count}")
    print(f"   • 數據完整性: {'✅ 良好' if data_count > 0 else '❌ 不足'}")
    
    if isinstance(data, dict) and 'driver' in data:
        print(f"   • 分析車手: {data['driver']}")
        print(f"   • 完成圈數: {data.get('basic_statistics', {}).get('completed_laps', 'N/A')}")
    
    print(f"✅ {analysis_type}分析完成！")
    return True

def _perform_comprehensive_analysis(driver, data, f1_analysis_instance):
    """執行車手的完整綜合分析"""
    try:
        laps = data['laps']
        session = data['session']
        results = data['results']
        
        # 篩選車手數據
        driver_laps = laps[laps['Driver'] == driver].copy()
        
        if driver_laps.empty:
            print(f"[ERROR] 沒有找到車手 {driver} 的數據")
            return
        
        print(f"\n[INFO] {driver} 綜合表現分析")
        print("=" * 60)
        
        # 基本統計分析
        total_laps = len(driver_laps)
        valid_laps = driver_laps[driver_laps['LapTime'].notna()]
        completed_laps = len(valid_laps)
        
        print(f"\n[FINISH] 基本統計:")
        print(f"   總圈數: {total_laps}")
        print(f"   完成圈數: {completed_laps}")
        
        if completed_laps == 0:
            print("[ERROR] 沒有有效的圈速數據")
            return
        
        # 圈速分析
        fastest_lap_time = valid_laps['LapTime'].min()
        average_lap_time = valid_laps['LapTime'].mean()
        
        print(f"\n⏱️ 圈速分析:")
        print(f"   最快圈速: {_format_time(fastest_lap_time)}")
        print(f"   平均圈速: {_format_time(average_lap_time)}")
        
        # 最快圈詳細信息
        fastest_lap_data = valid_laps[valid_laps['LapTime'] == fastest_lap_time].iloc[0]
        fastest_lap_num = fastest_lap_data['LapNumber']
        
        print(f"   最快圈圈數: {fastest_lap_num}")
        
        # 輪胎分析 - 呼叫原始函數
        if f1_analysis_instance:
            tire_compound, tire_life = _get_fastest_lap_tire_info(driver_laps, fastest_lap_num)
            print(f"\n🏎️ 最快圈輪胎資訊:")
            print(f"   輪胎配方: {tire_compound}")
            print(f"   輪胎生命週期: {tire_life}")
            
            # 區間時間分析
            sector_times = _get_fastest_lap_sector_times(driver_laps, fastest_lap_num)
            print(f"\n[FINISH] 最快圈區間時間:")
            print(f"   第一區間: {sector_times.get('Sector1Time', 'N/A')}")
            print(f"   第二區間: {sector_times.get('Sector2Time', 'N/A')}")
            print(f"   第三區間: {sector_times.get('Sector3Time', 'N/A')}")
        
        # Pitstop 分析
        pitstops = driver_laps[driver_laps['PitOutTime'].notna() | driver_laps['PitInTime'].notna()]
        if not pitstops.empty:
            print(f"\n[CONFIG] Pitstop 分析:")
            print(f"   Pitstop 次數: {len(pitstops)}")
            
            # 計算平均 Pitstop 時間
            if 'PitOutTime' in pitstops.columns and 'PitInTime' in pitstops.columns:
                pit_times = []
                for _, pit_lap in pitstops.iterrows():
                    if pd.notna(pit_lap['PitOutTime']) and pd.notna(pit_lap['PitInTime']):
                        pit_duration = pit_lap['PitOutTime'] - pit_lap['PitInTime']
                        if hasattr(pit_duration, 'total_seconds'):
                            pit_times.append(pit_duration.total_seconds())
                
                if pit_times:
                    avg_pit_time = np.mean(pit_times)
                    print(f"   平均 Pitstop 時間: {avg_pit_time:.3f}秒")
        else:
            print(f"\n[CONFIG] Pitstop 分析: 無 Pitstop 記錄")
        
        # 排位結果
        if not results.empty:
            driver_result = results[results['Abbreviation'] == driver]
            if not driver_result.empty:
                position = driver_result.iloc[0]['Position']
                print(f"\n🏆 比賽結果:")
                print(f"   最終排名: P{position}")
        
        # 生成超車分析表格（如果有超車分析器的話）
        if f1_analysis_instance and hasattr(f1_analysis_instance, 'overtaking_analyzer'):
            print(f"\n[INFO] 超車表現分析:")
            _generate_comprehensive_overtaking_table(data, f1_analysis_instance)
        
        # 生成全車手圈速趨勢圖
        if f1_analysis_instance:
            # 準備所有車手數據用於圖表
            all_driver_data = {}
            for d in laps['Driver'].unique():
                d_laps = laps[laps['Driver'] == d]
                d_valid = d_laps[d_laps['LapTime'].notna()]
                if not d_valid.empty:
                    all_driver_data[d] = {
                        'fastest_lap_num': d_valid.loc[d_valid['LapTime'].idxmin(), 'LapNumber'],
                        'driver_info': {'name': d}  # 簡化的車手資訊
                    }
            
            if all_driver_data:
                print(f"\n🎨 生成全車手圈速趨勢圖...")
                _create_all_drivers_lap_time_trend_chart(laps, all_driver_data, data, f1_analysis_instance)
        
        print(f"\n[SUCCESS] {driver} 綜合分析完成")
        
    except Exception as e:
        print(f"[ERROR] 綜合分析執行失敗: {e}")
        import traceback
        traceback.print_exc()

def _get_fastest_lap_tire_info(driver_laps, fastest_lap_num):
    """獲取最快圈的輪胎資訊"""
    try:
        if pd.isna(fastest_lap_num) or fastest_lap_num == 'N/A':
            return 'N/A', 'N/A'
        
        # 找到最快圈的資料
        fastest_lap_data = driver_laps[driver_laps['LapNumber'] == fastest_lap_num]
        
        if fastest_lap_data.empty:
            return 'N/A', 'N/A'
        
        # 安全獲取最快圈資料
        try:
            fastest_lap = fastest_lap_data.iloc[0] if hasattr(fastest_lap_data, 'iloc') and len(fastest_lap_data) > 0 else None
            if fastest_lap is None:
                return 'N/A', 'N/A'
        except:
            return 'N/A', 'N/A'
        compound = fastest_lap.get('Compound', 'N/A')
        tyre_life = fastest_lap.get('TyreLife', 'N/A')
        
        if pd.isna(compound):
            compound = 'N/A'
        if pd.isna(tyre_life):
            tyre_life = 'N/A'
        else:
            tyre_life = int(tyre_life)
        
        return compound, tyre_life
        
    except Exception as e:
        print(f"[ERROR] 獲取最快圈輪胎資訊時發生錯誤: {e}")
        return 'N/A', 'N/A'

def _get_fastest_lap_sector_times(driver_laps, fastest_lap_num):
    """獲取最快圈的區間時間"""
    try:
        if pd.isna(fastest_lap_num) or fastest_lap_num == 'N/A':
            return {'Sector1Time': 'N/A', 'Sector2Time': 'N/A', 'Sector3Time': 'N/A'}
        
        # 找到最快圈的資料
        fastest_lap_data = driver_laps[driver_laps['LapNumber'] == fastest_lap_num]
        
        if fastest_lap_data.empty:
            return {'Sector1Time': 'N/A', 'Sector2Time': 'N/A', 'Sector3Time': 'N/A'}
        
        # 安全獲取最快圈資料
        try:
            fastest_lap = fastest_lap_data.iloc[0] if hasattr(fastest_lap_data, 'iloc') and len(fastest_lap_data) > 0 else None
            if fastest_lap is None:
                return {'Sector1Time': 'N/A', 'Sector2Time': 'N/A', 'Sector3Time': 'N/A'}
        except:
            return {'Sector1Time': 'N/A', 'Sector2Time': 'N/A', 'Sector3Time': 'N/A'}
        
        # 獲取區間時間
        sector_times = {}
        for sector in ['Sector1Time', 'Sector2Time', 'Sector3Time']:
            if sector in fastest_lap_data.columns:
                sector_time = fastest_lap.get(sector, 'N/A')
                if pd.notna(sector_time):
                    # 如果是 timedelta 對象，轉換為字符串格式
                    if hasattr(sector_time, 'total_seconds'):
                        total_seconds = sector_time.total_seconds()
                        if total_seconds > 0:
                            sector_times[sector] = f"{total_seconds:.3f}s"
                        else:
                            sector_times[sector] = 'N/A'
                    else:
                        sector_times[sector] = str(sector_time)
                else:
                    sector_times[sector] = 'N/A'
            else:
                sector_times[sector] = 'N/A'
        
        return sector_times
        
    except Exception as e:
        print(f"[ERROR] 獲取最快圈區間時間時發生錯誤: {e}")
        return {'Sector1Time': 'N/A', 'Sector2Time': 'N/A', 'Sector3Time': 'N/A'}

def _generate_comprehensive_overtaking_table(data, f1_analysis_instance):
    """為車手綜合分析生成簡化的超車分析表格"""
    try:
        metadata = data['metadata']
        year = metadata['year']
        race_name = metadata['race_name']
        
        print(f"[INFO] 分析 {year} {race_name} 超車表現...")
        print("[NOTE] 說明：基於位置變化分析車手超車次數")
        
        # 獲取超車分析資料
        if hasattr(f1_analysis_instance, 'overtaking_analyzer'):
            # 直接使用已有的超車分析器
            result = f1_analysis_instance.overtaking_analyzer.analyze_all_drivers_overtaking([year], race_name)
            
            if result and 'drivers_stats' in result:
                drivers_stats = result['drivers_stats']
                
                # 篩選有超車資料的車手並排序
                active_drivers = [(driver, stats) for driver, stats in drivers_stats.items() 
                                if stats['total_races'] > 0]
                
                if active_drivers:
                    # 按總超車數排序
                    active_drivers.sort(key=lambda x: x[1]['total_overtakes'], reverse=True)
                    
                    # 建立簡化的超車表格
                    table = PrettyTable()
                    table.field_names = ["排名", "車手", "超車次數"]
                    table.align = "c"
                    
                    for rank, (driver, stats) in enumerate(active_drivers, 1):
                        table.add_row([
                            rank,
                            driver,
                            stats['total_overtakes']
                        ])
                    
                    print(table)
                    
                    # 顯示前3名
                    print(f"\n🏆 超車表現前3名:")
                    for rank, (driver, stats) in enumerate(active_drivers[:3], 1):
                        print(f"   {rank}. {driver}: {stats['total_overtakes']} 次")
                    
                    return True
                else:
                    print("[ERROR] 沒有找到有效的超車資料")
                    return False
            else:
                print("[ERROR] 超車分析失敗")
                return False
        else:
            print("[ERROR] 超車分析器尚未初始化")
            return False
            
    except Exception as e:
        print(f"[ERROR] 生成超車分析表格失敗: {e}")
        # 不影響主要分析流程，只顯示錯誤訊息
        return False

def _create_all_drivers_lap_time_trend_chart(laps, all_driver_data, data, f1_analysis_instance):
    """生成全車手的整場比賽圈速趨勢分析圖"""
    try:        
        print(f"\n🎨 生成全車手整場比賽圈速趨勢分析圖...")
        
        # 設定深色主題 (圈速趨勢圖使用深色背景)
        if hasattr(f1_analysis_instance, '_setup_chinese_font'):
            f1_analysis_instance._setup_chinese_font(dark_theme=True)
        
        # 創建圖表
        fig, ax = plt.subplots(figsize=(20, 12))
        ax.set_facecolor('#2d2d2d')
        
        # 為每個車手分配不同顏色
        colors = cm.tab20(np.linspace(0, 1, len(all_driver_data)))
        
        # 獲取賽事事件數據
        track_status = data.get('track_status')
        race_control_messages = data.get('race_control_messages')
        
        # 繪製每個車手的圈速趨勢
        legend_elements = []
        min_time = float('inf')
        max_time = 0
        max_lap = 0
        
        for i, (driver_abbr, driver_data) in enumerate(all_driver_data.items()):
            # 獲取該車手的所有有效圈速
            driver_laps = laps[laps['Driver'] == driver_abbr].copy()
            valid_laps = driver_laps[driver_laps['LapTime'].notna()].copy()
            
            if len(valid_laps) < 2:
                continue
            
            # 轉換圈速為秒數
            valid_laps['LapTimeSeconds'] = valid_laps['LapTime'].dt.total_seconds()
            lap_numbers = valid_laps['LapNumber'].values
            lap_times = valid_laps['LapTimeSeconds'].values
            
            # 更新統計數據
            min_time = min(min_time, np.min(lap_times))
            max_time = max(max_time, np.max(lap_times))
            max_lap = max(max_lap, np.max(lap_numbers))
            
            # 繪製該車手的圈速線
            color = colors[i]
            driver_info = driver_data['driver_info']
            label = f"{driver_abbr} ({driver_info['name'][:15]})"
            
            ax.plot(lap_numbers, lap_times, color=color, linewidth=1.5, 
                   alpha=0.8, label=label, marker='o', markersize=3)
            
            # 標註最快圈
            if driver_data['fastest_lap_num'] != 'N/A':
                fastest_lap_idx = np.where(lap_numbers == driver_data['fastest_lap_num'])[0]
                if len(fastest_lap_idx) > 0:
                    fastest_idx = fastest_lap_idx[0]
                    ax.scatter(lap_numbers[fastest_idx], lap_times[fastest_idx], 
                             color=color, s=100, marker='*', zorder=5, 
                             edgecolor='gold', linewidth=2)
        
        # 標註賽事事件（如果有數據的話）
        if track_status is not None or race_control_messages is not None:
            if hasattr(f1_analysis_instance, '_mark_race_events_on_all_drivers_chart'):
                f1_analysis_instance._mark_race_events_on_all_drivers_chart(ax, track_status, race_control_messages, max_lap, min_time, max_time)
        
        # 設定圖表屬性
        ax.set_xlabel('圈數', fontsize=14, fontweight='bold')
        ax.set_ylabel('圈速 (秒)', fontsize=14, fontweight='bold')
        ax.set_title('全車手整場比賽圈速趨勢分析 - 含最快圈標註', fontsize=16, fontweight='bold', pad=20)
        
        # 設定Y軸格式
        y_ticks = ax.get_yticks()
        ax.set_yticks(y_ticks)
        ax.set_yticklabels([_format_seconds_to_laptime(t) for t in y_ticks])
        
        # 設定圖例
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
        
        # 設定網格
        ax.grid(True, alpha=0.3, color='white')
        ax.set_axisbelow(True)
        
        # 調整佈局
        plt.tight_layout()
        
        # 生成檔名並儲存
        try:
            metadata = data['metadata']
            year = metadata['year']
            race_name = metadata['race_name']
            filename = f"{year}_{race_name}_All_Drivers_Lap_Time_Trend_Chart.png"
            
            # plt.savefig(filename, dpi=300, bbox_inches='tight',   # 圖表保存已禁用
            #            facecolor='#2d2d2d', edgecolor='none')
            print(f"[SUCCESS] 圖表生成已完成（保存已禁用）")
            
        except Exception as save_error:
            print(f"[ERROR] 生成圖表失敗: {save_error}")
        
        # 顯示圖表
        # plt.show()  # 圖表顯示已禁用
        
    except Exception as e:
        print(f"[ERROR] 生成全車手圈速趨勢圖失敗: {e}")
        import traceback
        traceback.print_exc()

def _format_time(time_value):
    """格式化時間顯示"""
    if pd.isna(time_value):
        return "N/A"
    
    try:
        if hasattr(time_value, 'total_seconds'):
            total_seconds = time_value.total_seconds()
            minutes = int(total_seconds // 60)
            seconds = total_seconds % 60
            return f"{minutes}:{seconds:06.3f}"
        else:
            return str(time_value)
    except:
        return "N/A"

def _format_seconds_to_laptime(seconds):
    """將秒數轉換為圈速格式 (MM:SS.mmm)"""
    try:
        if pd.isna(seconds) or seconds <= 0:
            return "N/A"
        
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:06.3f}"
    except:
        return "N/A"

# 為了相容主程式的導入，提供別名函數
def run_comprehensive_analysis(data_loader, open_analyzer=None, f1_analysis_instance=None):
    """綜合分析函數的別名，為了相容模組化主程式的導入"""
    return run_single_driver_comprehensive_analysis(data_loader, open_analyzer, f1_analysis_instance)

def run_single_driver_telemetry_json(data_loader, open_analyzer, f1_analysis_instance=None, enable_debug=False, selected_driver=None):
    """執行單一車手詳細遙測分析並返回JSON結果
    
    Args:
        data_loader: 數據載入器
        open_analyzer: OpenF1數據分析器
        f1_analysis_instance: F1分析實例
        enable_debug: 是否啟用調試模式
        selected_driver: 指定的車手代碼，如果為None則自動選擇第一個車手
        
    Returns:
        dict: 包含分析結果的JSON格式字典
    """
    try:
        from datetime import datetime
        
        if enable_debug:
            print("[DEBUG] 開始執行單一車手詳細遙測分析 (JSON版)...")
        
        # 獲取已載入的數據
        data = data_loader.get_loaded_data()
        if not data:
            return {
                "success": False,
                "message": "沒有可用的數據，請先載入數據",
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
        
        laps = data['laps']
        session = data['session']
        weather_data = data.get('weather_data')
        results = data['results']
        
        # 獲取可用車手
        drivers = sorted(laps['Driver'].unique())
        if not drivers:
            return {
                "success": False,
                "message": "沒有找到可用的車手數據",
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
        
        # 選擇車手
        if selected_driver:
            if selected_driver not in drivers:
                return {
                    "success": False,
                    "message": f"指定的車手 '{selected_driver}' 不在可用車手列表中",
                    "data": None,
                    "timestamp": datetime.now().isoformat()
                }
            driver = selected_driver
        else:
            # 默認選擇第一個車手
            driver = drivers[0]
        
        if enable_debug:
            print(f"[INFO] 分析車手: {driver}")
        
        # 獲取該車手的資料
        driver_laps = laps[laps['Driver'] == driver].copy()
        
        if driver_laps.empty:
            return {
                "success": False,
                "message": f"車手 {driver} 沒有圈速數據",
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
        
        # 分析有效圈速
        valid_laps = driver_laps[driver_laps['LapTime'].notna()].copy()
        if valid_laps.empty:
            return {
                "success": False,
                "message": f"車手 {driver} 沒有有效的圈速數據",
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
        
        # 轉換圈速為秒數以便計算
        valid_laps['LapTimeSeconds'] = valid_laps['LapTime'].dt.total_seconds()
        
        # 基本統計分析
        fastest_lap_time = valid_laps['LapTime'].min()
        fastest_lap_seconds = valid_laps['LapTimeSeconds'].min()
        slowest_lap_time = valid_laps['LapTime'].max()
        average_lap_time = valid_laps['LapTimeSeconds'].mean()
        lap_time_std = valid_laps['LapTimeSeconds'].std()
        
        # 最快圈詳細信息
        fastest_lap_data = valid_laps[valid_laps['LapTime'] == fastest_lap_time].iloc[0]
        fastest_lap_num = fastest_lap_data['LapNumber']
        
        # 輪胎分析
        tire_compound, tire_life = _get_fastest_lap_tire_info(driver_laps, fastest_lap_num)
        
        # 區間時間分析
        sector_times = _get_fastest_lap_sector_times(driver_laps, fastest_lap_num)
        
        # Pitstop 分析
        pitstops = driver_laps[driver_laps['PitOutTime'].notna() | driver_laps['PitInTime'].notna()]
        pitstop_count = len(pitstops)
        
        # 計算平均 Pitstop 時間
        avg_pit_time = None
        if not pitstops.empty and 'PitOutTime' in pitstops.columns and 'PitInTime' in pitstops.columns:
            pit_times = []
            for _, pit_lap in pitstops.iterrows():
                if pd.notna(pit_lap['PitOutTime']) and pd.notna(pit_lap['PitInTime']):
                    pit_duration = pit_lap['PitOutTime'] - pit_lap['PitInTime']
                    if hasattr(pit_duration, 'total_seconds'):
                        pit_times.append(pit_duration.total_seconds())
            
            if pit_times:
                avg_pit_time = np.mean(pit_times)
        
        # 比賽結果
        final_position = None
        if not results.empty:
            driver_result = results[results['Abbreviation'] == driver]
            if not driver_result.empty:
                final_position = int(driver_result.iloc[0]['Position'])
        
        # 構建遙測分析結果
        telemetry_analysis = {
            "driver_info": {
                "driver_code": driver,
                "total_laps": len(driver_laps),
                "valid_laps": len(valid_laps),
                "final_position": final_position
            },
            "lap_time_analysis": {
                "fastest_lap": {
                    "lap_number": int(fastest_lap_num),
                    "lap_time": _format_time(fastest_lap_time),
                    "lap_time_seconds": float(fastest_lap_seconds),
                    "tire_compound": tire_compound,
                    "tire_life": tire_life
                },
                "sector_times": sector_times,
                "statistics": {
                    "slowest_lap_time": _format_time(slowest_lap_time),
                    "average_lap_time": f"{average_lap_time:.3f}s",
                    "lap_time_std": f"{lap_time_std:.3f}s" if not pd.isna(lap_time_std) else "N/A"
                }
            },
            "pitstop_analysis": {
                "pitstop_count": pitstop_count,
                "pitstops_details": [],
                "average_pitstop_time": f"{avg_pit_time:.3f}s" if avg_pit_time else "N/A"
            }
        }
        
        # 添加詳細的Pitstop信息
        if not pitstops.empty:
            for _, pit_lap in pitstops.iterrows():
                pit_detail = {
                    "lap_number": int(pit_lap['LapNumber']),
                    "pit_in_time": _format_time(pit_lap.get('PitInTime')),
                    "pit_out_time": _format_time(pit_lap.get('PitOutTime'))
                }
                if pd.notna(pit_lap.get('PitInTime')) and pd.notna(pit_lap.get('PitOutTime')):
                    pit_duration = pit_lap['PitOutTime'] - pit_lap['PitInTime']
                    if hasattr(pit_duration, 'total_seconds'):
                        pit_detail["pit_duration"] = f"{pit_duration.total_seconds():.3f}s"
                
                telemetry_analysis["pitstop_analysis"]["pitstops_details"].append(pit_detail)
        
        # 創建metadata
        metadata = {
            "analysis_type": "single_driver_detailed_telemetry",
            "function_name": "Single Driver Detailed Telemetry Analysis",
            "generated_at": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        # 構建最終結果
        result = {
            "success": True,
            "message": f"成功完成 {driver} 的詳細遙測分析",
            "data": {
                "metadata": metadata,
                "single_driver_telemetry": telemetry_analysis
            },
            "timestamp": datetime.now().isoformat()
        }
        
        if enable_debug:
            print(f"[SUCCESS] 單一車手詳細遙測分析完成: {driver}")
        
        return result
        
    except Exception as e:
        if enable_debug:
            print(f"[ERROR] 單一車手詳細遙測分析失敗: {e}")
            import traceback
            traceback.print_exc()
        
        return {
            "success": False,
            "message": f"執行單一車手詳細遙測分析時發生錯誤: {str(e)}",
            "data": None,
            "timestamp": datetime.now().isoformat()
        }
