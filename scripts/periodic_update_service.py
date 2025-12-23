#!/usr/bin/env python3
"""
Periodic Update Service - 定時 API 更新服務

自動定時呼叫 CLI 功能以更新數據：
- F96: 賽事天氣預報
- F97: 賽季積分查詢
- F98: 顏色配置輸出
- F99: 賽季賽程查詢

支援三種智能更新模式：
- 平時維護模式 (Normal Maintenance)
- 賽後密集模式 (Post-Race Intensive) - 賽後 48h 內每 4h 更新 F97
- 賽前預熱模式 (Pre-Race Warm-Up) - 賽前 72h 內每 6h 更新 F96

Author: F1T Team
Date: 2025-10-13
Version: 1.0.0
"""

import os
import sys
import json
import time
import signal
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from logging.handlers import RotatingFileHandler

import schedule

# 添加專案根目錄到 Python 路徑
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.race_event_detector import RaceEventDetector


class PeriodicUpdateService:
    """定時更新服務 - 智能調度 CLI 功能執行"""
    
    def __init__(self, config_path: str = "scripts/config/update_service_config.json"):
        """
        初始化定時更新服務
        
        Args:
            config_path: 配置檔案路徑
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.detector = RaceEventDetector()
        self.current_mode = "normal"
        self.logger: Optional[logging.Logger] = None
        self.running = False
        self.last_execution: Dict[str, datetime] = {}
        
        # 載入配置
        self.load_config()
        
        # 設定日誌
        self.setup_logging()
        
        # 設定信號處理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def load_config(self) -> bool:
        """
        載入配置檔案
        
        Returns:
            是否成功載入
        """
        try:
            if not self.config_path.exists():
                print(f"[ERROR] 配置檔案不存在: {self.config_path}")
                return False
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 載入配置失敗: {e}")
            return False
    
    def setup_logging(self):
        """設定日誌系統"""
        log_config = self.config.get("logging", {})
        
        # 創建日誌目錄
        log_file = Path(log_config.get("file", "logs/periodic_update_service.log"))
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 創建 logger
        self.logger = logging.getLogger("PeriodicUpdateService")
        self.logger.setLevel(getattr(logging, log_config.get("level", "INFO")))
        
        # 清除現有 handlers
        self.logger.handlers.clear()
        
        # 檔案 handler（帶輪轉）
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=log_config.get("max_bytes", 10485760),  # 10MB
            backupCount=log_config.get("backup_count", 5),
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台 handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 格式化
        formatter = logging.Formatter(
            log_config.get("format", "[%(asctime)s] [%(levelname)s] %(message)s"),
            datefmt=log_config.get("date_format", "%Y-%m-%d %H:%M:%S")
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加 handlers
        self.logger.addHandler(file_handler)
        if log_config.get("console", True):
            self.logger.addHandler(console_handler)
    
    def update_mode(self):
        """更新當前模式"""
        old_mode = self.current_mode
        mode_info = self.detector.get_mode_info()
        new_mode = mode_info["mode"]
        
        if old_mode != new_mode:
            self.logger.info(f"🔄 模式切換: {old_mode} → {new_mode}")
            self.logger.info(f"   新模式: {mode_info['mode_name']}")
            
            # 記錄賽事資訊
            if mode_info.get("last_race"):
                last = mode_info["last_race"]
                self.logger.info(f"   最近完賽: 第 {last['round']} 站 {last['event_name']}")
            
            if mode_info.get("next_race"):
                next_race = mode_info["next_race"]
                time_until = mode_info["time_until_next_race"]
                self.logger.info(f"   下一場: 第 {next_race['round']} 站 {next_race['event_name']} ({time_until['formatted']})")
            
            self.current_mode = new_mode
            
            # 重新調度任務
            self.schedule_tasks()
    
    def schedule_tasks(self):
        """根據當前模式調度任務"""
        # 清除現有任務
        schedule.clear()
        
        # 獲取當前模式的更新間隔
        intervals = self.config["update_intervals"].get(self.current_mode, {})
        functions = self.config.get("functions", {})
        
        self.logger.info(f"📅 調度任務 - 模式: {self.current_mode}")
        
        for func_id, interval_hours in intervals.items():
            # 跳過元數據
            if func_id.startswith("_"):
                continue
            
            # 跳過 null 間隔（禁用）
            if interval_hours is None:
                func_name = functions.get(func_id, {}).get("name", f"F{func_id}")
                self.logger.info(f"   ⏸️  F{func_id} {func_name}: 暫停更新")
                continue
            
            # 跳過未啟用的功能
            if not functions.get(func_id, {}).get("enabled", False):
                continue
            
            func_name = functions.get(func_id, {}).get("name", f"F{func_id}")
            self.logger.info(f"   ✅ F{func_id} {func_name}: 每 {interval_hours} 小時")
            
            # 調度任務
            schedule.every(interval_hours).hours.do(
                self.execute_function,
                func_id=func_id
            )
        
        # 立即執行一次檢查（可選）
        # self.logger.info("🚀 立即執行初始更新...")
        # for func_id in functions.keys():
        #     if functions[func_id].get("enabled", False):
        #         self.execute_function(func_id)
    
    def execute_function(self, func_id: str) -> bool:
        """
        執行 CLI 功能
        
        Args:
            func_id: 功能 ID (96, 97, 98, 99)
            
        Returns:
            是否執行成功
        """
        functions = self.config.get("functions", {})
        func_info = functions.get(func_id, {})
        func_name = func_info.get("name", f"F{func_id}")
        
        self.logger.info(f"🚀 執行: F{func_id} {func_name}")
        
        try:
            # 構建 CLI 命令
            cli_args = func_info.get("cli_args", ["-f", func_id])
            
            # 添加 --force 參數（可選）
            # cli_args.append("--force")
            
            # 執行 CLI
            cmd = ["python", "f1_analysis_modular_main.py"] + cli_args
            self.logger.debug(f"   命令: {' '.join(cmd)}")
            
            start_time = time.time()
            
            result = subprocess.run(
                cmd,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=self.config.get("api", {}).get("timeout", 120)
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                self.logger.info(f"   ✅ 執行成功 ({duration:.1f}s)")
                self.last_execution[func_id] = datetime.now()
                return True
            else:
                self.logger.error(f"   ❌ 執行失敗 (exit code: {result.returncode})")
                if result.stderr:
                    self.logger.error(f"   錯誤: {result.stderr[:200]}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"   ❌ 執行超時")
            return False
        except Exception as e:
            self.logger.error(f"   ❌ 執行異常: {e}")
            return False
    
    def start(self):
        """啟動定時服務"""
        self.logger.info("=" * 60)
        self.logger.info("🎯 定時 API 更新服務啟動")
        self.logger.info("=" * 60)
        self.logger.info(f"📁 配置檔案: {self.config_path}")
        self.logger.info(f"📁 專案根目錄: {PROJECT_ROOT}")
        
        # 初始化賽事檢測器
        if not self.detector.load_calendar_data():
            self.logger.error("❌ 載入賽程數據失敗，服務無法啟動")
            return
        
        # 初始化模式
        self.update_mode()
        
        # 啟動延遲
        startup_delay = self.config.get("service", {}).get("startup_delay_seconds", 10)
        if startup_delay > 0:
            self.logger.info(f"⏳ 啟動延遲 {startup_delay} 秒...")
            time.sleep(startup_delay)
        
        self.running = True
        self.logger.info("✅ 服務運行中... (按 Ctrl+C 停止)")
        
        # 主循環
        check_interval = self.config.get("service", {}).get("check_interval_seconds", 60)
        
        while self.running:
            try:
                # 每小時檢查一次模式切換
                if datetime.now().minute == 0:
                    self.update_mode()
                
                # 執行排程任務
                schedule.run_pending()
                
                # 等待下次檢查
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                self.logger.info("\n⚠️  收到中斷信號，準備停止服務...")
                break
            except Exception as e:
                self.logger.error(f"❌ 主循環異常: {e}")
                if not self.config.get("error_handling", {}).get("continue_on_error", True):
                    break
    
    def stop(self):
        """停止定時服務"""
        self.logger.info("🛑 正在停止服務...")
        self.running = False
        
        # 清除所有任務
        schedule.clear()
        
        self.logger.info("✅ 服務已停止")
        self.logger.info("=" * 60)
    
    def _signal_handler(self, signum, frame):
        """信號處理器"""
        self.logger.warning(f"⚠️  收到信號 {signum}，準備優雅關閉...")
        self.stop()
        sys.exit(0)


def main():
    """主函數"""
    service = PeriodicUpdateService()
    
    try:
        service.start()
    except KeyboardInterrupt:
        print("\n收到中斷信號")
    finally:
        service.stop()


if __name__ == "__main__":
    main()
