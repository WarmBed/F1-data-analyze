#!/usr/bin/env python3
"""
輪胎策略分析 CLI 模組
Tire Strategy Analysis CLI Module

整合 FastF1 資料載入、快取管理和 JSON 生成功能
支援 CLI -f26 車手輪胎策略分析

版本: 3.0 - 完整整合版
作者: F1 Analysis Team
"""

import os
import sys
import json
import pickle
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import pandas as pd
import numpy as np
from pathlib import Path

# 添加路徑以便導入模組
current_dir = Path(__file__).parent
root_dir = current_dir.parent.parent.parent.parent  # 到達專案根目錄
cli_core_dir = current_dir.parent.parent / "core"   # core 目錄路徑

sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(cli_core_dir.parent))  # CLI_modules/cli 目錄

# 導入 core 模組
try:
    from core.json_generator import F1AnalysisJSONGenerator, F1SessionInfoExtractor
    from core.compatible_data_loader import CompatibleF1DataLoader
    from core.base import F1AnalysisBase
    print("✅ 成功導入 core 模組")
except ImportError as e:
    print(f"❌ 導入 core 模組失敗: {e}")
    
    # 嘗試直接導入
    try:
        sys.path.insert(0, str(cli_core_dir))
        from json_generator import F1AnalysisJSONGenerator, F1SessionInfoExtractor
        from compatible_data_loader import CompatibleF1DataLoader
        from base import F1AnalysisBase
        print("✅ 成功導入 core 模組 (直接導入)")
    except ImportError as e2:
        print(f"❌ 再次導入失敗: {e2}")
        print(f"核心目錄: {cli_core_dir}")
        print(f"當前路徑: {sys.path[:3]}")
        sys.exit(1)

# 導入 FastF1
try:
    import fastf1
    # 啟用快取
    fastf1.Cache.enable_cache('f1_analysis_cache')
    print("✅ FastF1 已啟用快取")
except ImportError:
    print("❌ FastF1 未安裝")
    sys.exit(1)


class TireStrategyAnalyzer(F1AnalysisBase):
    """輪胎策略分析器"""
    
    def __init__(self, cache_dir: str = "f1_analysis_cache", output_dir: str = "json"):
        """
        初始化輪胎策略分析器
        
        Args:
            cache_dir: 快取目錄
            output_dir: JSON 輸出目錄
        """
        super().__init__()
        self.cache_dir = Path(cache_dir)
        self.output_dir = Path(output_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        # 初始化 JSON 生成器
        self.json_generator = F1AnalysisJSONGenerator(str(self.output_dir))
        self.session_extractor = F1SessionInfoExtractor()
        
        # 初始化數據載入器
        self.data_loader = CompatibleF1DataLoader()
        
        print(f"🏎️ 輪胎策略分析器已初始化")
        print(f"   快取目錄: {self.cache_dir}")
        print(f"   輸出目錄: {self.output_dir}")
    
    def analyze_tire_strategy(self, year: int, race: str, session: str = 'R', 
                             driver: str = None, use_cache: bool = True, 
                             verbose: bool = True) -> Dict[str, Any]:
        """
        執行輪胎策略分析
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 賽段類型 (R/Q/P/FP1/FP2/FP3)
            driver: 車手代碼（可選，為 None 時分析所有車手）
            use_cache: 是否使用快取
            verbose: 是否顯示詳細輸出
            
        Returns:
            分析結果字典
        """
        if verbose:
            print(f"\n🏁 開始輪胎策略分析")
            print(f"📅 賽事: {year} {race} {session}")
            print(f"👨‍🏎️ 分析目標: {driver if driver else '所有車手'}")
            print("-" * 60)
        
        try:
            # 1. 嘗試載入快取資料
            session_data = None
            if use_cache:
                session_data = self._load_cached_session(year, race, session, verbose)
            
            # 2. 如果沒有快取，使用 FastF1 載入
            if session_data is None:
                if verbose:
                    print("📡 快取未找到，正在從 FastF1 載入資料...")
                session_data = self._load_session_from_fastf1(year, race, session, verbose)
                
                if session_data is None:
                    return self._create_error_result("無法載入會話資料")
                
                # 保存到快取
                self._save_session_to_cache(session_data, year, race, session, verbose)
            
            # 3. 提取輪胎資料
            tire_data = self._extract_tire_data(session_data, verbose)
            if tire_data is None or len(tire_data) == 0:
                return self._create_error_result("無法提取輪胎資料")
            
            # 4. 執行輪胎策略分析
            if driver:
                analysis_result = self._analyze_single_driver(tire_data, driver, year, race, session, verbose)
            else:
                analysis_result = self._analyze_all_drivers(tire_data, year, race, session, verbose)
            
            if not analysis_result:
                return self._create_error_result("輪胎策略分析失敗")
            
            # 5. 生成 JSON 輸出
            json_result = self._export_to_json(analysis_result, year, race, session, driver, verbose)
            
            # 6. 返回完整結果
            return {
                "success": True,
                "message": f"輪胎策略分析完成 - {'單一車手' if driver else '所有車手'}",
                "data": analysis_result,
                "json_export": json_result,
                "function_id": "26",
                "timestamp": datetime.now().isoformat(),
                "analysis_params": {
                    "year": year,
                    "race": race,
                    "session": session,
                    "driver": driver,
                    "use_cache": use_cache
                }
            }
            
        except Exception as e:
            if verbose:
                print(f"❌ 分析過程發生錯誤: {str(e)}")
                import traceback
                traceback.print_exc()
            return self._create_error_result(f"分析錯誤: {str(e)}")
    
    def _load_cached_session(self, year: int, race: str, session: str, verbose: bool = False) -> Optional[Any]:
        """載入快取的會話資料"""
        cache_file = self.cache_dir / f"f1_data_{year}_{race}_{session}.pkl"
        
        if not cache_file.exists():
            if verbose:
                print(f"📂 快取檔案不存在: {cache_file}")
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
            
            file_size = cache_file.stat().st_size
            if verbose:
                print(f"✅ 成功載入快取: {cache_file} ({file_size:,} bytes)")
            
            # 檢查快取資料結構
            if isinstance(cached_data, dict) and 'session' in cached_data:
                return cached_data['session']
            else:
                return cached_data
                
        except Exception as e:
            if verbose:
                print(f"❌ 載入快取失敗: {str(e)}")
            return None
    
    def _load_session_from_fastf1(self, year: int, race: str, session: str, verbose: bool = False) -> Optional[Any]:
        """從 FastF1 載入會話資料"""
        try:
            if verbose:
                print(f"📡 正在從 FastF1 載入: {year} {race} {session}")
            
            # 載入會話
            f1_session = fastf1.get_session(year, race, session)
            f1_session.load()
            
            if verbose:
                print(f"✅ FastF1 會話載入成功")
                if hasattr(f1_session, 'laps') and f1_session.laps is not None:
                    print(f"🏁 圈速資料: {len(f1_session.laps)} 筆記錄")
            
            return f1_session
            
        except Exception as e:
            if verbose:
                print(f"❌ FastF1 載入失敗: {str(e)}")
            return None
    
    def _save_session_to_cache(self, session_data: Any, year: int, race: str, session: str, verbose: bool = False):
        """保存會話資料到快取"""
        cache_file = self.cache_dir / f"f1_data_{year}_{race}_{session}.pkl"
        
        try:
            cache_data = {
                'session': session_data,
                'cached_at': datetime.now().isoformat(),
                'metadata': {
                    'year': year,
                    'race': race,
                    'session': session
                }
            }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            file_size = cache_file.stat().st_size
            if verbose:
                print(f"💾 已保存到快取: {cache_file} ({file_size:,} bytes)")
                
        except Exception as e:
            if verbose:
                print(f"⚠️ 保存快取失敗: {str(e)}")
    
    def _extract_tire_data(self, session_data: Any, verbose: bool = False) -> Optional[pd.DataFrame]:
        """提取輪胎相關資料"""
        try:
            if verbose:
                print("🔍 開始提取輪胎相關資料...")
            
            # 獲取圈速資料
            if hasattr(session_data, 'laps'):
                laps = session_data.laps
            else:
                if verbose:
                    print("❌ 找不到圈速資料")
                return None
            
            if verbose:
                print(f"🏁 圈速資料: {len(laps)} 筆記錄")
                print(f"📋 可用欄位: {list(laps.columns)}")
            
            # 檢查必要欄位
            essential_columns = ['Driver', 'LapNumber', 'LapTime', 'Stint']
            missing_columns = [col for col in essential_columns if col not in laps.columns]
            
            if missing_columns:
                if verbose:
                    print(f"⚠️ 缺少必要欄位: {missing_columns}")
            
            # 檢查輪胎相關欄位
            tire_columns = []
            for col in laps.columns:
                if any(tire_word in str(col).lower() for tire_word in ['tire', 'compound', 'tyre', 'stint']):
                    tire_columns.append(col)
            
            if verbose:
                print(f"🛞 輪胎相關欄位: {tire_columns}")
            
            # 獲取所有需要的欄位
            available_cols = [col for col in essential_columns if col in laps.columns]
            all_cols = tire_columns + available_cols
            
            # 去重並保持順序
            all_cols = list(dict.fromkeys(all_cols))
            
            if verbose:
                print(f"📋 提取欄位: {all_cols}")
            
            # 提取資料
            tire_data = laps[all_cols].copy()
            
            # 清理資料
            tire_data = tire_data.dropna(subset=['Driver', 'LapNumber'])
            
            if verbose:
                print(f"✅ 成功提取輪胎資料: {len(tire_data)} 筆有效記錄")
            
            return tire_data
            
        except Exception as e:
            if verbose:
                print(f"❌ 提取輪胎資料失敗: {str(e)}")
            return None
    
    def _analyze_single_driver(self, df: pd.DataFrame, driver: str, year: int, race: str, session: str, verbose: bool = False) -> Dict[str, Any]:
        """分析單一車手的輪胎策略"""
        
        if verbose:
            print(f"\n🏎️ 分析車手 {driver} 的輪胎策略")
            print("-" * 40)
        
        # 篩選該車手的資料
        driver_data = df[df['Driver'] == driver].sort_values('LapNumber').copy()
        
        if len(driver_data) == 0:
            if verbose:
                print(f"❌ 找不到車手 {driver} 的資料")
            return None
        
        # 基本統計
        total_laps = len(driver_data)
        stints = sorted(driver_data['Stint'].unique()) if 'Stint' in driver_data.columns else [1]
        compounds_used = list(driver_data['Compound'].unique()) if 'Compound' in driver_data.columns else ['UNKNOWN']
        
        if verbose:
            print(f"📊 基本統計:")
            print(f"   總圈數: {total_laps}")
            print(f"   Stint 數量: {len(stints)} ({stints})")
            print(f"   使用輪胎: {', '.join(compounds_used)}")
        
        # Stint 分析
        stint_analysis = []
        tire_changes = []
        
        prev_stint = None
        prev_compound = None
        
        for stint in stints:
            stint_data = driver_data[driver_data['Stint'] == stint]
            
            if len(stint_data) == 0:
                continue
            
            compound = stint_data['Compound'].iloc[0] if 'Compound' in stint_data.columns else 'UNKNOWN'
            start_lap = int(stint_data['LapNumber'].min())
            end_lap = int(stint_data['LapNumber'].max())
            stint_length = len(stint_data)
            
            # 計算輪胎壽命
            if 'TyreLife' in stint_data.columns:
                tyre_life_start = int(stint_data['TyreLife'].min())
                tyre_life_end = int(stint_data['TyreLife'].max())
            else:
                tyre_life_start = 1
                tyre_life_end = stint_length
            
            # 計算平均圈速（如果有LapTime資料）
            avg_lap_time = None
            if 'LapTime' in stint_data.columns:
                valid_times = stint_data['LapTime'].dropna()
                if len(valid_times) > 0:
                    avg_lap_time = valid_times.mean().total_seconds()
            
            stint_info = {
                'stint_number': int(stint),
                'compound': compound,
                'start_lap': start_lap,
                'end_lap': end_lap,
                'length': stint_length,
                'tyre_life_start': tyre_life_start,
                'tyre_life_end': tyre_life_end,
                'avg_lap_time': avg_lap_time
            }
            
            stint_analysis.append(stint_info)
            
            # 檢查是否有輪胎更換
            if prev_stint is not None and prev_compound is not None and compound != prev_compound:
                tire_change = {
                    'lap': start_lap - 1,
                    'from_compound': prev_compound,
                    'to_compound': compound,
                    'from_stint': int(prev_stint),
                    'to_stint': int(stint)
                }
                tire_changes.append(tire_change)
            
            prev_stint = stint
            prev_compound = compound
        
        # 輪胎配方使用統計
        compound_stats = {}
        if 'Compound' in driver_data.columns:
            compound_counts = driver_data['Compound'].value_counts()
            for compound, count in compound_counts.items():
                percentage = (count / total_laps) * 100
                compound_stats[compound] = {
                    'laps': int(count),
                    'percentage': round(percentage, 1)
                }
        
        # 構建結果
        result = {
            'analysis_info': {
                'year': year,
                'race': race,
                'session': session,
                'driver': driver,
                'analysis_timestamp': datetime.now().isoformat(),
                'data_source': 'FastF1'
            },
            'driver_summary': {
                'driver': driver,
                'total_laps': total_laps,
                'stint_count': len(stints),
                'tire_changes': len(tire_changes),
                'compounds_used': compounds_used
            },
            'stint_analysis': stint_analysis,
            'tire_changes': tire_changes,
            'compound_usage': compound_stats
        }
        
        if verbose:
            self._print_driver_analysis(result)
        
        return result
    
    def _analyze_all_drivers(self, df: pd.DataFrame, year: int, race: str, session: str, verbose: bool = False) -> Dict[str, Any]:
        """分析所有車手的輪胎策略"""
        
        if verbose:
            print(f"\n🏎️ 分析所有車手的輪胎策略")
            print("-" * 60)
        
        drivers = sorted(df['Driver'].unique())
        if verbose:
            print(f"👥 發現 {len(drivers)} 位車手: {', '.join(drivers)}")
        
        all_drivers_analysis = {}
        overall_stats = {
            'total_laps': len(df),
            'total_drivers': len(drivers),
            'compounds_used': []
        }
        
        # 整體輪胎配方統計
        if 'Compound' in df.columns:
            compound_distribution = df['Compound'].value_counts().to_dict()
            compound_stats = {}
            for compound, count in compound_distribution.items():
                compound_stats[compound] = {
                    'total_laps': int(count),
                    'percentage': round((count / len(df)) * 100, 1)
                }
            overall_stats['compound_distribution'] = compound_stats
            overall_stats['compounds_used'] = list(compound_stats.keys())
        
        # 分析每位車手
        success_count = 0
        for driver in drivers:
            if verbose:
                print(f"\n📊 正在分析車手: {driver}")
            
            driver_result = self._analyze_single_driver(df, driver, year, race, session, verbose=False)
            if driver_result:
                all_drivers_analysis[driver] = driver_result
                success_count += 1
            else:
                if verbose:
                    print(f"⚠️ 車手 {driver} 分析失敗")
        
        # 構建完整結果
        result = {
            'analysis_info': {
                'year': year,
                'race': race,
                'session': session,
                'analysis_timestamp': datetime.now().isoformat(),
                'data_source': 'FastF1',
                'total_drivers_analyzed': success_count
            },
            'overall_statistics': overall_stats,
            'drivers_analysis': all_drivers_analysis
        }
        
        if verbose:
            print(f"\n📋 整體分析完成:")
            print(f"   成功分析: {success_count}/{len(drivers)} 位車手")
            print(f"   總圈數: {overall_stats['total_laps']}")
            if 'compound_distribution' in overall_stats:
                print(f"   使用輪胎: {', '.join(overall_stats['compounds_used'])}")
        
        return result
    
    def _export_to_json(self, analysis_result: Dict[str, Any], year: int, race: str, session: str, driver: str = None, verbose: bool = False) -> Dict[str, Any]:
        """匯出分析結果為 JSON"""
        
        try:
            # 提取會話信息
            mock_data_loader = type('MockLoader', (), {
                'year': year, 'race_name': race, 'session_type': session
            })()
            
            session_info = self.session_extractor.extract_from_data_loader(mock_data_loader)
            
            # 使用統一 JSON 生成器
            result = self.json_generator.save_analysis_result(
                data=analysis_result,
                analysis_type="tire_strategy",
                function_id="26",
                session_info=session_info,
                driver=driver
            )
            
            if verbose:
                if result.get('success'):
                    print(f"✅ JSON 匯出成功: {result['filename']}")
                else:
                    print(f"❌ JSON 匯出失敗")
            
            return result
            
        except Exception as e:
            if verbose:
                print(f"❌ JSON 匯出錯誤: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _print_driver_analysis(self, result: Dict[str, Any]):
        """顯示車手分析結果"""
        driver_info = result['driver_summary']
        driver = driver_info['driver']
        
        print(f"\n📋 {driver} 輪胎策略分析:")
        print(f"   總圈數: {driver_info['total_laps']}")
        print(f"   Stint 數量: {driver_info['stint_count']}")
        print(f"   換胎次數: {driver_info['tire_changes']}")
        print(f"   使用輪胎: {', '.join(driver_info['compounds_used'])}")
        
        # Stint 詳細資訊
        print(f"\n🔄 Stint 詳細分析:")
        for stint in result['stint_analysis']:
            lap_time_info = f", 平均: {stint['avg_lap_time']:.3f}s" if stint['avg_lap_time'] else ""
            print(f"   Stint {stint['stint_number']}: {stint['compound']}, 第{stint['start_lap']}-{stint['end_lap']}圈 ({stint['length']}圈){lap_time_info}")
        
        # 換胎記錄
        if result['tire_changes']:
            print(f"\n🔧 換胎記錄:")
            for i, change in enumerate(result['tire_changes'], 1):
                print(f"   換胎 {i}: 第{change['lap']}圈後, {change['from_compound']} → {change['to_compound']}")
        else:
            print(f"\n🔧 未檢測到換胎 (可能為單一配方策略)")
    
    def _create_error_result(self, message: str) -> Dict[str, Any]:
        """創建錯誤結果"""
        return {
            "success": False,
            "message": message,
            "function_id": "26",
            "timestamp": datetime.now().isoformat()
        }


# CLI 介面函數
def run_tire_strategy_analysis(f1_data=None, year: int = 2025, race: str = "Japan", 
                              session: str = "R", driver: str = None, 
                              use_cache: bool = True, verbose: bool = True, **kwargs) -> Dict[str, Any]:
    """
    輪胎策略分析 CLI 介面函數
    
    適用於 CLI -f26 車手輪胎策略分析
    
    Args:
        f1_data: F1 資料載入器（相容性參數，可為 None）
        year: 年份
        race: 賽事名稱
        session: 賽段類型
        driver: 車手代碼（可選）
        use_cache: 是否使用快取
        verbose: 是否顯示詳細輸出
        **kwargs: 其他參數
        
    Returns:
        分析結果字典
    """
    
    # 創建輪胎策略分析器
    analyzer = TireStrategyAnalyzer()
    
    # 執行分析
    return analyzer.analyze_tire_strategy(
        year=year,
        race=race,
        session=session,
        driver=driver,
        use_cache=use_cache,
        verbose=verbose
    )


# 相容性別名
def run_fastf1_tire_strategy_analysis(*args, **kwargs):
    """相容性別名函數"""
    return run_tire_strategy_analysis(*args, **kwargs)

def run_tire_change_timing_inference(*args, **kwargs):
    """相容性別名函數"""
    return run_tire_strategy_analysis(*args, **kwargs)


if __name__ == "__main__":
    """測試模組"""
    print("🧪 測試輪胎策略分析模組...")
    
    # 測試分析
    result = run_tire_strategy_analysis(
        year=2025,
        race="Japan",
        session="R",
        driver="VER",
        verbose=True
    )
    
    if result['success']:
        print("\n✅ 測試成功！")
    else:
        print(f"\n❌ 測試失敗: {result['message']}")
