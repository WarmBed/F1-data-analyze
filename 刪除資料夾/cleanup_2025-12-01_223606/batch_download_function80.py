"""
批量下載 2025 賽季所有賽事的 Function 80 Q->R 正賽預測

功能：
- 自動下載 2025 賽季已完成賽事的 Q->R 預測數據
- 包含排位賽結果、正賽預測、實際結果和預測準確度
- 錯誤處理與重試機制
- 進度顯示與統計報告

使用方法：
    python batch_download_function80.py
    python batch_download_function80.py --races "Las Vegas" "Qatar"
    python batch_download_function80.py --force  # 強制重新生成
"""

import subprocess
import time
import argparse
from datetime import datetime
from pathlib import Path
import json
import sys

# ✅ 2025 賽季所有賽道列表（按賽曆順序）
ALL_RACES_2025 = [
    'Australia',         # 1. 澳洲 (2025-03-16)
    'China',             # 2. 中國 (2025-03-23)
    'Japan',             # 3. 日本 (2025-04-06)
    'Bahrain',           # 4. 巴林 (2025-04-13)
    'Saudi Arabia',      # 5. 沙烏地阿拉伯 (2025-04-20)
    'Miami',             # 6. 邁阿密 (2025-05-04)
    'Emilia Romagna',    # 7. 艾米利亞-羅馬涅 (2025-05-18)
    'Monaco',            # 8. 摩納哥 (2025-05-25)
    'Spain',             # 9. 西班牙 (2025-06-01)
    'Canada',            # 10. 加拿大 (2025-06-15)
    'Austria',           # 11. 奧地利 (2025-06-29)
    'Great Britain',     # 12. 英國 (2025-07-06)
    'Belgium',           # 13. 比利時 (2025-07-27)
    'Hungary',           # 14. 匈牙利 (2025-08-03)
    'Netherlands',       # 15. 荷蘭 (2025-08-31)
    'Italy',             # 16. 義大利 (2025-09-07)
    'Azerbaijan',        # 17. 亞塞拜然 (2025-09-21)
    'Singapore',         # 18. 新加坡 (2025-10-05)
    'United States',     # 19. 美國 (2025-10-19)
    'Mexico',            # 20. 墨西哥 (2025-10-26)
    'Brazil',            # 21. 巴西 (2025-11-09)
    'Las Vegas',         # 22. 拉斯維加斯 (2025-11-22)
    'Qatar',             # 23. 卡達 (2025-11-30)
    'Abu Dhabi'          # 24. 阿布達比 (2025-12-07)
]

# ✅ 截至 2025-11-27 已完成的賽事（有正賽結果）
COMPLETED_RACES_2025 = [
    'Australia',
    'China', 
    'Japan',
    'Bahrain',
    'Saudi Arabia',
    'Miami',
    'Emilia Romagna',
    'Monaco',
    'Spain',
    'Canada',
    'Austria',
    'Great Britain',
    'Belgium',
    'Hungary',
    'Netherlands',
    'Italy',
    'Azerbaijan',
    'Singapore',
    'United States',
    'Mexico',
    'Brazil',
    'Las Vegas',
    # 'Qatar',      # 2025-11-30 尚未完成
    # 'Abu Dhabi'   # 2025-12-07 尚未完成
]


class BatchFunction80Downloader:
    """批量下載 Function 80 Q->R 預測數據的管理器"""
    
    def __init__(self, year: int = 2025):
        self.year = year
        self.results = {
            'success': [],
            'failed': [],
            'skipped': []
        }
        self.start_time = None
        self.json_dir = Path('json') / 'prediction'
        
    def check_existing_file(self, race: str) -> bool:
        """檢查 JSON 檔案是否已存在"""
        # 檔案命名格式: race_prediction_{year}_{race}.json
        pattern = f"race_prediction_{self.year}_{race}.json"
        file_path = self.json_dir / pattern
        return file_path.exists()
    
    def run_function80(self, race: str, force: bool = False) -> dict:
        """
        執行 Function 80 Q->R 預測分析
        
        Args:
            race: 賽道名稱
            force: 是否強制重新生成（即使檔案已存在）
            
        Returns:
            dict: 執行結果 {'success': bool, 'message': str, 'time': float}
        """
        start = time.time()
        
        # 檢查檔案是否存在
        if not force and self.check_existing_file(race):
            return {
                'success': True,
                'message': 'File already exists (skipped)',
                'time': 0,
                'skipped': True
            }
        
        try:
            # 構建命令
            cmd = [
                sys.executable,  # 使用當前 Python 解釋器
                'f1_analysis_modular_main.py',
                '-f', '80',
                '-y', str(self.year),
                '-r', race
            ]
            
            print(f"  [CMD] {' '.join(cmd)}")
            
            # 執行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=120  # 2 分鐘超時
            )
            
            elapsed = time.time() - start
            
            if result.returncode == 0:
                # 檢查是否真的生成了檔案
                if self.check_existing_file(race):
                    return {
                        'success': True,
                        'message': 'Generated successfully',
                        'time': elapsed,
                        'skipped': False
                    }
                else:
                    return {
                        'success': False,
                        'message': 'Command succeeded but no file generated',
                        'time': elapsed,
                        'skipped': False
                    }
            else:
                error_msg = result.stderr[:200] if result.stderr else 'Unknown error'
                return {
                    'success': False,
                    'message': f'Command failed: {error_msg}',
                    'time': elapsed,
                    'skipped': False
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'message': 'Timeout (>120s)',
                'time': 120,
                'skipped': False
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Exception: {str(e)}',
                'time': time.time() - start,
                'skipped': False
            }
    
    def run_batch(self, races: list = None, force: bool = False, completed_only: bool = True):
        """
        批量執行 Function 80
        
        Args:
            races: 指定賽道列表，None 則使用全部
            force: 是否強制重新生成
            completed_only: 是否只處理已完成的賽事
        """
        self.start_time = datetime.now()
        
        # 確定要處理的賽道
        if races:
            target_races = races
        elif completed_only:
            target_races = COMPLETED_RACES_2025
        else:
            target_races = ALL_RACES_2025
        
        total = len(target_races)
        
        print("=" * 70)
        print(f"[BATCH] Function 80 Q->R Prediction Batch Download")
        print(f"[BATCH] Year: {self.year}")
        print(f"[BATCH] Total races: {total}")
        print(f"[BATCH] Force regenerate: {force}")
        print(f"[BATCH] Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        for i, race in enumerate(target_races, 1):
            print(f"\n[{i}/{total}] Processing: {race}")
            
            result = self.run_function80(race, force=force)
            
            if result.get('skipped'):
                self.results['skipped'].append(race)
                print(f"  [SKIP] {result['message']}")
            elif result['success']:
                self.results['success'].append(race)
                print(f"  [OK] {result['message']} ({result['time']:.1f}s)")
            else:
                self.results['failed'].append({'race': race, 'error': result['message']})
                print(f"  [FAIL] {result['message']}")
            
            # 避免 API 過載
            if not result.get('skipped') and i < total:
                print("  [WAIT] Cooling down for 2 seconds...")
                time.sleep(2)
        
        self._print_summary()
    
    def _print_summary(self):
        """打印執行摘要"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print("\n" + "=" * 70)
        print("[SUMMARY] Batch Download Complete")
        print("=" * 70)
        print(f"  Total time: {duration:.1f}s ({duration/60:.1f} min)")
        print(f"  Success: {len(self.results['success'])} races")
        print(f"  Skipped: {len(self.results['skipped'])} races (already exist)")
        print(f"  Failed: {len(self.results['failed'])} races")
        
        if self.results['success']:
            print(f"\n  [OK] Successfully generated:")
            for race in self.results['success']:
                print(f"       - {race}")
        
        if self.results['failed']:
            print(f"\n  [FAIL] Failed races:")
            for item in self.results['failed']:
                print(f"       - {item['race']}: {item['error'][:50]}")
        
        # 保存報告
        self._save_report()
    
    def _save_report(self):
        """保存執行報告到 JSON"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'year': self.year,
            'results': {
                'success': self.results['success'],
                'skipped': self.results['skipped'],
                'failed': [{'race': f['race'], 'error': f['error']} for f in self.results['failed']]
            },
            'statistics': {
                'total_success': len(self.results['success']),
                'total_skipped': len(self.results['skipped']),
                'total_failed': len(self.results['failed'])
            }
        }
        
        report_path = self.json_dir / f"batch_f80_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            self.json_dir.mkdir(parents=True, exist_ok=True)
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n  [REPORT] Saved to: {report_path}")
        except Exception as e:
            print(f"\n  [WARN] Failed to save report: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Batch download Function 80 Q->R prediction for 2025 season'
    )
    parser.add_argument(
        '--races', 
        nargs='+', 
        help='Specific races to download (e.g., --races "Las Vegas" Qatar)'
    )
    parser.add_argument(
        '--force', 
        action='store_true',
        help='Force regenerate even if file exists'
    )
    parser.add_argument(
        '--all', 
        action='store_true',
        help='Include all races (even upcoming ones without results)'
    )
    parser.add_argument(
        '--year',
        type=int,
        default=2025,
        help='Season year (default: 2025)'
    )
    
    args = parser.parse_args()
    
    downloader = BatchFunction80Downloader(year=args.year)
    downloader.run_batch(
        races=args.races,
        force=args.force,
        completed_only=not args.all
    )


if __name__ == '__main__':
    main()
