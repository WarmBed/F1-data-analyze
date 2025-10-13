#!/usr/bin/env python3
"""
Weather Timeline Data Loader

Loads race weather forecast data for timeline display
Follows API-ONLY pattern - prioritizes API, falls back to local JSON

Author: F1T Team
Date: 2025-10-13
Version: 1.0.0
"""

from modules.gui.base.universal_data_loader_base import UniversalDataLoader
from typing import Dict, Any, Optional, List
import json
from pathlib import Path


class WeatherTimelineDataLoader(UniversalDataLoader):
    """
    Weather Timeline Data Loader
    
    Inherits from UniversalDataLoader, implements loading, validation and transformation
    of race weather forecast data
    
    Data Sources:
    - API: refactored_api.py (function_id=96 for weather forecast)
    - Local JSON: json/weather/race_weather_forecast_{year}_{event}_{timestamp}.json
    
    Data Structure:
    {
        "forecast": {
            "days": [
                {
                    "label": "race_minus_2",
                    "date": "2025-10-17",
                    "summary": {
                        "temperature_max": float,
                        "temperature_min": float,
                        "precipitation_sum": float,
                        "cloudcover_mean": float,
                        "windspeed_max": float,
                        "winddirection_cardinal": str,
                        "relativehumidity_mean": float
                    }
                }
            ]
        },
        "historical": {
            "entries": {
                "2024_race_minus_0": {...},
                "2023_race_minus_0": {...}
            }
        },
        "calendar_event": {...},
        "circuit_info": {...}
    }
    """
    
    # CLI function ID
    CLI_FUNCTION = 96
    
    # JSON filename pattern
    WEATHER_PATTERN = "race_weather_forecast_{year}_{event}_*.json"
    
    # Analysis type identifier
    ANALYSIS_TYPE = "weather_timeline"
    
    def __init__(self, year: str, event: str, parent=None):
        """
        Initialize data loader
        
        Args:
            year: Season year (e.g., "2025")
            event: Event name (e.g., "United States")
            parent: Parent component (for signal connections)
        """
        super().__init__(analysis_type=self.ANALYSIS_TYPE, parent=parent)
        
        self.year = str(year)
        self.event = str(event)
        
        # API-ONLY mode: Allow local JSON fallback (for existing files)
        self._allow_local_fallback = True
        self._debug(f"[WEATHER_TIMELINE_LOADER] Initialized: year={year}, event={event}")
    
    def _validate_data_format(self, raw_data: Dict[str, Any]) -> bool:
        """
        Validate data format
        
        Args:
            raw_data: Raw JSON data
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check top-level structure
            if not isinstance(raw_data, dict):
                self._debug("[VALIDATE] ❌ Data is not a dictionary")
                return False
            
            # Must have forecast data
            if "forecast" not in raw_data:
                self._debug("[VALIDATE] ❌ Missing 'forecast' key")
                return False
            
            forecast = raw_data["forecast"]
            if not isinstance(forecast, dict):
                self._debug("[VALIDATE] ❌ 'forecast' is not a dictionary")
                return False
            
            # Must have days array
            if "days" not in forecast:
                self._debug("[VALIDATE] ❌ Missing 'forecast.days' key")
                return False
            
            days = forecast["days"]
            if not isinstance(days, list) or len(days) == 0:
                self._debug("[VALIDATE] ❌ 'forecast.days' is not a valid list")
                return False
            
            # Validate each day
            for i, day in enumerate(days):
                if not isinstance(day, dict):
                    self._debug(f"[VALIDATE] ❌ Day {i} is not a dictionary")
                    return False
                
                required_keys = ["label", "date", "summary"]
                for key in required_keys:
                    if key not in day:
                        self._debug(f"[VALIDATE] ❌ Day {i} missing '{key}' key")
                        return False
                
                # Validate summary
                summary = day["summary"]
                if not isinstance(summary, dict):
                    self._debug(f"[VALIDATE] ❌ Day {i} summary is not a dictionary")
                    return False
            
            # Historical data is optional but should be validated if present
            if "historical" in raw_data:
                historical = raw_data["historical"]
                if not isinstance(historical, dict):
                    self._debug("[VALIDATE] ⚠️ 'historical' is not a dictionary")
                else:
                    if "entries" in historical:
                        entries = historical["entries"]
                        if not isinstance(entries, dict):
                            self._debug("[VALIDATE] ⚠️ 'historical.entries' is not a dictionary")
            
            self._debug("[VALIDATE] ✅ Data format is valid")
            return True
            
        except Exception as e:
            self._debug(f"[VALIDATE] ❌ Validation error: {e}")
            return False
    
    def _transform_data_for_display(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw data for display in widget
        
        Args:
            raw_data: Validated raw JSON data
            
        Returns:
            Transformed data dictionary optimized for WeatherTimelineWidget
        """
        try:
            self._debug("[TRANSFORM] Starting data transformation")
            
            # Extract forecast days
            forecast_days = raw_data.get("forecast", {}).get("days", [])
            
            # Extract historical data
            historical_dict = raw_data.get("historical", {}).get("entries", {})
            
            # Extract calendar event info
            calendar_event = raw_data.get("calendar_event", {})
            event_name = calendar_event.get("EventName", "Unknown Event")
            event_date = calendar_event.get("EventDate", "")
            
            # Extract circuit info
            circuit_info = raw_data.get("circuit_info", {})
            location = circuit_info.get("location", "")
            
            # Build transformed data
            transformed = {
                "forecast_days": forecast_days,
                "historical_entries": historical_dict,
                "event_name": event_name,
                "event_date": event_date,
                "location": location,
                "year": self.year,
                "event": self.event,
            }
            
            self._debug(f"[TRANSFORM] ✅ Transformed data: {len(forecast_days)} forecast days")
            return transformed
            
        except Exception as e:
            self._debug(f"[TRANSFORM] ❌ Transformation error: {e}")
            return {}
    
    def _search_json_files(self, **kwargs) -> List[Path]:
        """
        Search for local JSON files matching criteria
        
        Args:
            **kwargs: Search parameters (year, event, etc.)
            
        Returns:
            List of matching file paths, sorted by modification time (newest first)
        """
        year = kwargs.get("year", self.year)
        event = kwargs.get("event", self.event)
        
        # Normalize event name for filename matching
        event_normalized = event.lower().replace(" ", "_")
        
        # Search pattern: race_weather_forecast_{year}_{event}_*.json
        json_dir = Path("json/weather")
        if not json_dir.exists():
            self._debug(f"[SEARCH] ⚠️ JSON directory does not exist: {json_dir}")
            return []
        
        pattern = f"race_weather_forecast_{year}_*{event_normalized}*.json"
        matches = list(json_dir.glob(pattern))
        
        # Sort by modification time (newest first)
        matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        
        self._debug(f"[SEARCH] Found {len(matches)} JSON files matching pattern: {pattern}")
        return matches
    
    def _generate_data_via_cli(self, **kwargs) -> bool:
        """
        [已禁用] 通過 CLI 生成數據
        
        ⚠️ API-ONLY 模式: 此方法已禁用，系統只允許通過 API 獲取數據
        
        Returns:
            False (always)
        """
        self._debug("⚠️  [API-ONLY] CLI 調用已禁用")
        self._debug("💡 提示: 請使用 API 獲取數據或手動執行 CLI -f96")
        return False
