#!/usr/bin/env python3
"""
Config Loader

Loads configuration databases for Race Strategy Simulator:
- Pit Loss Database (GREEN/SC/VSC)
- Fuel Coefficients Database
- Tire Degradation Database

Author: F1T Team
Date: 2025-12-30
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TrackConfig:
    """Track-specific configuration data"""
    name: str
    official_name: str
    
    # Pit Loss
    pit_loss_green: float = 22.0
    pit_loss_sc: float = 11.0
    pit_loss_vsc: float = 8.0
    
    # Fuel
    fuel_kg_per_lap: float = 1.70
    fuel_effect_coefficient: float = 0.030
    start_fuel_kg: float = 110.0
    typical_race_laps: int = 53
    
    # Base lap time (seconds)
    base_lap_time: float = 90.0
    
    # Track length (km)
    track_length_km: float = 5.0
    
    # Degradation rates (s/lap) - trained from real data
    deg_soft: float = 0.120
    deg_medium: float = 0.080
    deg_hard: float = 0.045
    
    # Degradation acceleration (s/lap²) - for time-varying model
    deg_accel_soft: float = 0.003
    deg_accel_medium: float = 0.002
    deg_accel_hard: float = 0.001
    
    # Optimal stint lengths from training
    optimal_stint_soft: int = 18
    optimal_stint_medium: int = 28
    optimal_stint_hard: int = 40
    
    # Traffic simulation parameters (based on overtaking_difficulty)
    # Higher overtaking_difficulty = slower traffic decay, higher loss per position
    overtaking_difficulty: float = 0.50  # 0.0 (easy) to 1.0 (impossible)
    overtaking_zones: int = 2  # Number of DRS/overtaking zones
    traffic_decay_rate: float = 0.05  # Traffic effect decay per lap
    traffic_loss_per_position: float = 0.15  # Seconds lost per position behind
    first_lap_loss: float = 5.0  # First lap time loss (formation, chaos)
    
    # Training info
    trained_from_data: bool = False
    training_method: str = ""


class ConfigLoader:
    """
    Loads and provides access to configuration databases.
    
    Usage:
        loader = ConfigLoader()
        track = loader.get_track_config("Suzuka")
        print(track.pit_loss_green)  # 24.0
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize ConfigLoader.
        
        Args:
            config_path: Path to config/ directory. 
                         If None, auto-detect from project root.
        """
        if config_path is None:
            # Auto-detect: go up from this file to find config/
            current = Path(__file__).resolve()
            # strategy_simulator/core/ -> strategy_simulator/ -> project_root/
            project_root = current.parent.parent.parent
            config_path = project_root / "config"
        
        self.config_path = Path(config_path)
        self.project_root = self.config_path.parent
        
        # Load databases
        self._pit_loss_db: Dict[str, Any] = {}
        self._fuel_db: Dict[str, Any] = {}
        self._tire_db: Dict[str, Any] = {}
        self._track_features_db: Dict[str, Any] = {}  # Track features (overtaking, etc.)
        self._overtaking_difficulty_db: Dict[str, Any] = {}  # Detailed overtaking stats from race data
        
        # Track name alias mapping (normalized -> canonical)
        self._track_aliases: Dict[str, str] = {}
        
        # Base lap times (from historical data or estimates)
        self._base_lap_times: Dict[str, float] = {
            "Bahrain": 92.0,
            "Jeddah": 89.0,
            "Melbourne": 79.0,
            "Suzuka": 91.5,
            "Shanghai": 96.0,
            "Miami": 88.0,
            "Imola": 76.0,
            "Monaco": 72.0,
            "Montreal": 75.0,
            "Barcelona": 78.0,
            "Spielberg": 66.0,
            "Silverstone": 88.0,
            "Hungaroring": 77.0,
            "Spa": 105.0,
            "Zandvoort": 72.0,
            "Monza": 82.0,
            "Baku": 104.0,
            "Singapore": 99.0,
            "Austin": 96.0,
            "Mexico City": 78.0,
            "Interlagos": 72.0,
            "Las Vegas": 95.0,
            "Lusail": 87.0,
            "Yas Marina": 85.0,
        }
        
        self._load_databases()
    
    def _normalize_track_name(self, name: str) -> str:
        """
        Normalize track name by replacing underscores with spaces.
        
        Args:
            name: Original track name (e.g., "Las_Vegas")
        
        Returns:
            Normalized name (e.g., "Las Vegas")
        """
        return name.replace("_", " ")
    
    def _load_databases(self) -> None:
        """Load all configuration databases."""
        # Pit Loss Database
        pit_loss_file = self.config_path / "pit_loss_database.json"
        if pit_loss_file.exists():
            with open(pit_loss_file, 'r', encoding='utf-8') as f:
                self._pit_loss_db = json.load(f)
                # Build aliases from pit_loss_database
                if 'aliases' in self._pit_loss_db:
                    self._track_aliases = self._pit_loss_db['aliases'].copy()
        
        # Add additional aliases for tire_degradation_database inconsistencies
        # tire_db uses: "Budapest", "Mexico", "Las_Vegas", "Yas_Marina"
        # pit_loss_db uses: "Hungaroring", "Mexico City", "Las Vegas", "Yas Marina"
        self._track_aliases.update({
            "Budapest": "Hungaroring",
            "Mexico": "Mexico City",
            "Las Vegas": "Las Vegas",  # canonical
            "Yas Marina": "Yas Marina",  # canonical
            "Sao Paulo": "Interlagos",
            "São Paulo": "Interlagos",
            "Brazil": "Interlagos",
            "Austria": "Spielberg",
            "Red Bull Ring": "Spielberg",
            "Spa-Francorchamps": "Spa",
            "Spa Francorchamps": "Spa",
        })
        
        # Track name to Race name mapping (for API calls)
        # Strategy Simulator uses track names, API/FastF1 uses race names
        self._track_to_race_name: Dict[str, str] = {
            "Yas Marina": "Abu Dhabi",
            "Hungaroring": "Hungary",
            "Spielberg": "Austria",
            "Interlagos": "Brazil",
            "Spa": "Belgium",
            "Monza": "Italy",
            "Silverstone": "Great Britain",
            "Zandvoort": "Netherlands",
            "Shanghai": "China",
            "Baku": "Azerbaijan",
            "Imola": "Emilia Romagna",
            "Marina Bay": "Singapore",
            "Suzuka": "Japan",
            "Jeddah": "Saudi Arabia",
            "Sakhir": "Bahrain",
            "Montreal": "Canada",
            "Albert Park": "Australia",
            "COTA": "United States",
            "Austin": "United States",
            "Mexico City": "Mexico",
            "Las Vegas": "Las Vegas",
            "Miami": "Miami",
            "Monaco": "Monaco",
            "Barcelona": "Spain",
            "Lusail": "Qatar",
        }
        
        # Fuel Coefficients Database
        fuel_file = self.config_path / "fuel_coefficients_database.json"
        if fuel_file.exists():
            with open(fuel_file, 'r', encoding='utf-8') as f:
                self._fuel_db = json.load(f)
        
        # Tire Degradation Database
        tire_file = self.config_path / "tire_degradation_database.json"
        if tire_file.exists():
            with open(tire_file, 'r', encoding='utf-8') as f:
                self._tire_db = json.load(f)
        
        # Track Features Database (for overtaking difficulty, etc.)
        track_features_file = self.config_path / "track_features_database.json"
        if track_features_file.exists():
            with open(track_features_file, 'r', encoding='utf-8') as f:
                self._track_features_db = json.load(f)
        
        # Track Overtaking Difficulty Database (detailed statistics from race data)
        # This provides more accurate difficulty indices based on actual 2023-2024 races
        overtaking_file = self.project_root / "json" / "track_overtaking_difficulty.json"
        if overtaking_file.exists():
            with open(overtaking_file, 'r', encoding='utf-8') as f:
                self._overtaking_difficulty_db = json.load(f)
        else:
            self._overtaking_difficulty_db = {}
        
        # Pit Strategy Database (contains accurate base_lap_time from training)
        pit_strategy_file = self.config_path / "pit_strategy_database.json"
        if pit_strategy_file.exists():
            with open(pit_strategy_file, 'r', encoding='utf-8') as f:
                pit_strategy_db = json.load(f)
                # Update base lap times from pit_strategy_database
                circuits_data = pit_strategy_db.get('circuits', {})
                for track_key, track_data in circuits_data.items():
                    base_time = track_data.get('base_lap_time_seconds')
                    if base_time:
                        # Normalize track name (replace underscore with space)
                        normalized_name = track_key.replace('_', ' ')
                        self._base_lap_times[normalized_name] = base_time
    
    def _calculate_traffic_params(self, overtaking_difficulty: float, overtaking_zones: int) -> dict:
        """
        Calculate traffic simulation parameters based on track characteristics.
        
        Formula derivation:
        - overtaking_difficulty: 0.0 (easy to overtake) to 1.0 (nearly impossible)
        - Higher difficulty = slower decay (cars stuck longer) + more loss per position
        
        Args:
            overtaking_difficulty: 0.0 to 1.0 scale
            overtaking_zones: Number of DRS/overtaking opportunities
            
        Returns:
            dict with traffic_decay_rate and traffic_loss_per_position
        """
        # traffic_decay_rate: how fast traffic effect diminishes per lap
        # - Monaco (diff=0.95): decay=0.02 (slow, stuck for ~50 laps)
        # - Monza (diff=0.30): decay=0.10 (fast, cleared in ~10 laps)
        # Linear mapping: decay = 0.12 - 0.10 * difficulty
        decay_rate = 0.12 - 0.10 * overtaking_difficulty
        
        # Adjust by overtaking zones (more zones = faster escape)
        zone_factor = 1.0 + 0.02 * overtaking_zones
        decay_rate = min(0.15, decay_rate * zone_factor)
        
        # traffic_loss_per_position: seconds lost per grid position behind
        # - Monaco (narrow): 0.30 s/position (hard to follow closely)
        # - Monza (wide): 0.08 s/position (easy to slipstream)
        # Linear mapping: loss = 0.08 + 0.22 * difficulty
        loss_per_pos = 0.08 + 0.22 * overtaking_difficulty
        
        # First lap loss: more chaotic on street circuits
        first_lap = 4.0 + 4.0 * overtaking_difficulty  # 4-8 seconds
        
        return {
            'traffic_decay_rate': round(decay_rate, 4),
            'traffic_loss_per_position': round(loss_per_pos, 3),
            'first_lap_loss': round(first_lap, 1),
        }
    
    def _resolve_track_name(self, track_name: str) -> str:
        """
        Resolve track name to canonical form using aliases.
        
        Args:
            track_name: Input track name
        
        Returns:
            Canonical track name
        """
        # First normalize (underscore to space)
        normalized = self._normalize_track_name(track_name)
        
        # Check if it's an alias
        if normalized in self._track_aliases:
            return self._track_aliases[normalized]
        
        return normalized
    
    def get_track_list(self) -> list:
        """
        Get list of available tracks (normalized, no duplicates).
        
        Returns:
            Sorted list of unique track names (canonical names only)
        """
        tracks = set()
        
        # Collect from all databases (normalize and resolve names)
        if 'circuits' in self._pit_loss_db:
            for name in self._pit_loss_db['circuits'].keys():
                resolved = self._resolve_track_name(name)
                tracks.add(resolved)
        if 'circuits' in self._fuel_db:
            for name in self._fuel_db['circuits'].keys():
                resolved = self._resolve_track_name(name)
                tracks.add(resolved)
        if 'circuits' in self._tire_db:
            for name in self._tire_db['circuits'].keys():
                resolved = self._resolve_track_name(name)
                tracks.add(resolved)
        
        return sorted(list(tracks))
    
    def get_race_name(self, track_name: str) -> str:
        """
        Convert track name to race name for API calls.
        
        Strategy Simulator uses track names (e.g., "Yas Marina")
        but API/FastF1 uses race names (e.g., "Abu Dhabi").
        
        Args:
            track_name: Track name from combo box
            
        Returns:
            Race name suitable for API calls
        """
        # Direct mapping
        if track_name in self._track_to_race_name:
            return self._track_to_race_name[track_name]
        
        # If no mapping, return as-is (might already be a race name)
        return track_name
    
    def _get_overtaking_stats(self, track_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed overtaking statistics for a track from race data.
        
        This uses the track_overtaking_difficulty.json which contains actual
        statistics from 2023-2024 races (avg_overtakes, overtakes_per_lap, etc.)
        
        Args:
            track_name: Track name (e.g., "Suzuka", "Monaco")
        
        Returns:
            Dict with difficulty_index, drs_zones, avg_overtakes, etc.
            None if track not found
        """
        if not self._overtaking_difficulty_db:
            return None
        
        tracks_data = self._overtaking_difficulty_db.get('tracks', {})
        
        # Build name variations to try
        names_to_try = [
            track_name,
            track_name.replace(" ", "_"),  # "Las Vegas" -> "Las_Vegas"
        ]
        
        # Add common aliases
        overtaking_aliases = {
            "Suzuka": "Japanese",
            "Japan": "Japanese",
            "Hungaroring": "Hungarian",
            "Hungary": "Hungarian",
            "Interlagos": "São_Paulo",
            "Brazil": "São_Paulo",
            "Sao Paulo": "São_Paulo",
            "Singapore": "Singapore",
            "Melbourne": "Australian",
            "Australia": "Australian",
            "Montreal": "Canadian",
            "Canada": "Canadian",
            "Spa": "Belgian",
            "Spa-Francorchamps": "Belgian",
            "Spielberg": "Austrian",
            "Austria": "Austrian",
            "Red Bull Ring": "Austrian",
            "Jeddah": "Saudi_Arabian",
            "Saudi Arabia": "Saudi_Arabian",
            "Monza": "Italian",
            "Italy": "Italian",
            "Silverstone": "British",
            "UK": "British",
            "Great Britain": "British",
            "Zandvoort": "Netherlands",
            "Netherlands": "Netherlands",
            "Shanghai": "Chinese",
            "China": "Chinese",
            "Abu Dhabi": "Abu_Dhabi",
            "Yas Marina": "Abu_Dhabi",
            "Miami": "Miami",
            "Imola": "Emilia_Romagna",
            "Emilia Romagna": "Emilia_Romagna",
            "Baku": "Azerbaijan",
            "Las Vegas": "Las_Vegas",
            "Mexico City": "Mexico_City",
            "Austin": "United_States",
            "COTA": "United_States",
        }
        
        if track_name in overtaking_aliases:
            names_to_try.append(overtaking_aliases[track_name])
        
        # Try to find data
        for name in names_to_try:
            if name in tracks_data:
                return tracks_data[name]
        
        return None
    
    def get_track_config(self, track_name: str) -> TrackConfig:
        """
        Get complete configuration for a track.
        
        Args:
            track_name: Track name (e.g., "Suzuka", "Monaco", "Las Vegas")
        
        Returns:
            TrackConfig with all parameters
        """
        # Normalize and resolve the track name
        normalized_name = self._normalize_track_name(track_name)
        resolved_name = self._resolve_track_name(normalized_name)
        
        config = TrackConfig(name=resolved_name, official_name=resolved_name)
        
        # Also try with underscore version for tire database
        underscore_name = resolved_name.replace(" ", "_")
        
        # Load Pit Loss
        pit_circuits = self._pit_loss_db.get('circuits', {})
        if resolved_name in pit_circuits:
            pit_data = pit_circuits[resolved_name]
            config.official_name = pit_data.get('official_name', resolved_name)
            pit_times = pit_data.get('pit_loss_times', {})
            config.pit_loss_green = pit_times.get('green_flag', 22.0)
            config.pit_loss_sc = pit_times.get('safety_car', 11.0)
            config.pit_loss_vsc = pit_times.get('virtual_safety_car', 8.0)
        
        # Load Fuel
        fuel_circuits = self._fuel_db.get('circuits', {})
        if resolved_name in fuel_circuits:
            fuel_data = fuel_circuits[resolved_name]
            config.fuel_kg_per_lap = fuel_data.get('fuel_kg_per_lap', 1.70)
            config.fuel_effect_coefficient = fuel_data.get('fuel_effect_coefficient', 0.030)
            config.start_fuel_kg = fuel_data.get('start_fuel_kg', 110.0)
            config.typical_race_laps = fuel_data.get('typical_race_laps', 53)
            config.track_length_km = fuel_data.get('track_length_km', 5.0)
        
        # Load Tire Degradation (try multiple name variations)
        tire_circuits = self._tire_db.get('circuits', {})
        tire_data = None
        
        # Build list of possible names to try
        names_to_try = [resolved_name, underscore_name]
        
        # Add reverse alias lookups (canonical -> possible tire_db name)
        reverse_aliases = {
            "Hungaroring": ["Budapest", "Hungary"],
            "Mexico City": ["Mexico"],
            "Interlagos": ["Sao Paulo", "São Paulo", "Brazil"],
            "Spielberg": ["Austria", "Red Bull Ring"],
        }
        if resolved_name in reverse_aliases:
            names_to_try.extend(reverse_aliases[resolved_name])
        
        # Try to find tire data
        for name in names_to_try:
            if name in tire_circuits:
                tire_data = tire_circuits[name]
                break
            # Also try underscore version
            underscore_ver = name.replace(" ", "_")
            if underscore_ver in tire_circuits:
                tire_data = tire_circuits[underscore_ver]
                break
        
        if tire_data:
            # New format: trained data with base_degradation
            base_deg = tire_data.get('base_degradation', {})
            deg_accel = tire_data.get('degradation_acceleration', {})
            optimal_stint = tire_data.get('optimal_stint_length', {})
            
            # Load degradation rates (s/lap)
            if 'SOFT' in base_deg:
                config.deg_soft = base_deg['SOFT']
            if 'MEDIUM' in base_deg:
                config.deg_medium = base_deg['MEDIUM']
            if 'HARD' in base_deg:
                config.deg_hard = base_deg['HARD']
            
            # Load degradation acceleration (s/lap²)
            if 'SOFT' in deg_accel:
                config.deg_accel_soft = deg_accel['SOFT']
            if 'MEDIUM' in deg_accel:
                config.deg_accel_medium = deg_accel['MEDIUM']
            if 'HARD' in deg_accel:
                config.deg_accel_hard = deg_accel['HARD']
            
            # Load optimal stint lengths
            if 'SOFT' in optimal_stint:
                config.optimal_stint_soft = optimal_stint['SOFT']
            if 'MEDIUM' in optimal_stint:
                config.optimal_stint_medium = optimal_stint['MEDIUM']
            if 'HARD' in optimal_stint:
                config.optimal_stint_hard = optimal_stint['HARD']
            
            # Training info
            config.trained_from_data = tire_data.get('trained_from_data', False)
            config.training_method = tire_data.get('training_method', '')
            
            # Also load race laps from tire database if available
            if 'typical_race_laps' in tire_data:
                config.typical_race_laps = tire_data['typical_race_laps']
            
            # Fallback: old format with compounds dict
            compounds = tire_data.get('compounds', {})
            if compounds and not base_deg:
                if 'SOFT' in compounds:
                    config.deg_soft = compounds['SOFT'].get('degradation_rate', 0.120)
                if 'MEDIUM' in compounds:
                    config.deg_medium = compounds['MEDIUM'].get('degradation_rate', 0.080)
                if 'HARD' in compounds:
                    config.deg_hard = compounds['HARD'].get('degradation_rate', 0.045)
        
        # Load base lap time from internal database
        if resolved_name in self._base_lap_times:
            config.base_lap_time = self._base_lap_times[resolved_name]
        else:
            # Estimate based on track length if available
            config.base_lap_time = config.track_length_km * 15.0  # ~15s per km as estimate
        
        # Load Track Features (overtaking difficulty, traffic parameters)
        track_features = self._track_features_db.get(resolved_name)
        if not track_features:
            # Try alternative names for track features
            features_aliases = {
                "Spa": "Spa-Francorchamps",
            }
            alt_name = features_aliases.get(resolved_name)
            if alt_name:
                track_features = self._track_features_db.get(alt_name)
        
        # First, try to load overtaking difficulty from detailed statistics database
        # This provides more accurate values based on actual 2023-2024 race data
        overtaking_stats = self._get_overtaking_stats(resolved_name)
        
        if track_features:
            characteristics = track_features.get('characteristics', {})
            historical = track_features.get('historical_patterns', {})
            
            # Prefer detailed overtaking stats if available
            if overtaking_stats:
                config.overtaking_difficulty = overtaking_stats.get('difficulty_index', 0.5)
                config.overtaking_zones = overtaking_stats.get('drs_zones', 2)
            else:
                # Fallback to track features database
                config.overtaking_difficulty = characteristics.get('overtaking_difficulty', 0.5)
                config.overtaking_zones = historical.get('overtaking_zones', 2)
            
            # Calculate traffic parameters based on track characteristics
            traffic_params = self._calculate_traffic_params(
                config.overtaking_difficulty,
                config.overtaking_zones
            )
            config.traffic_decay_rate = traffic_params['traffic_decay_rate']
            config.traffic_loss_per_position = traffic_params['traffic_loss_per_position']
            config.first_lap_loss = traffic_params['first_lap_loss']
        else:
            # No track features found, try to use overtaking stats from race data
            if overtaking_stats:
                config.overtaking_difficulty = overtaking_stats.get('difficulty_index', 0.5)
                config.overtaking_zones = overtaking_stats.get('drs_zones', 2)
            else:
                # Default values (medium difficulty track)
                config.overtaking_difficulty = 0.50
                config.overtaking_zones = 2
            
            # Calculate traffic parameters
            traffic_params = self._calculate_traffic_params(
                config.overtaking_difficulty,
                config.overtaking_zones
            )
            config.traffic_decay_rate = traffic_params['traffic_decay_rate']
            config.traffic_loss_per_position = traffic_params['traffic_loss_per_position']
            config.first_lap_loss = traffic_params['first_lap_loss']
        
        return config
    
    def get_race_calendar(self, year: int = 2025) -> list:
        """Get list of races for a given year (simplified)."""
        # For now, return tracks from database
        return self.get_track_list()


# Also export from data module
__all__ = ['ConfigLoader', 'TrackConfig']
