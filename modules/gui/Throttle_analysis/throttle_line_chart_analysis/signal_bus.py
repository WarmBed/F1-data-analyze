"""Throttle Line Chart 同步訊號匯流排。"""

from PyQt5.QtCore import QObject, pyqtSignal


class ThrottleLineChartSignalBus(QObject):
    """集中管理油門折線圖雙視窗的同步訊號。"""

    # source: "throttle" / "laptime"
    hoverLapChanged = pyqtSignal(str, int, dict)
    highlightRequested = pyqtSignal(str, int)
    viewTransformChanged = pyqtSignal(str, float, float)
    settingsChanged = pyqtSignal(dict)
    statusMessage = pyqtSignal(str)

    def emit_hover(self, source: str, lap_number: int, payload: dict) -> None:
        self.hoverLapChanged.emit(source, lap_number, payload)

    def emit_highlight(self, source: str, lap_number: int) -> None:
        self.highlightRequested.emit(source, lap_number)

    def emit_view_transform(self, source: str, x_scale: float, x_offset: float) -> None:
        self.viewTransformChanged.emit(source, x_scale, x_offset)

    def emit_settings(self, settings: dict) -> None:
        self.settingsChanged.emit(dict(settings) if isinstance(settings, dict) else {})

    def emit_status(self, message: str) -> None:
        self.statusMessage.emit(str(message))
