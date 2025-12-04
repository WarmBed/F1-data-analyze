#!/usr/bin/env python3
"""
Race Event Monitor - 賽事事件驅動監控系統

監控 Season Calendar 中的賽事時間，自動觸發 Function 96/97/99 刷新
實作事件驅動架構，在賽後自動更新數據
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import traceback

# 導入 CLI 檢查函數
from CLI_modules.cli.analyzer.season_calendar_analysis import check_calendar_freshness
from CLI_modules.cli.analyzer.championship_standings_analysis import check_standings_freshness
from CLI_modules.cli.analyzer.race_weather_forecast import check_weather_forecast_freshness

# 導入日誌系統
from core.logger import get_logger

logger = get_logger(component="api")


class RaceEventMonitor:
    """
    賽事事件監控器
    
    職責：
    1. 定期檢查 Season Calendar 中的賽事時間
    2. 偵測賽後 0-72 小時的賽事
    3. 自動觸發 Function 96/97/99 刷新
    """
    
    def __init__(self, analysis_service):
        """
        初始化監控器
        
        Args:
            analysis_service: SimpleF1AnalysisService 實例（用於調用 CLI）
        """
        self.analysis_service = analysis_service
        self.calendar_data: Optional[Dict[str, Any]] = None
        self.last_refresh: Dict[str, datetime] = {}
        self.running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        logger.info("🔍 RaceEventMonitor 初始化完成")
    
    async def start(self):
        """啟動監控循環"""
        if self.running:
            logger.warning("⚠️ 監控器已在運行中")
            return
        
        self.running = True
        logger.info("🚀 啟動賽事事件監控器...")
        
        # 啟動背景任務
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("✅ 監控器已啟動，檢查間隔: 5 分鐘")
    
    async def stop(self):
        """停止監控循環"""
        if not self.running:
            return
        
        self.running = False
        logger.info("🛑 停止賽事事件監控器...")
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("✅ 監控器已停止")
    
    async def _monitoring_loop(self):
        """
        主監控循環
        
        每 5 分鐘執行一次檢查
        """
        while self.running:
            try:
                await self._check_race_events()
            except Exception as e:
                logger.error(f"❌ 監控循環錯誤: {e}")
                traceback.print_exc()
            
            # 等待 5 分鐘後再次檢查
            await asyncio.sleep(300)
    
    async def _check_race_events(self):
        """
        檢查所有賽事的狀態
        
        核心邏輯：
        1. 載入 Season Calendar
        2. 檢查每個賽事的時間
        3. 觸發相應的刷新操作
        """
        now = datetime.now(timezone.utc)
        logger.debug(f"🔍 開始檢查賽事事件 ({now.isoformat()})")
        
        # 步驟 1: 檢查 Function 99 (Season Calendar) 新鮮度
        await self._check_and_refresh_calendar()
        
        # 步驟 2: 載入最新 Season Calendar
        if not await self._load_calendar():
            logger.warning("⚠️ 無法載入 Season Calendar，跳過本次檢查")
            return
        
        # 步驟 3: 檢查所有年份的賽事
        for year in [2024, 2025]:
            year_events = self.calendar_data.get(str(year), [])
            if not isinstance(year_events, list):
                continue
            
            for event in year_events:
                await self._check_single_event(event, year)
        
        logger.debug("✅ 賽事事件檢查完成")
    
    async def _check_and_refresh_calendar(self):
        """檢查並刷新 Season Calendar（如果需要）"""
        try:
            # 檢查新鮮度
            freshness = await asyncio.to_thread(check_calendar_freshness, all_years=True)
            
            if freshness.get('should_regenerate', False):
                reason = freshness.get('reason', '未知')
                trigger_mode = freshness.get('trigger_mode')
                
                logger.info(f"🔄 Season Calendar 需要刷新")
                logger.info(f"   └─ 原因: {reason}")
                logger.info(f"   └─ 觸發模式: {trigger_mode}")
                
                # 觸發 Function 99 刷新
                result = await self.analysis_service.execute_analysis("99", force_refresh=True)
                
                if result.get('success'):
                    logger.info(f"✅ Season Calendar 刷新完成")
                    # 重新載入
                    self.calendar_data = None
                else:
                    error_msg = result.get('error', result.get('message', '未知錯誤'))
                    logger.error(f"❌ Season Calendar 刷新失敗: {error_msg}")
                    logger.error(f"   └─ 完整回應: {result}")
            else:
                logger.debug("✅ Season Calendar 仍然新鮮，跳過刷新")
                
        except Exception as e:
            logger.error(f"❌ 檢查 Season Calendar 時發生錯誤: {e}")
            traceback.print_exc()
    
    async def _load_calendar(self) -> bool:
        """
        載入 Season Calendar 數據
        
        Returns:
            True 如果載入成功，False 否則
        """
        if self.calendar_data is not None:
            return True
        
        try:
            # 尋找最新的 Season Calendar JSON
            json_dir = Path("json")
            if not json_dir.exists():
                logger.warning("⚠️ JSON 目錄不存在")
                return False
            
            calendar_files = sorted(
                json_dir.glob("season_calendar_multi_year*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            if not calendar_files:
                logger.warning("⚠️ 找不到 Season Calendar 檔案")
                return False
            
            latest_file = calendar_files[0]
            logger.debug(f"📂 載入 Season Calendar: {latest_file.name}")
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.calendar_data = data.get('data', {})
            logger.debug(f"✅ 載入 Season Calendar 成功（{len(self.calendar_data)} 年份）")
            return True
            
        except Exception as e:
            logger.error(f"❌ 載入 Season Calendar 失敗: {e}")
            traceback.print_exc()
            return False
    
    async def _check_single_event(self, event: Dict[str, Any], year: int):
        """
        檢查單個賽事並觸發相應的刷新
        
        Args:
            event: 賽事數據
            year: 賽季年份
        """
        try:
            event_name = event.get('event_name', 'Unknown')
            location = event.get('location', 'Unknown')
            round_num = event.get('round', 'N/A')
            race_date_str = event.get('race_date_utc')
            
            if not race_date_str:
                return
            
            # 解析賽事時間
            race_date = datetime.fromisoformat(race_date_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            hours_since_race = (now - race_date).total_seconds() / 3600
            hours_until_race = (race_date - now).total_seconds() / 3600
            
            # 🏁 賽後 0-72 小時：觸發所有刷新
            if 0 <= hours_since_race <= 72:
                await self._handle_post_race_event(
                    event_name, location, round_num, year, hours_since_race
                )
            
            # 🌤️ 賽前 24 小時：觸發天氣刷新
            elif 0 <= hours_until_race <= 24:
                await self._handle_pre_race_weather(
                    event_name, location, year, hours_until_race
                )
                
        except Exception as e:
            logger.error(f"❌ 檢查賽事時發生錯誤: {e}")
            traceback.print_exc()
    
    async def _handle_post_race_event(
        self, 
        event_name: str, 
        location: str, 
        round_num: int, 
        year: int, 
        hours_since_race: float
    ):
        """
        處理賽後事件
        
        觸發：
        - Function 97 (Championship Standings) - 每 6 小時
        - Function 96 (Weather Forecast) - 賽後 6 小時內
        """
        logger.debug(f"🏁 賽後監控: {event_name} (R{round_num}) - 賽後 {hours_since_race:.1f}h")
        
        # 檢查 Function 97 (Championship Standings)
        await self._check_and_refresh_standings(year, hours_since_race)
        
        # 檢查 Function 96 (Weather Forecast) - 只在賽後 6 小時內
        if hours_since_race <= 6:
            await self._check_and_refresh_weather(year, location, hours_since_race, is_post_race=True)
    
    async def _handle_pre_race_weather(
        self, 
        event_name: str, 
        location: str, 
        year: int, 
        hours_until_race: float
    ):
        """
        處理賽前天氣刷新
        
        觸發：
        - Function 96 (Weather Forecast) - 賽前 24 小時內，每 2 小時
        """
        logger.debug(f"🌤️ 賽前監控: {event_name} - 賽前 {hours_until_race:.1f}h")
        
        await self._check_and_refresh_weather(year, location, hours_until_race, is_post_race=False)
    
    async def _check_and_refresh_standings(self, year: int, hours_since_race: float):
        """
        檢查並刷新 Championship Standings
        
        Args:
            year: 賽季年份
            hours_since_race: 賽後經過的小時數
        """
        try:
            # 檢查上次刷新時間（避免重複刷新）
            last_refresh_key = f"standings_{year}"
            last_refresh = self.last_refresh.get(last_refresh_key)
            now = datetime.now(timezone.utc)
            
            if last_refresh:
                hours_since_last_refresh = (now - last_refresh).total_seconds() / 3600
                if hours_since_last_refresh < 6:
                    logger.debug(f"⏭️ 積分榜上次刷新於 {hours_since_last_refresh:.1f}h 前，跳過")
                    return
            
            # 檢查新鮮度
            freshness = await asyncio.to_thread(check_standings_freshness, year)
            
            if freshness.get('should_regenerate', False):
                reason = freshness.get('reason', '未知')
                logger.info(f"🔄 {year} 積分榜需要刷新")
                logger.info(f"   └─ 原因: {reason}")
                logger.info(f"   └─ 賽後經過: {hours_since_race:.1f} 小時")
                
                # 觸發 Function 97 刷新
                result = await self.analysis_service.execute_analysis("97", year=year, force_refresh=True)
                
                if result.get('success'):
                    logger.info(f"✅ {year} 積分榜刷新完成")
                    self.last_refresh[last_refresh_key] = now
                else:
                    logger.error(f"❌ {year} 積分榜刷新失敗: {result.get('message')}")
            else:
                logger.debug(f"✅ {year} 積分榜仍然新鮮，跳過刷新")
                
        except Exception as e:
            logger.error(f"❌ 檢查積分榜時發生錯誤: {e}")
            traceback.print_exc()
    
    async def _check_and_refresh_weather(
        self, 
        year: int, 
        location: str, 
        hours_diff: float,
        is_post_race: bool
    ):
        """
        檢查並刷新 Weather Forecast
        
        Args:
            year: 賽季年份
            location: 賽事地點
            hours_diff: 賽前/賽後經過的小時數
            is_post_race: 是否為賽後模式
        """
        try:
            # 檢查上次刷新時間
            last_refresh_key = f"weather_{year}_{location}"
            last_refresh = self.last_refresh.get(last_refresh_key)
            now = datetime.now(timezone.utc)
            
            if last_refresh:
                hours_since_last_refresh = (now - last_refresh).total_seconds() / 3600
                min_interval = 0.5 if is_post_race else 2  # 賽後 0.5h，賽前 2h
                
                if hours_since_last_refresh < min_interval:
                    logger.debug(f"⏭️ {location} 天氣上次刷新於 {hours_since_last_refresh:.1f}h 前，跳過")
                    return
            
            # 檢查新鮮度
            freshness = await asyncio.to_thread(check_weather_forecast_freshness, year, location)
            
            if freshness.get('should_regenerate', False):
                mode = "賽後" if is_post_race else "賽前"
                logger.info(f"🔄 {location} 天氣預報需要刷新（{mode}模式）")
                logger.info(f"   └─ 原因: {freshness.get('reason', '未知')}")
                logger.info(f"   └─ {mode}經過: {hours_diff:.1f} 小時")
                
                # 觸發 Function 96 刷新
                result = await self.analysis_service.execute_analysis(
                    "96", 
                    year=year, 
                    race=location, 
                    session="R",
                    force_refresh=True
                )
                
                if result.get('success'):
                    logger.info(f"✅ {location} 天氣預報刷新完成")
                    self.last_refresh[last_refresh_key] = now
                else:
                    logger.error(f"❌ {location} 天氣預報刷新失敗: {result.get('message')}")
            else:
                logger.debug(f"✅ {location} 天氣預報仍然新鮮，跳過刷新")
                
        except Exception as e:
            logger.error(f"❌ 檢查天氣預報時發生錯誤: {e}")
            traceback.print_exc()
    
    def get_status(self) -> Dict[str, Any]:
        """
        獲取監控器狀態
        
        Returns:
            包含監控器狀態的字典
        """
        return {
            "running": self.running,
            "calendar_loaded": self.calendar_data is not None,
            "last_refresh_times": {
                key: value.isoformat() 
                for key, value in self.last_refresh.items()
            },
            "monitored_years": list(self.calendar_data.keys()) if self.calendar_data else []
        }
