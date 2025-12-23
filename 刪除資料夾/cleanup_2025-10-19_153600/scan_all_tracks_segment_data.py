#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
掃描 2024 賽季所有賽道的 Segment 加速數據覆蓋率
================================================================================
功能：
1. 自動獲取 2024 賽季所有賽道列表
2. 檢查 json/ 目錄中是否已有數據
3. 分析每個賽道的 Segment 覆蓋率
4. 生成詳細統計報告
5. 可選：自動執行 CLI 生成缺失的數據
================================================================================
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import fastf1


class SegmentDataScanner:
    """Segment 數據掃描器"""
    
    def __init__(self, year: int = 2024, session: str = "R"):
        self.year = year
        self.session = session
        self.json_dir = Path("json")
        self.results = []
        
    def get_all_races(self) -> List[Tuple[int, str]]:
        """
        獲取指定年份的所有賽事
        
        Returns:
            List[Tuple[int, str]]: [(round_number, race_name), ...]
        """
        try:
            schedule = fastf1.get_event_schedule(self.year)
            races = []
            
            for idx, event in schedule.iterrows():
                # 只包含正式賽事（排除測試和衝刺賽特殊會期）
                if event['EventFormat'] != 'testing':
                    round_num = event['RoundNumber']
                    # 使用 Country 作為賽事名稱
                    race_name = event['Country']
                    races.append((round_num, race_name))
            
            return races
        except Exception as e:
            print(f"❌ 獲取賽程失敗: {e}")
            return []
    
    def find_json_file(self, race_name: str) -> Optional[Path]:
        """
        查找指定賽事的 JSON 檔案
        
        Args:
            race_name: 賽事名稱（例如 "Japan"）
            
        Returns:
            Optional[Path]: JSON 檔案路徑，未找到返回 None
        """
        # 嘗試兩種可能的檔名格式
        patterns = [
            f"all_drivers_straight_line_speed_{self.year}_{race_name}_{self.session}.json",
            f"all_drivers_straight_line_speed_{self.year}_{race_name}_{self.session}_*.json"
        ]
        
        for pattern in patterns:
            matches = list(self.json_dir.glob(pattern))
            if matches:
                # 返回最新的檔案
                return max(matches, key=lambda p: p.stat().st_mtime)
        
        return None
    
    def analyze_json_coverage(self, json_path: Path) -> Dict:
        """
        分析 JSON 檔案的 Segment 覆蓋率
        
        Args:
            json_path: JSON 檔案路徑
            
        Returns:
            Dict: 分析結果
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 支援三種 JSON 格式
            if 'data' in data and 'data' in data['data'] and 'driver_speeds' in data['data']['data']:
                # 雙層嵌套格式：{"data": {"data": {"driver_speeds": [...]}}}
                drivers = data['data']['data']['driver_speeds']
            elif 'data' in data and 'driver_speeds' in data['data']:
                # 單層嵌套格式：{"data": {"driver_speeds": [...]}}
                drivers = data['data']['driver_speeds']
            elif 'drivers' in data:
                # 舊格式：{"drivers": [...]}
                drivers = data['drivers']
            else:
                return {
                    'status': 'invalid',
                    'error': '無效的 JSON 格式（缺少 drivers 或 driver_speeds 欄位）'
                }
            
            total = len(drivers)
            has_data = 0
            no_data = 0
            drivers_with_data = []
            drivers_without_data = []
            
            for driver in drivers:
                # 支援兩種欄位名稱
                driver_code = driver.get('driver_code') or driver.get('driver', 'UNKNOWN')
                segment_time = driver.get('segment_accel_time_seconds')
                segment_accel = driver.get('segment_acceleration_m_s2') or driver.get('segment_avg_acceleration_ms2')
                
                if segment_time is not None and segment_accel is not None:
                    has_data += 1
                    drivers_with_data.append({
                        'code': driver_code,
                        'time': segment_time,
                        'acceleration': segment_accel
                    })
                else:
                    no_data += 1
                    drivers_without_data.append(driver_code)
            
            coverage = (has_data / total * 100) if total > 0 else 0
            
            return {
                'status': 'success',
                'total': total,
                'has_data': has_data,
                'no_data': no_data,
                'coverage': coverage,
                'drivers_with_data': drivers_with_data,
                'drivers_without_data': drivers_without_data
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def generate_data_via_cli(self, race_name: str) -> bool:
        """
        通過 CLI 生成數據
        
        Args:
            race_name: 賽事名稱
            
        Returns:
            bool: 是否成功
        """
        try:
            cmd = [
                "python",
                "f1_analysis_modular_main.py",
                "-f", "48",
                "-y", str(self.year),
                "-r", race_name,
                "-s", self.session
            ]
            
            print(f"   ⏳ 執行: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=300  # 5 分鐘超時
            )
            
            if result.returncode == 0:
                print(f"   ✅ 數據生成成功")
                return True
            else:
                print(f"   ❌ 數據生成失敗: {result.stderr[:200]}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"   ⏰ 執行超時（5 分鐘）")
            return False
        except Exception as e:
            print(f"   ❌ 執行錯誤: {e}")
            return False
    
    def scan_all_tracks(self, auto_generate: bool = False) -> List[Dict]:
        """
        掃描所有賽道
        
        Args:
            auto_generate: 是否自動生成缺失的數據
            
        Returns:
            List[Dict]: 掃描結果列表
        """
        print("=" * 80)
        print(f"🔍 掃描 {self.year} 賽季所有賽道的 Segment 數據")
        print("=" * 80)
        print()
        
        # 獲取所有賽事
        races = self.get_all_races()
        if not races:
            print("❌ 無法獲取賽程")
            return []
        
        print(f"📋 找到 {len(races)} 場賽事")
        print()
        
        results = []
        
        for round_num, race_name in races:
            print(f"🏁 Round {round_num:02d}: {race_name}")
            print("-" * 80)
            
            # 檢查 JSON 檔案
            json_path = self.find_json_file(race_name)
            
            if json_path is None:
                print(f"   ⚠️  未找到 JSON 檔案")
                
                if auto_generate:
                    print(f"   🔄 嘗試自動生成數據...")
                    success = self.generate_data_via_cli(race_name)
                    
                    if success:
                        # 重新查找 JSON 檔案
                        json_path = self.find_json_file(race_name)
                        if json_path is None:
                            result = {
                                'round': round_num,
                                'race': race_name,
                                'status': 'generated_but_not_found',
                                'message': '數據生成成功但未找到 JSON 檔案'
                            }
                        else:
                            # 分析生成的數據
                            analysis = self.analyze_json_coverage(json_path)
                            result = {
                                'round': round_num,
                                'race': race_name,
                                'json_path': str(json_path),
                                **analysis
                            }
                    else:
                        result = {
                            'round': round_num,
                            'race': race_name,
                            'status': 'generation_failed',
                            'message': 'CLI 數據生成失敗'
                        }
                else:
                    result = {
                        'round': round_num,
                        'race': race_name,
                        'status': 'missing',
                        'message': '未找到 JSON 檔案（使用 --generate 自動生成）'
                    }
            else:
                print(f"   📂 找到檔案: {json_path.name}")
                
                # 分析覆蓋率
                analysis = self.analyze_json_coverage(json_path)
                
                if analysis['status'] == 'success':
                    coverage = analysis['coverage']
                    has_data = analysis['has_data']
                    total = analysis['total']
                    
                    if coverage == 100.0:
                        print(f"   ✅ 覆蓋率: {coverage:.1f}% ({has_data}/{total})")
                    elif coverage >= 80.0:
                        print(f"   ⚠️  覆蓋率: {coverage:.1f}% ({has_data}/{total})")
                    else:
                        print(f"   ❌ 覆蓋率: {coverage:.1f}% ({has_data}/{total})")
                    
                    # 顯示缺失數據的車手
                    if analysis['drivers_without_data']:
                        print(f"   🚫 缺失數據車手: {', '.join(analysis['drivers_without_data'])}")
                else:
                    print(f"   ❌ 分析失敗: {analysis.get('error', '未知錯誤')}")
                
                result = {
                    'round': round_num,
                    'race': race_name,
                    'json_path': str(json_path),
                    **analysis
                }
            
            results.append(result)
            print()
        
        self.results = results
        return results
    
    def print_summary(self):
        """列印統計摘要"""
        if not self.results:
            print("❌ 沒有掃描結果")
            return
        
        print("=" * 80)
        print("📊 統計摘要")
        print("=" * 80)
        print()
        
        total_races = len(self.results)
        perfect_coverage = []  # 100% 覆蓋率
        good_coverage = []     # 80-99% 覆蓋率
        poor_coverage = []     # < 80% 覆蓋率
        missing_data = []      # 未找到數據
        errors = []            # 錯誤
        
        for result in self.results:
            race_name = result['race']
            status = result.get('status', 'unknown')
            
            if status == 'success':
                coverage = result['coverage']
                if coverage == 100.0:
                    perfect_coverage.append(race_name)
                elif coverage >= 80.0:
                    good_coverage.append((race_name, coverage))
                else:
                    poor_coverage.append((race_name, coverage))
            elif status in ['missing', 'generation_failed', 'generated_but_not_found']:
                missing_data.append(race_name)
            else:
                errors.append(race_name)
        
        # 統計輸出
        print(f"📋 總賽事數: {total_races}")
        print()
        
        print(f"✅ 完美覆蓋率 (100%): {len(perfect_coverage)} 場")
        if perfect_coverage:
            for race in perfect_coverage:
                print(f"   • {race}")
        print()
        
        print(f"⚠️  良好覆蓋率 (80-99%): {len(good_coverage)} 場")
        if good_coverage:
            for race, coverage in good_coverage:
                print(f"   • {race}: {coverage:.1f}%")
        print()
        
        print(f"❌ 較低覆蓋率 (< 80%): {len(poor_coverage)} 場")
        if poor_coverage:
            for race, coverage in poor_coverage:
                print(f"   • {race}: {coverage:.1f}%")
        print()
        
        print(f"🚫 缺失數據: {len(missing_data)} 場")
        if missing_data:
            for race in missing_data:
                print(f"   • {race}")
        print()
        
        print(f"⚠️  錯誤: {len(errors)} 場")
        if errors:
            for race in errors:
                print(f"   • {race}")
        print()
        
        # 總體統計
        success_rate = (len(perfect_coverage) + len(good_coverage)) / total_races * 100 if total_races > 0 else 0
        print(f"🎯 整體成功率: {success_rate:.1f}% ({len(perfect_coverage) + len(good_coverage)}/{total_races})")
        print()
    
    def export_report(self, output_file: str = "segment_scan_report.json"):
        """
        導出詳細報告到 JSON 檔案
        
        Args:
            output_file: 輸出檔案名稱
        """
        if not self.results:
            print("❌ 沒有掃描結果可導出")
            return
        
        report = {
            'scan_info': {
                'year': self.year,
                'session': self.session,
                'total_races': len(self.results)
            },
            'results': self.results
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"📄 報告已導出: {output_file}")
        except Exception as e:
            print(f"❌ 導出失敗: {e}")


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='掃描 F1 賽季所有賽道的 Segment 加速數據覆蓋率',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例：
  # 掃描 2024 賽季（僅檢查已有數據）
  python scan_all_tracks_segment_data.py
  
  # 掃描 2024 賽季並自動生成缺失的數據
  python scan_all_tracks_segment_data.py --generate
  
  # 掃描 2025 賽季
  python scan_all_tracks_segment_data.py -y 2025
  
  # 掃描排位賽數據
  python scan_all_tracks_segment_data.py -s Q
  
  # 導出詳細報告
  python scan_all_tracks_segment_data.py --export report.json
        """
    )
    
    parser.add_argument(
        '-y', '--year',
        type=int,
        default=2024,
        help='賽季年份（預設：2024）'
    )
    
    parser.add_argument(
        '-s', '--session',
        type=str,
        default='R',
        choices=['R', 'Q', 'FP1', 'FP2', 'FP3', 'Sprint'],
        help='會話類型（預設：R）'
    )
    
    parser.add_argument(
        '--generate',
        action='store_true',
        help='自動生成缺失的數據（通過 CLI）'
    )
    
    parser.add_argument(
        '--export',
        type=str,
        metavar='FILE',
        help='導出詳細報告到 JSON 檔案'
    )
    
    args = parser.parse_args()
    
    # 創建掃描器
    scanner = SegmentDataScanner(year=args.year, session=args.session)
    
    # 執行掃描
    results = scanner.scan_all_tracks(auto_generate=args.generate)
    
    # 列印摘要
    scanner.print_summary()
    
    # 導出報告
    if args.export:
        scanner.export_report(args.export)
    
    print("=" * 80)
    print("✅ 掃描完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
