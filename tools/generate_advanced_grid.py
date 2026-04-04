import os
import configparser
from pathlib import Path

# Configuration
AC_SERVER_DIR = r"D:\SteamLibrary\steamapps\common\assettocorsa\server"  # Adjust if needed, or output to local
OUTPUT_FILE = "entry_list_advanced.ini"

# Mapping: Driver Code -> Car Model ID
# Must match what physics_cloner.py generated
GRID_MAPPING = {
    # Red Bull
    "VER": "rss_fh_26_redbullracing_ver",
    "LAW": "rss_fh_26_redbullracing_law",
    # Mercedes
    "RUS": "rss_fh_26_mercedes_rus",
    "ANT": "rss_fh_26_mercedes_ant",
    # Ferrari
    "LEC": "rss_fh_26_ferrari_lec",
    "HAM": "rss_fh_26_ferrari_ham",
    # McLaren
    "NOR": "rss_fh_26_mclaren_nor",
    "PIA": "rss_fh_26_mclaren_pia",
    # Aston Martin
    "ALO": "rss_fh_26_astonmartin_alo",
    "STR": "rss_fh_26_astonmartin_str",
    # Alpine
    "GAS": "rss_fh_26_alpine_gas",
    "DOO": "rss_fh_26_alpine_doo",
    # Williams
    "ALB": "rss_fh_26_williams_alb",
    "SAI": "rss_fh_26_williams_sai",
    # Racing Bulls
    "TSU": "rss_fh_26_racingbulls_tsu",
    "HAD": "rss_fh_26_racingbulls_had",
    # Haas
    "OCO": "rss_fh_26_haasf1team_oco",
    "BEA": "rss_fh_26_haasf1team_bea",
    # Sauber
    "HUL": "rss_fh_26_kicksauber_hul",
    "BOR": "rss_fh_26_kicksauber_bor",
}

# Grid Order (2025 Australia Qualifying Result or Default)
GRID_ORDER = [
    "VER", "NOR", "LEC", "RUS", "PIA", "HAM", "SAI", "ALO", "GAS", "ALB",
    "TSU", "OCO", "HUL", "STR", "LAW", "BEA", "DOO", "HAD", "ANT", "BOR"
]

def generate_entry_list():
    config = configparser.ConfigParser()
    config.optionxform = str # Preserve case

    for i, driver_code in enumerate(GRID_ORDER):
        section = f"CAR_{i}"
        config.add_section(section)
        
        car_model = GRID_MAPPING.get(driver_code, "rss_formula_hybrid_x_2026")
        
        config.set(section, "MODEL", car_model)
        config.set(section, "SKIN", "default") # Cloner copies skins, default is fine or specific if needed
        config.set(section, "SPECTATOR_MODE", "0")
        config.set(section, "DRIVERNAME", driver_code)
        config.set(section, "TEAM", "") 
        config.set(section, "GUID", "")
        config.set(section, "BALLAST", "0") # ZERO BALLAST! Physics handles it now.
        config.set(section, "RESTRICTOR", "0")

    with open(OUTPUT_FILE, 'w') as f:
        config.write(f)
    
    print(f"Generated {OUTPUT_FILE} with {len(GRID_ORDER)} Advanced Physics cars.")
    print("Instructions:")
    print("1. In Content Manager -> Drive -> Single -> Grid Type: 'Manual'.")
    print(f"2. Drag and drop this '{OUTPUT_FILE}' into the grid list area (or load it manually).")
    print("3. Enjoy the simulation!")

if __name__ == "__main__":
    generate_entry_list()
