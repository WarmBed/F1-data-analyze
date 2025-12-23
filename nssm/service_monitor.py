"""
NSSM Service Monitor - Core Module
提供 NSSM 服務狀態監控的核心功能

功能:
- 讀取 Windows 服務狀態
- 獲取進程資訊 (CPU/記憶體/PID)
- 讀取服務日誌
- 啟動/停止/重啟服務
"""

import subprocess
import os
import re
import psutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class NSSMServiceMonitor:
    """NSSM 服務監控類別"""
    
    def __init__(self, debug_enabled: bool = False):
        """初始化監控器"""
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent
        # 修正：使用專案根目錄下的 logs，而非 nssm/logs
        self.logs_dir = self.project_root / "logs"
        self.debug_enabled = debug_enabled
        
        # F1T 服務列表
        self.services = {
            "F1T-API": {
                "log_stdout": self.logs_dir / "f1t-api.log",
                "log_stderr": self.logs_dir / "f1t-api.error.log",
                "process_name": "python.exe"
            },
            "F1T-PeriodicUpdate": {
                "log_stdout": self.logs_dir / "periodic-update.log",
                "log_stderr": self.logs_dir / "periodic-update.error.log",
                "process_name": "python.exe"
            },
            "F1T-CloudflareTunnel": {
                "log_stdout": self.logs_dir / "cloudflare-tunnel.log",
                "log_stderr": self.logs_dir / "cloudflare-tunnel.error.log",
                "process_name": "cloudflared.exe"
            }
        }
    
    def _debug(self, message: str):
        """DEBUG 訊息輸出"""
        if self.debug_enabled:
            print(f"[DEBUG] {message}")
    
    def get_service_status(self, service_name: str) -> Dict:
        """
        獲取服務狀態
        
        Returns:
            {
                "exists": bool,
                "state": str (RUNNING/STOPPED/...),
                "pid": int,
                "startup_type": str,
                "process_info": {...} or None
            }
        """
        self._debug(f"獲取服務狀態: {service_name}")
        try:
            # 使用 sc query 獲取服務狀態（使用 cp950 編碼）
            result = subprocess.run(
                ["sc", "query", service_name],
                capture_output=True,
                text=True,
                encoding='cp950',
                errors='ignore'
            )
            self._debug(f"命令返回碼: {result.returncode}")
            
            if result.returncode != 0:
                self._debug(f"服務 {service_name} 不存在或查詢失敗")
                self._debug(f"錯誤輸出: {result.stderr}")
                return {
                    "exists": False,
                    "state": "NOT_INSTALLED",
                    "pid": None,
                    "startup_type": None,
                    "process_info": None
                }
            
            # 解析輸出
            output = result.stdout
            self._debug(f"sc query 輸出 (部分):\n{output[:200]}...")
            
            # 提取狀態
            state_match = re.search(r'STATE\s+:\s+\d+\s+(\w+)', output)
            state = state_match.group(1) if state_match else "UNKNOWN"
            self._debug(f"解析狀態: {state}")
            
            # 提取 PID - sc query 不包含 PID，需要用其他方法獲取
            pid = None
            
            # 方法 1: 使用 WMIC 獲取服務 PID
            try:
                wmic_result = subprocess.run(
                    ["wmic", "service", "where", f"name='{service_name}'", "get", "processid", "/format:value"],
                    capture_output=True,
                    text=True,
                    encoding='cp950',
                    errors='ignore'
                )
                if wmic_result.returncode == 0:
                    pid_match = re.search(r'ProcessId=(\d+)', wmic_result.stdout)
                    if pid_match:
                        pid = int(pid_match.group(1))
                        self._debug(f"WMIC 獲取 PID: {pid}")
            except Exception as e:
                self._debug(f"WMIC 獲取 PID 失敗: {e}")
            
            # 方法 2: 如果 WMIC 失敗，嘗試用 PowerShell
            if not pid:
                try:
                    ps_result = subprocess.run(
                        ["powershell", "-Command", f"Get-WmiObject -Class Win32_Service -Filter \"Name='{service_name}'\" | Select-Object -Property ProcessId"],
                        capture_output=True,
                        text=True,
                        encoding='cp950',
                        errors='ignore'
                    )
                    if ps_result.returncode == 0:
                        pid_match = re.search(r'(\d+)', ps_result.stdout)
                        if pid_match:
                            pid = int(pid_match.group(1))
                            self._debug(f"PowerShell 獲取 PID: {pid}")
                except Exception as e:
                    self._debug(f"PowerShell 獲取 PID 失敗: {e}")
            
            self._debug(f"最終 PID: {pid}")
            
            # 獲取進程資訊
            process_info = None
            if pid and pid > 0:
                try:
                    process = psutil.Process(pid)
                    cpu_percent = process.cpu_percent(interval=0.1)
                    memory_mb = process.memory_info().rss / (1024 * 1024)
                    
                    process_info = {
                        "pid": pid,
                        "name": process.name(),
                        "cpu_percent": cpu_percent,
                        "memory_mb": memory_mb,
                        "create_time": process.create_time(),
                        "status": process.status()
                    }
                    self._debug(f"進程資訊獲取成功: CPU={cpu_percent:.1f}%, MEM={memory_mb:.1f}MB")
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    self._debug(f"獲取進程資訊失敗: {e}")
            else:
                self._debug(f"PID 無效或為 0，跳過進程資訊獲取")
            
            # 獲取啟動類型（使用 cp950 編碼）
            startup_result = subprocess.run(
                ["sc", "qc", service_name],
                capture_output=True,
                text=True,
                encoding='cp950',
                errors='ignore'
            )
            
            startup_type = "UNKNOWN"
            if startup_result.returncode == 0:
                startup_match = re.search(r'START_TYPE\s+:\s+\d+\s+(\w+)', startup_result.stdout)
                if startup_match:
                    startup_type = startup_match.group(1)
                self._debug(f"解析啟動類型: {startup_type}")
            else:
                self._debug(f"獲取啟動類型失敗，返回碼: {startup_result.returncode}")
            
            result_data = {
                "exists": True,
                "state": state,
                "pid": pid,
                "startup_type": startup_type,
                "process_info": process_info
            }
            self._debug(f"服務狀態結果: {result_data}")
            return result_data
            
        except Exception as e:
            print(f"[ERROR] 獲取服務狀態失敗: {e}")
            import traceback
            print(f"[ERROR] 詳細錯誤: {traceback.format_exc()}")
            return {
                "exists": False,
                "state": "ERROR",
                "pid": None,
                "startup_type": None,
                "process_info": None,
                "error": str(e)
            }
    
    def start_service(self, service_name: str) -> bool:
        """啟動服務"""
        self._debug(f"嘗試啟動服務: {service_name}")
        try:
            result = subprocess.run(
                ["net", "start", service_name],
                capture_output=True,
                text=True,
                encoding='cp950',
                errors='ignore'
            )
            self._debug(f"net start 返回碼: {result.returncode}")
            if result.stderr:
                self._debug(f"net start 錯誤: {result.stderr}")
            
            success = result.returncode == 0
            self._debug(f"啟動服務結果: {success}")
            return success
        except Exception as e:
            print(f"[ERROR] 啟動服務失敗: {e}")
            import traceback
            print(f"[ERROR] 詳細錯誤: {traceback.format_exc()}")
            return False
    
    def stop_service(self, service_name: str) -> bool:
        """停止服務"""
        self._debug(f"嘗試停止服務: {service_name}")
        try:
            result = subprocess.run(
                ["net", "stop", service_name],
                capture_output=True,
                text=True,
                encoding='cp950',
                errors='ignore'
            )
            self._debug(f"net stop 返回碼: {result.returncode}")
            if result.stderr:
                self._debug(f"net stop 錯誤: {result.stderr}")
            
            success = result.returncode == 0
            self._debug(f"停止服務結果: {success}")
            return success
        except Exception as e:
            print(f"[ERROR] 停止服務失敗: {e}")
            import traceback
            print(f"[ERROR] 詳細錯誤: {traceback.format_exc()}")
            return False
    
    def restart_service(self, service_name: str) -> bool:
        """重啟服務 - 異步友好版本"""
        self._debug(f"嘗試重啟服務: {service_name}")
        try:
            # 先停止服務
            if not self.stop_service(service_name):
                self._debug(f"停止服務 {service_name} 失敗")
                return False
            
            # 非阻塞等待 - 使用輪詢方式確認服務已停止
            import time
            max_wait = 10  # 最多等待 10 秒
            wait_step = 0.5  # 每次等待 0.5 秒
            waited = 0
            
            while waited < max_wait:
                time.sleep(wait_step)
                waited += wait_step
                status = self.get_service_status(service_name)
                if status["state"] == "STOPPED":
                    break
                self._debug(f"等待服務停止... ({waited:.1f}s)")
            
            # 啟動服務
            success = self.start_service(service_name)
            self._debug(f"重啟服務 {service_name} 結果: {success}")
            return success
            
        except Exception as e:
            print(f"[ERROR] 重啟服務 {service_name} 失敗: {e}")
            import traceback
            print(f"[ERROR] 詳細錯誤: {traceback.format_exc()}")
            return False
    
    def get_service_logs(self, service_name: str, tail: int = 100, error_log: bool = False) -> List[str]:
        """
        獲取服務日誌 - 增強編碼支援
        
        Args:
            service_name: 服務名稱
            tail: 讀取最後 N 行
            error_log: 是否讀取錯誤日誌
        
        Returns:
            日誌行列表
        """
        self._debug(f"獲取服務日誌: {service_name} (錯誤日誌: {error_log}, 尾行數: {tail})")
        
        if service_name not in self.services:
            self._debug(f"服務 {service_name} 不在配置中")
            return []
        
        log_file = (self.services[service_name]["log_stderr"] if error_log 
                   else self.services[service_name]["log_stdout"])
        
        self._debug(f"日誌檔案路徑: {log_file}")
        
        if not log_file.exists():
            self._debug(f"日誌檔案不存在: {log_file}")
            return []
        
        try:
            # 嘗試多種編碼讀取
            encodings = ['utf-8', 'cp950', 'gbk', 'big5', 'latin1']
            
            for encoding in encodings:
                try:
                    self._debug(f"嘗試使用編碼 {encoding} 讀取日誌")
                    with open(log_file, 'r', encoding=encoding, errors='replace') as f:
                        lines = f.readlines()
                        result = [line.rstrip() for line in lines[-tail:]]
                    self._debug(f"成功使用 {encoding} 讀取 {len(result)} 行")
                    return result
                except Exception as e:
                    self._debug(f"使用 {encoding} 讀取失敗: {e}")
                    continue
            
            # 所有編碼都失敗
            print(f"[ERROR] 無法讀取日誌檔案 {log_file}（所有編碼嘗試均失敗）")
            return []
            
        except Exception as e:
            print(f"[ERROR] 讀取日誌失敗: {e}")
            import traceback
            print(f"[ERROR] 詳細錯誤: {traceback.format_exc()}")
            return []
    
    def get_log_file_path(self, service_name: str, error_log: bool = False) -> Optional[Path]:
        """獲取日誌檔案路徑"""
        if service_name not in self.services:
            return None
        
        return (self.services[service_name]["log_stderr"] if error_log 
               else self.services[service_name]["log_stdout"])
    
    def get_all_services_status(self) -> Dict[str, Dict]:
        """獲取所有服務狀態"""
        return {
            name: self.get_service_status(name)
            for name in self.services.keys()
        }
    
    def get_service_history(self, service_name: str, hours: int = 24) -> List[Dict]:
        """
        獲取服務歷史狀態（從日誌解析）
        
        Args:
            service_name: 服務名稱
            hours: 獲取過去 N 小時的資料
        
        Returns:
            歷史狀態列表
        """
        # TODO: 實現歷史狀態解析
        # 可以從日誌檔案中解析時間戳和狀態變化
        return []
    
    def check_admin_privileges(self) -> bool:
        """檢查是否有管理員權限"""
        try:
            result = subprocess.run(
                ["net", "session"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False


# 測試程式碼
if __name__ == "__main__":
    monitor = NSSMServiceMonitor()
    
    print("=" * 60)
    print("F1T NSSM 服務監控測試")
    print("=" * 60)
    
    for service_name in monitor.services.keys():
        print(f"\n服務: {service_name}")
        print("-" * 60)
        
        status = monitor.get_service_status(service_name)
        print(f"存在: {status['exists']}")
        print(f"狀態: {status['state']}")
        print(f"PID: {status['pid']}")
        print(f"啟動類型: {status['startup_type']}")
        
        if status['process_info']:
            info = status['process_info']
            print(f"CPU: {info['cpu_percent']:.1f}%")
            print(f"記憶體: {info['memory_mb']:.1f} MB")
        
        # 讀取最新 5 行日誌
        logs = monitor.get_service_logs(service_name, tail=5)
        if logs:
            print(f"\n最新日誌 (前 5 行):")
            for line in logs:
                print(f"  {line}")
    
    print("\n" + "=" * 60)
    print(f"管理員權限: {'是' if monitor.check_admin_privileges() else '否'}")
    print("=" * 60)
