#!/usr/bin/env python3
"""
TrafficTimelineAnalysisAdapter - Workspace Factory Adapter
============================================================

Provides a workspace-safe adapter for creating Traffic Timeline Analysis modules.
This adapter is used by the workspace factory to create analysis instances.

Author: F1T Team
Date: 2025-12-23
Version: 1.0.0
"""

from __future__ import annotations

from typing import Optional, Dict, Any

from PyQt5.QtWidgets import QWidget

from core.gui_i18n import tr
from core.logger import get_logger


logger = get_logger("gui.traffic_timeline_adapter", component="gui")


class TrafficTimelineAnalysisAdapter:
    """
    Workspace adapter for Traffic Timeline Analysis.
    
    This adapter provides a consistent interface for the workspace factory
    to create and manage Traffic Timeline Analysis instances.
    """

    MODULE_ID = "traffic_timeline_analysis"
    MODULE_NAME = tr("traffic_timeline", "Traffic Timeline")
    MODULE_CATEGORY = "multi_season"
    
    def __init__(self):
        self._module = None
        self._widget = None
        logger.info("[TRAFFIC_TIMELINE_ADAPTER] Adapter created")

    @classmethod
    def get_module_info(cls) -> Dict[str, Any]:
        """
        Returns module metadata for workspace discovery.
        
        Returns:
            dict: Module metadata including id, name, category, etc.
        """
        return {
            "id": cls.MODULE_ID,
            "name": cls.MODULE_NAME,
            "category": cls.MODULE_CATEGORY,
            "description": tr(
                "traffic_timeline.description",
                "Visualizes traffic status (clean air / dirty air) for each lap per driver."
            ),
            "icon": "traffic",
            "requires_driver": False,
            "requires_lap": False,
            "supports_multi_session": True,
            "data_source": "api",
            "function_id": 127,
        }

    def create_widget(
        self,
        year: Optional[int] = None,
        race: Optional[str] = None,
        session: Optional[str] = None,
        parent: Optional[QWidget] = None,
        **kwargs,
    ) -> Optional[QWidget]:
        """
        Create and return a Traffic Timeline Analysis widget.
        
        Args:
            year: Race year
            race: Race name
            session: Session type
            parent: Parent widget
            **kwargs: Additional parameters
            
        Returns:
            QWidget: The created analysis widget
        """
        try:
            from .traffic_timeline_analysis_module import TrafficTimelineAnalysisModule
            
            logger.info(
                "[TRAFFIC_TIMELINE_ADAPTER] Creating widget: year=%s, race=%s, session=%s",
                year, race, session,
            )

            self._module = TrafficTimelineAnalysisModule()
            self._widget = self._module.create_widget(
                year=year,
                race=race,
                session=session,
                parent=parent,
                **kwargs,
            )

            return self._widget

        except Exception as exc:
            logger.exception("[TRAFFIC_TIMELINE_ADAPTER] Failed to create widget: %s", exc)
            return None

    def get_widget(self) -> Optional[QWidget]:
        """Returns the currently created widget."""
        return self._widget

    def get_module(self):
        """Returns the underlying analysis module."""
        return self._module

    def update_parameters(
        self,
        year: str,
        race: str,
        session: str,
        **kwargs,
    ) -> bool:
        """
        Update analysis parameters.
        
        Args:
            year: Race year
            race: Race name
            session: Session type
            **kwargs: Additional parameters
            
        Returns:
            bool: True if update succeeded
        """
        if not self._module:
            logger.warning("[TRAFFIC_TIMELINE_ADAPTER] No module to update")
            return False

        return self._module.update_parameters(
            year=year,
            race=race,
            session=session,
            **kwargs,
        )

    def refresh(self) -> None:
        """Refresh the analysis data."""
        if self._module:
            self._module.refresh()

    def clear(self) -> None:
        """Clear the current display."""
        if self._module:
            self._module.clear()

    def export_chart(self) -> bool:
        """Export the current chart."""
        if self._module:
            return self._module.export_chart()
        return False

    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        """Export the analysis data."""
        if self._module:
            return self._module.export_data(export_path, export_format)
        return False

    def dispose(self) -> None:
        """Cleanup resources."""
        logger.info("[TRAFFIC_TIMELINE_ADAPTER] Disposing adapter")
        if self._module:
            self._module.dispose()
            self._module = None
        self._widget = None
