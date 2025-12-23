import sys
import math
import pytest

from PyQt5.QtWidgets import QApplication

from modules.gui.track_analysis.track_map_widget import TrackMapWidget
try:
    from modules.gui.lap_analysis.linkage import linkage_manager
except ImportError:  # pragma: no cover
    linkage_manager = None


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def track_widget(qt_app):
    widget = TrackMapWidget()
    sample_data = {
        "session_info": {"track_name": "Test Circuit"},
        "detailed_position_records": [
            {"position_x": 0.0, "position_y": 0.0, "distance_m": 0.0},
            {"position_x": 100.0, "position_y": 0.0, "distance_m": 100.0},
            {"position_x": 200.0, "position_y": 50.0, "distance_m": 200.0},
            {"position_x": 300.0, "position_y": 100.0, "distance_m": 300.0},
        ],
        "track_bounds": {"x_min": 0.0, "x_max": 400.0, "y_min": -50.0, "y_max": 150.0},
    }
    widget.load_track_data(sample_data)
    yield widget
    if linkage_manager is not None:
        linkage_manager.unregister_module(widget)
    widget.deleteLater()


def test_dynamic_marker_updates_from_linkage(track_widget):
    track_widget.on_x_linkage_received(150.0, 0.4)
    state = track_widget.get_marker_state()
    assert state["dynamic_distance"] == pytest.approx(150.0)
    assert state["dynamic_world"] is not None
    x, y = state["dynamic_world"]
    assert math.isclose(x, 150.0, rel_tol=0.05)
    assert math.isclose(y, 25.0, rel_tol=0.05)


def test_fixed_marker_handles_signals(track_widget):
    track_widget.on_click_linkage_received(250.0)
    state = track_widget.get_marker_state()
    assert state["fixed_distance"] == pytest.approx(250.0)
    assert state["fixed_world"] is not None

    track_widget.on_click_linkage_clear()
    state_after_clear = track_widget.get_marker_state()
    assert state_after_clear["fixed_distance"] is None
    assert state_after_clear["fixed_world"] is None


def test_marker_visibility_toggle(track_widget):
    track_widget.set_dynamic_marker_visibility(False)
    track_widget.on_x_linkage_received(120.0, 0.3)
    state = track_widget.get_marker_state()
    assert state["dynamic_world"] is not None
    assert state["dynamic_visible"] is False

    track_widget.set_dynamic_marker_visibility(True)
    state_enabled = track_widget.get_marker_state()
    assert state_enabled["dynamic_visible"] is True


def test_master_linkage_disable_clears_markers(track_widget):
    track_widget.on_x_linkage_received(180.0, 0.2)
    track_widget.on_click_linkage_received(220.0)
    track_widget.set_master_linkage_enabled(False)
    state = track_widget.get_marker_state()
    assert state["dynamic_world"] is None
    assert state["fixed_world"] is None

    track_widget.set_master_linkage_enabled(True)


def test_distance_scaling_normalizes_large_ranges(qt_app):
    widget = TrackMapWidget()
    scaled_payload = {
        "session_info": {"track_name": "Scaled Circuit"},
        "detailed_position_records": [
            {"position_x": 0.0, "position_y": 0.0, "distance_m": 0.0},
            {"position_x": 100.0, "position_y": 10.0, "distance_m": 10000.0},
            {"position_x": 200.0, "position_y": 20.0, "distance_m": 20000.0},
            {"position_x": 300.0, "position_y": 30.0, "distance_m": 30000.0},
        ],
        "track_bounds": {"x_min": 0.0, "x_max": 300.0, "y_min": 0.0, "y_max": 30.0},
    }

    widget.load_track_data(scaled_payload)

    assert math.isclose(widget.get_distance_scale(), 0.1, rel_tol=1e-6)

    widget.on_x_linkage_received(1500.0, 0.4)
    marker = widget.get_marker_state()
    assert marker["dynamic_world"] is not None
    x, y = marker["dynamic_world"]
    assert math.isclose(x, 150.0, rel_tol=0.05)
    assert math.isclose(y, 15.0, rel_tol=0.05)

    if linkage_manager is not None:
        linkage_manager.unregister_module(widget)
    widget.deleteLater()


@pytest.mark.skipif(linkage_manager is None, reason="linkage manager not available")
def test_linkage_manager_global_dispatch(track_widget):
    prev_master = linkage_manager.is_master_linkage_enabled()
    try:
        linkage_manager.set_master_linkage_enabled(True)

        linkage_manager.send_x_linkage(175.0, 0.45, sender=None)
        state = track_widget.get_marker_state()
        assert state["dynamic_distance"] == pytest.approx(175.0)
        assert state["dynamic_world"] is not None

        linkage_manager.send_click_linkage(210.0, sender=None)
        state = track_widget.get_marker_state()
        assert state["fixed_distance"] == pytest.approx(210.0)
        assert state["fixed_world"] is not None

        linkage_manager.send_click_linkage_clear()
        linkage_manager.send_x_linkage_clear()

        cleared_state = track_widget.get_marker_state()
        assert cleared_state["dynamic_world"] is None
        assert cleared_state["fixed_world"] is None
    finally:
        linkage_manager.set_master_linkage_enabled(prev_master)


def test_distance_lookup_accepts_alternative_keys(qt_app):
    widget = TrackMapWidget()
    alt_data = {
        "session_info": {"track_name": "Fallback Circuit"},
        "detailed_position_records": [
            {"position_x": 0.0, "position_y": 0.0, "distance": 0.0},
            {"position_x": 50.0, "position_y": 25.0, "distance": 50.0},
            {"position_x": 120.0, "position_y": 40.0, "distance": 120.0},
            {"position_x": 200.0, "position_y": 80.0, "distance": 200.0},
        ],
        "track_bounds": {"x_min": -20.0, "x_max": 220.0, "y_min": -20.0, "y_max": 120.0},
    }
    widget.load_track_data(alt_data)
    widget.on_x_linkage_received(110.0, 0.5)
    state = widget.get_marker_state()
    assert state["dynamic_world"] is not None

    if linkage_manager is not None:
        linkage_manager.unregister_module(widget)
    widget.deleteLater()
