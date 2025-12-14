#!/usr/bin/env python3
"""
Ideal Lap Sector Heatmap Widget
===============================

PyQt5 widget that renders a sector heatmap (S1/S2/S3/Total across drivers)
using native QPainter for high-performance rendering.

作者: F1T Team
日期: 2025-10-11
版本: 2.0.0 (QPainter 重構版)
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple, Any

from PyQt5.QtCore import Qt, QRectF, QRect, QPointF, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QPen, QColor, QBrush, QFont, QLinearGradient, QPolygonF
)
from PyQt5.QtWidgets import QWidget

from core.logger import get_logger
logger = get_logger(__name__)



class IdealLapSectorHeatmapWidget(QWidget):
    """
    Matplotlib-backed widget for plotting the sector heatmap.

    Signals:
        cell_clicked(driver_code: str, sector_label: str)
    """

    cell_clicked = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent if isinstance(parent, QWidget) else None)

        self.figure = Figure(figsize=(10, 4.5), tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self._colorbar = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

        self._base_df: pd.DataFrame = pd.DataFrame()
        self._current_df: pd.DataFrame = pd.DataFrame()
        self._sector_summary: Dict[str, Dict[str, any]] = {}
        self._cell_details: Dict[Tuple[str, str], Dict[str, any]] = {}
        self._driver_best_map: Dict[str, str] = {}

        self._highlight_options = {
            "show_global_fastest": True,
            "show_personal_best": False,
        }
        self._highlight_artists: List = []
        self._last_hover_cell: Optional[Tuple[str, str]] = None
        self._driver_order: List[str] = []

        self._cmap = self._build_colormap()

        # Register matplotlib interaction callbacks.
        self.canvas.mpl_connect("motion_notify_event", self._on_motion)
        self.canvas.mpl_connect("figure_leave_event", self._on_leave_figure)
        self.canvas.mpl_connect("button_press_event", self._on_click)

        self._update_empty_state()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def set_data(self, payload: Dict[str, any]) -> None:
        """
        Receive processed payload from the data loader and redraw the chart.
        """
        df = payload.get("sector_matrix")
        if df is None:
            self.clear_data()
            return

        if not isinstance(df, pd.DataFrame):
            df = pd.DataFrame(df)

        self._base_df = df.copy()
        self._current_df = self._base_df.copy()
        self._driver_order = payload.get("driver_order", list(self._base_df.columns))
        self._sector_summary = payload.get("sector_summary", {})
        self._cell_details = payload.get("cell_details", {})
        self._driver_best_map = payload.get("driver_best_map", {})

        self.render_heatmap(self._driver_order)

    def render_heatmap(self, driver_order: Optional[List[str]] = None) -> None:
        """
        Reorder columns and redraw the heatmap.
        """
        if self._base_df.empty:
            self._update_empty_state()
            return

        if driver_order:
            ordered = [code for code in driver_order if code in self._base_df.columns]
            if ordered:
                self._current_df = self._base_df.loc[:, ordered]
            else:
                self._current_df = self._base_df.copy()
        else:
            self._current_df = self._base_df.copy()

        self._draw_heatmap()

    def set_highlight_options(
        self,
        *,
        show_global_fastest: Optional[bool] = None,
        show_personal_best: Optional[bool] = None,
    ) -> None:
        """
        Update highlight toggles and redraw markers if required.
        """
        changed = False
        if show_global_fastest is not None:
            if (
                self._highlight_options["show_global_fastest"]
                != show_global_fastest
            ):
                self._highlight_options["show_global_fastest"] = show_global_fastest
                changed = True

        if show_personal_best is not None:
            if (
                self._highlight_options["show_personal_best"]
                != show_personal_best
            ):
                self._highlight_options["show_personal_best"] = show_personal_best
                changed = True

        if changed and not self._current_df.empty:
            self._draw_highlights()
            self.canvas.draw_idle()

    def clear_data(self) -> None:
        """Reset chart content."""
        self._base_df = pd.DataFrame()
        self._current_df = pd.DataFrame()
        self._sector_summary = {}
        self._cell_details = {}
        self._driver_best_map = {}
        self._driver_order = []
        self._update_empty_state()

    def get_current_data(self) -> Dict[str, any]:
        """Expose current dataframe for exports."""
        return {
            "sector_matrix": self._current_df.copy(),
            "sector_summary": self._sector_summary,
            "highlight_options": dict(self._highlight_options),
        }

    def save_plot(self, file_path: str) -> bool:
        """Persist the current figure."""
        try:
            self.figure.savefig(file_path, dpi=300, bbox_inches="tight")
            return True
        except Exception as exc:  # pragma: no cover - best effort
            logger.debug(f"[SECTOR_HEATMAP_WIDGET] Failed to save plot: {exc}")
            return False

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _build_colormap(self):
        """
        Create a colour map with a neutral colour for missing entries.
        """
        base = cm.get_cmap("RdYlGn_r", 512)
        if hasattr(base, "copy"):
            cmap = base.copy()
        else:  # matplotlib < 3.5 fallback
            cmap = colors.LinearSegmentedColormap.from_list(
                "sector_heatmap", base(np.linspace(0, 1, 512))
            )
        cmap.set_bad(color="#f0f0f0")
        return cmap

    def _draw_heatmap(self) -> None:
        """Render the heatmap using seaborn if available, otherwise fallback."""
        self.ax.clear()
        self._clear_highlights(remove_colorbar=True)

        if self._current_df.empty:
            self._update_empty_state()
            return

        df = self._current_df.astype(float)

        if HAS_SEABORN:
            heatmap = sns.heatmap(
                df,
                cmap=self._cmap,
                mask=df.isna(),
                annot=True,
                fmt=".3f",
                linewidths=0.4,
                linecolor="#e0e0e0",
                cbar=True,
                cbar_kws={"label": "Sector Time (s)"},
                ax=self.ax,
                annot_kws={"fontsize": 8},
            )
            self._colorbar = heatmap.collections[0].colorbar
        else:
            masked_values = np.ma.masked_invalid(df.values)
            image = self.ax.imshow(
                masked_values, cmap=self._cmap, aspect="auto", origin="upper"
            )
            self._colorbar = self.figure.colorbar(
                image, ax=self.ax, label="Sector Time (s)"
            )

            for (row_idx, col_idx), value in np.ndenumerate(df.values):
                if math.isnan(value):
                    continue
                self.ax.text(
                    col_idx,
                    row_idx,
                    f"{value:.3f}",
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="#222222",
                )

            self.ax.set_xticks(np.arange(df.shape[1]))
            self.ax.set_xticklabels(df.columns, rotation=45, ha="right")
            self.ax.set_yticks(np.arange(df.shape[0]))
            self.ax.set_yticklabels(df.index)

        self.ax.set_xlabel("Driver", fontsize=9)
        self.ax.set_ylabel("Sector", fontsize=9)
        self.ax.set_title("Ideal Lap Sector Performance Heatmap", fontsize=11)

        self._draw_highlights()

        self.figure.tight_layout()
        self.canvas.draw_idle()

    def _draw_highlights(self) -> None:
        """Overlay markers for fastest sector and per-driver highlights."""
        self._clear_highlights()

        if self._current_df.empty:
            return

        if self._highlight_options.get("show_global_fastest", True):
            for sector_label, summary in self._sector_summary.items():
                driver_code = summary.get("fastest_driver")
                if not driver_code:
                    continue
                coords = self._cell_to_coordinates(sector_label, driver_code)
                if not coords:
                    continue
                scatter = self.ax.scatter(
                    coords[0],
                    coords[1],
                    marker="*",
                    s=160,
                    c="#FFD700",
                    edgecolors="#9E7E00",
                    linewidths=0.8,
                    zorder=6,
                )
                self._highlight_artists.append(scatter)

        if self._highlight_options.get("show_personal_best", False):
            for driver_code, sector_label in self._driver_best_map.items():
                coords = self._cell_to_coordinates(sector_label, driver_code)
                if not coords:
                    continue
                scatter = self.ax.scatter(
                    coords[0],
                    coords[1],
                    marker="o",
                    s=60,
                    facecolors="none",
                    edgecolors="#1976D2",
                    linewidths=1.2,
                    zorder=5,
                )
                self._highlight_artists.append(scatter)

    def _clear_highlights(self, remove_colorbar: bool = False) -> None:
        for artist in self._highlight_artists:
            try:
                artist.remove()
            except Exception:
                pass
        self._highlight_artists.clear()

        if remove_colorbar and self._colorbar is not None:
            try:
                self._colorbar.remove()
            except Exception:
                pass
            self._colorbar = None

    def _cell_to_coordinates(
        self, sector_label: str, driver_code: str
    ) -> Optional[Tuple[float, float]]:
        """Convert matrix indices to axis coordinates."""
        if self._current_df.empty:
            return None

        if (
            sector_label not in self._current_df.index
            or driver_code not in self._current_df.columns
        ):
            return None

        row_idx = list(self._current_df.index).index(sector_label)
        col_idx = list(self._current_df.columns).index(driver_code)

        # Place marker at the centre of the cell.
        return (col_idx + 0.5, row_idx + 0.5)

    def _update_empty_state(self) -> None:
        """Display a placeholder message when no data is available."""
        self.ax.clear()
        self._clear_highlights(remove_colorbar=True)
        self.ax.text(
            0.5,
            0.5,
            "No data available",
            ha="center",
            va="center",
            fontsize=11,
            color="#666666",
            transform=self.ax.transAxes,
        )
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas.draw_idle()

    # ------------------------------------------------------------------ #
    # Matplotlib interaction handlers
    # ------------------------------------------------------------------ #
    def _on_motion(self, event) -> None:
        if event.inaxes != self.ax or self._current_df.empty:
            self._hide_tooltip()
            return

        if event.xdata is None or event.ydata is None:
            self._hide_tooltip()
            return

        col_idx = int(math.floor(event.xdata + 0.5))
        row_idx = int(math.floor(event.ydata + 0.5))

        if (
            col_idx < 0
            or row_idx < 0
            or col_idx >= len(self._current_df.columns)
            or row_idx >= len(self._current_df.index)
        ):
            self._hide_tooltip()
            return

        driver_code = self._current_df.columns[col_idx]
        sector_label = self._current_df.index[row_idx]
        cell_key = (sector_label, driver_code)

        if self._last_hover_cell == cell_key:
            return

        self._last_hover_cell = cell_key
        details = self._cell_details.get(cell_key)
        if not details:
            self._hide_tooltip()
            return

        time_val = details.get("time")
        lap = details.get("lap")
        sector_rank = details.get("sector_rank")
        delta = details.get("delta_to_fastest")

        time_text = (
            f"{time_val:.3f}s" if time_val is not None and not math.isnan(time_val) else "N/A"
        )

        if delta is None or math.isnan(delta):
            delta_text = "N/A"
        elif math.isclose(delta, 0.0, abs_tol=1e-6):
            delta_text = "0.000s"
        elif delta > 0:
            delta_text = f"+{delta:.3f}s"
        else:
            delta_text = f"{delta:.3f}s"

        tooltip_lines = [
            f"Driver: {driver_code}",
            f"Sector: {sector_label}",
            f"Time: {time_text}",
        ]
        if lap:
            tooltip_lines.append(f"Lap: {lap}")
        if sector_rank:
            tooltip_lines.append(f"Rank: P{sector_rank}")
        tooltip_lines.append(f"Δ to Fastest: {delta_text}")

        QToolTip.showText(QCursor.pos(), "\n".join(tooltip_lines), self)

    def _on_click(self, event) -> None:
        if event.button != 1 or event.inaxes != self.ax or self._current_df.empty:
            return

        if event.xdata is None or event.ydata is None:
            return

        col_idx = int(math.floor(event.xdata + 0.5))
        row_idx = int(math.floor(event.ydata + 0.5))

        if (
            col_idx < 0
            or row_idx < 0
            or col_idx >= len(self._current_df.columns)
            or row_idx >= len(self._current_df.index)
        ):
            return

        driver_code = self._current_df.columns[col_idx]
        sector_label = self._current_df.index[row_idx]
        self.cell_clicked.emit(driver_code, sector_label)

    def _on_leave_figure(self, _event) -> None:
        self._hide_tooltip()

    def _hide_tooltip(self) -> None:
        if self._last_hover_cell is not None:
            QToolTip.hideText()
            self._last_hover_cell = None
