#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Team Radio Batch Downloader - 2025 全賽季
==========================================

下載 2025 年所有賽事的 Team Radio 數據

使用方式：
    python download_team_radio_2025_all.py

輸出目錄：team_radio_data/2025/

Author: F1T Team
Date: 2026-01-14
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# 添加專案路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from download_team_radio import TeamRadioDownloader


# 2025 年賽事列表（使用 F1 官方 API 名稱格式）
RACES_2025 = [
    "Australian",       # Australia → Australian Grand Prix
    "Chinese",          # China → Chinese Grand Prix
    "Japanese",         # Japan → Japanese Grand Prix
    "Bahrain",
    "Saudi Arabian",    # Saudi Arabia → Saudi Arabian Grand Prix
    "Miami",
    "Emilia Romagna",   # Imola
    "Monaco",
    "Spanish",          # Spain → Spanish Grand Prix
    "Canadian",         # Canada → Canadian Grand Prix
    "Austrian",         # Austria → Austrian Grand Prix
    "British",          # Great Britain → British Grand Prix
    "Hungarian",        # Hungary → Hungarian Grand Prix
    "Belgian",          # Belgium → Belgian Grand Prix
    "Dutch",            # Netherlands → Dutch Grand Prix
    "Italian",          # Italy → Italian Grand Prix (Monza)
    "Azerbaijan",
    "Singapore",
    "United States",    # Austin
    "Mexico City",      # Mexico → Mexico City Grand Prix
    "São Paulo",        # Brazil → São Paulo Grand Prix
    "Las Vegas",
    "Qatar",
    "Abu Dhabi",
]

# 會話類型
SESSIONS = ["R"]  # 只下載正賽，可以加入 ["FP1", "FP2", "FP3", "Q", "R"]


def download_all_2025_team_radio(
    output_dir: str = "team_radio_data",
    sessions: List[str] = None,
    skip_existing: bool = True,
    download_audio: bool = False
) -> Dict[str, Any]:
    """
    下載 2025 全賽季 Team Radio 數據
    
    Args:
        output_dir: 輸出目錄
        sessions: 要下載的會話類型列表，預設只下載正賽
        skip_existing: 是否跳過已存在的檔案
        download_audio: 是否下載 MP3 音檔（很大量，建議關閉）
        
    Returns:
        下載統計結果
    """
    if sessions is None:
        sessions = SESSIONS
    
    year = 2025
    
    print("\n" + "=" * 80)
    print(f" F1 Team Radio Batch Downloader - {year} Full Season")
    print(f" 團隊語音批量下載 - {year} 全賽季")
    print("=" * 80 + "\n")
    
    # 初始化下載器
    base_output = Path(output_dir) / str(year)
    base_output.mkdir(parents=True, exist_ok=True)
    
    downloader = TeamRadioDownloader(output_dir=str(base_output))
    
    # 統計
    stats = {
        "year": year,
        "total_races": len(RACES_2025),
        "total_sessions": len(sessions),
        "successful": [],
        "failed": [],
        "skipped": [],
        "total_records": 0,
    }
    
    print(f"📅 計劃下載：{len(RACES_2025)} 場賽事 × {len(sessions)} 個會話")
    print(f"📂 輸出目錄：{base_output}")
    print(f"⏭️  跳過已存在：{'是' if skip_existing else '否'}")
    print(f"🎵 下載音檔：{'是' if download_audio else '否'}")
    print("\n" + "-" * 80 + "\n")
    
    for race_idx, race in enumerate(RACES_2025, 1):
        for session in sessions:
            race_session = f"{race} {session}"
            
            print(f"\n[{race_idx}/{len(RACES_2025)}] 🏎️  處理: {year} {race} - {session}")
            print("-" * 60)
            
            # 檢查是否已存在
            expected_file = base_output / f"TeamRadio_{year}_{race.replace(' ', '_')}_{session}.jsonStream"
            parsed_file = base_output / f"TeamRadio_{year}_{race.replace(' ', '_')}_{session}_parsed.json"
            
            if skip_existing and parsed_file.exists():
                print(f"   ⏭️  已存在，跳過: {parsed_file.name}")
                stats["skipped"].append(race_session)
                
                # 讀取現有統計
                try:
                    with open(parsed_file, 'r', encoding='utf-8') as f:
                        existing_records = json.load(f)
                    stats["total_records"] += len(existing_records)
                except:
                    pass
                
                continue
            
            try:
                # 1. 下載 TeamRadio 數據流
                stream_file = downloader.download_race_data(year, race, session)
                
                if not stream_file:
                    print(f"   ❌ 無法下載: 找不到賽事或無數據")
                    stats["failed"].append(race_session)
                    continue
                
                # 2. 解析數據流
                records = downloader.parse_team_radio_stream(stream_file)
                
                if not records:
                    print(f"   ⚠️  未找到 TeamRadio 記錄")
                    stats["failed"].append(race_session)
                    continue
                
                print(f"   ✅ 成功: {len(records)} 筆 Team Radio 記錄")
                
                # 統計車手
                drivers = {}
                for record in records:
                    num = record.get('racing_number', '?')
                    drivers[num] = drivers.get(num, 0) + 1
                
                print(f"   📊 車手數: {len(drivers)}")
                top_drivers = sorted(drivers.items(), key=lambda x: x[1], reverse=True)[:3]
                for num, count in top_drivers:
                    print(f"      車手 {num}: {count} 次")
                
                stats["successful"].append(race_session)
                stats["total_records"] += len(records)
                
                # 3. 可選：下載音檔
                if download_audio:
                    print(f"   🎵 下載音檔...")
                    audio_files = downloader.download_audio_files(records)
                    print(f"   ✅ 已下載: {len(audio_files)} 個音檔")
                
                # 避免請求過快
                time.sleep(1)
                
            except Exception as e:
                print(f"   ❌ 錯誤: {e}")
                stats["failed"].append(race_session)
                continue
    
    # 輸出總結
    print("\n" + "=" * 80)
    print(f" 下載完成！總結")
    print("=" * 80 + "\n")
    
    print(f"📊 統計:")
    print(f"   • 總賽事數: {len(RACES_2025)}")
    print(f"   • 成功: {len(stats['successful'])} 場")
    print(f"   • 失敗: {len(stats['failed'])} 場")
    print(f"   • 跳過: {len(stats['skipped'])} 場")
    print(f"   • 總 Team Radio 記錄: {stats['total_records']} 筆")
    
    if stats["failed"]:
        print(f"\n❌ 失敗列表:")
        for failed in stats["failed"]:
            print(f"   • {failed}")
    
    print(f"\n📂 輸出目錄: {base_output}")
    
    # 保存統計結果
    stats_file = base_output / "download_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"📋 統計已保存: {stats_file}")
    
    print("\n" + "=" * 80 + "\n")
    
    return stats


def list_downloaded_races(output_dir: str = "team_radio_data") -> None:
    """
    列出已下載的賽事
    """
    base_dir = Path(output_dir) / "2025"
    
    if not base_dir.exists():
        print(f"目錄不存在: {base_dir}")
        return
    
    print("\n已下載的 Team Radio 數據:")
    print("-" * 60)
    
    total_records = 0
    
    for parsed_file in sorted(base_dir.glob("*_parsed.json")):
        try:
            with open(parsed_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
            
            # 從檔名解析賽事信息
            # TeamRadio_2025_Abu_Dhabi_R_parsed.json
            name = parsed_file.stem.replace("TeamRadio_2025_", "").replace("_parsed", "")
            
            print(f"  ✅ {name}: {len(records)} 筆記錄")
            total_records += len(records)
            
        except Exception as e:
            print(f"  ⚠️  {parsed_file.name}: 讀取失敗 - {e}")
    
    print("-" * 60)
    print(f"總計: {total_records} 筆 Team Radio 記錄")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="下載 2025 全賽季 Team Radio 數據")
    parser.add_argument("--list", action="store_true", help="列出已下載的賽事")
    parser.add_argument("--output", type=str, default="team_radio_data", help="輸出目錄")
    parser.add_argument("--force", action="store_true", help="強制重新下載（不跳過已存在）")
    parser.add_argument("--with-audio", action="store_true", help="同時下載 MP3 音檔")
    parser.add_argument("--session", type=str, default="R", help="會話類型 (R/Q/FP1/FP2/FP3)")
    
    args = parser.parse_args()
    
    if args.list:
        list_downloaded_races(args.output)
    else:
        sessions = [args.session.upper()]
        download_all_2025_team_radio(
            output_dir=args.output,
            sessions=sessions,
            skip_existing=not args.force,
            download_audio=args.with_audio
        )
