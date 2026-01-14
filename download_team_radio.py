"""
Team Radio Downloader & Transcriber
====================================

獨立模組：下載 F1 團隊語音並轉錄為文字

功能：
1. 從 F1 官方 API 下載 TeamRadio 數據（包含 .mp3 URL）
2. 下載所有語音檔案到本地
3. 使用語音識別將 .mp3 轉錄為文字
4. 輸出結構化的文字記錄

需求套件：
- requests (HTTP 下載)
- SpeechRecognition (語音轉文字)
- pydub (音檔處理)
- ffmpeg 或 ffprobe (音檔解碼，需系統安裝)

安裝指令：
    pip install requests SpeechRecognition pydub
    # Windows: 下載 ffmpeg.exe 並添加到 PATH

Author: F1T Team
Date: 2026-01-12
"""

import os
import sys
import json
import time
import hashlib
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse

# 添加專案路徑以導入現有模組
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 強制 UTF-8 輸出
import io
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 檢查可選依賴
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    print("⚠️  SpeechRecognition 未安裝，將跳過語音轉文字功能")
    print("   安裝指令: pip install SpeechRecognition pydub")

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("⚠️  pydub 未安裝，語音轉換功能可能受限")


class TeamRadioDownloader:
    """
    團隊語音下載器
    
    從 F1 官方 API 下載 TeamRadio 數據並提取語音檔案 URL
    """
    
    BASE_URL = "https://livetiming.formula1.com/static"
    
    def __init__(self, output_dir: str = "team_radio_data"):
        """
        初始化下載器
        
        Args:
            output_dir: 輸出目錄（音檔和文字記錄）
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.audio_dir = self.output_dir / "audio"
        self.audio_dir.mkdir(exist_ok=True)
        
        self.transcript_dir = self.output_dir / "transcripts"
        self.transcript_dir.mkdir(exist_ok=True)
        
        # HTTP 會話
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.timeout = 60
        
    def download_race_data(self, year: int, race: str, session: str = "R") -> Optional[str]:
        """
        下載賽事的 TeamRadio 數據流
        
        Args:
            year: 年份 (例: 2025)
            race: 賽事名稱 (例: "Abu Dhabi")
            session: 會話類型 (R/Q/FP1/FP2/FP3)
            
        Returns:
            TeamRadio.jsonStream 的本地檔案路徑，失敗返回 None
        """
        print(f"\n{'='*70}")
        print(f"下載 {year} {race} {session} 的 TeamRadio 數據")
        print(f"{'='*70}\n")
        
        # 1. 獲取會話路徑
        session_path = self._find_session_path(year, race, session)
        if not session_path:
            print(f"❌ 找不到賽事路徑: {year} {race} {session}")
            return None
        
        print(f"✅ 會話路徑: {session_path}")
        
        # 2. 下載 TeamRadio.jsonStream
        url = f"{self.BASE_URL}/{session_path}TeamRadio.jsonStream"
        print(f"📥 下載 URL: {url}")
        
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code != 200:
                print(f"❌ HTTP {resp.status_code}: 無法下載 TeamRadio 數據")
                return None
            
            # 保存原始 jsonStream
            filename = f"TeamRadio_{year}_{race.replace(' ', '_')}_{session}.jsonStream"
            file_path = self.output_dir / filename
            
            with open(file_path, 'wb') as f:
                f.write(resp.content)
            
            print(f"✅ 已保存: {file_path}")
            print(f"   檔案大小: {len(resp.content) / 1024:.2f} KB")
            
            return str(file_path)
            
        except Exception as e:
            print(f"❌ 下載失敗: {e}")
            return None
    
    def parse_team_radio_stream(self, stream_file: str) -> List[Dict[str, Any]]:
        """
        解析 TeamRadio.jsonStream 檔案
        
        Args:
            stream_file: jsonStream 檔案路徑
            
        Returns:
            TeamRadio 記錄列表，每筆包含 timestamp 和語音 URL
        """
        print(f"\n{'='*70}")
        print(f"解析 TeamRadio 數據流")
        print(f"{'='*70}\n")
        
        records = []
        
        try:
            with open(stream_file, 'r', encoding='utf-8-sig') as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            print(f"📊 總行數: {len(lines)}")
            
            for line_num, line in enumerate(lines, 1):
                if len(line) <= 12:
                    continue
                
                # jsonStream 格式: 前 12 字元是時間戳，後面是 JSON
                timestamp = line[:12]
                payload_text = line[12:]
                
                try:
                    data = json.loads(payload_text)
                    
                    # TeamRadio 數據結構:
                    # {"Captures": [{"Utc": "...", "RacingNumber": "63", "Path": "..."}]}
                    # 或 {"Captures": {"1": {"Utc": "...", "RacingNumber": "5", "Path": "..."}}}
                    
                    if isinstance(data, dict) and 'Captures' in data:
                        captures = data['Captures']
                        
                        # 情況 1: Captures 是列表
                        if isinstance(captures, list):
                            for capture in captures:
                                if isinstance(capture, dict) and 'Path' in capture:
                                    records.append({
                                        'timestamp': timestamp,
                                        'racing_number': capture.get('RacingNumber', '?'),
                                        'path': capture.get('Path'),
                                        'utc': capture.get('Utc', timestamp),
                                        'raw_data': capture
                                    })
                        
                        # 情況 2: Captures 是字典（索引 -> 數據）
                        elif isinstance(captures, dict):
                            for key, capture in captures.items():
                                if isinstance(capture, dict) and 'Path' in capture:
                                    records.append({
                                        'timestamp': timestamp,
                                        'racing_number': capture.get('RacingNumber', '?'),
                                        'path': capture.get('Path'),
                                        'utc': capture.get('Utc', timestamp),
                                        'raw_data': capture
                                    })
                    
                except json.JSONDecodeError:
                    continue
            
            print(f"✅ 解析完成: 找到 {len(records)} 筆 TeamRadio 記錄")
            
            # 保存解析結果為 JSON
            if records:
                output_file = stream_file.replace('.jsonStream', '_parsed.json')
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(records, f, indent=2, ensure_ascii=False)
                print(f"✅ 已保存解析結果: {output_file}")
            
            return records
            
        except Exception as e:
            print(f"❌ 解析失敗: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def download_audio_files(self, records: List[Dict[str, Any]], session_path: str = None) -> List[Tuple[str, str]]:
        """
        下載所有語音檔案
        
        Args:
            records: TeamRadio 記錄列表
            session_path: 會話路徑 (例如 "2025/2025-12-07_Abu_Dhabi_Grand_Prix/2025-12-07_Race/")
            
        Returns:
            (本地檔案路徑, 車手號碼) 的列表
        """
        print(f"\n{'='*70}")
        print(f"下載語音檔案")
        print(f"{'='*70}\n")
        
        if session_path:
            print(f"📂 會話路徑: {session_path}")
        
        downloaded = []
        
        for idx, record in enumerate(records, 1):
            relative_path = record.get('path')
            if not relative_path:
                continue
            
            # 構建完整 URL
            # 正確格式: https://livetiming.formula1.com/static/{session_path}TeamRadio/{filename}.mp3
            if session_path:
                # 使用會話路徑構建完整 URL
                # relative_path 格式: "TeamRadio/GEORUS01_63_20251207_162402.mp3"
                url = f"{self.BASE_URL}/{session_path}{relative_path}"
            else:
                # 降級使用舊格式（可能失敗）
                url = f"{self.BASE_URL}/{relative_path}"
            
            racing_number = record.get('racing_number', 'unknown')
            utc_time = record.get('utc', record.get('timestamp', ''))
            
            # 生成檔案名（使用 MD5 避免重複）
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"radio_{racing_number}_{utc_time.replace(':', '-')}_{url_hash}.mp3"
            file_path = self.audio_dir / filename
            
            # 跳過已下載
            if file_path.exists():
                print(f"[{idx}/{len(records)}] ⏭️  已存在: {filename}")
                downloaded.append((str(file_path), racing_number))
                continue
            
            # 下載音檔
            try:
                print(f"[{idx}/{len(records)}] 📥 下載: 車手 {racing_number}")
                resp = self.session.get(url, timeout=30)
                
                if resp.status_code == 200:
                    with open(file_path, 'wb') as f:
                        f.write(resp.content)
                    
                    file_size = len(resp.content) / 1024
                    print(f"             ✅ 已保存: {filename} ({file_size:.2f} KB)")
                    downloaded.append((str(file_path), racing_number))
                else:
                    print(f"             ❌ HTTP {resp.status_code}")
                
                # 避免請求過快
                time.sleep(0.3)
                
            except Exception as e:
                print(f"             ❌ 下載失敗: {e}")
        
        print(f"\n✅ 下載完成: {len(downloaded)}/{len(records)} 個音檔")
        return downloaded
    
    def _find_session_path(self, year: int, race: str, session: str) -> Optional[str]:
        """
        查找會話的 API 路徑（複製自 f1_api_downloader.py）
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 會話類型
            
        Returns:
            會話路徑（例如 "2025/2025-12-07_Abu_Dhabi_Grand_Prix/2025-12-07_Race/"）
        """
        # 獲取年度索引
        index_url = f"{self.BASE_URL}/{year}/Index.json"
        try:
            resp = self.session.get(index_url, timeout=self.timeout)
            if resp.status_code != 200:
                return None
            
            index_data = json.loads(resp.content.decode('utf-8-sig'))
            meetings = index_data.get("Meetings", [])
            
        except Exception as e:
            print(f"❌ 獲取索引失敗: {e}")
            return None
        
        # 查找匹配的賽事
        race_lower = race.lower().replace("_", " ")
        target_meeting = None
        
        for meeting in meetings:
            name = meeting.get("Name", "").lower()
            key = str(meeting.get("Key", "")).lower()
            
            if race_lower in name or race_lower in key:
                target_meeting = meeting
                break
        
        if not target_meeting:
            return None
        
        # 查找匹配的會話
        available_sessions = target_meeting.get("Sessions", [])
        session_upper = session.upper()
        
        for sess in available_sessions:
            sess_name = sess.get("Name", "").upper()
            sess_path = sess.get("Path")
            
            if not sess_path:
                continue
            
            # 匹配邏輯
            if session_upper == "R" and "RACE" in sess_name and "SPRINT" not in sess_name:
                return sess_path
            elif session_upper == "Q" and "QUALIFYING" in sess_name and "SPRINT" not in sess_name:
                return sess_path
        
        return None


class TeamRadioTranscriber:
    """
    團隊語音轉錄器
    
    使用語音識別將 .mp3 轉錄為文字
    """
    
    def __init__(self):
        """初始化轉錄器"""
        if not SPEECH_RECOGNITION_AVAILABLE:
            print("⚠️  語音識別功能不可用")
            self.recognizer = None
            return
        
        self.recognizer = sr.Recognizer()
        
        # 調整識別參數
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        
    def transcribe_audio_file(self, audio_path: str) -> Optional[str]:
        """
        轉錄單個音檔
        
        Args:
            audio_path: 音檔路徑
            
        Returns:
            轉錄的文字，失敗返回 None
        """
        if not self.recognizer:
            return None
        
        try:
            # 使用 pydub 轉換為 WAV（SpeechRecognition 需要）
            if PYDUB_AVAILABLE:
                audio = AudioSegment.from_mp3(audio_path)
                wav_path = audio_path.replace('.mp3', '.wav')
                audio.export(wav_path, format="wav")
                source_file = wav_path
            else:
                source_file = audio_path
            
            # 語音識別
            with sr.AudioFile(source_file) as source:
                audio_data = self.recognizer.record(source)
            
            # 使用 Google Web Speech API（免費但有限制）
            text = self.recognizer.recognize_google(audio_data, language='en-US')
            
            # 清理臨時 WAV
            if PYDUB_AVAILABLE and Path(wav_path).exists():
                Path(wav_path).unlink()
            
            return text
            
        except sr.UnknownValueError:
            return "[無法識別語音]"
        except sr.RequestError as e:
            return f"[API 錯誤: {e}]"
        except Exception as e:
            return f"[轉錄失敗: {e}]"
    
    def transcribe_batch(
        self, 
        audio_files: List[Tuple[str, str]], 
        output_file: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        批次轉錄音檔
        
        Args:
            audio_files: (音檔路徑, 車手號碼) 的列表
            output_file: 輸出 JSON 檔案路徑
            
        Returns:
            轉錄結果列表
        """
        if not self.recognizer:
            print("❌ 語音識別不可用，跳過轉錄")
            return []
        
        print(f"\n{'='*70}")
        print(f"語音轉文字")
        print(f"{'='*70}\n")
        
        results = []
        
        for idx, (audio_path, racing_number) in enumerate(audio_files, 1):
            filename = Path(audio_path).name
            print(f"[{idx}/{len(audio_files)}] 🎤 轉錄: {filename}")
            
            start_time = time.time()
            text = self.transcribe_audio_file(audio_path)
            elapsed = time.time() - start_time
            
            result = {
                'audio_file': filename,
                'racing_number': racing_number,
                'transcript': text,
                'transcription_time': f"{elapsed:.2f}s"
            }
            
            results.append(result)
            
            if text:
                print(f"             ✅ \"{text}\" ({elapsed:.2f}s)")
            else:
                print(f"             ⚠️  無法轉錄")
            
            # 避免 API 限制
            time.sleep(1)
        
        # 保存結果
        if output_file and results:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n✅ 轉錄結果已保存: {output_file}")
        
        return results


def main():
    """主程式"""
    print("\n" + "="*70)
    print(" F1 Team Radio Downloader & Transcriber")
    print(" 團隊語音下載與轉錄工具")
    print("="*70 + "\n")
    
    # 測試參數
    year = 2025
    race = "Abu Dhabi"
    session = "R"
    
    # 1. 下載器
    downloader = TeamRadioDownloader(output_dir="team_radio_data")
    
    # 2. 下載 TeamRadio 數據流
    stream_file = downloader.download_race_data(year, race, session)
    if not stream_file:
        print("\n❌ 無法下載 TeamRadio 數據")
        return
    
    # 3. 解析數據流
    records = downloader.parse_team_radio_stream(stream_file)
    if not records:
        print("\n⚠️  未找到 TeamRadio 記錄")
        return
    
    print(f"\n📊 TeamRadio 統計:")
    print(f"   總記錄數: {len(records)}")
    
    # 統計車手
    drivers = {}
    for record in records:
        num = record.get('racing_number', '?')
        drivers[num] = drivers.get(num, 0) + 1
    
    print(f"   車手數量: {len(drivers)}")
    for num, count in sorted(drivers.items(), key=lambda x: x[1], reverse=True):
        print(f"      車手 {num}: {count} 次")
    
    # 4. 下載語音檔案
    audio_files = downloader.download_audio_files(records)
    
    if not audio_files:
        print("\n⚠️  未下載任何音檔")
        return
    
    # 5. 語音轉文字（可選）
    if SPEECH_RECOGNITION_AVAILABLE:
        transcriber = TeamRadioTranscriber()
        
        output_json = downloader.transcript_dir / f"transcripts_{year}_{race.replace(' ', '_')}_{session}.json"
        results = transcriber.transcribe_batch(audio_files, str(output_json))
        
        print(f"\n{'='*70}")
        print(f"轉錄摘要")
        print(f"{'='*70}\n")
        
        for result in results[:5]:  # 只顯示前 5 筆
            print(f"車手 {result['racing_number']}: {result['transcript']}")
    else:
        print("\n⚠️  跳過語音轉文字（需安裝 SpeechRecognition 和 pydub）")
        print("   安裝指令: pip install SpeechRecognition pydub")
    
    print(f"\n{'='*70}")
    print(" 完成！")
    print(f"{'='*70}\n")
    print(f"輸出目錄: {downloader.output_dir}")
    print(f"   音檔: {downloader.audio_dir}")
    print(f"   文字記錄: {downloader.transcript_dir}")


if __name__ == "__main__":
    main()
