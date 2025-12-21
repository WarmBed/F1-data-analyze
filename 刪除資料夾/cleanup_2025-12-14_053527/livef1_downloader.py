"""
Live F1 歷史數據下載器

用途：批量下載 2022-2025 年的 Live F1 歷史賽事數據
儲存位置：json/LiveF1/{year}/{race}_{session}/

使用方式：
    # 列出可用賽事
    python livef1_downloader.py --list --year 2025
    
    # 下載單場賽事
    python livef1_downloader.py --year 2025 --race Japan --session R
    
    # 下載整個賽季
    python livef1_downloader.py --year 2025 --all
    
    # 下載整個賽季的正賽
    python livef1_downloader.py --year 2025 --all --session R
    
    # 下載多個賽季
    python livef1_downloader.py --years 2022-2025 --all --session R
"""

import os
import sys
import json
import time
import zlib
import base64
import argparse
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime


class LiveF1Downloader:
    """Live F1 歷史數據下載器"""
    
    BASE_URL = "https://livetiming.formula1.com/static"
    
    # 需要下載的數據流
    STREAMS = [
        ("Position.z.jsonStream", True),           # 車手位置 (壓縮)
        ("TimingData.jsonStream", False),          # 計時數據
        ("CarData.z.jsonStream", True),            # 車輛遙測 (壓縮)
        ("TimingAppData.jsonStream", False),       # 輪胎策略
        ("WeatherData.jsonStream", False),         # 天氣數據
        ("RaceControlMessages.jsonStream", False), # 比賽控制訊息
        ("TrackStatus.jsonStream", False),         # 賽道狀態
        ("LapCount.jsonStream", False),            # 圈數進度
        ("PitLaneTimeCollection.jsonStream", False), # 維修站時間
        ("DriverList.jsonStream", False),          # 車手列表
        ("SessionInfo.jsonStream", False),         # 賽事資訊
        ("SessionData.jsonStream", False),         # 會話數據
        ("LapSeries.jsonStream", False),           # 圈時序列
        ("TopThree.jsonStream", False),            # 前三名
        ("TimingStats.jsonStream", False),         # 計時統計
        ("ExtrapolatedClock.jsonStream", False),   # 時鐘
        ("TeamRadio.jsonStream", False),           # 車隊無線電
        ("TyreStintSeries.jsonStream", False),     # 輪胎策略序列
    ]
    
    def __init__(self, output_dir: str = "json/LiveF1"):
        """
        初始化下載器
        
        Args:
            output_dir: 輸出目錄
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 請求設定
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.timeout = 30
        
        # 統計
        self.stats = {
            'downloaded': 0,
            'skipped': 0,
            'failed': 0,
            'total_size': 0
        }
    
    def get_year_index(self, year: int) -> Optional[Dict]:
        """取得年度賽事索引"""
        url = f"{self.BASE_URL}/{year}/Index.json"
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                # 處理 UTF-8 BOM
                content = resp.content.decode('utf-8-sig')
                return json.loads(content)
            else:
                print(f"[ERROR] 無法取得 {year} 年索引: HTTP {resp.status_code}")
                return None
        except Exception as e:
            print(f"[ERROR] 取得 {year} 年索引失敗: {e}")
            return None
    
    def list_meetings(self, year: int) -> List[Dict]:
        """列出指定年份的所有賽事"""
        index = self.get_year_index(year)
        if not index:
            return []
        
        meetings = index.get("Meetings", [])
        return meetings
    
    def print_available_meetings(self, year: int):
        """印出可用的賽事列表"""
        meetings = self.list_meetings(year)
        if not meetings:
            print(f"[INFO] {year} 年沒有可用的賽事")
            return
        
        print(f"\n{'='*70}")
        print(f" {year} 年 F1 賽事列表 (共 {len(meetings)} 場)")
        print(f"{'='*70}")
        
        for i, meeting in enumerate(meetings, 1):
            name = meeting.get("Name", "Unknown")
            key = meeting.get("Key", "")
            location = meeting.get("Location", "")
            sessions = meeting.get("Sessions", [])
            
            print(f"\n{i:2}. {name}")
            print(f"    Key: {key}")
            if location:
                print(f"    Location: {location}")
            
            session_names = []
            for sess in sessions:
                sess_name = sess.get("Name", "")
                session_names.append(sess_name)
            print(f"    Sessions: {', '.join(session_names)}")
    
    def _decode_payload(self, payload_text: str, compressed: bool) -> Any:
        """解碼 payload"""
        if compressed:
            try:
                # Base64 解碼 + zlib 解壓
                decoded = base64.b64decode(payload_text)
                decompressed = zlib.decompress(decoded, -zlib.MAX_WBITS)
                return json.loads(decompressed.decode('utf-8'))
            except Exception:
                # 嘗試直接解析
                return json.loads(payload_text)
        else:
            return json.loads(payload_text)
    
    def _parse_stream(self, stream_text: str, compressed: bool) -> List[Dict]:
        """解析 jsonStream 格式"""
        records = []
        lines = stream_text.strip().split('\n')
        
        for line in lines:
            if len(line) <= 12:
                continue
            
            timestamp = line[:12]
            payload_text = line[12:]
            
            try:
                decoded = self._decode_payload(payload_text, compressed)
                records.append({
                    "timestamp": timestamp,
                    "data": decoded
                })
            except Exception:
                # 跳過無法解析的行
                continue
        
        return records
    
    def download_stream(self, url: str, compressed: bool) -> Tuple[bool, Optional[List[Dict]], int]:
        """
        下載並解析單個數據流
        
        Returns:
            (success, data, size_bytes)
        """
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                content = resp.text
                size = len(resp.content)
                records = self._parse_stream(content, compressed)
                return True, records, size
            elif resp.status_code == 404:
                return False, None, 0
            else:
                return False, None, 0
        except Exception as e:
            print(f"    [WARN] 下載失敗: {e}")
            return False, None, 0
    
    def _extract_race_name_from_path(self, path: str) -> str:
        """從 path 提取賽事名稱"""
        # 例如: "2025/2025-04-06_Japanese_Grand_Prix/2025-04-06_Race/" -> "Japanese"
        parts = path.strip('/').split('/')
        if len(parts) >= 2:
            meeting_part = parts[1]  # "2025-04-06_Japanese_Grand_Prix"
            meeting_parts = meeting_part.split('_')
            if len(meeting_parts) >= 2:
                # 找到 Grand Prix 之前的部分
                for i, part in enumerate(meeting_parts):
                    if part == "Grand":
                        return "_".join(meeting_parts[1:i])
                return meeting_parts[1]
        return "Unknown"
    
    def _extract_session_type_from_path(self, path: str) -> str:
        """從 path 提取會話類型"""
        # 例如: "2025/2025-04-06_Japanese_Grand_Prix/2025-04-06_Race/" -> "Race"
        parts = path.strip('/').split('/')
        if len(parts) >= 3:
            session_part = parts[2]  # "2025-04-06_Race"
            if '_' in session_part:
                return session_part.split('_', 1)[-1]  # 取最後部分
        return "Unknown"

    def download_session_by_path(self, session_path: str, meeting_name: str,
                                  session_name: str, force: bool = False) -> Dict[str, Any]:
        """
        使用 path 下載單場會話的所有數據
        
        Args:
            session_path: 會話路徑 (例如 "2025/2025-04-06_Japanese_Grand_Prix/2025-04-06_Race/")
            meeting_name: 賽事名稱
            session_name: 會話名稱
            force: 是否強制重新下載
            
        Returns:
            下載結果統計
        """
        # 提取年份
        year = session_path.split('/')[0]
        
        # 提取名稱
        race_name = self._extract_race_name_from_path(session_path)
        session_type = self._extract_session_type_from_path(session_path)
        
        # 建立輸出目錄
        output_path = self.output_dir / str(year) / f"{race_name}_{session_type}"
        output_path.mkdir(parents=True, exist_ok=True)
        
        result = {
            'year': year,
            'meeting': meeting_name,
            'session': session_name,
            'race_name': race_name,
            'session_type': session_type,
            'output_path': str(output_path),
            'streams': {},
            'total_records': 0,
            'total_size': 0,
            'success': True
        }
        
        print(f"\n[INFO] 下載 {year} {race_name} {session_type}")
        print(f"       輸出目錄: {output_path}")
        
        base_url = f"{self.BASE_URL}/{session_path}"
        
        for stream_name, compressed in self.STREAMS:
            # 輸出檔案名稱
            output_name = stream_name.replace('.z.jsonStream', '.json').replace('.jsonStream', '.json')
            output_file = output_path / output_name
            
            # 檢查是否已存在
            if output_file.exists() and not force:
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                    record_count = len(existing_data.get('records', []))
                    result['streams'][output_name] = {
                        'status': 'skipped',
                        'records': record_count
                    }
                    result['total_records'] += record_count
                    self.stats['skipped'] += 1
                    print(f"  [SKIP] {output_name}: 已存在 ({record_count} 筆)")
                    continue
                except Exception:
                    pass  # 檔案損壞，重新下載
            
            # 下載
            url = f"{base_url}{stream_name}"
            success, data, size = self.download_stream(url, compressed)
            
            if success and data:
                # 儲存
                output_data = {
                    'metadata': {
                        'year': year,
                        'meeting': meeting_name,
                        'session': session_name,
                        'race_name': race_name,
                        'session_type': session_type,
                        'stream': stream_name,
                        'download_time': datetime.now().isoformat(),
                        'record_count': len(data)
                    },
                    'records': data
                }
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, ensure_ascii=False)
                
                result['streams'][output_name] = {
                    'status': 'downloaded',
                    'records': len(data),
                    'size': size
                }
                result['total_records'] += len(data)
                result['total_size'] += size
                self.stats['downloaded'] += 1
                self.stats['total_size'] += size
                
                print(f"  [OK]   {output_name}: {len(data)} 筆 ({size/1024:.1f} KB)")
            else:
                result['streams'][output_name] = {
                    'status': 'not_found',
                    'records': 0
                }
                self.stats['failed'] += 1
                # 不印出 not_found，太多了
        
        # 儲存元數據
        metadata_file = output_path / "_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump({
                'year': year,
                'meeting': meeting_name,
                'session': session_name,
                'race_name': race_name,
                'session_type': session_type,
                'download_time': datetime.now().isoformat(),
                'streams': result['streams'],
                'total_records': result['total_records']
            }, f, ensure_ascii=False, indent=2)
        
        return result
    
    def download_meeting(self, year: int, meeting_identifier: str,
                         session_filter: str = None, force: bool = False) -> List[Dict]:
        """
        下載整場賽事的所有會話
        
        Args:
            year: 年份
            meeting_identifier: 賽事名稱或 Key
            session_filter: 會話過濾器 (R, Q, FP1 等)
            force: 強制重新下載
        """
        results = []
        
        # 取得賽事資訊
        meetings = self.list_meetings(year)
        target_meeting = None
        
        # 將 meeting_identifier 轉為字串
        meeting_identifier = str(meeting_identifier)
        
        for m in meetings:
            key = str(m.get("Key", ""))
            name = m.get("Name", "")
            # 支援模糊匹配
            if (meeting_identifier.lower() in key.lower() or
                meeting_identifier.lower() in name.lower()):
                target_meeting = m
                break
        
        if not target_meeting:
            print(f"[ERROR] 找不到賽事: {meeting_identifier}")
            return results
        
        meeting_key = target_meeting.get("Key")
        meeting_name = target_meeting.get("Name")
        available_sessions = target_meeting.get("Sessions", [])
        
        print(f"\n{'='*70}")
        print(f" 下載 {year} {meeting_name}")
        print(f"{'='*70}")
        
        for sess in available_sessions:
            sess_name = sess.get("Name")
            sess_path = sess.get("Path")  # 使用 Path 欄位
            
            if not sess_path:
                print(f"  [WARN] {sess_name} 沒有 Path，跳過")
                continue
            
            # 過濾會話
            if session_filter:
                filter_upper = session_filter.upper()
                sess_name_upper = sess_name.upper()
                
                # 匹配邏輯
                match = False
                if filter_upper == "R" and "RACE" in sess_name_upper and "SPRINT" not in sess_name_upper:
                    match = True
                elif filter_upper == "Q" and "QUALIFYING" in sess_name_upper and "SPRINT" not in sess_name_upper:
                    match = True
                elif filter_upper == "S" and "SPRINT" in sess_name_upper and "QUALIFYING" not in sess_name_upper and "SHOOTOUT" not in sess_name_upper:
                    match = True
                elif filter_upper == "SQ" and "SPRINT" in sess_name_upper and "QUALIFYING" in sess_name_upper:
                    match = True
                elif filter_upper == "SS" and "SPRINT" in sess_name_upper and "SHOOTOUT" in sess_name_upper:
                    match = True
                elif filter_upper in ["FP1", "FP2", "FP3"]:
                    if filter_upper.replace("FP", "PRACTICE ") in sess_name_upper:
                        match = True
                    elif filter_upper in sess_name_upper:
                        match = True
                
                if not match:
                    continue
            
            # 使用新的 path-based 下載函數
            result = self.download_session_by_path(sess_path, meeting_name, sess_name, force)
            results.append(result)
            
            # 短暫延遲避免請求過快
            time.sleep(0.5)
        
        return results
    
    def download_season(self, year: int, session_filter: str = None,
                        force: bool = False) -> List[Dict]:
        """下載整個賽季"""
        results = []
        meetings = self.list_meetings(year)
        
        if not meetings:
            print(f"[ERROR] 無法取得 {year} 年賽事列表")
            return results
        
        print(f"\n{'='*70}")
        print(f" 下載 {year} 賽季 (共 {len(meetings)} 場賽事)")
        print(f"{'='*70}")
        
        for meeting in meetings:
            meeting_key = meeting.get("Key")
            meeting_results = self.download_meeting(year, meeting_key, session_filter, force)
            results.extend(meeting_results)
        
        return results
    
    def download_range(self, start_year: int, end_year: int,
                       session_filter: str = None, force: bool = False) -> List[Dict]:
        """下載多個賽季"""
        results = []
        
        for year in range(start_year, end_year + 1):
            season_results = self.download_season(year, session_filter, force)
            results.extend(season_results)
        
        return results
    
    def print_stats(self):
        """印出下載統計"""
        print(f"\n{'='*70}")
        print(" 下載統計")
        print(f"{'='*70}")
        print(f"  成功下載: {self.stats['downloaded']} 個檔案")
        print(f"  跳過 (已存在): {self.stats['skipped']} 個檔案")
        print(f"  失敗/不存在: {self.stats['failed']} 個檔案")
        print(f"  總下載大小: {self.stats['total_size']/1024/1024:.2f} MB")


def main():
    parser = argparse.ArgumentParser(
        description='Live F1 歷史數據下載器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 列出 2025 年所有賽事
  python livef1_downloader.py --list --year 2025
  
  # 下載單場正賽
  python livef1_downloader.py --year 2025 --race Japan --session R
  
  # 下載整場賽事 (所有會話)
  python livef1_downloader.py --year 2025 --race Japan
  
  # 下載整個賽季的正賽
  python livef1_downloader.py --year 2025 --all --session R
  
  # 下載 2022-2025 所有正賽
  python livef1_downloader.py --years 2022-2025 --all --session R
  
  # 強制重新下載
  python livef1_downloader.py --year 2025 --race Japan --session R --force
        """
    )
    
    parser.add_argument('--list', action='store_true', help='列出可用賽事')
    parser.add_argument('--year', type=int, help='年份')
    parser.add_argument('--years', type=str, help='年份範圍 (例如: 2022-2025)')
    parser.add_argument('--race', type=str, help='賽事名稱 (例如: Japan, Monaco)')
    parser.add_argument('--session', type=str, help='會話類型 (R, Q, FP1, FP2, FP3, S, SQ, SS)')
    parser.add_argument('--all', action='store_true', help='下載所有賽事')
    parser.add_argument('--force', action='store_true', help='強制重新下載')
    parser.add_argument('--output', type=str, default='json/LiveF1', help='輸出目錄')
    
    args = parser.parse_args()
    
    downloader = LiveF1Downloader(output_dir=args.output)
    
    # 列出賽事
    if args.list:
        if args.year:
            downloader.print_available_meetings(args.year)
        else:
            for year in [2025, 2024, 2023, 2022]:
                downloader.print_available_meetings(year)
        return
    
    # 解析年份範圍
    if args.years:
        parts = args.years.split('-')
        start_year = int(parts[0])
        end_year = int(parts[1]) if len(parts) > 1 else start_year
        
        downloader.download_range(start_year, end_year, args.session, args.force)
        downloader.print_stats()
        return
    
    # 單一年份
    if not args.year:
        parser.print_help()
        return
    
    if args.all:
        # 下載整個賽季
        downloader.download_season(args.year, args.session, args.force)
    elif args.race:
        # 下載單場賽事
        downloader.download_meeting(args.year, args.race, args.session, args.force)
    else:
        parser.print_help()
        return
    
    downloader.print_stats()


if __name__ == "__main__":
    main()
