import sys
import math
import pandas as pd
import fastf1
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLabel

# Enable caching
fastf1.Cache.enable_cache('cache')

# Mapping from team names to power unit (engine supplier)
def get_engine_from_team(team_name: str) -> str:
    """Return the power unit supplier for a given team name."""
    name_lower = team_name.lower()
    if "red bull" in name_lower or "bulls" in name_lower or "alphatauri" in name_lower or "rbpt" in name_lower or "honda" in name_lower:
        return "Honda"
    elif "mercedes" in name_lower or "aston martin" in name_lower or "mclaren" in name_lower or "williams" in name_lower:
        return "Mercedes"
    elif "ferrari" in name_lower or "haas" in name_lower or "alfa romeo" in name_lower or "sauber" in name_lower:
        return "Ferrari"
    elif "alpine" in name_lower or "renault" in name_lower:
        return "Renault"
    else:
        return "Unknown"

class SpeedAnalysisApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("F1 2025 Japan GP Top Speed Analysis")
        self.resize(800, 600)
        
        # Layouts
        main_layout = QVBoxLayout()
        control_layout = QHBoxLayout()
        
        # Session selection checkboxes
        self.cb_fp1 = QCheckBox("FP1")
        self.cb_fp2 = QCheckBox("FP2")
        self.cb_fp3 = QCheckBox("FP3")
        self.cb_quali = QCheckBox("Qualifying")
        # Default all selected
        self.cb_fp1.setChecked(True)
        self.cb_fp2.setChecked(True)
        self.cb_fp3.setChecked(True)
        self.cb_quali.setChecked(True)
        
        control_layout.addWidget(QLabel("Select sessions:"))
        control_layout.addWidget(self.cb_fp1)
        control_layout.addWidget(self.cb_fp2)
        control_layout.addWidget(self.cb_fp3)
        control_layout.addWidget(self.cb_quali)
        
        # Analyze button
        self.btn_analyze = QPushButton("Analyze Speeds")
        control_layout.addWidget(self.btn_analyze)
        
        # Table for results
        self.table = QTableWidget()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.table)
        self.setLayout(main_layout)
        
        # Connect button to analysis function
        self.btn_analyze.clicked.connect(self.load_and_analyze)
    
    def load_and_analyze(self):
        # Determine selected sessions
        sessions_to_load = []
        if self.cb_fp1.isChecked():
            sessions_to_load.append(("FP1", "Practice 1"))
        if self.cb_fp2.isChecked():
            sessions_to_load.append(("FP2", "Practice 2"))
        if self.cb_fp3.isChecked():
            sessions_to_load.append(("FP3", "Practice 3"))
        if self.cb_quali.isChecked():
            sessions_to_load.append(("Q", "Qualifying"))
        if not sessions_to_load:
            return  # nothing selected
        
        session_speed_data = {}
        loaded_sessions = {}
        # Load each selected session and compute top speeds
        for sess_code, sess_name in sessions_to_load:
            session = fastf1.get_session(2025, "Japan", sess_name)
            session.load()  # load data from cache
            loaded_sessions[sess_code] = session
            laps = session.laps
            if laps.empty:
                continue
            if 'SpeedST' in laps.columns:
                # Use Speed Trap data if available
                speeds = laps.groupby('Driver')['SpeedST'].max()
            else:
                # Fallback: manual telemetry extraction if SpeedST not available
                speeds_dict = {}
                drivers = pd.unique(laps['Driver'])
                for drv in drivers:
                    drv_laps = laps.pick_drivers(drv)
                    max_speed = 0.0
                    for _, lap in drv_laps.iterlaps():
                        car_data = lap.get_car_data()
                        if car_data is None or car_data.empty:
                            continue
                        lap_max = car_data['Speed'].max()
                        if pd.notna(lap_max) and float(lap_max) > max_speed:
                            max_speed = float(lap_max)
                    speeds_dict[drv] = max_speed
                speeds = pd.Series(speeds_dict)
            session_speed_data[sess_code] = speeds
        
        if not session_speed_data:
            return
        
        # Combine speeds into DataFrame (index: Driver code)
        speed_df = pd.DataFrame(session_speed_data)
        
        # Map each driver code to name and team
        driver_info_map = {}
        for code in speed_df.index:
            for sess_code, speeds in session_speed_data.items():
                if code in speeds.index:
                    info = loaded_sessions[sess_code].get_driver(code)
                    if info:
                        driver_info_map[code] = {
                            'FullName': info.get('FullName', code),
                            'TeamName': info.get('TeamName', "")
                        }
                        break
            if code not in driver_info_map:
                driver_info_map[code] = {'FullName': code, 'TeamName': ""}
        
        # Add columns for Driver name, Team, Power Unit
        speed_df['Driver'] = [driver_info_map[code]['FullName'] for code in speed_df.index]
        speed_df['Team'] = [driver_info_map[code]['TeamName'] for code in speed_df.index]
        speed_df['Power Unit'] = [get_engine_from_team(driver_info_map[code]['TeamName']) for code in speed_df.index]
        
        # Compute average speed across selected sessions
        session_cols = list(session_speed_data.keys())
        speed_df['Average Speed'] = speed_df[session_cols].mean(axis=1, skipna=True)
        
        # Rank drivers by average speed and guess aero setup
        speed_df.sort_values('Average Speed', ascending=False, inplace=True)
        N = len(speed_df)
        top_count = math.ceil(0.25 * N)
        bottom_count = math.ceil(0.25 * N)
        guesses = []
        for idx, (_, row) in enumerate(speed_df.iterrows(), start=1):
            if idx <= top_count:
                guesses.append("Low Downforce")
            elif idx > N - bottom_count:
                guesses.append("High Downforce")
            else:
                guesses.append("")
        speed_df['Aero Setup Guess'] = guesses
        
        # Prepare table columns order
        table_columns = ["Driver", "Team", "Power Unit"]
        session_order = []
        for code in ["FP1", "FP2", "FP3", "Q"]:
            if code in session_speed_data:
                session_order.append(code)
        for code in session_order:
            col_name = f"{code} Speed"
            if code in speed_df.columns:
                speed_df.rename(columns={code: col_name}, inplace=True)
            table_columns.append(col_name)
        table_columns.append("Average Speed")
        table_columns.append("Aero Setup Guess")
        
        # Populate QTableWidget
        self.table.clearContents()
        self.table.setRowCount(len(speed_df))
        self.table.setColumnCount(len(table_columns))
        self.table.setHorizontalHeaderLabels(table_columns)
        
        for row_idx, (_, row) in enumerate(speed_df.iterrows()):
            for col_idx, col_name in enumerate(table_columns):
                value = row.get(col_name, "")
                if pd.isna(value):
                    display_text = ""
                elif isinstance(value, (int, float)):
                    if col_name.endswith("Speed") and col_name != "Average Speed":
                        display_text = f"{value:.0f}"
                    elif col_name == "Average Speed":
                        display_text = f"{value:.1f}"
                    else:
                        display_text = str(value)
                else:
                    display_text = str(value)
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(display_text))
        
        self.table.resizeColumnsToContents()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpeedAnalysisApp()
    window.show()
    sys.exit(app.exec_())
