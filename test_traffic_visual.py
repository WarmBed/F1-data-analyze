#!/usr/bin/env python3
"""
Test Traffic Heatmap Visual Display
測試 Traffic 熱力圖視覺化顯示
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from strategy_simulator.gui.widgets.traffic_heatmap_widget import TrafficHeatmapWidget


def create_test_data(num_laps=20, num_drivers=10):
    """創建測試數據"""
    import random
    
    driver_codes = ["VER", "LEC", "NOR", "PIA", "SAI", "HAM", "RUS", "ALO", "STR", "PER"][:num_drivers]
    
    drivers_data = []
    
    for idx, driver_code in enumerate(driver_codes):
        final_position = idx + 1
        
        # 生成隨機的 lap states
        lap_states = {}
        blocked_count = 0
        clean_count = 0
        sc_vsc_count = 0
        
        for lap in range(1, num_laps + 1):
            # SC/VSC on laps 10-12
            if 10 <= lap <= 12:
                lap_states[lap] = 2  # SC/VSC
                sc_vsc_count += 1
            else:
                # Random traffic or clean
                # Leaders (P1-P3) have less traffic
                if final_position <= 3:
                    traffic_chance = 0.2
                elif final_position <= 6:
                    traffic_chance = 0.4
                else:
                    traffic_chance = 0.6
                
                if random.random() < traffic_chance:
                    lap_states[lap] = 1  # Traffic
                    blocked_count += 1
                else:
                    lap_states[lap] = 0  # Clean
                    clean_count += 1
        
        drivers_data.append({
            "driver_code": driver_code,
            "final_position": final_position,
            "lap_states": lap_states,
            "traffic_stats": {
                "blocked_laps": blocked_count,
                "clean_laps": clean_count,
                "sc_vsc_laps": sc_vsc_count
            }
        })
    
    return drivers_data


class TestWindow(QMainWindow):
    """測試視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Traffic Heatmap Test - 2025 Japan GP")
        self.setGeometry(100, 100, 1200, 700)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Create heatmap widget
        self.heatmap = TrafficHeatmapWidget()
        layout.addWidget(self.heatmap)
        
        # Load test data
        print("[TEST] Creating test data...")
        drivers_data = create_test_data(num_laps=25, num_drivers=10)
        print(f"[TEST] ✅ Created data for {len(drivers_data)} drivers, 25 laps")
        
        # Update heatmap
        print("[TEST] Updating heatmap...")
        self.heatmap.update_data(
            drivers_data=drivers_data,
            max_lap=25,
            race_info="2025 Japan GP - 25 Laps (Test Data)"
        )
        print("[TEST] ✅ Heatmap updated")
        
        print("\n[TEST] Heatmap is now displayed. Hover over cells to see details.")
        print("[TEST] Legend: Green=Clean, Orange=Traffic, Grey=SC/VSC, Light Grey=No Data")


def main():
    print("=" * 60)
    print("Traffic Heatmap Visual Test")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    print("\n" + "=" * 60)
    print("Visual test started! ✅")
    print("Close the window to exit.")
    print("=" * 60)
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
