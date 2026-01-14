#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Team Radio MP3 Batch Downloader
================================

下載所有已解析的 Team Radio MP3 音檔

使用方式：
    python download_team_radio_mp3_batch.py

Author: F1T Team
Date: 2026-01-14
"""

import os
import sys
import json
import time
import hashlib
import requests
from pathlib import Path
from typing import Dict, List, Any

# 強制 UTF-8 輸出
import io
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 添加專案路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

BASE_URL = "https://livetiming.formula1.com/static"

# 2025 賽事會話路徑映射
SESSION_PATHS_2025 = {
    "Australian": "2025/2025-03-16_Australian_Grand_Prix/2025-03-16_Race/",
    "Chinese": "2025/2025-03-23_Chinese_Grand_Prix/2025-03-23_Race/",
    "Japanese": "2025/2025-04-06_Japanese_Grand_Prix/2025-04-06_Race/",
    "Bahrain": "2025/2025-04-13_Bahrain_Grand_Prix/2025-04-13_Race/",
    "Saudi_Arabian": "2025/2025-04-20_Saudi_Arabian_Grand_Prix/2025-04-20_Race/",
    "Miami": "2025/2025-05-04_Miami_Grand_Prix/2025-05-04_Race/",
    "Emilia_Romagna": "2025/2025-05-18_Emilia_Romagna_Grand_Prix/2025-05-18_Race/",
    "Monaco": "2025/2025-05-25_Monaco_Grand_Prix/2025-05-25_Race/",
    "Spanish": "2025/2025-06-01_Spanish_Grand_Prix/2025-06-01_Race/",
    "Canadian": "2025/2025-06-15_Canadian_Grand_Prix/2025-06-15_Race/",
    "Austrian": "2025/2025-06-29_Austrian_Grand_Prix/2025-06-29_Race/",
    "British": "2025/2025-07-06_British_Grand_Prix/2025-07-06_Race/",
    "Hungarian": "2025/2025-07-27_Hungarian_Grand_Prix/2025-07-27_Race/",
    "Belgian": "2025/2025-08-03_Belgian_Grand_Prix/2025-08-03_Race/",
    "Dutch": "2025/2025-08-31_Dutch_Grand_Prix/2025-08-31_Race/",
    "Italian": "2025/2025-09-07_Italian_Grand_Prix/2025-09-07_Race/",
    "Azerbaijan": "2025/2025-09-21_Azerbaijan_Grand_Prix/2025-09-21_Race/",
    "Singapore": "2025/2025-10-05_Singapore_Grand_Prix/2025-10-05_Race/",
    "United_States": "2025/2025-10-19_United_States_Grand_Prix/2025-10-19_Race/",
    "Mexico_City": "2025/2025-10-26_Mexico_City_Grand_Prix/2025-10-26_Race/",
    "São_Paulo": "2025/2025-11-09_São_Paulo_Grand_Prix/2025-11-09_Race/",
    "Las_Vegas": "2025/2025-11-22_Las_Vegas_Grand_Prix/2025-11-22_Race/",
    "Qatar": "2025/2025-11-30_Qatar_Grand_Prix/2025-11-30_Race/",
    "Abu_Dhabi": "2025/2025-12-07_Abu_Dhabi_Grand_Prix/2025-12-07_Race/",
    # 舊命名兼容
    "Australia": "2025/2025-03-16_Australian_Grand_Prix/2025-03-16_Race/",
    "Japan": "2025/2025-04-06_Japanese_Grand_Prix/2025-04-06_Race/",
    "Saudi_Arabia": "2025/2025-04-20_Saudi_Arabian_Grand_Prix/2025-04-20_Race/",
    "Austria": "2025/2025-06-29_Austrian_Grand_Prix/2025-06-29_Race/",
    "Mexico": "2025/2025-10-26_Mexico_City_Grand_Prix/2025-10-26_Race/",
}


def download_all_mp3(base_dir: str = "team_radio_data/2025"):
    """下載所有 MP3 音檔"""
    base_path = Path(base_dir)
    audio_dir = base_path / "audio"
    audio_dir.mkdir(exist_ok=True)
    
    print("\n" + "=" * 80)
    print(" F1 Team Radio MP3 Batch Downloader")
    print(" 團隊語音 MP3 批量下載")
    print("=" * 80 + "\n")
    
    # 設置 HTTP session
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    # 統計
    total_downloaded = 0
    total_skipped = 0
    total_failed = 0
    total_size = 0
    
    # 處理每個已解析的 JSON
    parsed_files = sorted(base_path.glob("*_parsed.json"))
    print(f"📂 找到 {len(parsed_files)} 個已解析的 JSON 檔案\n")
    
    for file_idx, parsed_file in enumerate(parsed_files, 1):
        # 從檔名提取賽事名稱
        # TeamRadio_2025_Abu_Dhabi_R_parsed.json -> Abu_Dhabi
        filename = parsed_file.stem
        parts = filename.replace("TeamRadio_2025_", "").replace("_parsed", "").rsplit("_", 1)
        race_key = parts[0] if parts else "Unknown"
        
        # 獲取會話路徑
        session_path = SESSION_PATHS_2025.get(race_key)
        if not session_path:
            print(f"[{file_idx}/{len(parsed_files)}] ⚠️  找不到會話路徑: {race_key}")
            continue
        
        print(f"\n[{file_idx}/{len(parsed_files)}] 🏎️  {race_key}")
        print(f"    📂 會話路徑: {session_path}")
        
        # 載入記錄
        try:
            with open(parsed_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
        except Exception as e:
            print(f"    ❌ 載入失敗: {e}")
            continue
        
        print(f"    📊 記錄數: {len(records)}")
        
        # 下載每個 MP3
        race_downloaded = 0
        race_skipped = 0
        race_failed = 0
        
        for idx, record in enumerate(records, 1):
            relative_path = record.get('path')
            if not relative_path:
                continue
            
            # 構建完整 URL
            url = f"{BASE_URL}/{session_path}{relative_path}"
            
            racing_number = record.get('racing_number', 'unknown')
            utc_time = record.get('utc', record.get('timestamp', ''))
            
            # 生成檔案名
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            mp3_filename = f"{race_key}_radio_{racing_number}_{url_hash}.mp3"
            file_path = audio_dir / mp3_filename
            
            # 跳過已下載
            if file_path.exists():
                race_skipped += 1
                total_skipped += 1
                continue
            
            # 下載
            try:
                resp = session.get(url, timeout=30)
                
                if resp.status_code == 200:
                    with open(file_path, 'wb') as f:
                        f.write(resp.content)
                    
                    file_size = len(resp.content)
                    total_size += file_size
                    race_downloaded += 1
                    total_downloaded += 1
                    
                    if race_downloaded <= 3 or race_downloaded % 10 == 0:
                        print(f"    [{idx}/{len(records)}] ✅ 車手 {racing_number} ({file_size/1024:.1f} KB)")
                else:
                    race_failed += 1
                    total_failed += 1
                    if race_failed <= 3:
                        print(f"    [{idx}/{len(records)}] ❌ HTTP {resp.status_code}")
                
                # 避免請求過快
                time.sleep(0.2)
                
            except Exception as e:
                race_failed += 1
                total_failed += 1
        
        print(f"    📈 下載: {race_downloaded} / 跳過: {race_skipped} / 失敗: {race_failed}")
    
    # 總結
    print("\n" + "=" * 80)
    print(" 下載完成！")
    print("=" * 80 + "\n")
    
    print(f"📊 統計:")
    print(f"   • 成功下載: {total_downloaded} 個 MP3")
    print(f"   • 已跳過: {total_skipped} 個")
    print(f"   • 失敗: {total_failed} 個")
    print(f"   • 總大小: {total_size / (1024*1024):.2f} MB")
    print(f"\n📂 輸出目錄: {audio_dir}")


if __name__ == "__main__":
    download_all_mp3()
