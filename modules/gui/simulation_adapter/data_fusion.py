
import json
import os
import glob
from datetime import datetime

# 2025 車手-車隊對應表 (來自 FastF1)
DRIVER_TEAM_MAP_2025 = {
    "VER": "Red Bull Racing",
    "NOR": "McLaren",
    "BOR": "Kick Sauber",
    "HAD": "Racing Bulls",
    "DOO": "Alpine",
    "GAS": "Alpine",
    "ANT": "Mercedes",
    "ALO": "Aston Martin",
    "LEC": "Ferrari",
    "STR": "Aston Martin",
    "TSU": "Racing Bulls",
    "ALB": "Williams",
    "HUL": "Kick Sauber",
    "LAW": "Red Bull Racing",
    "OCO": "Haas F1 Team",
    "HAM": "Ferrari",
    "SAI": "Williams",
    "RUS": "Mercedes",
    "PIA": "McLaren",
    "BEA": "Haas F1 Team",
}

# 車隊對應的 AC 塗裝名稱 (需根據實際 MOD 調整)
TEAM_SKIN_MAP = {
    "Red Bull Racing": "red_bull",
    "McLaren": "mclaren",
    "Ferrari": "ferrari",
    "Mercedes": "mercedes",
    "Aston Martin": "aston_martin",
    "Alpine": "alpine",
    "Williams": "williams",
    "Racing Bulls": "racing_bulls",
    "Kick Sauber": "sauber",
    "Haas F1 Team": "haas",
}

# 測試/後備車手過濾列表 (這些車手的 FP2 數據不代表正賽表現)
TEST_DRIVERS_FILTER = [
    "DOO",  # Jack Doohan - Alpine 後備車手
    "DRU",  # Drugovitch
    "SHW",  # Shwartzman
    "MAZ",  # Mazepin (如果出現)
]

# 隊友對應表 (用於缺失 Long Run 時的推算)
TEAMMATE_MAP_2025 = {
    # Red Bull Racing
    "VER": "LAW", "LAW": "VER",
    # McLaren
    "NOR": "PIA", "PIA": "NOR",
    # Ferrari
    "LEC": "HAM", "HAM": "LEC",
    # Mercedes
    "RUS": "ANT", "ANT": "RUS",
    # Aston Martin
    "ALO": "STR", "STR": "ALO",
    # Alpine
    "GAS": "DOO", "DOO": "GAS",  # DOO 會被過濾
    # Williams
    "ALB": "SAI", "SAI": "ALB",
    # Racing Bulls
    "TSU": "HAD", "HAD": "TSU",
    # Kick Sauber
    "BOR": "HUL", "HUL": "BOR",
    # Haas
    "OCO": "BEA", "BEA": "OCO",
}

class AcDataFusion:
    """
    AC 數據融合器
    負責讀取 CLI 模組 121 (FP2 Straight Line Analysis) 的 JSON 輸出,
    提取 Pace (Long Run 圈速) 和 Speed (最高尾速) 數據,
    並計算 Assetto Corsa 所需的 BoP 參數。
    """
    def __init__(self, year, race, session='FP2', filter_test_drivers=True):
        self.year = year
        self.race = race
        self.session = session
        self.filter_test_drivers = filter_test_drivers  # 是否過濾測試車手
        self.raw_data = {}
        self.pace_data = {}      # {driver: avg_pace_seconds}
        self.speed_data = {}     # {driver: max_speed_kmh}
        self.team_data = {}      # {driver: team_name}
        self.estimated_pace = {} # {driver: estimated_pace} - 推算的 pace
        self.fused_grid = []
        
        # BoP 轉換設定 (可校準)
        self.SEC_PER_10KG = 0.3                  # 每 10kg 約慢 0.3 秒
        self.SPEED_KMH_PER_1PCT_RESTRICTOR = 1.0  # 每慢 1 km/h 加 1% restrictor
        self.MAX_BALLAST = 150                  # 最大壓艙物 (kg)
        self.MAX_RESTRICTOR = 30                # 最大進氣限制 (%)
    
    def _estimate_missing_pace(self, driver):
        """
        為缺失 Long Run 數據的車手推算 pace
        策略: 使用隊友數據 + 0.2s 懲罰
        """
        teammate = TEAMMATE_MAP_2025.get(driver)
        if teammate and teammate in self.pace_data:
            estimated = self.pace_data[teammate] + 0.2  # 隊友 + 0.2s 懲罰
            print(f"  [ESTIMATE] {driver}: 使用隊友 {teammate} 數據 + 0.2s = {estimated:.3f}s")
            return estimated
        
        # 無隊友數據時，使用中位數 + 0.3s
        if self.pace_data:
            sorted_paces = sorted(self.pace_data.values())
            median_pace = sorted_paces[len(sorted_paces) // 2]
            estimated = median_pace + 0.3
            print(f"  [ESTIMATE] {driver}: 使用中位數 + 0.3s = {estimated:.3f}s")
            return estimated
        
        return None

    def _find_json_file(self, pattern_keyword):
        """在 json/ 目錄搜尋符合關鍵字的最新 JSON 檔案"""
        json_dir = os.path.join(os.getcwd(), 'json')
        if not os.path.exists(json_dir):
            print(f"[ERROR] json/ 目錄不存在")
            return None
        
        # 建構搜尋模式
        search_pattern = os.path.join(json_dir, f"*{pattern_keyword}*{self.year}*{self.race}*{self.session}*.json")
        files = glob.glob(search_pattern)
        
        if not files:
            # 嘗試不同的命名格式 (例如 Australian vs Australia)
            alt_race = self.race + "*"
            search_pattern = os.path.join(json_dir, f"*{pattern_keyword}*{self.year}*{alt_race}*{self.session}*.json")
            files = glob.glob(search_pattern)
        
        if not files:
            print(f"[WARN] 找不到符合的 JSON: {pattern_keyword}")
            return None
        
        latest_file = max(files, key=os.path.getmtime)
        print(f"[OK] 找到數據檔案: {os.path.basename(latest_file)}")
        return latest_file

    def fetch_source_data(self):
        """
        讀取 Function 121 的 JSON 輸出。
        從中提取:
        - Pace: Long Run stint 的平均圈速
        - Speed: 最高尾速 (absolute_max_speed_kmh)
        """
        print(f"\n{'='*60}")
        print(f"AC Data Fusion - 數據載入")
        print(f"賽事: {self.year} {self.race} {self.session}")
        print(f"{'='*60}")
        
        # 搜尋 Function 121 輸出
        json_file = self._find_json_file("fp2_straight_line")
        
        if not json_file:
            print("[ERROR] 無法找到 FP2 直線分析數據")
            print("[HINT] 請先執行: python f1_analysis_modular_main.py -f 121 -y {年份} -r {賽道} -s FP2")
            return False
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                self.raw_data = json.load(f)
        except Exception as e:
            print(f"[ERROR] 讀取 JSON 失敗: {e}")
            return False
        
        if "drivers" not in self.raw_data:
            print("[ERROR] JSON 結構異常: 缺少 'drivers' 欄位")
            return False
        
        # 提取每位車手的 Pace 和 Speed
        for driver_data in self.raw_data["drivers"]:
            driver = driver_data.get("driver", "UNK")
            
            # --- 提取 Speed (最高尾速) ---
            max_speed = driver_data.get("absolute_max_speed_kmh", 0)
            if max_speed > 0:
                self.speed_data[driver] = max_speed
            
            # --- 提取 Pace (Long Run 平均圈速) ---
            stints = driver_data.get("stints", [])
            long_run_laps = []
            for stint in stints:
                if stint.get("is_long_run", False):
                    laps_detail = stint.get("laps_detail", [])
                    for lap in laps_detail:
                        lap_time = lap.get("lap_time_seconds", 0)
                        if 60 < lap_time < 200:  # 合理範圍過濾
                            long_run_laps.append(lap_time)
            
            if long_run_laps:
                avg_pace = sum(long_run_laps) / len(long_run_laps)
                self.pace_data[driver] = avg_pace
        
        # 過濾測試車手
        filtered_count = 0
        if self.filter_test_drivers:
            for test_driver in TEST_DRIVERS_FILTER:
                if test_driver in self.pace_data:
                    del self.pace_data[test_driver]
                    filtered_count += 1
                    print(f"  [FILTER] 移除測試車手: {test_driver}")
                if test_driver in self.speed_data:
                    del self.speed_data[test_driver]
        
        print(f"\n[SUMMARY] 載入完成:")
        print(f"  - Pace 數據: {len(self.pace_data)} 位車手")
        print(f"  - Speed 數據: {len(self.speed_data)} 位車手")
        if filtered_count > 0:
            print(f"  - 已過濾測試車手: {filtered_count} 位")
        
        return len(self.pace_data) > 0

    def fuse_data(self):
        """
        執行 BoP (Balance of Performance) 計算:
        - Ballast: 基於 Pace Gap
        - Restrictor: 基於 Speed Gap
        """
        if not self.pace_data:
            print("[ERROR] 無 Pace 數據，無法計算 BoP")
            return []
        
        print(f"\n{'='*60}")
        print("BoP (Balance of Performance) 計算")
        print(f"{'='*60}")
        
        # 1. 確定基準值 (Benchmark)
        best_pace = min(self.pace_data.values())
        best_speed = max(self.speed_data.values()) if self.speed_data else 330.0
        
        print(f"[BENCHMARK] 最快圈速: {best_pace:.3f}s")
        print(f"[BENCHMARK] 最高尾速: {best_speed:.1f} km/h")
        
        # 2. 計算每位車手的 BoP 參數
        all_drivers = set(self.pace_data.keys())
        if self.speed_data:
            all_drivers.update(self.speed_data.keys())
        
        fused_list = []
        
        for driver in sorted(all_drivers):
            # 獲取車隊名稱
            team_name = DRIVER_TEAM_MAP_2025.get(driver, "Unknown")
            skin_name = TEAM_SKIN_MAP.get(team_name, "default")
            
            entry = {
                "driver": driver,
                "team": team_name,
                "model": "rss_formula_hybrid_x_2026",
                "skin": skin_name,
                "sim_params": {
                    "ballast": 0,
                    "restrictor": 0,
                    "ai_level": 100,
                    "aggression": 80
                },
                "source_data": {}
            }
            
            # --- Ballast 計算 (Pace) ---
            if driver in self.pace_data:
                pace = self.pace_data[driver]
                gap = pace - best_pace
                
                # 公式: Ballast = (Gap / SEC_PER_10KG) * 10
                ballast = int((gap / self.SEC_PER_10KG) * 10)
                ballast = max(0, min(self.MAX_BALLAST, ballast))
                
                entry["sim_params"]["ballast"] = ballast
                entry["source_data"]["pace"] = round(pace, 3)
                entry["source_data"]["pace_gap"] = round(gap, 3)
                entry["source_data"]["pace_source"] = "measured"
            else:
                # 嘗試推算缺失的 pace
                estimated_pace = self._estimate_missing_pace(driver)
                if estimated_pace:
                    gap = estimated_pace - best_pace
                    ballast = int((gap / self.SEC_PER_10KG) * 10)
                    ballast = max(0, min(self.MAX_BALLAST, ballast))
                    
                    entry["sim_params"]["ballast"] = ballast
                    entry["source_data"]["pace"] = round(estimated_pace, 3)
                    entry["source_data"]["pace_gap"] = round(gap, 3)
                    entry["source_data"]["pace_source"] = "estimated"
                    self.estimated_pace[driver] = estimated_pace
                else:
                    entry["sim_params"]["ballast"] = 50  # 最後手段懲罰值
                    entry["source_data"]["pace"] = "N/A"
                    entry["source_data"]["pace_source"] = "fallback"
            
            # --- Restrictor 計算 (Speed) ---
            if driver in self.speed_data:
                speed = self.speed_data[driver]
                speed_delta = best_speed - speed
                
                if speed_delta > 0:
                    restrictor = int(speed_delta * self.SPEED_KMH_PER_1PCT_RESTRICTOR)
                    restrictor = max(0, min(self.MAX_RESTRICTOR, restrictor))
                    entry["sim_params"]["restrictor"] = restrictor
                
                entry["source_data"]["top_speed"] = round(speed, 1)
                entry["source_data"]["speed_gap"] = round(speed_delta, 1)
            else:
                entry["source_data"]["top_speed"] = "N/A"
            
            fused_list.append(entry)
        
        # 按 Ballast 排序 (最快的在前)
        fused_list.sort(key=lambda x: x["sim_params"]["ballast"])
        
        self.fused_grid = fused_list
        
        # 輸出預覽
        print(f"\n{'Pos':<4} {'Driver':<8} {'Pace Gap':<10} {'Ballast':<10} {'Speed Gap':<10} {'Restrictor':<10}")
        print("-" * 60)
        for i, entry in enumerate(fused_list[:10]):  # 只顯示前 10
            d = entry["driver"]
            pg = entry["source_data"].get("pace_gap", "N/A")
            b = entry["sim_params"]["ballast"]
            sg = entry["source_data"].get("speed_gap", "N/A")
            r = entry["sim_params"]["restrictor"]
            pg_str = f"+{pg:.3f}s" if isinstance(pg, float) else pg
            sg_str = f"{sg:.1f}km/h" if isinstance(sg, float) else sg
            print(f"P{i+1:<3} {d:<8} {pg_str:<10} {b:<10}kg {sg_str:<10} {r:<10}%")
        
        if len(fused_list) > 10:
            print(f"... 共 {len(fused_list)} 位車手")
        
        return self.fused_grid

