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
    
    def __init__(self):
        """初始化監控器"""
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent
        self.logs_dir = self.script_dir / "logs"
        
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
        try:
            # 使用 sc query 獲取服務狀態
            result = subprocess.run(
                ["sc", "query", service_name],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode != 0:
                return {
                    "exists": False,
                    "state": "NOT_INSTALLED",
                    "pid": None,
                    "startup_type": None,
                    "process_info": None
                }
            
            # 解析輸出
            output = result.stdout
            
            # 提取狀態
            state_match = re.search(r'STATE\s+:\s+\d+\s+(\w+)', output)
            state = state_match.group(1) if state_match else "UNKNOWN"
            
            # 提取 PID
            pid_match = re.search(r'PID\s+:\s+(\d+)', output)
            pid = int(pid_match.group(1)) if pid_match else None
            
            # 獲取進程資訊
            process_info = None
            if pid and pid > 0:
                try:
                    process = psutil.Process(pid)
                    process_info = {
                        "pid": pid,
                        "name": process.name(),
                        "cpu_percent": process.cpu_percent(interval=0.1),
                        "memory_mb": process.memory_info().rss / (1024 * 1024),
                        "create_time": process.create_time(),
                        "status": process.status()
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 獲取啟動類型
            startup_result = subprocess.run(
                ["sc", "qc", service_name],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            startup_type = "UNKNOWN"
            if startup_result.returncode == 0:
                startup_match = re.search(r'START_TYPE\s+:\s+\d+\s+(\w+)', startup_result.stdout)
                if startup_match:
                    startup_type = startup_match.group(1)
            
            return {
                "exists": True,
                "state": state,
                "pid": pid,
                "startup_type": startup_type,
                "process_info": process_info
            }
            
        except Exception as e:
            print(f"[ERROR] 獲取服務狀態失敗: {e}")
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
        try:
            result = subprocess.run(
                ["net", "start", service_name],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            return result.returncode == 0
        except Exception as e:
            print(f"[ERROR] 啟動服務失敗: {e}")
            return False
    
    def stop_service(self, service_name: str) -> bool:
        """停止服務"""
        try:
            result = subprocess.run(
                ["net", "stop", service_name],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            return result.returncode == 0
        except Exception as e:
            print(f"[ERROR] 停止服務失敗: {e}")
            return False
    
    def restart_service(self, service_name: str) -> bool:
        """重啟服務"""
        if self.stop_service(service_name):
            import time
            time.sleep(2)  # 等待 2 秒
            return self.start_service(service_name)
        return False
    
    def get_service_logs(self, service_name: str, tail: int = 100, error_log: bool = False) -> List[str]:
        """
        獲取服務日誌
        
        Args:
            service_name: 服務名稱
            tail: 讀取最後 N 行
            error_log: 是否讀取錯誤日誌
        
        Returns:
            日誌行列表
        """
        if service_name not in self.services:
            return []
        
        log_file = (self.services[service_name]["log_stderr"] if error_log 
                   else self.services[service_name]["log_stdout"])
        
        if not log_file.exists():
            return []
        
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                return [line.rstrip() for line in lines[-tail:]]
        except Exception as e:
            print(f"[ERROR] 讀取日誌失敗: {e}")
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
