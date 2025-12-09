"""
Realtime Live F1 Data Source
=============================

通過 SignalR WebSocket 連接 F1 官方 Live Timing 服務，
提供即時數據給 Live Timing GUI 模組。

使用 SQLite 資料庫儲存即時數據，支援其他模組讀取。

Author: F1T Team
Date: 2025-12-05
Updated: 2025-12-07 - 加入資料庫儲存功能
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import time

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer

from .signalr_client import RealTimeLiveF1Worker, WEBSOCKETS_AVAILABLE
from .realtime_database import get_realtime_db, RealtimeDatabase


class RealTimeLiveF1DataSource(QObject):
    """
    即時 Live F1 數據源
    
    通過 SignalR WebSocket 連接 F1 官方 Live Timing 服務，
    並將數據轉換為 DataManager 可用的快照格式。
    
    信號:
        snapshot_updated: 當數據更新時發出，包含完整快照
        connection_changed: 連接狀態變更
        error_occurred: 錯誤發生
    """
    
    # 信號
    snapshot_updated = pyqtSignal(dict)  # 快照數據
    connection_changed = pyqtSignal(str)  # 連接狀態
    error_occurred = pyqtSignal(str)  # 錯誤訊息
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 數據存儲 (保存最新狀態)
        self._position_data: Dict[str, Any] = {}  # driver_num -> position data
        self._timing_data: Dict[str, Any] = {}    # driver_num -> timing data
        self._car_data: Dict[str, Any] = {}       # driver_num -> car data
        self._tyre_data: Dict[str, Any] = {}      # driver_num -> tyre data
        self._weather_data: Dict[str, Any] = {}
        self._track_status: str = "1"  # 1=綠旗
        self._race_control_messages: List[Dict] = []
        self._lap_count: Dict[str, Any] = {"CurrentLap": 0, "TotalLaps": 0}
        self._driver_list: Dict[str, Dict] = {}
        self._session_info: Dict[str, Any] = {}
        
        # 時間追蹤
        self._session_start_time: Optional[datetime] = None
        self._last_update_time: Optional[datetime] = None
        
        # 調試計數器
        self._data_receive_count = 0
        self._snapshot_emit_count = 0
        
        # 節流控制 (100ms)
        self._throttle_interval_ms = 100  # 最小更新間隔 (毫秒)
        self._last_emit_time = 0.0  # 上次發送時間 (秒)
        self._pending_snapshot = False  # 是否有待發送的快照
        self._throttle_timer = QTimer(self)
        self._throttle_timer.setSingleShot(True)
        self._throttle_timer.timeout.connect(self._emit_pending_snapshot)
        
        # Worker 執行緒
        self._worker: Optional[RealTimeLiveF1Worker] = None
        self._is_connected = False
        
        # 資料庫
        self._db: RealtimeDatabase = get_realtime_db()
        
    def start_connection(self) -> bool:
        """
        開始即時連接
        
        Returns:
            True 如果成功啟動，False 如果已在運行或 websockets 不可用
        """
        if not WEBSOCKETS_AVAILABLE:
            self.error_occurred.emit("websockets package not installed. Run: pip install websockets")
            return False
        
        if self._worker is not None and self._worker.isRunning():
            print("[REALTIME_SOURCE] Connection already running")
            return False
        
        print("[REALTIME_SOURCE] Starting realtime connection...")
        
        # 清除舊數據並初始化資料庫
        self._db.connect()
        self._db.clear_session()
        print("[REALTIME_SOURCE] Database initialized and cleared")
        
        self._worker = RealTimeLiveF1Worker(parent=self)
        self._worker.data_received.connect(self._on_data_received)
        self._worker.connection_status.connect(self._on_connection_status)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()
        
        return True
        
    def stop_connection(self):
        """停止即時連接"""
        if self._worker is not None:
            print("[REALTIME_SOURCE] Stopping realtime connection...")
            self._worker.stop()
            self._worker = None
        self._is_connected = False
        self.connection_changed.emit("Disconnected")
        
    def is_connected(self) -> bool:
        """檢查是否已連接"""
        return self._is_connected
    
    def get_current_snapshot(self) -> Dict[str, Any]:
        """
        獲取當前快照數據
        
        Returns:
            與 DataManager 兼容的快照格式
        """
        return self._build_snapshot()
    
    def get_driver_info(self) -> Dict[str, Dict]:
        """獲取車手資訊"""
        return self._driver_list.copy()
    
    def get_session_info(self) -> Dict[str, Any]:
        """獲取賽事資訊"""
        return self._session_info.copy()
    
    def get_weather_data(self) -> Dict[str, Any]:
        """獲取天氣數據"""
        return self._weather_data.copy()
    
    def get_track_status(self) -> str:
        """獲取賽道狀態"""
        return self._track_status
    
    def get_lap_count(self) -> Dict[str, Any]:
        """獲取圈數資訊"""
        return self._lap_count.copy()
    
    def get_race_control_messages(self) -> List[Dict]:
        """獲取賽事控制訊息"""
        return self._race_control_messages.copy()
    
    # =========================================================================
    # 內部方法
    # =========================================================================
    
    def _parse_gap_value(self, gap_str: str) -> float:
        """
        解析 GapToLeader 字串為浮點數秒數
        
        格式範例:
        - "+4.377" → 4.377
        - "4.377" → 4.377
        - "LAP" → 0.0 (落後圈數，非秒數)
        - "" → 0.0
        """
        if not gap_str or not isinstance(gap_str, str):
            return 0.0
        
        gap_str = gap_str.strip()
        
        # 檢查是否為落後圈數格式
        if "LAP" in gap_str.upper():
            return 0.0  # 落後圈數時返回 0，使用 _parse_gap_laps 獲取圈數
        
        try:
            # 移除開頭的 + 號
            if gap_str.startswith("+"):
                gap_str = gap_str[1:]
            return float(gap_str)
        except (ValueError, TypeError):
            return 0.0
    
    def _parse_gap_laps(self, gap_str: str) -> int:
        """
        解析 GapToLeader 字串為落後圈數
        
        格式範例:
        - "LAP" → 1 (落後 1 圈)
        - "2 LAP" 或 "2 LAPS" → 2
        - "+4.377" → 0 (非落後圈數)
        """
        if not gap_str or not isinstance(gap_str, str):
            return 0
        
        gap_str = gap_str.strip().upper()
        
        # 檢查是否包含 LAP
        if "LAP" not in gap_str:
            return 0
        
        # 嘗試提取數字
        import re
        match = re.search(r'(\d+)\s*LAP', gap_str)
        if match:
            return int(match.group(1))
        
        # 單純 "LAP" 表示落後 1 圈
        if gap_str == "LAP":
            return 1
        
        return 1  # 預設落後 1 圈
    
    def _extract_nested_value(self, data: dict, key: str, sub_key: str, default: Any = "") -> Any:
        """
        從巢狀結構提取值
        
        例如：
        - data = {"LastLapTime": {"Value": "1:23.456"}}
        - key = "LastLapTime", sub_key = "Value"
        - 返回 "1:23.456"
        """
        value = data.get(key, default)
        
        if isinstance(value, dict):
            return value.get(sub_key, default)
        
        # 如果不是 dict，直接返回
        return value if value is not None else default
    
    def _extract_sector_value(self, timing_info: dict, sector_index: int) -> str:
        """
        提取 sector 時間
        
        Sectors 格式可能是:
        - {"Sectors": [{"Value": "28.123"}, {"Value": "32.456"}, ...]}
        - {"Sectors": {"0": {"Value": "28.123"}, "1": {"Value": "32.456"}, ...}}
        """
        sectors = timing_info.get("Sectors")
        if not sectors:
            return ""
        
        sector_data = None
        
        if isinstance(sectors, list):
            if 0 <= sector_index < len(sectors):
                sector_data = sectors[sector_index]
        elif isinstance(sectors, dict):
            sector_data = sectors.get(str(sector_index))
        
        if sector_data is None:
            return ""
        
        if isinstance(sector_data, dict):
            return sector_data.get("Value", "")
        
        return str(sector_data) if sector_data else ""

    @pyqtSlot(str, object)
    def _on_data_received(self, topic: str, data_list):
        """處理接收到的數據"""
        self._last_update_time = datetime.now()
        
        # 調試：記錄收到的 topic
        if not hasattr(self, '_topic_counts'):
            self._topic_counts = {}
        self._topic_counts[topic] = self._topic_counts.get(topic, 0) + 1
        
        # 每 100 次輸出一次統計
        total_count = sum(self._topic_counts.values())
        if total_count % 100 == 1:
            print(f"[REALTIME_SOURCE] Topic stats: {self._topic_counts}")
        
        if not isinstance(data_list, list):
            data_list = [data_list]
        
        # 根據 topic 處理不同數據
        for record in data_list:
            if not isinstance(record, dict):
                continue
                
            if topic == "Position.z" or topic == "Position":
                self._process_position_record(record)
            elif topic == "CarData.z" or topic == "CarData":
                self._process_car_data_record(record)
            elif topic == "TimingData":
                self._process_timing_data_record(record)
            elif topic == "WeatherData":
                self._weather_data.update(record)
            elif topic == "TrackStatus":
                status = record.get("Status")
                if status:
                    self._track_status = str(status)
            elif topic == "RaceControlMessages":
                self._race_control_messages.append(record)
                # 限制訊息數量
                if len(self._race_control_messages) > 100:
                    self._race_control_messages = self._race_control_messages[-100:]
            elif topic == "LapCount":
                self._lap_count.update(record)
            elif topic == "DriverList":
                self._process_driver_list_record(record)
            elif topic == "SessionInfo":
                self._session_info.update(record)
                # 記錄賽事開始時間
                if "StartDate" in record and self._session_start_time is None:
                    try:
                        self._session_start_time = datetime.fromisoformat(
                            record["StartDate"].replace("Z", "+00:00")
                        )
                    except:
                        pass
            elif topic == "CurrentTyres":
                self._process_tyre_record(record)
            elif topic == "TyreStintSeries":
                self._process_tyre_stint_record(record)
        
        # 節流發送快照 (100ms)
        self._data_receive_count += 1
        self._schedule_snapshot_emit()
    
    def _schedule_snapshot_emit(self):
        """
        直接發送快照 (暫時取消節流以調試)
        """
        self._emit_snapshot_now()
    
    def _emit_pending_snapshot(self):
        """計時器觸發：發送待處理的快照"""
        if self._pending_snapshot:
            self._emit_snapshot_now()
    
    def _emit_snapshot_now(self):
        """立即發送快照並寫入資料庫"""
        self._pending_snapshot = False
        self._last_emit_time = time.time()
        
        snapshot = self._build_snapshot()
        self._snapshot_emit_count += 1
        
        # 寫入資料庫
        try:
            # 更新圈數
            self._db.update_lap_count(
                snapshot.get("current_lap", 0),
                snapshot.get("total_laps", 0)
            )
            
            # 批量更新車手數據
            if snapshot.get("drivers"):
                self._db.batch_update_drivers(snapshot["drivers"])
        except Exception as e:
            print(f"[REALTIME_SOURCE] Database write error: {e}")
        
        # 詳細調試輸出（每 50 次輸出一次）
        if self._snapshot_emit_count % 50 == 1:
            driver_count = len(snapshot.get('drivers', {}))
            lap_info = f"Lap {snapshot.get('current_lap', 0)}/{snapshot.get('total_laps', 0)}"
            print(f"[REALTIME_SOURCE] Emit #{self._snapshot_emit_count}: {driver_count} drivers | {lap_info}")
            
            # 輸出一個範例車手的數據
            drivers = snapshot.get('drivers', {})
            if drivers:
                sample_num = next(iter(drivers.keys()))
                sample = drivers[sample_num]
                print(f"[REALTIME_SOURCE] Sample driver {sample_num}: pos={sample.get('position')}, "
                      f"tla={sample.get('tla')}, gap={sample.get('gap_to_leader_raw')}, "
                      f"last_lap={sample.get('last_lap_time')}, compound={sample.get('compound')}, "
                      f"s1={sample.get('sector_1')}, s2={sample.get('sector_2')}, s3={sample.get('sector_3')}")
        
        self.snapshot_updated.emit(snapshot)
    
    @pyqtSlot(str)
    def _on_connection_status(self, status: str):
        """處理連接狀態變更"""
        print(f"[REALTIME_SOURCE] Connection status: {status}")
        
        if "connected" in status.lower() or "established" in status.lower():
            self._is_connected = True
        elif "closed" in status.lower() or "failed" in status.lower():
            self._is_connected = False
        
        self.connection_changed.emit(status)
    
    @pyqtSlot(str)
    def _on_error(self, error: str):
        """處理錯誤"""
        print(f"[REALTIME_SOURCE] Error: {error}")
        self.error_occurred.emit(error)
    
    def _process_position_record(self, record: dict):
        """處理單筆位置數據"""
        driver_num = str(record.get("DriverNo", ""))
        if not driver_num:
            return
        
        if driver_num not in self._position_data:
            self._position_data[driver_num] = {}
        
        x_val = record.get("X", 0)
        y_val = record.get("Y", 0)
        z_val = record.get("Z", 0)
        
        # 調試：記錄第一筆位置數據
        if not hasattr(self, '_position_debug_count'):
            self._position_debug_count = 0
        self._position_debug_count += 1
        if self._position_debug_count <= 3:
            print(f"[REALTIME_SOURCE] Position record: driver={driver_num}, X={x_val}, Y={y_val}, Z={z_val}")
        
        self._position_data[driver_num].update({
            "X": x_val,
            "Y": y_val,
            "Z": z_val,
            "Status": record.get("Status", "OnTrack"),
            "timestamp": record.get("timestamp", "")
        })
    
    def _process_car_data_record(self, record: dict):
        """處理單筆車輛遙測數據"""
        driver_num = str(record.get("DriverNo", ""))
        if not driver_num:
            return
        
        if driver_num not in self._car_data:
            self._car_data[driver_num] = {}
        
        # 調試：記錄第一筆車輛數據
        if not hasattr(self, '_cardata_debug_count'):
            self._cardata_debug_count = 0
        self._cardata_debug_count += 1
        if self._cardata_debug_count <= 3:
            print(f"[REALTIME_SOURCE] CarData record: driver={driver_num}, keys={list(record.keys())}")
            print(f"[REALTIME_SOURCE] CarData values: {record}")
        
        # 支援大小寫欄位名
        self._car_data[driver_num].update({
            "rpm": record.get("rpm") or record.get("RPM", 0),
            "speed": record.get("speed") or record.get("Speed", 0),
            "gear": record.get("gear") or record.get("nGear", 0),
            "throttle": record.get("throttle") or record.get("Throttle", 0),
            "brake": record.get("brake") or record.get("Brake", 0),
            "drs": record.get("drs") or record.get("DRS", 0)
        })
    
    def _process_timing_data_record(self, record: dict):
        """處理單筆計時數據"""
        driver_num = str(record.get("DriverNo", ""))
        if not driver_num:
            return
        
        if driver_num not in self._timing_data:
            self._timing_data[driver_num] = {}
        
        # 更新所有非空值
        for key, value in record.items():
            if key not in ["SessionKey", "timestamp"] and value is not None:
                self._timing_data[driver_num][key] = value
    
    def _process_driver_list_record(self, record: dict):
        """處理車手列表數據"""
        driver_num = str(record.get("RacingNumber", ""))
        if not driver_num:
            return
        
        self._driver_list[driver_num] = {
            "RacingNumber": driver_num,
            "Tla": record.get("Tla", driver_num),
            "BroadcastName": record.get("BroadcastName", ""),
            "FullName": record.get("FullName", ""),
            "TeamName": record.get("TeamName", ""),
            "TeamColour": record.get("TeamColour", "CCCCCC"),
        }
    
    def _process_tyre_record(self, record: dict):
        """處理 CurrentTyres 數據"""
        driver_num = str(record.get("DriverNo", ""))
        if not driver_num:
            return
        
        if driver_num not in self._tyre_data:
            self._tyre_data[driver_num] = {}
        
        # 處理 New 欄位可能是字串 "true"/"false" 的情況
        new_value = record.get("New", False)
        if isinstance(new_value, str):
            new_value = new_value.lower() == "true"
        
        self._tyre_data[driver_num].update({
            "Compound": record.get("Compound", "UNKNOWN"),
            "New": new_value,
            "TyresNotChanged": record.get("TyresNotChanged", "0"),
        })
    
    def _process_tyre_stint_record(self, record: dict):
        """處理 TyreStintSeries 數據"""
        driver_num = str(record.get("DriverNo", ""))
        if not driver_num:
            return
        
        if driver_num not in self._tyre_data:
            self._tyre_data[driver_num] = {}
        
        # stint 數據包含歷史記錄
        if "Stints" not in self._tyre_data[driver_num]:
            self._tyre_data[driver_num]["Stints"] = []
        
        # 處理 New 欄位可能是字串 "true"/"false" 的情況
        new_value = record.get("New", False)
        if isinstance(new_value, str):
            new_value = new_value.lower() == "true"
        
        stint_info = {
            "Compound": record.get("Compound", "UNKNOWN"),
            "New": new_value,
            "TotalLaps": record.get("TotalLaps", 0),
            "StartLaps": record.get("StartLaps", 0),
        }
        
        # 計算 stint 的起始圈數（根據之前的 stint 累計）
        stints = self._tyre_data[driver_num]["Stints"]
        
        # 檢查是否為更新現有 stint 還是新增
        # 如果最後一個 stint 的 Compound 相同且 StartLaps 相同，更新它
        if stints:
            last_stint = stints[-1]
            if (last_stint.get("Compound") == stint_info["Compound"] and 
                last_stint.get("StartLaps") == stint_info["StartLaps"]):
                # 更新現有 stint
                last_stint.update(stint_info)
                return
        
        # 添加新 stint
        stints.append(stint_info)
    
    def _build_snapshot(self) -> Dict[str, Any]:
        """
        構建與 DataManager 兼容的快照格式
        
        Returns:
            {
                "race_time": "01:23:45.678",
                "race_time_seconds": 5025.678,
                "current_lap": 15,
                "total_laps": 57,
                "track_status": "1",
                "drivers": {
                    "1": {
                        "driver_num": "1",
                        "tla": "VER",
                        "position": 1,
                        "gap_to_leader": "",
                        "interval": "",
                        "last_lap_time": "1:23.456",
                        "speed": 320,
                        "x": 1234,
                        "y": 5678,
                        "status": "OnTrack",
                        "compound": "MEDIUM",
                        "tyre_age": 5,
                        ...
                    },
                    ...
                }
            }
        """
        # 計算賽事時間
        race_time_seconds = 0.0
        race_time_str = ""
        
        if self._last_update_time and self._session_start_time:
            delta = self._last_update_time - self._session_start_time
            race_time_seconds = delta.total_seconds()
            hours = int(race_time_seconds // 3600)
            minutes = int((race_time_seconds % 3600) // 60)
            seconds = race_time_seconds % 60
            race_time_str = f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
        elif self._last_update_time:
            race_time_str = self._last_update_time.strftime("%H:%M:%S.%f")[:-3]
        
        # 構建車手數據
        drivers = {}
        
        # 合併所有車手號碼
        all_driver_nums = set()
        all_driver_nums.update(self._position_data.keys())
        all_driver_nums.update(self._timing_data.keys())
        all_driver_nums.update(self._car_data.keys())
        all_driver_nums.update(self._driver_list.keys())
        
        for driver_num in all_driver_nums:
            driver_info = self._driver_list.get(driver_num, {})
            position_info = self._position_data.get(driver_num, {})
            timing_info = self._timing_data.get(driver_num, {})
            car_info = self._car_data.get(driver_num, {})
            tyre_info = self._tyre_data.get(driver_num, {})
            
            # 解析位置
            position = timing_info.get("Position", 0)
            if isinstance(position, str):
                try:
                    position = int(position)
                except:
                    position = 0
            
            # 計算輪胎使用圈數和進站次數
            tyre_age = 0
            pit_count = 0
            stints = tyre_info.get("Stints", [])
            if stints:
                last_stint = stints[-1]
                tyre_age = last_stint.get("TotalLaps", 0)
                # pit_count = stint 數量 - 1 (第一個 stint 不算進站)
                pit_count = max(0, len(stints) - 1)
            
            drivers[driver_num] = {
                "driver_num": driver_num,
                "driver_number": driver_num,  # 向後相容
                "tla": driver_info.get("Tla", driver_num),
                "driver_tla": driver_info.get("Tla", driver_num),  # 與歷史模式一致
                "full_name": driver_info.get("FullName", ""),
                "driver_name": driver_info.get("BroadcastName", driver_info.get("FullName", "")),  # 向後相容
                "team_name": driver_info.get("TeamName", ""),
                "team_colour": driver_info.get("TeamColour", "CCCCCC"),
                "team_color": driver_info.get("TeamColour", "CCCCCC"),  # 與歷史模式一致
                
                # 位置和狀態
                "position": position,
                "status": position_info.get("Status", "Unknown"),
                "x": position_info.get("X", 0),
                "y": position_info.get("Y", 0),
                "z": position_info.get("Z", 0),
                
                # 計時數據 - 解析 GapToLeader
                "gap_to_leader": self._parse_gap_value(timing_info.get("GapToLeader", "")),
                "gap_to_leader_raw": timing_info.get("GapToLeader", ""),  # 保留原始值供顯示
                "gap_to_leader_laps": self._parse_gap_laps(timing_info.get("GapToLeader", "")),
                "interval": self._extract_nested_value(timing_info, "IntervalToPositionAhead", "Value", ""),
                "last_lap_time": self._extract_nested_value(timing_info, "LastLapTime", "Value", ""),
                "best_lap_time": self._extract_nested_value(timing_info, "BestLapTime", "Value", ""),
                "sector_1": self._extract_sector_value(timing_info, 0),
                "sector_2": self._extract_sector_value(timing_info, 1),
                "sector_3": self._extract_sector_value(timing_info, 2),
                "in_pit": timing_info.get("InPit", False),
                "pit_out": timing_info.get("PitOut", False),
                "number_of_laps": timing_info.get("NumberOfLaps", 0),
                
                # 車輛遙測
                "speed": car_info.get("speed", 0),
                "rpm": car_info.get("rpm", 0),
                "gear": car_info.get("gear", 0),
                "throttle": car_info.get("throttle", 0),
                "brake": car_info.get("brake", 0),
                "drs": car_info.get("drs", 0),
                
                # 輪胎數據
                "compound": tyre_info.get("Compound", "UNKNOWN"),
                "tyre_new": tyre_info.get("New", False),
                "tyre_age": tyre_age,
                "pit_count": pit_count,
                "stints": stints,
            }
        
        return {
            "race_time": race_time_str,
            "race_time_seconds": race_time_seconds,
            "current_lap": self._lap_count.get("CurrentLap", 0),
            "total_laps": self._lap_count.get("TotalLaps", 0),
            "track_status": self._track_status,
            "weather": self._weather_data,
            "session_info": self._session_info,
            "drivers": drivers,
        }
    
    def clear_data(self):
        """清除所有數據"""
        self._position_data.clear()
        self._timing_data.clear()
        self._car_data.clear()
        self._tyre_data.clear()
        self._weather_data.clear()
        self._track_status = "1"
        self._race_control_messages.clear()
        self._lap_count = {"CurrentLap": 0, "TotalLaps": 0}
        self._driver_list.clear()
        self._session_info.clear()
        self._session_start_time = None
        self._last_update_time = None


# 導出
__all__ = ['RealTimeLiveF1DataSource', 'WEBSOCKETS_AVAILABLE']
