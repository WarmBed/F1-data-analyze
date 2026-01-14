"""
Strategy Prediction Core
========================

共用的策略預測核心模組，供 Driver Strategy 和 Chase Strategy 使用。
確保兩個模組使用完全一致的預測邏輯。

Features:
- XGBoost v2.0 策略係數 (優先)
- 輪胎衰退二次方程式模型
- 燃油效果計算
- 配方抓地力優勢

Author: F1T Team
Date: 2026-01-12
"""

from typing import Dict, Any, Optional, Tuple
import json
from pathlib import Path

from core.logger import get_logger

logger = get_logger(__name__)

# =============================================================================
# Constants
# =============================================================================

# 預設衰退值
DEFAULT_BASE_DEGRADATION = {
    'SOFT': 0.08,
    'MEDIUM': 0.05,
    'HARD': 0.03,
    'INTERMEDIATE': 0.06,
    'WET': 0.04
}

DEFAULT_DEGRADATION_ACCELERATION = {
    'SOFT': 0.003,
    'MEDIUM': 0.002,
    'HARD': 0.001,
    'INTERMEDIATE': 0.002,
    'WET': 0.0015
}

# 配方抓地力優勢 (相對於 HARD)
COMPOUND_GRIP_ADVANTAGE = {
    'SOFT': -0.5,      # 比 HARD 快 0.5 秒/圈
    'MEDIUM': -0.25,   # 比 HARD 快 0.25 秒/圈
    'HARD': 0.0,       # 基準
    'INTERMEDIATE': -0.3,
    'WET': -0.2
}

# 預設燃油係數 (秒/圈)
DEFAULT_FUEL_EFFECT = -0.03

# 賽事名稱到賽道鍵值的映射 (用於 strategy_coefficients_xgboost.json)
RACE_TO_CIRCUIT_MAP = {
    'Qatar': 'Qatar_Grand_Prix',
    'Abu Dhabi': 'Abu_Dhabi_Grand_Prix',
    'Abu_Dhabi': 'Abu_Dhabi_Grand_Prix',
    'Saudi Arabia': 'Saudi_Arabian_Grand_Prix',
    'Australia': 'Australian_Grand_Prix',
    'Japan': 'Japanese_Grand_Prix',
    'China': 'Chinese_Grand_Prix',
    'Emilia Romagna': 'Emilia_Romagna_Grand_Prix',
    'Canada': 'Canadian_Grand_Prix',
    'Spain': 'Spanish_Grand_Prix',
    'Austria': 'Austrian_Grand_Prix',
    'Great Britain': 'British_Grand_Prix',
    'Britain': 'British_Grand_Prix',
    'Hungary': 'Hungarian_Grand_Prix',
    'Belgium': 'Belgian_Grand_Prix',
    'Netherlands': 'Dutch_Grand_Prix',
    'Italy': 'Italian_Grand_Prix',
    'Azerbaijan': 'Azerbaijan_Grand_Prix',
    'United States': 'United_States_Grand_Prix',
    'USA': 'United_States_Grand_Prix',
    'Mexico': 'Mexico_City_Grand_Prix',
    'Brazil': 'São_Paulo_Grand_Prix',
    'Las Vegas': 'Las_Vegas_Grand_Prix',
    'Monaco': 'Monaco_Grand_Prix',
    'Miami': 'Miami_Grand_Prix',
    'Singapore': 'Singapore_Grand_Prix',
    'Bahrain': 'Bahrain_Grand_Prix',
}

# 國家名稱到城市/賽道名稱的映射 (用於 pit_loss_database.json)
RACE_TO_CITY_MAP = {
    'Qatar': 'Lusail',
    'Abu Dhabi': 'Yas Marina',
    'Abu_Dhabi': 'Yas Marina',
    'Saudi Arabia': 'Jeddah',
    'Australia': 'Melbourne',
    'Japan': 'Suzuka',
    'China': 'Shanghai',
    'Emilia Romagna': 'Imola',
    'Canada': 'Montreal',
    'Spain': 'Barcelona',
    'Austria': 'Spielberg',
    'Great Britain': 'Silverstone',
    'Britain': 'Silverstone',
    'Hungary': 'Hungaroring',
    'Belgium': 'Spa',
    'Netherlands': 'Zandvoort',
    'Italy': 'Monza',
    'Azerbaijan': 'Baku',
    'United States': 'Austin',
    'USA': 'Austin',
    'Mexico': 'Mexico City',
    'Brazil': 'Interlagos',
    'Las Vegas': 'Las Vegas',
    'Monaco': 'Monaco',
    'Miami': 'Miami',
    'Singapore': 'Singapore',
    'Bahrain': 'Bahrain',
}


# =============================================================================
# Coefficient Loaders
# =============================================================================

_strategy_coefficients_cache: Optional[Dict] = None
_tyre_deg_database_cache: Optional[Dict] = None
_pit_loss_database_cache: Optional[Dict] = None


def _get_config_path() -> Path:
    """Get the config directory path."""
    return Path(__file__).parent.parent.parent.parent.parent / "config"


def load_strategy_coefficients() -> Dict[str, Any]:
    """
    Load XGBoost v2.0 strategy coefficients.
    
    Returns:
        Strategy coefficients dictionary
    """
    global _strategy_coefficients_cache
    
    if _strategy_coefficients_cache is not None:
        return _strategy_coefficients_cache
    
    try:
        coeff_path = _get_config_path() / "strategy_coefficients_xgboost.json"
        with open(coeff_path, 'r', encoding='utf-8') as f:
            _strategy_coefficients_cache = json.load(f)
            logger.debug("Loaded XGBoost strategy coefficients: %d circuits",
                        len(_strategy_coefficients_cache.get('circuits', {})))
            return _strategy_coefficients_cache
    except Exception as e:
        logger.warning("Unable to load strategy_coefficients_xgboost.json: %s", e)
        _strategy_coefficients_cache = {}
        return {}


def load_tyre_degradation_database() -> Dict[str, Any]:
    """
    Load legacy tyre degradation database (fallback).
    
    Returns:
        Tyre degradation database dictionary
    """
    global _tyre_deg_database_cache
    
    if _tyre_deg_database_cache is not None:
        return _tyre_deg_database_cache
    
    try:
        db_path = _get_config_path() / "tire_degradation_database.json"
        with open(db_path, 'r', encoding='utf-8') as f:
            _tyre_deg_database_cache = json.load(f)
            return _tyre_deg_database_cache
    except Exception as e:
        logger.warning("Unable to load tire_degradation_database.json: %s", e)
        _tyre_deg_database_cache = {}
        return {}


def load_pit_loss_database() -> Dict[str, Any]:
    """
    Load pit loss database with team offsets.
    
    Returns:
        Pit loss database dictionary
    """
    global _pit_loss_database_cache
    
    if _pit_loss_database_cache is not None:
        return _pit_loss_database_cache
    
    try:
        db_path = _get_config_path() / "pit_loss_database.json"
        with open(db_path, 'r', encoding='utf-8') as f:
            _pit_loss_database_cache = json.load(f)
            return _pit_loss_database_cache
    except Exception as e:
        logger.warning("Unable to load pit_loss_database.json: %s", e)
        _pit_loss_database_cache = {}
        return {}


def clear_caches():
    """Clear all cached data (useful for testing)."""
    global _strategy_coefficients_cache, _tyre_deg_database_cache, _pit_loss_database_cache
    _strategy_coefficients_cache = None
    _tyre_deg_database_cache = None
    _pit_loss_database_cache = None


# =============================================================================
# Coefficient Getters
# =============================================================================

def get_strategy_coefficients(circuit: str, compound: str) -> Dict[str, Any]:
    """
    Get strategy coefficients for a specific circuit and compound.
    
    Prioritizes XGBoost v2.0 coefficients, falls back to legacy database.
    
    Args:
        circuit: Circuit name (e.g., "Japan", "Monaco", "Japanese_Grand_Prix")
        compound: Tyre compound (SOFT, MEDIUM, HARD)
        
    Returns:
        Dictionary with keys:
        - base_rate: Base degradation rate (s/lap)
        - acceleration: Degradation acceleration (s/lap^2)
        - fuel_effect: Fuel effect coefficient (s/lap, negative = faster)
        - is_default: True if using default values
    """
    # Normalize compound
    compound_key = compound.upper()
    if compound_key in ['S']:
        compound_key = 'SOFT'
    elif compound_key in ['M']:
        compound_key = 'MEDIUM'
    elif compound_key in ['H']:
        compound_key = 'HARD'
    
    # Map circuit name to coefficient key
    circuit_key = RACE_TO_CIRCUIT_MAP.get(circuit, circuit)
    if not circuit_key.endswith('_Grand_Prix'):
        circuit_key = circuit.replace(' ', '_') + '_Grand_Prix'
    
    # Try XGBoost coefficients first
    xgb_coeffs = load_strategy_coefficients()
    circuits_data = xgb_coeffs.get('circuits', {})
    
    if circuit_key in circuits_data:
        circuit_data = circuits_data[circuit_key]
        compounds_data = circuit_data.get('compounds', {})
        
        if compound_key in compounds_data:
            comp_data = compounds_data[compound_key]
            return {
                'base_rate': comp_data.get('base_rate', DEFAULT_BASE_DEGRADATION.get(compound_key, 0.05)),
                'acceleration': comp_data.get('acceleration', DEFAULT_DEGRADATION_ACCELERATION.get(compound_key, 0.002)),
                'fuel_effect': comp_data.get('fuel_effect', DEFAULT_FUEL_EFFECT),
                'is_default': False
            }
    
    # Fallback to legacy database
    legacy_db = load_tyre_degradation_database()
    # Map to legacy key format
    legacy_key = RACE_TO_CIRCUIT_MAP.get(circuit, circuit)
    legacy_circuits = legacy_db.get('circuits', {})
    
    if legacy_key in legacy_circuits:
        circuit_data = legacy_circuits[legacy_key]
        base_deg = circuit_data.get('base_degradation', {})
        deg_accel = circuit_data.get('degradation_acceleration', {})
        
        return {
            'base_rate': base_deg.get(compound_key, DEFAULT_BASE_DEGRADATION.get(compound_key, 0.05)),
            'acceleration': deg_accel.get(compound_key, DEFAULT_DEGRADATION_ACCELERATION.get(compound_key, 0.002)),
            'fuel_effect': DEFAULT_FUEL_EFFECT,
            'is_default': False
        }
    
    # Return defaults
    return {
        'base_rate': DEFAULT_BASE_DEGRADATION.get(compound_key, 0.05),
        'acceleration': DEFAULT_DEGRADATION_ACCELERATION.get(compound_key, 0.002),
        'fuel_effect': DEFAULT_FUEL_EFFECT,
        'is_default': True
    }


def get_pit_loss(circuit: str, condition: str = 'green_flag', team: str = None) -> float:
    """
    Get pit loss time for a specific circuit and condition.
    
    Args:
        circuit: Circuit name
        condition: 'green_flag', 'safety_car', or 'virtual_safety_car'
        team: Optional team name for team-specific offset
        
    Returns:
        Pit loss time in seconds
    """
    db = load_pit_loss_database()
    circuits = db.get('circuits', {})
    
    # Default values
    defaults = {
        'green_flag': 22.0,
        'safety_car': 11.0,
        'virtual_safety_car': 8.0
    }
    
    # Handle None or empty circuit name
    if not circuit:
        return defaults.get(condition, 22.0)
    
    # Try various circuit name formats (including city mapping)
    city_name = RACE_TO_CITY_MAP.get(circuit, circuit)
    circuit_variants = [
        circuit,
        circuit.title() if circuit else None,
        city_name,
        city_name.title() if city_name else None,
        RACE_TO_CIRCUIT_MAP.get(circuit, circuit) if circuit else None
    ]
    # Filter out None values
    circuit_variants = [v for v in circuit_variants if v]
    
    circuit_data = None
    for variant in circuit_variants:
        if variant in circuits:
            circuit_data = circuits[variant]
            break
    
    if circuit_data is None:
        return defaults.get(condition, 22.0)
    
    pit_times = circuit_data.get('pit_loss_times', {})
    base_time = pit_times.get(condition, defaults.get(condition, 22.0))
    
    # Apply team offset if available
    if team:
        team_offsets = circuit_data.get('team_offsets', {})
        offset = team_offsets.get(team, 0.0)
        base_time += offset
    
    return base_time


# =============================================================================
# Core Prediction Functions
# =============================================================================

def calculate_lap_time_prediction(
    lap: int,
    tyre_age: int,
    compound: str,
    base_lap_time: float,
    circuit: str,
    include_fuel: bool = True,
    include_grip: bool = True
) -> float:
    """
    Calculate predicted lap time for a specific lap within a stint.
    
    This is the CORE prediction function used by both Driver Strategy and Chase Strategy.
    
    Uses time-varying linear degradation model:
        degradation(t) = base_rate * t + 0.5 * acceleration * t^2
    
    Args:
        lap: The lap number (1-based)
        tyre_age: Laps on current tyres (1-based)
        compound: Tyre compound (SOFT, MEDIUM, HARD)
        base_lap_time: Base lap time (fastest clean lap)
        circuit: Circuit name
        include_fuel: Whether to include fuel effect
        include_grip: Whether to include compound grip advantage
        
    Returns:
        Predicted lap time in seconds
    """
    # Get coefficients
    coeffs = get_strategy_coefficients(circuit, compound)
    base_rate = coeffs['base_rate']
    acceleration = coeffs['acceleration']
    fuel_coeff = coeffs['fuel_effect']
    
    # Calculate tyre degradation (quadratic model)
    # degradation(t) = base_rate * t + 0.5 * acceleration * t^2
    tyre_degradation = base_rate * tyre_age + 0.5 * acceleration * (tyre_age ** 2)
    
    # Calculate fuel effect (optional)
    fuel_effect = 0.0
    if include_fuel:
        fuel_effect = fuel_coeff * lap  # 負值 = 變輕變快
    
    # Compound grip advantage (optional)
    compound_advantage = 0.0
    if include_grip:
        compound_key = compound.upper()
        compound_advantage = COMPOUND_GRIP_ADVANTAGE.get(compound_key, 0.0)
    
    # Final prediction
    predicted = base_lap_time + tyre_degradation + fuel_effect + compound_advantage
    
    return predicted


def calculate_degradation_rate(
    compound: str,
    tyre_age: int,
    circuit: str
) -> float:
    """
    Calculate instantaneous tyre degradation rate (s/lap).
    
    This is the derivative of the degradation function:
        d(degradation)/dt = base_rate + acceleration * t
    
    Args:
        compound: Tyre compound
        tyre_age: Current tyre age
        circuit: Circuit name
        
    Returns:
        Degradation rate in seconds per lap
    """
    coeffs = get_strategy_coefficients(circuit, compound)
    base_rate = coeffs['base_rate']
    acceleration = coeffs['acceleration']
    
    # Instantaneous rate = base_rate + acceleration * tyre_age
    rate = base_rate + acceleration * tyre_age
    
    return rate


def calculate_new_tyre_advantage(
    new_compound: str,
    old_compound: str,
    old_tyre_age: int,
    circuit: str
) -> float:
    """
    Calculate the speed advantage of new tyres vs old tyres.
    
    Args:
        new_compound: New tyre compound
        old_compound: Old tyre compound
        old_tyre_age: Age of old tyres
        circuit: Circuit name
        
    Returns:
        Advantage in seconds per lap (positive = new tyres faster)
    """
    # Get degradation rates
    new_rate = calculate_degradation_rate(new_compound, 1, circuit)
    old_rate = calculate_degradation_rate(old_compound, old_tyre_age, circuit)
    
    # Degradation advantage (old tyres degrading faster)
    deg_advantage = old_rate - new_rate
    
    # Grip advantage from compound
    old_grip = COMPOUND_GRIP_ADVANTAGE.get(old_compound.upper(), 0.0)
    new_grip = COMPOUND_GRIP_ADVANTAGE.get(new_compound.upper(), 0.0)
    grip_advantage = old_grip - new_grip  # Positive if new compound is faster
    
    # Total advantage
    total_advantage = deg_advantage + grip_advantage
    
    return total_advantage


def predict_gap_over_stint(
    current_gap: float,
    laps_remaining: int,
    p1_compound: str,
    p1_tyre_age: int,
    p2_compound: str,
    p2_tyre_age: int,
    circuit: str
) -> Tuple[float, int]:
    """
    Predict gap change over remaining stint.
    
    Args:
        current_gap: Current gap P2 to P1 (positive = P2 behind)
        laps_remaining: Laps remaining in race
        p1_compound: P1's tyre compound
        p1_tyre_age: P1's tyre age
        p2_compound: P2's tyre compound
        p2_tyre_age: P2's tyre age
        circuit: Circuit name
        
    Returns:
        Tuple of (final_gap, catchup_lap or -1 if not caught)
    """
    gap = current_gap
    catchup_lap = -1
    
    for i in range(laps_remaining):
        # Calculate degradation rates at this point
        p1_rate = calculate_degradation_rate(p1_compound, p1_tyre_age + i, circuit)
        p2_rate = calculate_degradation_rate(p2_compound, p2_tyre_age + i, circuit)
        
        # P2's advantage this lap
        advantage = p1_rate - p2_rate
        
        # Update gap
        gap -= advantage
        
        # Check if caught
        if gap <= 0 and catchup_lap < 0:
            catchup_lap = i + 1
    
    return gap, catchup_lap
