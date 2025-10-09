"""
F1 分析緩存批量下載工具
===================================
自動下載 2020-2025 年所有 F1 賽季的緩存數據

功能：
- 支援多年份賽季數據下載
- 自動處理所有賽事和會話類型
- 錯誤處理和進度追蹤
- UTF-8 編碼支援中文輸出

使用方式：
    python download_all_cache.py
    python download_all_cache.py --years 2024 2025  # 只下載特定年份
    python download_all_cache.py --sessions R Q     # 只下載特定會話
    python download_all_cache.py --skip-practice   # 跳過練習賽

Author: F1T Team
Date: 2025-10-07
"""

import fastf1
import argparse
import sys
import os
from datetime import datetime
from pathlib import Path
import time

# 設定 UTF-8 輸出編碼
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class F1CacheDownloader:
    """F1 賽事數據緩存下載器"""
    
    def __init__(self, cache_dir: str = "f1_analysis_cache"):
        """
        初始化下載器
        
        Args:
            cache_dir: 緩存目錄路徑
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # 設定 FastF1 緩存
        fastf1.Cache.enable_cache(str(self.cache_dir))
        
        # 統計數據
        self.total_sessions = 0
        self.successful_downloads = 0
        self.failed_downloads = 0
        self.skipped_sessions = 0
        self.errors = []
        
        # 會話類型映射
        self.session_types = {
            'FP1': 'Practice 1',
            'FP2': 'Practice 2', 
            'FP3': 'Practice 3',
            'Q': 'Qualifying',
            'S': 'Sprint',
            'R': 'Race'
        }
    
    def print_header(self):
        """顯示程式標題"""
        print("=" * 80)
        print("🏎️  F1 分析緩存批量下載工具")
        print("=" * 80)
        print(f"📁 緩存目錄: {self.cache_dir.absolute()}")
        print(f"⏰ 開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()
    
    def print_progress(self, current: int, total: int, year: int, race_name: str, session: str):
        """
        顯示下載進度
        
        Args:
            current: 當前進度
            total: 總數
            year: 年份
            race_name: 賽事名稱
            session: 會話類型
        """
        percentage = (current / total * 100) if total > 0 else 0
        bar_length = 40
        filled_length = int(bar_length * current // total)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        print(f"\r[{bar}] {percentage:.1f}% ({current}/{total}) | "
              f"{year} {race_name} - {session}", end='', flush=True)
    
    def download_session(self, year: int, race_name: str, session_type: str, 
                        current: int, total: int) -> bool:
        """
        下載單一會話數據
        
        Args:
            year: 賽季年份
            race_name: 賽事名稱
            session_type: 會話類型 (R, Q, FP1, etc.)
            current: 當前進度
            total: 總進度
            
        Returns:
            下載是否成功
        """
        try:
            self.print_progress(current, total, year, race_name, session_type)
            
            # 載入會話數據 (這會自動緩存)
            session = fastf1.get_session(year, race_name, session_type)
            session.load()
            
            self.successful_downloads += 1
            return True
            
        except Exception as e:
            error_msg = f"{year} {race_name} {session_type}: {str(e)}"
            self.errors.append(error_msg)
            self.failed_downloads += 1
            return False
    
    def download_year(self, year: int, session_filter: list = None, 
                     skip_practice: bool = False) -> None:
        """
        下載整年賽季數據
        
        Args:
            year: 賽季年份
            session_filter: 只下載特定會話類型 (例如: ['R', 'Q'])
            skip_practice: 是否跳過練習賽
        """
        try:
            print(f"\n📅 正在處理 {year} 年賽季...")
            print("-" * 80)
            
            # 獲取賽季賽程
            schedule = fastf1.get_event_schedule(year)
            
            # 過濾已完成的賽事
            completed_events = schedule[schedule['EventDate'] < datetime.now()]
            
            if len(completed_events) == 0:
                print(f"⚠️  {year} 年尚無已完成的賽事")
                return
            
            print(f"📊 找到 {len(completed_events)} 場已完成的賽事")
            
            # 計算總會話數
            sessions_to_download = []
            for _, event in completed_events.iterrows():
                race_name = event['EventName']
                
                # 確定要下載的會話
                available_sessions = []
                for session_abbr in ['FP1', 'FP2', 'FP3', 'Q', 'S', 'R']:
                    # 應用過濾條件
                    if session_filter and session_abbr not in session_filter:
                        continue
                    if skip_practice and session_abbr.startswith('FP'):
                        continue
                    available_sessions.append(session_abbr)
                
                for session_abbr in available_sessions:
                    sessions_to_download.append((year, race_name, session_abbr))
            
            total_sessions = len(sessions_to_download)
            self.total_sessions += total_sessions
            
            print(f"🎯 計劃下載 {total_sessions} 個會話")
            print()
            
            # 下載所有會話
            for idx, (year, race_name, session_abbr) in enumerate(sessions_to_download, 1):
                current_progress = self.successful_downloads + self.failed_downloads + self.skipped_sessions
                success = self.download_session(
                    year, race_name, session_abbr, 
                    current_progress + 1, 
                    self.total_sessions
                )
                
                # 添加延遲以避免 API 限制
                if success:
                    time.sleep(0.5)
                else:
                    time.sleep(1.0)
            
            print()  # 換行
            
        except Exception as e:
            print(f"\n❌ 處理 {year} 年賽季時發生錯誤: {str(e)}")
            self.errors.append(f"{year} 賽季: {str(e)}")
    
    def download_all_years(self, years: list = None, session_filter: list = None,
                          skip_practice: bool = False) -> None:
        """
        下載多個年份的數據
        
        Args:
            years: 年份列表，預設為 2020-2025
            session_filter: 只下載特定會話類型
            skip_practice: 是否跳過練習賽
        """
        if years is None:
            years = list(range(2020, 2026))  # 2020-2025
        
        print(f"🎯 目標年份: {', '.join(map(str, years))}")
        
        if session_filter:
            print(f"🎯 會話過濾: {', '.join(session_filter)}")
        
        if skip_practice:
            print("⏭️  跳過練習賽")
        
        for year in years:
            self.download_year(year, session_filter, skip_practice)
    
    def print_summary(self):
        """顯示下載摘要"""
        print("\n" + "=" * 80)
        print("📊 下載完成摘要")
        print("=" * 80)
        print(f"✅ 成功: {self.successful_downloads} 個會話")
        print(f"❌ 失敗: {self.failed_downloads} 個會話")
        print(f"⏭️  跳過: {self.skipped_sessions} 個會話")
        print(f"📦 總計: {self.total_sessions} 個會話")
        
        if self.successful_downloads > 0:
            success_rate = (self.successful_downloads / self.total_sessions * 100)
            print(f"📈 成功率: {success_rate:.1f}%")
        
        print(f"📁 緩存位置: {self.cache_dir.absolute()}")
        
        # 顯示緩存大小
        cache_size = self._get_cache_size()
        print(f"💾 緩存大小: {self._format_size(cache_size)}")
        
        if self.errors:
            print(f"\n⚠️  錯誤列表 ({len(self.errors)} 項):")
            print("-" * 80)
            for error in self.errors[:10]:  # 只顯示前10個錯誤
                print(f"  • {error}")
            if len(self.errors) > 10:
                print(f"  ... 還有 {len(self.errors) - 10} 個錯誤")
        
        print("=" * 80)
        print(f"⏰ 完成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
    
    def _get_cache_size(self) -> int:
        """計算緩存目錄大小"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(self.cache_dir):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception as e:
            print(f"⚠️  計算緩存大小時出錯: {e}")
        return total_size
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化檔案大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='F1 分析緩存批量下載工具 - 下載 2020-2025 年所有賽季數據',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 下載所有年份所有會話
  python download_all_cache.py
  
  # 只下載 2024 和 2025 年
  python download_all_cache.py --years 2024 2025
  
  # 只下載正賽和排位賽
  python download_all_cache.py --sessions R Q
  
  # 跳過練習賽
  python download_all_cache.py --skip-practice
  
  # 組合使用
  python download_all_cache.py --years 2024 2025 --sessions R Q --cache-dir my_cache
        """
    )
    
    parser.add_argument(
        '--years',
        type=int,
        nargs='+',
        help='指定要下載的年份 (預設: 2020-2025)',
        metavar='YEAR'
    )
    
    parser.add_argument(
        '--sessions',
        type=str,
        nargs='+',
        choices=['FP1', 'FP2', 'FP3', 'Q', 'S', 'R'],
        help='只下載特定會話類型',
        metavar='SESSION'
    )
    
    parser.add_argument(
        '--skip-practice',
        action='store_true',
        help='跳過所有練習賽 (FP1, FP2, FP3)'
    )
    
    parser.add_argument(
        '--cache-dir',
        type=str,
        default='f1_analysis_cache',
        help='緩存目錄路徑 (預設: f1_analysis_cache)',
        metavar='DIR'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='減少輸出訊息'
    )
    
    args = parser.parse_args()
    
    # 創建下載器
    downloader = F1CacheDownloader(cache_dir=args.cache_dir)
    
    if not args.quiet:
        downloader.print_header()
    
    try:
        # 開始下載
        start_time = time.time()
        
        downloader.download_all_years(
            years=args.years,
            session_filter=args.sessions,
            skip_practice=args.skip_practice
        )
        
        elapsed_time = time.time() - start_time
        
        # 顯示摘要
        if not args.quiet:
            downloader.print_summary()
            print(f"\n⏱️  總耗時: {elapsed_time:.1f} 秒")
        
        # 根據結果設定退出碼
        if downloader.failed_downloads > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  使用者中斷下載")
        downloader.print_summary()
        sys.exit(130)
    
    except Exception as e:
        print(f"\n❌ 發生嚴重錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
