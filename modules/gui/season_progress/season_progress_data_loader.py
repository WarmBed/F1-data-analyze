#!/usr/bin/env python3
"""
Season Progress Data Loader

Loads championship standings and race calendar data
Follows API-ONLY pattern - prioritizes API, falls back to local JSON

Author: F1T Team
Date: 2025-10-13
Version: 1.0.0
"""

from modules.gui.base.universal_data_loader_base import UniversalDataLoader
from typing import Dict, Any, Optional, List
import json
from pathlib import Path


class SeasonProgressDataLoader(UniversalDataLoader):
    """
    Season Progress Data Loader
    
    Inherits from UniversalDataLoader, implements loading, validation and transformation
    of championship standings and race calendar data
    
    Data Sources:
    - API: refactored_api.py (function_id=97 for standings)
    - Local JSON: json/championship_standings_{year}_R{round}.json
    - Local JSON: json/season_calendar_multi_year_*.json
    
    Data Structure:
    {
        "standings": {
            "drivers": [...],
            "constructors": [...]
        },
        "calendar": {
            "completed": int,
            "remaining": int,
            "next_race": {...}
        },
        "leaders": {
            "driver": {...},
            "constructor": {...}
        }
    }
    """
    
    # CLI function ID
    CLI_FUNCTION = 97
    
    # JSON filename patterns
    STANDINGS_PATTERN = "championship_standings_{year}_R*.json"
    CALENDAR_PATTERN = "season_calendar_multi_year_*.json"
    
    # Analysis type identifier
    ANALYSIS_TYPE = "season_progress"
    
    def __init__(self, year: str, parent=None):
        """
        Initialize data loader
        
        Args:
            year: Season year (e.g., "2025")
            parent: Parent component (for signal connections)
        """
        super().__init__(analysis_type=self.ANALYSIS_TYPE, parent=parent)
        
        self.year = str(year)
        self._calendar_data = None

        # API-ONLY mode: Allow local JSON fallback (for existing files)
        self._allow_local_fallback = True
        self._debug(f"[SEASON_PROGRESS_LOADER] Initialized: year={year}")
    
    def _validate_data_format(self, raw_data: Dict[str, Any]) -> bool:
        """
        Validate data format
        
        Args:
            raw_data: Raw JSON data
            
        Returns:
            bool: Whether validation passed
        """
        if not isinstance(raw_data, dict):
            self._debug("[VALIDATION] Data must be dict")
            return False
        
        if not raw_data.get("success"):
            self._debug(f"[VALIDATION] success=False: {raw_data.get('message')}")
            return False
        
        data = raw_data.get("data")
        if not isinstance(data, dict):
            self._debug("[VALIDATION] Missing data field")
            return False
        
        # Check for drivers or constructors list
        drivers = data.get("drivers", [])
        constructors = data.get("constructors", [])
        
        if not drivers and not constructors:
            self._debug("[VALIDATION] Missing both drivers and constructors")
            return False
        
        self._debug(f"[VALIDATION] Data validation passed ({len(drivers)} drivers, {len(constructors)} constructors)")
        return True
    
    def _build_filename_patterns(self, **kwargs) -> List[str]:
        """
        Build filename search patterns
        
        Args:
            **kwargs: Search parameters (includes year)
            
        Returns:
            List[str]: Filename pattern list
        """
        year = kwargs.get("year", self.year)
        
        # Standings file pattern
        patterns = [
            f"championship_standings_{year}_R*.json",
            f"championship_standings_{year}*.json",
        ]
        
        self._debug(f"[PATTERN] Search patterns: {patterns}")
        return patterns
    
    def _load_calendar_data(self) -> Optional[Dict[str, Any]]:
        """
        Load race calendar data from local JSON
        
        Returns:
            Calendar data or None
        """
        try:
            json_dir = Path("json")
            if not json_dir.exists():
                self._debug("[CALENDAR] JSON directory not found")
                return None
            
            # Search for calendar JSON files
            calendar_files = list(json_dir.glob(self.CALENDAR_PATTERN))
            if not calendar_files:
                self._debug("[CALENDAR] No calendar JSON files found")
                return None
            
            # Use the most recent file
            latest_file = max(calendar_files, key=lambda p: p.stat().st_mtime)
            self._debug(f"[CALENDAR] Loading: {latest_file.name}")
            
            with open(latest_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if not data.get("success"):
                self._debug("[CALENDAR] Calendar data success=False")
                return None
            
            return data.get("data", {})
            
        except Exception as e:
            self._debug(f"[CALENDAR] Error loading calendar: {e}")
            return None
    
    def _transform_data_for_display(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw data for GUI display
        
        Args:
            raw_data: Raw JSON data
            
        Returns:
            Transformed data (suitable for Widget display)
        """
        data = raw_data.get("data", {})
        drivers = data.get("drivers", [])
        constructors = data.get("constructors", [])
        metadata = data.get("metadata", {})
        
        # Get top driver
        top_driver = None
        if drivers:
            top_driver = {
                "full_name": drivers[0].get("driver", {}).get("full_name", "Unknown"),
                "constructor": drivers[0].get("constructors", [{}])[0].get("name", "Unknown") if drivers[0].get("constructors") else "Unknown",
                "points": drivers[0].get("points", 0)
            }
        
        # Get top constructor
        top_constructor = None
        if constructors:
            constructor_info = constructors[0].get("constructor", {})
            top_constructor = {
                "name": constructor_info.get("name", "Unknown").replace(" F1 Team", "").strip(),
                "points": constructors[0].get("points", 0)
            }
        
        # Load calendar data
        if self._calendar_data is None:
            self._calendar_data = self._load_calendar_data()
        
        # Process calendar data
        calendar_summary = {
            "completed": 0,
            "remaining": 0,
            "total": 0,
            "next_race": None
        }
        
        if self._calendar_data:
            year_events = self._calendar_data.get(str(self.year), [])
            if year_events:
                completed = [e for e in year_events if e.get("is_completed")]
                upcoming = [e for e in year_events if not e.get("is_completed")]
                
                calendar_summary["completed"] = len(completed)
                calendar_summary["remaining"] = len(upcoming)
                calendar_summary["total"] = len(year_events)
                
                if upcoming:
                    next_race = upcoming[0]
                    calendar_summary["next_race"] = {
                        "name": next_race.get("event_name", "Unknown"),
                        "date": next_race.get("race_date_local", "")
                    }
        
        self._debug(f"[TRANSFORM] Transformed data: {len(drivers)} drivers, {len(constructors)} constructors")
        
        return {
            "season_year": metadata.get("season_year", int(self.year)),
            "round": metadata.get("resolved_round", 0),
            "leaders": {
                "driver": top_driver,
                "constructor": top_constructor
            },
            "calendar": calendar_summary,
            "metadata": metadata
        }
    
    def load_data(self, force_refresh: bool = False):
        """
        Load season progress data
        
        Args:
            force_refresh: Whether to force refresh (ignore cache)
        """
        params = {
            "year": self.year,
            "function_id": self.CLI_FUNCTION,
            "force_refresh": force_refresh
        }
        
        self._debug(f"[LOAD] Loading season progress data: {params}")
        
        # Call base class load_data() method
        super().load_data(**params)
