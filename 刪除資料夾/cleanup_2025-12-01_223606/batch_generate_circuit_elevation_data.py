#!/usr/bin/env python3
"""
批次生成 F1 賽道高程資料（2020-2025 賽季）
Batch Generate F1 Circuit Elevation Data (2020-2025 Seasons)

功能：
1. 讀取所有 f1-circuits-master GeoJSON 賽道檔案
2. 篩選 2020-2025 賽季使用的賽道
3. 呼叫 Open-Elevation API 獲取每個座標點的高程資料
4. 計算累積距離和高程統計
5. 生成新的 JSON 檔案到 circuit_data 資料夾
6. 支援斷點續傳（處理失敗可重啟繼續）
7. 記錄失敗的賽道供後續處理
"""

import json
import requests
import numpy as np
from pathlib import Path
from datetime import datetime
import time
from typing import List, Dict, Tuple, Optional

# ============================= 配置參數 =============================

# 2020-2025 賽季使用的賽道列表（根據 FIA 官方賽曆）
CIRCUITS_2020_2025 = [
    "au-1953.geojson",  # Australia - Albert Park
    "bh-2002.geojson",  # Bahrain - Sakhir
    "sa-2021.geojson",  # Saudi Arabia - Jeddah
    "ae-2009.geojson",  # UAE - Yas Marina
    "it-1922.geojson",  # Italy - Monza
    "mc-1929.geojson",  # Monaco - Monte Carlo
    "es-1991.geojson",  # Spain - Catalunya
    "ca-1978.geojson",  # Canada - Montreal
    "at-1969.geojson",  # Austria - Red Bull Ring
    "gb-1948.geojson",  # Great Britain - Silverstone
    "hu-1986.geojson",  # Hungary - Hungaroring
    "be-1925.geojson",  # Belgium - Spa-Francorchamps
    "nl-1948.geojson",  # Netherlands - Zandvoort
    "it-1914.geojson",  # Italy - Imola (Emilia Romagna)
    "sg-2008.geojson",  # Singapore - Marina Bay
    "jp-1962.geojson",  # Japan - Suzuka
    "qa-2004.geojson",  # Qatar - Losail
    "us-2012.geojson",  # USA - COTA (Austin)
    "mx-1962.geojson",  # Mexico - Autódromo Hermanos Rodríguez
    "br-1940.geojson",  # Brazil - Interlagos
    "us-2023.geojson",  # USA - Las Vegas
    "us-2022.geojson",  # USA - Miami
    "az-2016.geojson",  # Azerbaijan - Baku
    "cn-2004.geojson",  # China - Shanghai
    "pt-2008.geojson",  # Portugal - Portimão (2020-2021)
    "tr-2005.geojson",  # Turkey - Istanbul (2020-2021)
    "fr-1969.geojson",  # France - Paul Ricard (2018-2022)
]

# API 配置
OPEN_ELEVATION_API_URL = "https://api.open-elevation.com/api/v1/lookup"
DELAY_EVERY_N_CIRCUITS = 5  # 每 N 條賽道延遲
LONG_DELAY_SECONDS = 15  # 長延遲時間（秒）
API_TIMEOUT = 120  # API 請求超時時間（秒）- 增加以應對大量點數

# 路徑配置
CIRCUITS_DIR = Path("json/f1-circuits-master/circuits")
OUTPUT_DIR = Path("json/f1-circuits-master/circuit_data")
PROGRESS_FILE = OUTPUT_DIR / "processing_progress.json"
ERROR_LOG_FILE = OUTPUT_DIR / "failed_circuits_log.json"

# ============================= 工具函數 =============================

def load_progress() -> Dict:
    """載入處理進度（斷點續傳）"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"processed": [], "failed": [], "last_update": None}

def save_progress(progress: Dict):
    """儲存處理進度"""
    progress["last_update"] = datetime.now().isoformat()
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)

def log_failed_circuit(circuit_file: str, error_message: str):
    """記錄失敗的賽道"""
    error_log = {"circuits": []}
    
    if ERROR_LOG_FILE.exists():
        with open(ERROR_LOG_FILE, 'r', encoding='utf-8') as f:
            error_log = json.load(f)
    
    error_log["circuits"].append({
        "file": circuit_file,
        "error": error_message,
        "timestamp": datetime.now().isoformat()
    })
    
    with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(error_log, f, indent=2, ensure_ascii=False)
    
    print(f"   ⚠️  錯誤已記錄至: {ERROR_LOG_FILE}")

def extract_circuit_id(filename: str) -> str:
    """從檔案名稱提取賽道 ID（例：jp-1962.geojson → jp-1962）"""
    return filename.replace(".geojson", "")

def parse_country_code(filename: str) -> str:
    """提取國家代碼（例：jp-1962.geojson → jp）"""
    return filename.split("-")[0]

def parse_year(filename: str) -> str:
    """提取年份（例：jp-1962.geojson → 1962）"""
    return filename.split("-")[1].replace(".geojson", "")

def load_circuit_geojson(circuit_file: Path) -> Optional[Dict]:
    """載入賽道 GeoJSON 檔案"""
    try:
        with open(circuit_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"   ❌ 載入失敗: {e}")
        return None

def extract_coordinates(geojson_data: Dict) -> List[Tuple[float, float]]:
    """從 GeoJSON 提取座標列表 [(lon, lat), ...]"""
    features = geojson_data.get("features", [])
    if not features:
        raise ValueError("GeoJSON 沒有 features")
    
    geometry = features[0].get("geometry", {})
    coordinates = geometry.get("coordinates", [])
    
    if not coordinates:
        raise ValueError("找不到座標資料")
    
    return coordinates

def fetch_elevation_batch(coordinates: List[Tuple[float, float]]) -> List[Optional[float]]:
    """
    一次性查詢所有座標點的高程資料（無批次限制）
    
    Args:
        coordinates: GPS 座標列表 [(lon, lat), ...]
    
    Returns:
        elevations: 高程列表（失敗的點返回 None）
    """
    total_points = len(coordinates)
    
    print(f"   🌐 查詢高程資料... ({total_points} 個點，一次性查詢)")
    
    # 轉換為 API 格式
    locations = [
        {"latitude": lat, "longitude": lon}
        for lon, lat in coordinates
    ]
    
    payload = {"locations": locations}
    
    try:
        print(f"      ⏳ 發送 API 請求 (可能需要 10-30 秒)...", end=" ")
        response = requests.post(OPEN_ELEVATION_API_URL, json=payload, timeout=API_TIMEOUT)
        
        if response.status_code == 200:
            result = response.json()
            elevations = [point["elevation"] for point in result["results"]]
            
            if len(elevations) == total_points:
                print(f"✅ 成功")
                print(f"      📊 高度範圍: {min(elevations):.0f}m - {max(elevations):.0f}m")
                return elevations
            else:
                print(f"⚠️  返回點數不匹配 ({len(elevations)}/{total_points})")
                # 補齊缺失的點
                while len(elevations) < total_points:
                    elevations.append(None)
                return elevations
        else:
            print(f"❌ HTTP {response.status_code}")
            return [None] * total_points
            
    except requests.Timeout:
        print(f"❌ 請求超時 (>{API_TIMEOUT}秒)")
        return [None] * total_points
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return [None] * total_points

def calculate_track_distances(coordinates: List[Tuple[float, float]]) -> List[float]:
    """計算賽道累積距離（公里）"""
    distances = [0.0]
    
    for i in range(1, len(coordinates)):
        lon1, lat1 = coordinates[i-1]
        lon2, lat2 = coordinates[i]
        
        # 簡化的平面距離計算
        lat_avg = (lat1 + lat2) / 2
        dx = (lon2 - lon1) * 111 * np.cos(np.radians(lat_avg))
        dy = (lat2 - lat1) * 111
        
        distance = np.sqrt(dx**2 + dy**2)
        distances.append(distances[-1] + distance)
    
    return distances

def calculate_elevation_statistics(coordinates_with_elevation: List[Dict]) -> Dict:
    """計算高程統計資訊"""
    elevations = [c["elevation"] for c in coordinates_with_elevation if c["elevation"] is not None]
    distances = [c["distance_km"] for c in coordinates_with_elevation if c["elevation"] is not None]
    
    if not elevations:
        return {
            "min_elevation": None,
            "max_elevation": None,
            "elevation_change": None,
            "avg_elevation": None,
            "max_elevation_point": None,
            "min_elevation_point": None
        }
    
    min_elev = min(elevations)
    max_elev = max(elevations)
    min_idx = elevations.index(min_elev)
    max_idx = elevations.index(max_elev)
    
    return {
        "min_elevation": round(min_elev, 1),
        "max_elevation": round(max_elev, 1),
        "elevation_change": round(max_elev - min_elev, 1),
        "avg_elevation": round(np.mean(elevations), 1),
        "max_elevation_point": {
            "distance_km": round(distances[max_idx], 3),
            "elevation": round(max_elev, 1)
        },
        "min_elevation_point": {
            "distance_km": round(distances[min_idx], 3),
            "elevation": round(min_elev, 1)
        }
    }

def generate_circuit_elevation_json(circuit_file: str, geojson_data: Dict, 
                                   coordinates: List[Tuple[float, float]], 
                                   elevations: List[Optional[float]]) -> Dict:
    """生成新的賽道高程 JSON 資料"""
    circuit_id = extract_circuit_id(circuit_file)
    properties = geojson_data["features"][0]["properties"]
    
    # 計算距離
    distances = calculate_track_distances(coordinates)
    
    # 組合座標、高程、距離
    coordinates_with_elevation = [
        {
            "lon": round(lon, 6),
            "lat": round(lat, 6),
            "elevation": round(elev, 1) if elev is not None else None,
            "distance_km": round(dist, 3)
        }
        for (lon, lat), elev, dist in zip(coordinates, elevations, distances)
    ]
    
    # 計算高程統計
    elevation_stats = calculate_elevation_statistics(coordinates_with_elevation)
    
    # 組裝完整 JSON
    output_data = {
        "circuit_id": circuit_id,
        "basic_info": {
            "name": properties.get("Name", "Unknown"),
            "location": properties.get("Location", "Unknown"),
            "country": properties.get("Country", parse_country_code(circuit_file).upper()),
            "length_meters": properties.get("length", None),
            "opened_year": properties.get("opened", None),
            "first_gp_year": properties.get("first_gp", None),
            "reference_altitude": properties.get("altitude", None)
        },
        "coordinates": coordinates_with_elevation,
        "elevation_profile": elevation_stats,
        "metadata": {
            "total_points": len(coordinates),
            "valid_elevation_points": len([e for e in elevations if e is not None]),
            "track_length_calculated_km": round(distances[-1], 3),
            "generated_timestamp": datetime.now().isoformat(),
            "data_source": "Open-Elevation API v1"
        }
    }
    
    return output_data

def save_circuit_data(output_data: Dict, circuit_file: str):
    """儲存賽道資料到 JSON 檔案"""
    country_code = parse_country_code(circuit_file)
    year = parse_year(circuit_file)
    output_filename = f"{country_code}_{year}_elevation_data.json"
    output_path = OUTPUT_DIR / output_filename
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ 已儲存至: {output_filename}")
    return output_filename

# ============================= 主處理流程 =============================

def process_single_circuit(circuit_file: str, circuit_num: int, total_circuits: int) -> bool:
    """
    處理單一賽道
    
    Returns:
        success: 是否成功處理
    """
    print(f"\n{'='*60}")
    print(f"[{circuit_num}/{total_circuits}] 處理賽道: {circuit_file}")
    print(f"{'='*60}")
    
    try:
        # 1. 載入 GeoJSON
        circuit_path = CIRCUITS_DIR / circuit_file
        geojson_data = load_circuit_geojson(circuit_path)
        
        if geojson_data is None:
            raise Exception("無法載入 GeoJSON 檔案")
        
        circuit_name = geojson_data["features"][0]["properties"].get("Name", "Unknown")
        print(f"   📍 賽道名稱: {circuit_name}")
        
        # 2. 提取座標
        coordinates = extract_coordinates(geojson_data)
        print(f"   ✅ 提取 {len(coordinates)} 個座標點")
        
        # 3. 查詢高程資料
        elevations = fetch_elevation_batch(coordinates)
        
        # 檢查是否有有效高程資料
        valid_count = len([e for e in elevations if e is not None])
        if valid_count == 0:
            raise Exception("所有高程查詢失敗，無有效資料")
        
        # 4. 生成新 JSON
        output_data = generate_circuit_elevation_json(circuit_file, geojson_data, 
                                                     coordinates, elevations)
        
        # 5. 儲存檔案
        save_circuit_data(output_data, circuit_file)
        
        # 6. 顯示統計摘要
        stats = output_data["elevation_profile"]
        print(f"\n   📊 高程統計:")
        print(f"      最高點: {stats['max_elevation']}m (距離 {stats['max_elevation_point']['distance_km']}km)")
        print(f"      最低點: {stats['min_elevation']}m (距離 {stats['min_elevation_point']['distance_km']}km)")
        print(f"      高低差: {stats['elevation_change']}m")
        
        return True
        
    except Exception as e:
        print(f"\n   ❌ 處理失敗: {e}")
        log_failed_circuit(circuit_file, str(e))
        return False

def main():
    """主程式"""
    print("=" * 70)
    print("🏁 F1 賽道高程資料批次生成工具 (2020-2025 賽季)")
    print("=" * 70)
    
    # 確保輸出目錄存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 載入處理進度
    progress = load_progress()
    processed_circuits = set(progress.get("processed", []))
    
    print(f"\n📂 賽道檔案目錄: {CIRCUITS_DIR}")
    print(f"📂 輸出目錄: {OUTPUT_DIR}")
    print(f"📋 目標賽道數量: {len(CIRCUITS_2020_2025)}")
    
    if processed_circuits:
        print(f"♻️  已處理賽道: {len(processed_circuits)} 條（斷點續傳）")
    
    # 篩選待處理賽道
    circuits_to_process = [c for c in CIRCUITS_2020_2025 if c not in processed_circuits]
    
    if not circuits_to_process:
        print("\n✅ 所有賽道已處理完成！")
        return
    
    print(f"⏳ 待處理賽道: {len(circuits_to_process)} 條")
    print(f"\n⚙️  API 配置:")
    print(f"   - 查詢模式: 一次性查詢所有座標點（無批次限制）")
    print(f"   - 請求超時: {API_TIMEOUT} 秒")
    print(f"   - 每 {DELAY_EVERY_N_CIRCUITS} 條賽道延遲: {LONG_DELAY_SECONDS} 秒")
    
    input("\n按 Enter 開始處理...")
    
    # 批次處理賽道
    start_time = time.time()
    success_count = 0
    failed_count = 0
    
    for i, circuit_file in enumerate(circuits_to_process, 1):
        success = process_single_circuit(circuit_file, i, len(circuits_to_process))
        
        if success:
            success_count += 1
            processed_circuits.add(circuit_file)
            progress["processed"] = list(processed_circuits)
            save_progress(progress)
        else:
            failed_count += 1
            progress["failed"].append(circuit_file)
            save_progress(progress)
        
        # 每 N 條賽道延遲
        if i % DELAY_EVERY_N_CIRCUITS == 0 and i < len(circuits_to_process):
            print(f"\n⏸️  已處理 {i} 條賽道，延遲 {LONG_DELAY_SECONDS} 秒...")
            time.sleep(LONG_DELAY_SECONDS)
    
    # 完成統計
    elapsed_time = time.time() - start_time
    
    print("\n" + "=" * 70)
    print("✅ 批次處理完成！")
    print("=" * 70)
    print(f"📊 統計摘要:")
    print(f"   ✅ 成功處理: {success_count} 條賽道")
    print(f"   ❌ 失敗: {failed_count} 條賽道")
    print(f"   ⏱️  總耗時: {elapsed_time/60:.1f} 分鐘")
    print(f"\n📁 輸出位置: {OUTPUT_DIR.absolute()}")
    
    if failed_count > 0:
        print(f"\n⚠️  失敗賽道記錄: {ERROR_LOG_FILE}")
        print("   請稍後重新執行此腳本，將自動跳過已處理的賽道")

if __name__ == "__main__":
    main()
