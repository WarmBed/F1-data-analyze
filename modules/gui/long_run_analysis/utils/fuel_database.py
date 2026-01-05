#!/usr/bin/env python3
"""
Fuel Database Reader

Reads fuel coefficients from config/fuel_coefficients_database.json
Provides track-specific fuel consumption and effect data.

Author: F1T Team
Date: 2025-12-30
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from core.logger import get_logger

logger = get_logger(__name__)


class FuelDatabase:
    """Fuel coefficients database reader"""
    
    # Default values if database not found
    DEFAULT_FUEL_KG_PER_LAP = 1.70
    DEFAULT_FUEL_EFFECT_COEFFICIENT = 0.030
    DEFAULT_START_FUEL_KG = 85  # FP sessions typically use less fuel
    
    def __init__(self):
        self._data: Optional[Dict[str, Any]] = None
        self._load_database()
    
    def _load_database(self) -> None:
        """Load fuel coefficients database from config file"""
        try:
            config_path = Path(__file__).parent.parent.parent.parent.parent / "config" / "fuel_coefficients_database.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
                logger.info(f"[FUEL_DB] Loaded fuel database from {config_path}")
            else:
                logger.warning(f"[FUEL_DB] Database not found at {config_path}, using defaults")
                self._data = None
        except Exception as e:
            logger.error(f"[FUEL_DB] Failed to load database: {e}")
            self._data = None
    
    def get_track_data(self, track_name: str) -> Dict[str, Any]:
        """
        Get fuel data for a specific track
        
        Args:
            track_name: Track name (e.g., 'Suzuka', 'Japan', 'Japanese Grand Prix')
        
        Returns:
            Dict with fuel_kg_per_lap, fuel_effect_coefficient, start_fuel_kg
        """
        default_result = {
            'fuel_kg_per_lap': self.DEFAULT_FUEL_KG_PER_LAP,
            'fuel_effect_coefficient': self.DEFAULT_FUEL_EFFECT_COEFFICIENT,
            'start_fuel_kg': self.DEFAULT_START_FUEL_KG,
            'source': 'default'
        }
        
        if not self._data or 'circuits' not in self._data:
            return default_result
        
        # Normalize track name for matching
        track_lower = track_name.lower().strip()
        
        # Try direct match
        circuits = self._data.get('circuits', {})
        for circuit_key, circuit_data in circuits.items():
            if circuit_key.lower() == track_lower:
                return self._extract_fuel_data(circuit_data, circuit_key)
            
            # Try matching official name
            official_name = circuit_data.get('official_name', '').lower()
            if track_lower in official_name or official_name in track_lower:
                return self._extract_fuel_data(circuit_data, circuit_key)
        
        # Try fuzzy match (partial)
        for circuit_key, circuit_data in circuits.items():
            if track_lower in circuit_key.lower() or circuit_key.lower() in track_lower:
                return self._extract_fuel_data(circuit_data, circuit_key)
        
        logger.warning(f"[FUEL_DB] Track '{track_name}' not found in database, using defaults")
        return default_result
    
    def _extract_fuel_data(self, circuit_data: Dict[str, Any], circuit_name: str) -> Dict[str, Any]:
        """Extract fuel data from circuit entry"""
        return {
            'fuel_kg_per_lap': circuit_data.get('fuel_kg_per_lap', self.DEFAULT_FUEL_KG_PER_LAP),
            'fuel_effect_coefficient': circuit_data.get('fuel_effect_coefficient', self.DEFAULT_FUEL_EFFECT_COEFFICIENT),
            'start_fuel_kg': self.DEFAULT_START_FUEL_KG,  # FP sessions use less fuel
            'source': f'database:{circuit_name}',
            'official_name': circuit_data.get('official_name', circuit_name),
            'notes': circuit_data.get('notes', '')
        }
    
    def get_all_tracks(self) -> list:
        """Get list of all tracks in database"""
        if not self._data or 'circuits' not in self._data:
            return []
        return list(self._data.get('circuits', {}).keys())
    
    def reload(self) -> None:
        """Reload database from file"""
        self._load_database()


# Module-level singleton instance
_fuel_database_instance: Optional[FuelDatabase] = None


def get_fuel_database() -> FuelDatabase:
    """Get singleton instance of FuelDatabase"""
    global _fuel_database_instance
    if _fuel_database_instance is None:
        _fuel_database_instance = FuelDatabase()
    return _fuel_database_instance
