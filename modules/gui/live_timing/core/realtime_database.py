"""
Realtime Database - 即時數據儲存
================================

使用 SQLite 儲存即時 F1 數據，支援：
- 連接時開始錄製
- 各模組讀取最新狀態
- 歷史數據查詢

Author: F1T Team
Date: 2025-12-07
"""

import sqlite3
import json
import os
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from core.logger import get_logger


logger = get_logger("live_timing.realtime_database", component="gui")


class RealtimeDatabase:
    """
    即時數據 SQLite 資料庫
    
    表結構:
    - drivers: 車手最新狀態
    - timing_history: 計時歷史
    - lap_count: 圈數資訊
    - session_info: 賽事資訊
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # 資料庫路徑
        self._db_dir = Path(__file__).parent.parent.parent.parent.parent / "data" / "live_timing_cache"
        self._db_dir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._db_dir / "realtime_session.db"
        
        self._conn: Optional[sqlite3.Connection] = None
        self._write_lock = threading.Lock()
        
        self._initialized = True
        logger.info("[REALTIME_DB] Database path: %s", self._db_path)
    
    def connect(self):
        """連接資料庫並初始化表"""
        if self._conn is not None:
            return
            
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()
        logger.info("[REALTIME_DB] Connected to database")
    
    def _create_tables(self):
        """創建資料表"""
        cursor = self._conn.cursor()
        
        # 車手最新狀態表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drivers (
                driver_num TEXT PRIMARY KEY,
                tla TEXT,
                full_name TEXT,
                team_name TEXT,
                team_colour TEXT,
                position INTEGER,
                gap_to_leader TEXT,
                gap_to_leader_value REAL,
                interval TEXT,
                last_lap_time TEXT,
                best_lap_time TEXT,
                sector_1 TEXT,
                sector_2 TEXT,
                sector_3 TEXT,
                compound TEXT,
                tyre_age INTEGER,
                tyre_new INTEGER,
                pit_count INTEGER,
                in_pit INTEGER,
                speed INTEGER,
                rpm INTEGER,
                gear INTEGER,
                throttle INTEGER,
                brake INTEGER,
                drs INTEGER,
                x REAL,
                y REAL,
                z REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 圈數資訊表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lap_count (
                id INTEGER PRIMARY KEY,
                current_lap INTEGER,
                total_laps INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 賽事資訊表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_info (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 計時歷史表 (用於追蹤變化)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timing_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_num TEXT,
                lap_number INTEGER,
                sector_1 TEXT,
                sector_2 TEXT,
                sector_3 TEXT,
                lap_time TEXT,
                compound TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 輪胎 stint 表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tyre_stints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_num TEXT,
                stint_number INTEGER,
                compound TEXT,
                start_lap INTEGER,
                total_laps INTEGER,
                is_new INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(driver_num, stint_number)
            )
        """)
        
        self._conn.commit()
        logger.info("[REALTIME_DB] Tables created/verified")
    
    def clear_session(self):
        """清除當前賽事數據（開始新連接時調用）"""
        with self._write_lock:
            if self._conn is None:
                self.connect()
            
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM drivers")
            cursor.execute("DELETE FROM lap_count")
            cursor.execute("DELETE FROM session_info")
            cursor.execute("DELETE FROM timing_history")
            cursor.execute("DELETE FROM tyre_stints")
            self._conn.commit()
            logger.info("[REALTIME_DB] Session cleared")
    
    # ========================================
    # 寫入方法 (由 realtime_source 調用)
    # ========================================
    
    def update_lap_count(self, current_lap: int, total_laps: int):
        """更新圈數"""
        with self._write_lock:
            if self._conn is None:
                self.connect()
            
            cursor = self._conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO lap_count (id, current_lap, total_laps, updated_at)
                VALUES (1, ?, ?, CURRENT_TIMESTAMP)
            """, (current_lap, total_laps))
            self._conn.commit()
    
    def update_session_info(self, key: str, value: Any):
        """更新賽事資訊"""
        with self._write_lock:
            if self._conn is None:
                self.connect()
            
            value_str = json.dumps(value) if not isinstance(value, str) else value
            cursor = self._conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO session_info (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value_str))
            self._conn.commit()
    
    def update_driver(self, driver_num: str, data: Dict[str, Any]):
        """更新車手數據"""
        with self._write_lock:
            if self._conn is None:
                self.connect()
            
            cursor = self._conn.cursor()
            
            # 解析 gap_to_leader
            gap_raw = data.get('gap_to_leader_raw', data.get('gap_to_leader', ''))
            gap_value = 0.0
            if gap_raw and isinstance(gap_raw, str):
                if gap_raw.startswith('+'):
                    try:
                        gap_value = float(gap_raw[1:])
                    except:
                        pass
            
            cursor.execute("""
                INSERT OR REPLACE INTO drivers (
                    driver_num, tla, full_name, team_name, team_colour,
                    position, gap_to_leader, gap_to_leader_value, interval,
                    last_lap_time, best_lap_time, sector_1, sector_2, sector_3,
                    compound, tyre_age, tyre_new, pit_count, in_pit,
                    speed, rpm, gear, throttle, brake, drs,
                    x, y, z, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                driver_num,
                data.get('tla', driver_num),
                data.get('full_name', ''),
                data.get('team_name', ''),
                data.get('team_colour', data.get('team_color', 'CCCCCC')),
                data.get('position', 0),
                gap_raw,
                gap_value,
                data.get('interval', ''),
                data.get('last_lap_time', ''),
                data.get('best_lap_time', ''),
                data.get('sector_1', ''),
                data.get('sector_2', ''),
                data.get('sector_3', ''),
                data.get('compound', 'UNKNOWN'),
                data.get('tyre_age', 0),
                1 if data.get('tyre_new', False) else 0,
                data.get('pit_count', 0),
                1 if data.get('in_pit', False) else 0,
                data.get('speed', 0),
                data.get('rpm', 0),
                data.get('gear', 0),
                data.get('throttle', 0),
                data.get('brake', 0),
                data.get('drs', 0),
                data.get('x', 0),
                data.get('y', 0),
                data.get('z', 0),
            ))
            self._conn.commit()
    
    def update_tyre_stint(self, driver_num: str, stint_number: int, 
                          compound: str, start_lap: int, total_laps: int, is_new: bool):
        """更新輪胎 stint"""
        with self._write_lock:
            if self._conn is None:
                self.connect()
            
            cursor = self._conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO tyre_stints 
                (driver_num, stint_number, compound, start_lap, total_laps, is_new, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (driver_num, stint_number, compound, start_lap, total_laps, 1 if is_new else 0))
            self._conn.commit()
    
    def batch_update_drivers(self, drivers_data: Dict[str, Dict[str, Any]]):
        """批量更新車手數據"""
        with self._write_lock:
            if self._conn is None:
                self.connect()
            
            cursor = self._conn.cursor()
            
            for driver_num, data in drivers_data.items():
                gap_raw = data.get('gap_to_leader_raw', data.get('gap_to_leader', ''))
                gap_value = 0.0
                if gap_raw and isinstance(gap_raw, str):
                    if gap_raw.startswith('+'):
                        try:
                            gap_value = float(gap_raw[1:])
                        except:
                            pass
                
                cursor.execute("""
                    INSERT OR REPLACE INTO drivers (
                        driver_num, tla, full_name, team_name, team_colour,
                        position, gap_to_leader, gap_to_leader_value, interval,
                        last_lap_time, best_lap_time, sector_1, sector_2, sector_3,
                        compound, tyre_age, tyre_new, pit_count, in_pit,
                        speed, rpm, gear, throttle, brake, drs,
                        x, y, z, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    driver_num,
                    data.get('tla', driver_num),
                    data.get('full_name', ''),
                    data.get('team_name', ''),
                    data.get('team_colour', data.get('team_color', 'CCCCCC')),
                    data.get('position', 0),
                    gap_raw,
                    gap_value,
                    data.get('interval', ''),
                    data.get('last_lap_time', ''),
                    data.get('best_lap_time', ''),
                    data.get('sector_1', ''),
                    data.get('sector_2', ''),
                    data.get('sector_3', ''),
                    data.get('compound', 'UNKNOWN'),
                    data.get('tyre_age', 0),
                    1 if data.get('tyre_new', False) else 0,
                    data.get('pit_count', 0),
                    1 if data.get('in_pit', False) else 0,
                    data.get('speed', 0),
                    data.get('rpm', 0),
                    data.get('gear', 0),
                    data.get('throttle', 0),
                    data.get('brake', 0),
                    data.get('drs', 0),
                    data.get('x', 0),
                    data.get('y', 0),
                    data.get('z', 0),
                ))
            
            self._conn.commit()
    
    # ========================================
    # 讀取方法 (由 GUI 模組調用)
    # ========================================
    
    def get_lap_count(self) -> Dict[str, int]:
        """獲取圈數"""
        if self._conn is None:
            self.connect()
        
        cursor = self._conn.cursor()
        cursor.execute("SELECT current_lap, total_laps FROM lap_count WHERE id = 1")
        row = cursor.fetchone()
        
        if row:
            return {"current_lap": row["current_lap"], "total_laps": row["total_laps"]}
        return {"current_lap": 0, "total_laps": 0}
    
    def get_all_drivers(self) -> Dict[str, Dict[str, Any]]:
        """獲取所有車手數據"""
        if self._conn is None:
            self.connect()
        
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM drivers ORDER BY position")
        
        drivers = {}
        for row in cursor.fetchall():
            driver_num = row["driver_num"]
            drivers[driver_num] = {
                "driver_num": driver_num,
                "tla": row["tla"],
                "driver_tla": row["tla"],
                "full_name": row["full_name"],
                "team_name": row["team_name"],
                "team_colour": row["team_colour"],
                "team_color": row["team_colour"],
                "position": row["position"],
                "gap_to_leader": row["gap_to_leader_value"],
                "gap_to_leader_raw": row["gap_to_leader"],
                "interval": row["interval"],
                "last_lap_time": row["last_lap_time"],
                "best_lap_time": row["best_lap_time"],
                "sector_1": row["sector_1"],
                "sector_2": row["sector_2"],
                "sector_3": row["sector_3"],
                "compound": row["compound"],
                "tyre_age": row["tyre_age"],
                "tyre_new": bool(row["tyre_new"]),
                "pit_count": row["pit_count"],
                "in_pit": bool(row["in_pit"]),
                "speed": row["speed"],
                "rpm": row["rpm"],
                "gear": row["gear"],
                "throttle": row["throttle"],
                "brake": row["brake"],
                "drs": row["drs"],
                "x": row["x"],
                "y": row["y"],
                "z": row["z"],
            }
        
        return drivers
    
    def get_driver(self, driver_num: str) -> Optional[Dict[str, Any]]:
        """獲取單個車手數據"""
        if self._conn is None:
            self.connect()
        
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM drivers WHERE driver_num = ?", (driver_num,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
    
    def get_tyre_stints(self, driver_num: str) -> List[Dict[str, Any]]:
        """獲取車手的輪胎 stint 歷史"""
        if self._conn is None:
            self.connect()
        
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT * FROM tyre_stints 
            WHERE driver_num = ? 
            ORDER BY stint_number
        """, (driver_num,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_session_info(self, key: str) -> Optional[str]:
        """獲取賽事資訊"""
        if self._conn is None:
            self.connect()
        
        cursor = self._conn.cursor()
        cursor.execute("SELECT value FROM session_info WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        if row:
            return row["value"]
        return None
    
    def get_snapshot(self) -> Dict[str, Any]:
        """獲取完整快照 (兼容 DataManager 格式)"""
        lap_count = self.get_lap_count()
        drivers = self.get_all_drivers()
        
        return {
            "current_lap": lap_count.get("current_lap", 0),
            "total_laps": lap_count.get("total_laps", 0),
            "drivers": drivers,
            "track_status": self.get_session_info("track_status") or "1",
            "race_time": "",
            "race_time_seconds": 0.0,
        }
    
    def close(self):
        """關閉資料庫連接"""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("[REALTIME_DB] Connection closed")


# 單例訪問
def get_realtime_db() -> RealtimeDatabase:
    """獲取 RealtimeDatabase 單例"""
    return RealtimeDatabase()
