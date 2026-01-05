#!/usr/bin/env python3
"""
FP2->Q Prediction Tab for Strategy Simulator

Displays FP2->Q qualifying prediction and allows driver selection
to automatically set starting position.

Integrated with main GUI's FP2 Qualifying Prediction module.
Now shows full 10-column comparison with actual Q results when available.

Author: F1T Team
Date: 2026-01-05
Version: 2.0.0 (Full GUI Integration)
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont

# Import from main GUI's modules
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# Import main GUI's FP2→Q modules
from modules.gui.fp2_qualifying_prediction.fp2_qualifying_prediction_widget import FP2QualifyingPredictionWidget
from modules.gui.fp2_qualifying_prediction.fp2_qualifying_prediction_data_loader import FP2QualifyingPredictionDataLoader

# Import i18n with lazy loading
from strategy_simulator.gui.i18n_helper import tr


# Mapping from circuit name to Grand Prix name (for JSON file lookup)
CIRCUIT_TO_GP_NAME = {
    "Suzuka": "Japan",
    "Melbourne": "Australia",
    "Bahrain": "Bahrain",
    "Jeddah": "Saudi Arabia",
    "Shanghai": "China",
    "Miami": "Miami",
    "Imola": "Emilia Romagna",
    "Monaco": "Monaco",
    "Barcelona": "Spain",
    "Montreal": "Canada",
    "Spielberg": "Austria",
    "Silverstone": "Great Britain",
    "Hungaroring": "Hungary",
    "Spa": "Belgium",
    "Zandvoort": "Netherlands",
    "Monza": "Italy",
    "Baku": "Azerbaijan",
    "Singapore": "Singapore",
    "Austin": "USA",
    "Mexico City": "Mexico",
    "Interlagos": "Brazil",
    "Las Vegas": "Las Vegas",
    "Lusail": "Qatar",
    "Yas Marina": "Abu Dhabi",
}


class FP2PredictionTab(QWidget):
    """
    FP2->Q Prediction Tab (Full GUI Integration)
    
    Integrates main GUI's FP2QualifyingPredictionWidget to display:
    - 10-column full comparison table (includes actual Q results when available)
    - Model statistics (R², MAE, reliability)
    - Driver selection for simulation setup
    
    Features:
    - Automatically shows Q results when CLI Function 76 has actual_q_time data
    - Full prediction error analysis (prediction_error, rank_change)
    - Backward compatible with pre-Q predictions
    
    Signals:
        driver_selected(str, int): Emits (driver_code, predicted_position)
        q_data_available(bool): Emits whether actual Q results are available
    """
    
    # Signal: driver_code, predicted_position
    driver_selected = pyqtSignal(str, int)
    # Signal: whether actual Q data is available
    q_data_available = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._current_year: str = ""
        self._current_race: str = ""
        self._data_loader: Optional[FP2QualifyingPredictionDataLoader] = None
        self._current_data: Optional[Dict] = None
            
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Top: Selection control panel
        control_group = self._create_control_group()
        layout.addWidget(control_group)
        
        # Main: Use main GUI's full FP2→Q widget (10 columns with Q results)
        widget_group = QGroupBox(tr("FP2_PREDICTION_TITLE", "FP2 → Q Prediction (Full Analysis)"))
        widget_layout = QVBoxLayout(widget_group)
        
        self.prediction_widget = FP2QualifyingPredictionWidget()
        widget_layout.addWidget(self.prediction_widget)
        
        layout.addWidget(widget_group, 1)  # Stretch
        
        # Bottom: Action button
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        
        self.btn_apply = QPushButton(tr("APPLY_DRIVER_TO_SIM", "Apply Selected Driver to Simulation"))
        self.btn_apply.setEnabled(False)
        self.btn_apply.clicked.connect(self._on_apply_clicked)
        self.btn_apply.setMinimumWidth(250)
        action_layout.addWidget(self.btn_apply)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        # Connect table click signal to enable button
        self.prediction_widget.table.itemClicked.connect(self._on_table_item_clicked)
    
    def _create_control_group(self) -> QGroupBox:
        """Create selection control panel."""
        group = QGroupBox(tr("DRIVER_SELECTION", "Driver Selection for Simulation"))
        layout = QHBoxLayout(group)
        
        # Selected driver label
        self.lbl_selected = QLabel(tr("SELECTED", "Selected") + ": " + tr("CLICK_TABLE_TO_SELECT", "Click table to select driver"))
        self.lbl_selected.setFont(QFont("", 10, QFont.Bold))
        self.lbl_selected.setStyleSheet("color: #0066CC;")
        layout.addWidget(self.lbl_selected)
        
        layout.addStretch()
        
        return group
    
    def _on_table_item_clicked(self, item):
        """
        Handle table item click - auto-sync selection to simulation.
        
        Automatically emits driver_selected signal so the input panel
        stays in sync with the FP2→Q table selection.
        """
        if not item:
            return
        
        row = item.row()
        if not self._current_data:
            return
        
        predictions = self._current_data.get("predictions", [])
        if row < len(predictions):
            pred = predictions[row]
            driver = pred.get("driver", "N/A")
            
            # Get rank based on current selection mode
            # Will be overridden by main_window based on driver_selection_mode
            fp2_rank = pred.get("fp2_predicted_rank", pred.get("rank", row + 1))
            actual_q_rank = pred.get("actual_q_rank")
            
            # Display shows the original table rank
            display_rank = pred.get("rank", row + 1)
            self.lbl_selected.setText(f"{tr('SELECTED', 'Selected')}: {driver} (P{display_rank})")
            self.btn_apply.setEnabled(True)
            
            # Auto-emit driver selection signal with FP2 rank
            # The main_window will determine whether to use FP2 or Q rank
            # based on the driver_selection_mode setting
            self.driver_selected.emit(driver, fp2_rank)
            print(f"[FP2_PRED_TAB] Auto-selected: {driver} (FP2: P{fp2_rank}, Q: P{actual_q_rank})", flush=True)
    
    def load_prediction(self, year: str, race: str) -> bool:
        """
        Load FP2→Q prediction data using main GUI's data loader.
        
        Automatically shows actual Q results when available (Function 76 updated after qualifying).
        
        Args:
            year: Season year (e.g., "2025")
            race: Race/circuit name (e.g., "Japan" or "Suzuka")
            
        Returns:
            bool: True if loaded successfully
        """
        self._current_year = str(year)
        self._current_race = race
        
        # Convert circuit name to GP name if needed
        gp_name = CIRCUIT_TO_GP_NAME.get(race, race)
        
        print(f"[FP2_PRED_TAB] ============ 開始載入 FP2→Q 預測 ============", flush=True)
        print(f"[FP2_PRED_TAB] 年份: {year}, 賽道: {race}, GP名稱: {gp_name}", flush=True)
        
        try:
            # Initialize data loader
            print(f"[FP2_PRED_TAB] 初始化 FP2QualifyingPredictionDataLoader...", flush=True)
            self._data_loader = FP2QualifyingPredictionDataLoader(year=year, race=gp_name, parent=self)
            
            # Enable debug output
            self._data_loader._debug_enabled = True
            print(f"[FP2_PRED_TAB] Data Loader 初始化完成", flush=True)
            
            # Connect signals (use base class signal names)
            print(f"[FP2_PRED_TAB] 連接信號 (data_loaded, load_error)...", flush=True)
            self._data_loader.data_loaded.connect(self._on_data_loaded)
            self._data_loader.load_error.connect(self._on_load_error)
            
            # Start loading - MUST pass year and race parameters!
            print(f"[FP2_PRED_TAB] 呼叫 load_data(year={year}, race={gp_name})...", flush=True)
            result = self._data_loader.load_data(year=year, race=gp_name)
            print(f"[FP2_PRED_TAB] load_data() 返回: {result}", flush=True)
            
            return result
            
        except Exception as e:
            print(f"[FP2_PRED_TAB] ❌ 例外錯誤: {e}", flush=True)
            import traceback
            traceback.print_exc()
            self._show_no_data()
            return False
    
    def _on_data_loaded(self, data: Dict[str, Any]):
        """Handle successful data load."""
        print(f"[FP2_PRED_TAB] ✅ 數據載入成功！", flush=True)
        
        metadata = data.get("metadata", {})
        predictions = data.get("predictions", [])
        
        print(f"[FP2_PRED_TAB] 賽道: {metadata.get('track', 'N/A')}, 年份: {metadata.get('year', 'N/A')}", flush=True)
        print(f"[FP2_PRED_TAB] 模型 R²: {metadata.get('model_r2', 0):.4f}, MAE: {metadata.get('model_mae', 0):.4f}s", flush=True)
        print(f"[FP2_PRED_TAB] 車手數量: {len(predictions)}", flush=True)
        
        self._current_data = data
        
        # Update main GUI widget with full data (10 columns)
        self.prediction_widget.update_display(data)
        
        # Enable interaction
        self.prediction_widget.table.setEnabled(True)
        
        # Emit Q data availability signal
        has_q_data = metadata.get("has_actual_results", False)
        print(f"[FP2_PRED_TAB] 實際 Q 數據可用: {has_q_data}", flush=True)
        self.q_data_available.emit(has_q_data)
        
    def _on_load_error(self, error_msg: str):
        """Handle load error."""
        print(f"[FP2_PRED_TAB] ❌ 載入錯誤: {error_msg}", flush=True)
        self._show_no_data()
    
    def _show_no_data(self):
        """Show no data state."""
        self.lbl_selected.setText(tr("SELECTED", "Selected") + ": " + tr("NO_DATA_AVAILABLE", "No data available"))
        self.btn_apply.setEnabled(False)
        self.prediction_widget.table.setEnabled(False)
    
    def _on_apply_clicked(self):
        """Apply selected driver to simulation."""
        if not self._current_data:
            return
        
        # Get selected row from main GUI widget
        selected_items = self.prediction_widget.table.selectedItems()
        if not selected_items:
            return
        
        row = selected_items[0].row()
        predictions = self._current_data.get("predictions", [])
        
        if row < len(predictions):
            pred = predictions[row]
            driver = pred.get("driver", "N/A")
            rank = pred.get("rank", row + 1)
            
            # Emit signal
            self.driver_selected.emit(driver, rank)
            
            print(f"[FP2_PRED_TAB] Applied driver {driver} at P{rank}")
    
    def get_selected_driver(self) -> Optional[Dict]:
        """Get currently selected driver prediction data."""
        if not self._current_data:
            return None
        
        selected_items = self.prediction_widget.table.selectedItems()
        if not selected_items:
            return None
        
        row = selected_items[0].row()
        predictions = self._current_data.get("predictions", [])
        
        if row < len(predictions):
            return predictions[row]
        return None
    
    def get_all_predictions(self) -> List[Dict]:
        """Get all loaded predictions for use in Strategy analysis."""
        if not self._current_data:
            return []
        return self._current_data.get("predictions", []).copy()
    
    def get_predictions_with_mode(self, use_q_ranking: bool = False) -> List[Dict]:
        """
        Get predictions with appropriate ranking based on mode.
        
        Args:
            use_q_ranking: If True, use actual Q ranking (actual_q_rank) 
                          instead of FP2 predicted ranking (fp2_predicted_rank)
        
        Returns:
            List of predictions sorted by the appropriate ranking,
            with 'effective_rank' field set for simulation use.
        """
        if not self._current_data:
            return []
        
        predictions = self._current_data.get("predictions", []).copy()
        
        if use_q_ranking:
            # Sort by actual Q ranking if available
            for pred in predictions:
                actual_q_rank = pred.get("actual_q_rank")
                if actual_q_rank is not None:
                    pred["effective_rank"] = actual_q_rank
                else:
                    # Fallback to FP2 predicted rank if no actual Q data
                    pred["effective_rank"] = pred.get("fp2_predicted_rank", pred.get("rank", 99))
            
            # Sort by effective rank
            predictions.sort(key=lambda x: x.get("effective_rank", 99))
        else:
            # Use FP2 predicted ranking (default)
            for pred in predictions:
                fp2_rank = pred.get("fp2_predicted_rank", pred.get("rank", 99))
                pred["effective_rank"] = fp2_rank
            
            predictions.sort(key=lambda x: x.get("effective_rank", 99))
        
        return predictions
    
    def has_actual_q_data(self) -> bool:
        """Check if actual Q results are available."""
        if not self._current_data:
            return False
        
        metadata = self._current_data.get("metadata", {})
        return metadata.get("has_actual_results", False)
