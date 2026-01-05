#!/usr/bin/env python3
"""
Team Color Helper

Provides team color mapping and driver style utilities for degradation charts.
References the shared_colors module for consistent team colors across the application.

Author: F1T Team
Date: 2025-12-30
"""

from typing import Dict, Tuple, Optional, List
from PyQt5.QtGui import QColor
from core.logger import get_logger

logger = get_logger(__name__)

# Import shared team colors
try:
    from modules.gui.lap_analysis.ideal_lap.shared_colors import TEAM_COLORS, get_team_color
except ImportError:
    logger.warning("[TEAM_COLOR] Failed to import shared_colors, using fallback")
    TEAM_COLORS = {}
    def get_team_color(team: str) -> QColor:
        return QColor(128, 128, 128)


# 2025 Season Team-Driver Mapping (updated per season)
TEAM_DRIVER_MAPPING_2025 = {
    'Red Bull Racing': ['VER', 'LAW'],
    'Red Bull': ['VER', 'LAW'],
    'Ferrari': ['LEC', 'HAM'],
    'McLaren': ['NOR', 'PIA'],
    'Mercedes': ['RUS', 'ANT'],
    'Aston Martin': ['ALO', 'STR'],
    'Alpine': ['GAS', 'DOO'],
    'Williams': ['SAI', 'ALB'],
    'RB': ['TSU', 'HAD'],
    'Racing Bulls': ['TSU', 'HAD'],
    'Kick Sauber': ['HUL', 'BOR'],
    'Sauber': ['HUL', 'BOR'],
}

# Fallback team color mapping (hex strings for matplotlib)
TEAM_COLORS_HEX = {
    'Red Bull Racing': '#3671C6',
    'Red Bull': '#3671C6',
    'Ferrari': '#E80020',
    'McLaren': '#FF8000',
    'Mercedes': '#27F4D2',
    'Aston Martin': '#229971',
    'Alpine': '#0093CC',
    'Williams': '#64C4FF',
    'RB': '#6692FF',
    'Racing Bulls': '#6692FF',
    'Kick Sauber': '#52E252',
    'Sauber': '#52E252',
    'Haas F1 Team': '#B6BABD',
    'Haas': '#B6BABD',
}


class TeamColorHelper:
    """Helper class for team colors and driver styling"""
    
    def __init__(self, dynamic_team_mapping: Optional[Dict[str, Dict]] = None):
        """
        Initialize with optional dynamic team mapping from API
        
        Args:
            dynamic_team_mapping: Dict mapping driver codes to team info
                                  Format: {'VER': {'team': 'Red Bull Racing', ...}}
        """
        self._dynamic_mapping = dynamic_team_mapping or {}
    
    def set_dynamic_mapping(self, mapping: Dict[str, Dict]) -> None:
        """Update dynamic team mapping from API data"""
        self._dynamic_mapping = mapping or {}
        logger.info(f"[TEAM_COLOR] Updated dynamic mapping with {len(self._dynamic_mapping)} drivers")
    
    def get_driver_team(self, driver_code: str) -> str:
        """
        Get team name for a driver
        
        Args:
            driver_code: 3-letter driver code (e.g., 'VER')
        
        Returns:
            Team name or 'Unknown'
        """
        # Try dynamic mapping first (from API)
        if driver_code in self._dynamic_mapping:
            team_info = self._dynamic_mapping[driver_code]
            if isinstance(team_info, dict):
                return team_info.get('team', team_info.get('team_name', 'Unknown'))
            return str(team_info)
        
        # Fallback to static mapping
        for team, drivers in TEAM_DRIVER_MAPPING_2025.items():
            if driver_code in drivers:
                return team
        
        return 'Unknown'
    
    def get_team_drivers(self, team_name: str) -> List[str]:
        """
        Get all drivers for a team
        
        Args:
            team_name: Team name
        
        Returns:
            List of driver codes, first driver is team lead
        """
        # Try from dynamic mapping
        team_drivers = []
        for driver, info in self._dynamic_mapping.items():
            if isinstance(info, dict):
                driver_team = info.get('team', info.get('team_name', ''))
            else:
                driver_team = str(info)
            
            if team_name.lower() in driver_team.lower() or driver_team.lower() in team_name.lower():
                team_drivers.append(driver)
        
        if team_drivers:
            return team_drivers
        
        # Fallback to static mapping
        for team, drivers in TEAM_DRIVER_MAPPING_2025.items():
            if team_name.lower() in team.lower() or team.lower() in team_name.lower():
                return list(drivers)
        
        return []
    
    def is_second_driver(self, driver_code: str, team_name: Optional[str] = None) -> bool:
        """
        Check if driver is the second driver on their team
        
        Args:
            driver_code: 3-letter driver code
            team_name: Optional team name (will be looked up if not provided)
        
        Returns:
            True if second driver (should use dashed line)
        """
        if team_name is None:
            team_name = self.get_driver_team(driver_code)
        
        team_drivers = self.get_team_drivers(team_name)
        if len(team_drivers) >= 2:
            return driver_code == team_drivers[1]
        
        return False
    
    def get_driver_color_hex(self, driver_code: str) -> str:
        """
        Get team color as hex string for matplotlib
        
        Args:
            driver_code: 3-letter driver code
        
        Returns:
            Hex color string (e.g., '#3671C6')
        """
        team_name = self.get_driver_team(driver_code)
        return TEAM_COLORS_HEX.get(team_name, '#808080')
    
    def get_driver_color_qcolor(self, driver_code: str) -> QColor:
        """
        Get team color as QColor for PyQt
        
        Args:
            driver_code: 3-letter driver code
        
        Returns:
            QColor object
        """
        team_name = self.get_driver_team(driver_code)
        return get_team_color(team_name)
    
    def get_driver_style(self, driver_code: str) -> Tuple[str, str]:
        """
        Get driver color and line style for charts
        
        Args:
            driver_code: 3-letter driver code
        
        Returns:
            Tuple of (color_hex, linestyle)
            - linestyle: '-' for first driver, '--' for second driver
        """
        team_name = self.get_driver_team(driver_code)
        color = self.get_driver_color_hex(driver_code)
        linestyle = '--' if self.is_second_driver(driver_code, team_name) else '-'
        
        return color, linestyle
    
    def get_all_driver_styles(self, driver_codes: List[str]) -> Dict[str, Tuple[str, str]]:
        """
        Get styles for multiple drivers
        
        Args:
            driver_codes: List of driver codes
        
        Returns:
            Dict mapping driver code to (color, linestyle) tuple
        """
        return {driver: self.get_driver_style(driver) for driver in driver_codes}


# Module-level singleton instance
_team_color_helper_instance: Optional[TeamColorHelper] = None


def get_team_color_helper(dynamic_mapping: Optional[Dict] = None) -> TeamColorHelper:
    """Get singleton instance of TeamColorHelper"""
    global _team_color_helper_instance
    if _team_color_helper_instance is None:
        _team_color_helper_instance = TeamColorHelper(dynamic_mapping)
    elif dynamic_mapping:
        _team_color_helper_instance.set_dynamic_mapping(dynamic_mapping)
    return _team_color_helper_instance
