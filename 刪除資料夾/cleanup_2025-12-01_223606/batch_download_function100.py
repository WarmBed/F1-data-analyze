"""
批量下載所有賽道的 Function 100 歷年旗幟統計

功能：
- 自動下載所有 2024-2025 賽季的賽道數據
- 支援自定義年份範圍
- 錯誤處理與重試機制
- 進度顯示與統計報告

使用方法：
    python batch_download_function100.py
    python batch_download_function100.py --start-year 2022 --end-year 2025
    python batch_download_function100.py --races Bahrain Japan Brazil
"""

import subprocess
import time
import argparse
from datetime import datetime
from pathlib import Path
import json

# ✅ 2024-2025 賽季所有賽道列表（按賽曆順序）
ALL_RACES_2024_2025 = [
    'Bahrain',           # 1. 巴林
    'Saudi Arabia',      # 2. 沙烏地阿拉伯
    'Australia',         # 3. 澳洲
    'Japan',             # 4. 日本
    'China',             # 5. 中國
    'Miami',             # 6. 邁阿密
    'Emilia Romagna',    # 7. 艾米利亞-羅馬涅
    'Monaco',            # 8. 摩納哥
    'Canada',            # 9. 加拿大
    'Spain',             # 10. 西班牙
    'Austria',           # 11. 奧地利
    'Great Britain',     # 12. 英國
    'Hungary',           # 13. 匈牙利
    'Belgium',           # 14. 比利時
    'Netherlands',       # 15. 荷蘭
    'Italy',             # 16. 義大利
    'Azerbaijan',        # 17. 亞塞拜然
    'Singapore',         # 18. 新加坡
    'United States',     # 19. 美國
    'Mexico',            # 20. 墨西哥
    'Brazil',            # 21. 巴西
    'Las Vegas',         # 22. 拉斯維加斯
    'Qatar',             # 23. 卡達
    'Abu Dhabi'          # 24. 阿布達比
]


class BatchFunction100Downloader:
    """批量下載 Function 100 數據的管理器"""
    
    def __init__(self, start_year=2022, end_year=2025):
        self.start_year = start_year
        self.end_year = end_year
        self.results = {
            'success': [],
            'failed': [],
            'skipped': []
        }
        self.start_time = None
        self.json_dir = Path('json')
        
    def check_existing_file(self, race: str) -> bool:
        """檢查 JSON 檔案是否已存在"""
        # 檔案命名格式: historical_flags_{race}_{start_year}-{end_year}.json
        pattern = f"historical_flags_{race}_{self.start_year}-{self.end_year}.json"
        file_path = self.json_dir / pattern
        return file_path.exists()
    
    def run_function100(self, race: str, force: bool = False) -> dict:
        """
        執行 Function 100 分析
        
        Args:
            race: 賽道名稱
            force: 是否強制重新生成（即使檔案已存在）
            
        Returns:
            結果字典 {'success': bool, 'message': str, 'time': float}
        """
        # 檢查檔案是否已存在
        if not force and self.check_existing_file(race):
            return {
                'success': True,
                'message': f'檔案已存在，跳過',
                'time': 0,
                'skipped': True
            }
        
        # 構建命令
        cmd = [
            'python',
            'f1_analysis_modular_main.py',
            '-f', '100',
            '-y', str(self.end_year),  # 使用結束年份作為參數
            '-r', race
        ]
        
        print(f"\n{'='*70}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 開始處理: {race}")
        print(f"{'='*70}")
        print(f"執行命令: {' '.join(cmd)}")
        
        start_time = time.time()
        
        try:
            # 執行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=600  # 10 分鐘超時
            )
            
            elapsed_time = time.time() - start_time
            
            # 檢查執行結果
            if result.returncode == 0:
                # 驗證 JSON 檔案是否生成
                if self.check_existing_file(race):
                    return {
                        'success': True,
                        'message': f'✅ 成功生成 JSON',
                        'time': elapsed_time,
                        'skipped': False
                    }
                else:
                    return {
                        'success': False,
                        'message': f'⚠️  程式執行成功但未找到 JSON 檔案',
                        'time': elapsed_time,
                        'skipped': False
                    }
            else:
                error_msg = result.stderr.strip() if result.stderr else '未知錯誤'
                return {
                    'success': False,
                    'message': f'❌ 執行失敗: {error_msg[:100]}',
                    'time': elapsed_time,
                    'skipped': False
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'message': '❌ 執行超時（> 10 分鐘）',
                'time': 600,
                'skipped': False
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'❌ 異常: {str(e)}',
                'time': 0,
                'skipped': False
            }
    
    def download_all(self, races: list = None, force: bool = False):
        """
        批量下載所有賽道
        
        Args:
            races: 指定賽道列表（None = 所有賽道）
            force: 是否強制重新生成
        """
        self.start_time = time.time()
        
        # 使用指定賽道或所有賽道
        target_races = races if races else ALL_RACES_2024_2025
        
        print("\n" + "="*70)
        print("🏁 F1 歷年旗幟統計批量下載工具")
        print("="*70)
        print(f"年份範圍: {self.start_year}-{self.end_year}")
        print(f"賽道數量: {len(target_races)}")
        print(f"強制重新生成: {'是' if force else '否'}")
        print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        # 逐個處理賽道
        for idx, race in enumerate(target_races, 1):
            print(f"\n[進度 {idx}/{len(target_races)}] 處理: {race}")
            
            result = self.run_function100(race, force)
            
            # 記錄結果
            race_info = {
                'race': race,
                'message': result['message'],
                'time': result['time']
            }
            
            if result.get('skipped'):
                self.results['skipped'].append(race_info)
                print(f"⏭️  {result['message']}")
            elif result['success']:
                self.results['success'].append(race_info)
                print(f"✅ {result['message']} (耗時: {result['time']:.1f}秒)")
            else:
                self.results['failed'].append(race_info)
                print(f"❌ {result['message']}")
            
            # 避免 API 限制，短暫延遲
            if idx < len(target_races):
                time.sleep(2)
        
        # 顯示最終報告
        self.print_summary()
    
    def print_summary(self):
        """顯示下載統計報告"""
        total_time = time.time() - self.start_time
        total_races = len(self.results['success']) + len(self.results['failed']) + len(self.results['skipped'])
        
        print("\n" + "="*70)
        print("📊 批量下載完成報告")
        print("="*70)
        print(f"總耗時: {total_time:.1f} 秒 ({total_time/60:.1f} 分鐘)")
        print(f"總賽道數: {total_races}")
        print(f"✅ 成功: {len(self.results['success'])} 場")
        print(f"⏭️  跳過: {len(self.results['skipped'])} 場")
        print(f"❌ 失敗: {len(self.results['failed'])} 場")
        
        # 成功列表
        if self.results['success']:
            print(f"\n✅ 成功生成的賽道 ({len(self.results['success'])}):")
            for item in self.results['success']:
                print(f"   - {item['race']:20s} ({item['time']:.1f}秒)")
        
        # 跳過列表
        if self.results['skipped']:
            print(f"\n⏭️  已跳過的賽道 ({len(self.results['skipped'])}):")
            for item in self.results['skipped']:
                print(f"   - {item['race']:20s} (檔案已存在)")
        
        # 失敗列表
        if self.results['failed']:
            print(f"\n❌ 失敗的賽道 ({len(self.results['failed'])}):")
            for item in self.results['failed']:
                print(f"   - {item['race']:20s} {item['message']}")
        
        # 平均時間
        if self.results['success']:
            avg_time = sum(item['time'] for item in self.results['success']) / len(self.results['success'])
            print(f"\n⏱️  平均處理時間: {avg_time:.1f} 秒/場")
        
        print("="*70)
        print(f"完成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70 + "\n")


def main():
    """主程式入口"""
    parser = argparse.ArgumentParser(
        description='批量下載所有賽道的 Function 100 歷年旗幟統計',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 下載所有賽道（2022-2025）
  python batch_download_function100.py
  
  # 自定義年份範圍
  python batch_download_function100.py --start-year 2020 --end-year 2025
  
  # 只下載特定賽道
  python batch_download_function100.py --races Bahrain Japan Brazil
  
  # 強制重新生成（即使檔案已存在）
  python batch_download_function100.py --force
  
  # 組合使用
  python batch_download_function100.py --start-year 2023 --races China Japan --force
        """
    )
    
    parser.add_argument(
        '--start-year',
        type=int,
        default=2022,
        help='起始年份（預設: 2022）'
    )
    
    parser.add_argument(
        '--end-year',
        type=int,
        default=2025,
        help='結束年份（預設: 2025）'
    )
    
    parser.add_argument(
        '--races',
        nargs='+',
        help='指定要下載的賽道（空格分隔），不指定則下載所有賽道'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='強制重新生成（即使檔案已存在）'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='列出所有可用賽道後退出'
    )
    
    args = parser.parse_args()
    
    # 列出賽道
    if args.list:
        print("\n可用賽道列表:")
        for idx, race in enumerate(ALL_RACES_2024_2025, 1):
            print(f"  {idx:2d}. {race}")
        print(f"\n總計: {len(ALL_RACES_2024_2025)} 場賽事\n")
        return
    
    # 驗證賽道名稱
    if args.races:
        invalid_races = [r for r in args.races if r not in ALL_RACES_2024_2025]
        if invalid_races:
            print(f"❌ 錯誤: 無效的賽道名稱: {', '.join(invalid_races)}")
            print(f"\n提示: 使用 --list 查看所有可用賽道")
            return
    
    # 創建下載器並執行
    downloader = BatchFunction100Downloader(
        start_year=args.start_year,
        end_year=args.end_year
    )
    
    downloader.download_all(
        races=args.races,
        force=args.force
    )


if __name__ == '__main__':
    main()
