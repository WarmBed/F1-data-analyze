#!/usr/bin/env python3
"""
TrafficTimelineAnalysisModule - IAnalysisModule Implementation
================================================================

Provides a factory interface for the Traffic Timeline Analysis MDI widget.
Implements all required abstract methods from IAnalysisModule.

Author: F1T Team
Date: 2025-12-23
Version: 1.0.0
"""

from __future__ import annotations

from typing import Optional, Dict, Any

from PyQt5.QtWidgets import QWidget

from core.gui_i18n import tr
from core.logger import get_logger
from modules.gui.interfaces.analysis_module import IAnalysisModule

from .traffic_timeline_analysis_mdi import TrafficTimelineAnalysis


logger = get_logger("gui.traffic_timeline_module", component="gui")


class TrafficTimelineAnalysisModule(IAnalysisModule):
    """
    IAnalysisModule interface implementation for Traffic Timeline Analysis.
    
    This module integrates with the workspace factory pattern and multi-season tree.
    Implements all required abstract methods from IAnalysisModule.
    """

    MODULE_ID = "traffic_timeline_analysis"
    MODULE_ICON = "traffic"
    MODULE_CATEGORY = "multi_season"
    SUPPORTS_MULTI_SESSION = True
    REQUIRES_DRIVER_SELECTION = False
    REQUIRES_LAP_SELECTION = False

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mdi_instance: Optional[TrafficTimelineAnalysis] = None
        self._parent_widget: Optional[QWidget] = None
        self._current_year: Optional[int] = None
        self._current_race: Optional[str] = None
        self._current_session: Optional[str] = None
        logger.info("[TRAFFIC_TIMELINE_MODULE] TrafficTimelineAnalysisModule created")

    # ================== Required Abstract Properties ==================

    @property
    def module_name(self) -> str:
        """Return module name"""
        return self.MODULE_ID

    @property
    def display_name(self) -> str:
        """Return display name for UI"""
        return tr("traffic_timeline", "Traffic Timeline")

    @property
    def version(self) -> str:
        """Return module version"""
        return "1.0.0"

    @property
    def description(self) -> str:
        """Return module description"""
        return tr(
            "traffic_timeline.description",
            "Visualizes traffic status (clean air / dirty air) for each lap per driver."
        )

    # ================== Required Abstract Methods ==================

    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """
        Initialize module
        
        Args:
            parent_widget: Parent widget (usually PopoutSubWindow)
            **kwargs: Additional initialization parameters
            
        Returns:
            bool: True if initialization succeeded
        """
        try:
            logger.info("[TRAFFIC_TIMELINE_MODULE] Initializing module...")
            self._parent_widget = parent_widget

            year = kwargs.get("year")
            race = kwargs.get("race")
            session = kwargs.get("session")

            self._mdi_instance = TrafficTimelineAnalysis(
                year=year,
                race=race,
                session=session,
                parent=parent_widget,
            )

            if self._mdi_instance:
                self._is_initialized = True
                logger.info("[TRAFFIC_TIMELINE_MODULE] Module initialized successfully")
                return True
            return False

        except Exception as exc:
            logger.exception("[TRAFFIC_TIMELINE_MODULE] Module initialization failed: %s", exc)
            return False

    def get_widget(self) -> Optional[QWidget]:
        """
        Return the module's main widget
        
        Returns:
            QWidget: The module's main interface widget
        """
        if self._mdi_instance:
            return self._mdi_instance.main_widget
        return None

    def update_parameters(self, year: int, race: str, session: str) -> bool:
        """
        Update analysis parameters
        
        Args:
            year: Year
            race: Race name
            session: Session (FP1, FP2, FP3, Q, R, S)
            
        Returns:
            bool: True if update succeeded
        """
        try:
            self._current_year = year
            self._current_race = race
            self._current_session = session

            if not self._mdi_instance:
                logger.warning("[TRAFFIC_TIMELINE_MODULE] Cannot update - no MDI instance")
                return False

            return self._mdi_instance.update_lap_parameters(
                year=str(year),
                race=race,
                session=session,
            )

        except Exception as exc:
            logger.exception("[TRAFFIC_TIMELINE_MODULE] Parameter update failed: %s", exc)
            return False

    def load_data(self, **kwargs) -> bool:
        """
        Load analysis data
        
        Args:
            **kwargs: Load parameters
            
        Returns:
            bool: True if load succeeded
        """
        try:
            if not self._mdi_instance:
                logger.warning("[TRAFFIC_TIMELINE_MODULE] Cannot load - no MDI instance")
                return False

            year = kwargs.get("year", self._current_year)
            race = kwargs.get("race", self._current_race)
            session = kwargs.get("session", self._current_session)

            if not all([year, race, session]):
                logger.warning("[TRAFFIC_TIMELINE_MODULE] Missing required parameters")
                return False

            if hasattr(self._mdi_instance, "data_manager") and self._mdi_instance.data_manager:
                return self._mdi_instance.data_manager.load_data(
                    year=year,
                    race=race,
                    session=session,
                    **kwargs,
                )
            return False

        except Exception as exc:
            logger.exception("[TRAFFIC_TIMELINE_MODULE] Data load failed: %s", exc)
            return False

    def refresh_analysis(self) -> None:
        """Re-execute analysis"""
        if self._mdi_instance:
            self._mdi_instance.refresh_analysis()

    def clear_data(self) -> None:
        """Clear all data"""
        if self._mdi_instance:
            self._mdi_instance.clear_data()

    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        """
        Export analysis data
        
        Args:
            export_path: Export path
            export_format: Export format ("json", "csv", "png", etc.)
            
        Returns:
            bool: True if export succeeded
        """
        if not self._mdi_instance:
            return False
        return self._mdi_instance.export_data(export_path, export_format)

    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """
        Get current analysis data
        
        Returns:
            Dict[str, Any]: Current analysis data, or None if no data
        """
        if self._mdi_instance and hasattr(self._mdi_instance, "data_manager"):
            dm = self._mdi_instance.data_manager
            if dm and hasattr(dm, "get_processed_data"):
                return dm.get_processed_data()
        return None

    # ================== Additional Properties ==================

    @property
    def module_id(self) -> str:
        return self.MODULE_ID

    @property
    def module_icon(self) -> str:
        return self.MODULE_ICON

    @property
    def module_category(self) -> str:
        return self.MODULE_CATEGORY

    @property
    def supports_multi_session(self) -> bool:
        return self.SUPPORTS_MULTI_SESSION

    @property
    def requires_driver_selection(self) -> bool:
        return self.REQUIRES_DRIVER_SELECTION

    @property
    def requires_lap_selection(self) -> bool:
        return self.REQUIRES_LAP_SELECTION

    # ================== Additional Methods ==================

    def create_widget(
        self,
        year: Optional[int] = None,
        race: Optional[str] = None,
        session: Optional[str] = None,
        parent: Optional[QWidget] = None,
        **kwargs,
    ) -> Optional[QWidget]:
        """
        Factory method to create a new TrafficTimelineAnalysis MDI instance.
        
        Args:
            year: Race year (optional, can be set later)
            race: Race name (optional, can be set later)
            session: Session type (optional, can be set later)
            parent: Parent QWidget
            **kwargs: Additional parameters
            
        Returns:
            QWidget: A new TrafficTimelineAnalysis instance
        """
        logger.info(
            "[TRAFFIC_TIMELINE_MODULE] Creating widget: year=%s, race=%s, session=%s",
            year, race, session,
        )

        success = self.initialize_module(
            parent_widget=parent,
            year=year,
            race=race,
            session=session,
            **kwargs,
        )

        if success:
            return self.get_widget()
        return None

    def get_mdi_instance(self) -> Optional[TrafficTimelineAnalysis]:
        """
        Returns the underlying MDI instance.
        
        Returns:
            TrafficTimelineAnalysis or None if not created yet
        """
        return self._mdi_instance

    def refresh(self) -> None:
        """Refresh the analysis data (alias for refresh_analysis)."""
        self.refresh_analysis()

    def clear(self) -> None:
        """Clear the current data display (alias for clear_data)."""
        self.clear_data()

    def export_chart(self) -> bool:
        """Export the current chart to a file."""
        if not self._mdi_instance:
            return False
        return self._mdi_instance.export_current_chart()

    def dispose(self) -> None:
        """Cleanup resources when module is closed."""
        logger.info("[TRAFFIC_TIMELINE_MODULE] Disposing module")
        if self._mdi_instance:
            try:
                if hasattr(self._mdi_instance, "data_manager") and self._mdi_instance.data_manager:
                    self._mdi_instance.data_manager._cleanup_api_worker()
            except Exception as exc:
                logger.warning("[TRAFFIC_TIMELINE_MODULE] Cleanup warning: %s", exc)
            self._mdi_instance = None
        self._is_initialized = False
