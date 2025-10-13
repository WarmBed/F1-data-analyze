#!/usr/bin/env python3
"""
Race Event Detector - 賽事檢測模組

自動檢測當前處於何種更新模式：
- 平時維護模式 (Normal Maintenance)
- 賽後密集模式 (Post-Race Intensive)
- 賽前預熱模式 (Pre-Race Warm-Up)

Author: F1T Team
Date: 2025-10-13
Version: 1.0.0
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

# 添加專案根目錄到 Python 路徑
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class RaceEventDetector:
    """賽事檢測器 - 判斷當前更新模式"""
    
    # 模式常數
    MODE_NORMAL = "normal"           # 平時維護模式
    MODE_POST_RACE = "post_race"     # 賽後密集模式
    MODE_PRE_RACE = "pre_race"       # 賽前預熱模式
    
    # 時間窗口配置（小時）
    POST_RACE_WINDOW_HOURS = 48      # 賽後密集更新持續 48 小時
    PRE_RACE_WINDOW_HOURS = 72       # 賽前預熱提前 72 小時
    
    def __init__(self, json_dir: str = "json"):
        """
        初始化賽事檢測器
        
        Args:
            json_dir: JSON 檔案目錄
        """
        self.json_dir = Path(json_dir)
        self.calendar_data: Optional[Dict[str, Any]] = None
        self.current_time = datetime.now(timezone.utc)
    
    def load_calendar_data(self) -> bool:
        """
        載入賽季賽程數據
        
        Returns:
            是否成功載入
        """
        try:
            # 搜尋最新的賽程檔案
            pattern = "season_calendar_multi_year_*.json"
            calendar_files = sorted(
                self.json_dir.glob(pattern),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            if not calendar_files:
                print(f"[ERROR] 找不到賽程檔案: {pattern}")
                return False
            
            latest_file = calendar_files[0]
            print(f"[INFO] 載入賽程檔案: {latest_file.name}")
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                self.calendar_data = json.load(f)
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 載入賽程失敗: {e}")
            return False
    
    def get_all_races(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        獲取所有賽事列表
        
        Args:
            year: 指定年份（None = 當前年份）
            
        Returns:
            賽事列表
        """
        if not self.calendar_data:
            return []
        
        target_year = year or self.current_time.year
        data_node = self.calendar_data.get("data", {})
        
        # 支援兩種數據結構
        if str(target_year) in data_node:
            # 新格式: {"data": {"2025": [...]}}
            return data_node[str(target_year)]
        elif isinstance(data_node, list):
            # 舊格式: {"data": [...]}
            return [race for race in data_node if race.get("year") == target_year]
        else:
            return []
    
    def find_last_completed_race(self) -> Optional[Dict[str, Any]]:
        """
        找出最近完賽的比賽
        
        Returns:
            最近完賽的比賽資訊，或 None
        """
        races = self.get_all_races()
        if not races:
            return None
        
        completed_races = [
            race for race in races
            if race.get("is_completed", False)
        ]
        
        if not completed_races:
            return None
        
        # 按日期排序，取最近的
        completed_races.sort(
            key=lambda r: r.get("race_date_utc", ""),
            reverse=True
        )
        
        return completed_races[0]
    
    def find_next_upcoming_race(self) -> Optional[Dict[str, Any]]:
        """
        找出下一場未完賽的比賽
        
        Returns:
            下一場比賽資訊，或 None
        """
        races = self.get_all_races()
        if not races:
            return None
        
        upcoming_races = [
            race for race in races
            if not race.get("is_completed", False)
        ]
        
        if not upcoming_races:
            return None
        
        # 按日期排序，取最早的
        upcoming_races.sort(
            key=lambda r: r.get("race_date_utc", "")
        )
        
        return upcoming_races[0]
    
    def detect_mode(self) -> str:
        """
        檢測當前處於何種更新模式
        
        Returns:
            模式字串 (MODE_NORMAL, MODE_POST_RACE, MODE_PRE_RACE)
        """
        # 載入賽程數據
        if not self.calendar_data:
            if not self.load_calendar_data():
                return self.MODE_NORMAL
        
        # 檢查賽後模式
        last_race = self.find_last_completed_race()
        if last_race:
            race_end_time = self._parse_datetime(last_race.get("race_date_utc"))
            if race_end_time:
                # 正賽約 2 小時，加上緩衝時間
                actual_end_time = race_end_time + timedelta(hours=2)
                time_since_race = self.current_time - actual_end_time
                
                # 檢查是否在賽後 48 小時內
                if timedelta(0) <= time_since_race <= timedelta(hours=self.POST_RACE_WINDOW_HOURS):
                    return self.MODE_POST_RACE
        
        # 檢查賽前模式
        next_race = self.find_next_upcoming_race()
        if next_race:
            race_start_time = self._parse_datetime(next_race.get("race_date_utc"))
            if race_start_time:
                time_until_race = race_start_time - self.current_time
                
                # 檢查是否在賽前 72 小時內
                if timedelta(0) <= time_until_race <= timedelta(hours=self.PRE_RACE_WINDOW_HOURS):
                    return self.MODE_PRE_RACE
        
        # 預設為平時模式
        return self.MODE_NORMAL
    
    def get_mode_info(self) -> Dict[str, Any]:
        """
        獲取當前模式的詳細資訊
        
        Returns:
            包含模式和相關資訊的字典
        """
        mode = self.detect_mode()
        info = {
            "mode": mode,
            "mode_name": self._get_mode_name(mode),
            "current_time": self.current_time.isoformat(),
            "last_race": None,
            "next_race": None,
            "time_since_last_race": None,
            "time_until_next_race": None,
        }
        
        # 添加最近完賽比賽資訊
        last_race = self.find_last_completed_race()
        if last_race:
            race_end_time = self._parse_datetime(last_race.get("race_date_utc"))
            if race_end_time:
                actual_end_time = race_end_time + timedelta(hours=2)
                time_since = self.current_time - actual_end_time
                
                info["last_race"] = {
                    "event_name": last_race.get("event_name"),
                    "round": last_race.get("round"),
                    "race_date": last_race.get("race_date_utc"),
                    "country": last_race.get("country"),
                }
                info["time_since_last_race"] = {
                    "hours": time_since.total_seconds() / 3600,
                    "formatted": self._format_timedelta(time_since),
                }
        
        # 添加下一場比賽資訊
        next_race = self.find_next_upcoming_race()
        if next_race:
            race_start_time = self._parse_datetime(next_race.get("race_date_utc"))
            if race_start_time:
                time_until = race_start_time - self.current_time
                
                info["next_race"] = {
                    "event_name": next_race.get("event_name"),
                    "round": next_race.get("round"),
                    "race_date": next_race.get("race_date_utc"),
                    "country": next_race.get("country"),
                }
                info["time_until_next_race"] = {
                    "hours": time_until.total_seconds() / 3600,
                    "formatted": self._format_timedelta(time_until),
                }
        
        return info
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """解析 ISO 格式日期時間字串"""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except Exception:
            return None
    
    def _format_timedelta(self, td: timedelta) -> str:
        """格式化時間差為易讀字串"""
        total_hours = td.total_seconds() / 3600
        
        if total_hours < 0:
            return f"{abs(total_hours):.1f} 小時前"
        elif total_hours < 24:
            return f"{total_hours:.1f} 小時後"
        else:
            days = total_hours / 24
            return f"{days:.1f} 天後"
    
    def _get_mode_name(self, mode: str) -> str:
        """獲取模式的中文名稱"""
        mode_names = {
            self.MODE_NORMAL: "平時維護模式",
            self.MODE_POST_RACE: "賽後密集模式",
            self.MODE_PRE_RACE: "賽前預熱模式",
        }
        return mode_names.get(mode, "未知模式")


# 測試代碼
if __name__ == "__main__":
    print("=" * 60)
    print("賽事檢測器測試")
    print("=" * 60)
    
    detector = RaceEventDetector()
    
    # 測試載入賽程
    if detector.load_calendar_data():
        print("\n✅ 賽程數據載入成功")
    else:
        print("\n❌ 賽程數據載入失敗")
        sys.exit(1)
    
    # 獲取模式資訊
    mode_info = detector.get_mode_info()
    
    print(f"\n🎯 當前模式: {mode_info['mode_name']} ({mode_info['mode']})")
    print(f"📅 當前時間: {mode_info['current_time']}")
    
    # 顯示最近完賽比賽
    if mode_info.get("last_race"):
        last = mode_info["last_race"]
        time_since = mode_info["time_since_last_race"]
        print(f"\n🏁 最近完賽:")
        print(f"   第 {last['round']} 站 - {last['event_name']} ({last['country']})")
        print(f"   完賽時間: {last['race_date']}")
        print(f"   距今: {time_since['formatted']} ({time_since['hours']:.1f} 小時)")
    
    # 顯示下一場比賽
    if mode_info.get("next_race"):
        next_race = mode_info["next_race"]
        time_until = mode_info["time_until_next_race"]
        print(f"\n📍 下一場比賽:")
        print(f"   第 {next_race['round']} 站 - {next_race['event_name']} ({next_race['country']})")
        print(f"   比賽時間: {next_race['race_date']}")
        print(f"   倒數: {time_until['formatted']} ({time_until['hours']:.1f} 小時)")
    
    print("\n" + "=" * 60)
