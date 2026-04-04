import fastf1
import pandas as pd
import json
import os
import numpy as np
from datetime import datetime

# Setup cache
CACHE_DIR = 'f1_analysis_cache'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)
fastf1.Cache.enable_cache(CACHE_DIR)

class ACDataConverter:
    def __init__(self, year, race, session='FP2'):
        self.year = year
        self.race = race
        self.session_identifier = session
        self.session = None
        self.drivers_data = {}
        
        # AC Physics Calibration (Estimated)
        # 10kg ballast ~= 0.3s time loss (General approximation)
        self.SECONDS_PER_10KG = 0.3 
        # Base AI Strength (0-100)
        self.BASE_AI_LEVEL = 100 
        
    def load_data(self):
        print(f"📥 Loading {self.year} {self.race} {self.session_identifier} data...")
        try:
            self.session = fastf1.get_session(self.year, self.race, self.session_identifier)
            self.session.load(telemetry=False, laps=True, weather=False)
            print("✅ Data loaded successfully.")
            return True
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False

    def analyze_pace(self):
        print("📊 Analyzing driver pace...")
        laps = self.session.laps.pick_quicklaps()
        
        driver_stats = []
        
        # Get list of drivers
        drivers = np.unique(laps['Driver'])
        
        # 1. Get fastest lap for each driver
        for driver in drivers:
            driver_laps = laps.pick_driver(driver)
            if len(driver_laps) == 0:
                continue
                
            fastest_lap = driver_laps.pick_fastest()
            if pd.isnull(fastest_lap['LapTime']):
                continue
                
            driver_stats.append({
                'Driver': driver,
                'Team': fastest_lap['Team'],
                'LapTime': fastest_lap['LapTime'].total_seconds()
            })
            
        # Convert to DataFrame for easier sorting
        df = pd.DataFrame(driver_stats)
        if df.empty:
            print("⚠️ No valid lap times found.")
            return
            
        # Sort by LapTime
        df = df.sort_values('LapTime').reset_index(drop=True)
        
        # 2. Calculate Gaps
        p1_time = df.iloc[0]['LapTime']
        df['Gap'] = df['LapTime'] - p1_time
        
        # 3. Handle outliers (Safety check)
        # If gap is too large (> 5s), it might be an issue or valid slow car. 
        # For AC, we cap the ballast to reasonable limits (e.g. 150kg)
        
        self.drivers_data = df
        print(f"✅ Analyzed {len(df)} drivers. P1: {df.iloc[0]['Driver']} ({p1_time:.3f}s)")
        # print(df[['Driver', 'Gap']].head())

    def generate_ac_config(self, output_path='ac_sim_config.json'):
        print("⚙️ Generating Assetto Corsa configuration...")
        
        ac_config = {
            "metadata": {
                "year": self.year,
                "race": self.race,
                "source_session": self.session_identifier,
                "generated_at": datetime.now().isoformat(),
                "calibration": {
                    "sec_per_10kg": self.SECONDS_PER_10KG
                }
            },
            "grid": []
        }
        
        if self.drivers_data is None or self.drivers_data.empty:
            print("❌ No data to generate config.")
            return

        for index, row in self.drivers_data.iterrows():
            driver = row['Driver']
            gap = row['Gap']
            
            # Calculate Ballast
            # Formula: Required Ballast = (Gap / Time_Loss_Per_Kg) * Kg_Unit
            # e.g. Gap 0.3s -> (0.3 / 0.3) * 10 = 10kg
            ballast_kg = int((gap / self.SECONDS_PER_10KG) * 10)
            
            # Clamp Ballast (0 to 170kg is usually AC limit, let's say 150kg safe limit)
            ballast_kg = max(0, min(150, ballast_kg))
            
            # AI Level Logic
            # P1 gets AI 100 (or 99)
            # We can slightly vary AI Level/Aggression based on position if needed
            # For pure pace simulation via Ballast, we keep AI Level high and consistent
            ai_level = self.BASE_AI_LEVEL
            
            # Restrictor (0-100%) - Optional to fine tune top speed
            # For now, let's stick to Ballast for Lap Time
            restrictor = 0
            
            entry = {
                "name": driver,
                "team": row['Team'],
                "real_gap": round(gap, 3),
                "ac_params": {
                    "ballast": ballast_kg,
                    "restrictor": restrictor,
                    "ai_level": ai_level,
                    "aggression": 80 # Default, can be tuned by history
                }
            }
            ac_config['grid'].append(entry)
            
        # Write JSON
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(ac_config, f, indent=4, ensure_ascii=False)
            print(f"💾 Configuration saved to: {output_path}")
            
            # Also print a preview table
            print("\n--- AC Simulation Preview ---")
            print(f"{'Driver':<8} | {'Real Gap':<10} | {'AC Ballast (kg)':<15}")
            print("-" * 40)
            for entry in ac_config['grid']:
                d = entry['name']
                g = f"+{entry['real_gap']}s"
                b = entry['ac_params']['ballast']
                print(f"{d:<8} | {g:<10} | {b:<15}")
                
        except Exception as e:
            print(f"❌ Error writing output: {e}")

if __name__ == "__main__":
    # Test Run
    # Example: 2024 Japan FP2
    # Note: Using 2024 because 2025 data depends on current date in simulation context.
    # User mentioned 2025, let's try 2024 first as stable test or user's current context 2025.
    # Provided context says date is 2026, so 2025 is available.
    
    converter = ACDataConverter(2025, "Japan", "FP2")
    if converter.load_data():
        converter.analyze_pace()
        converter.generate_ac_config("ac_sim_toolkit/test_sim_config_2025_Japan.json")
