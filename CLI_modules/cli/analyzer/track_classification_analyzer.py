#!/usr/bin/env python3
"""Track Classification Analyzer (Function 73).

使用 K-Means 自動聚類賽道，基於實際賽道特徵數據：
- F48: 速度統計
- F54: 油門比例
- F34: 煞車性能
- F47: 彎道分析
- F1:  天氣數據

產出賽道分類以供 XGBoost 訓練器使用，目標是降低 MAE 從 0.986s 到 0.70s。
"""

from __future__ import annotations

import json
import os
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings('ignore', category=FutureWarning)

_JSON_DIR = "json"
_OUTPUT_DIR = "json"  # ✅ 所有 CLI 分析結果統一保存在 json/ 目錄
_REPORTS_DIR = "reports"


@dataclass
class TrackFeatures:
    """賽道特徵容器 (方案 B: 增強版)"""
    track_name: str
    year: int
    avg_speed: Optional[float] = None
    max_speed: Optional[float] = None
    throttle_ratio: Optional[float] = None
    brake_intensity: Optional[float] = None
    corner_count: Optional[int] = None
    air_temp: Optional[float] = None
    track_temp: Optional[float] = None
    # 新增特徵 (方案 B)
    track_length_km: Optional[float] = None  # 賽道長度
    straight_line_ratio: Optional[float] = None  # 直線段比例 (高速賽道特徵)
    avg_corner_speed: Optional[float] = None  # 平均彎道速度
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'track_name': self.track_name,
            'year': self.year,
            'avg_speed': self.avg_speed,
            'max_speed': self.max_speed,
            'throttle_ratio': self.throttle_ratio,
            'brake_intensity': self.brake_intensity,
            'corner_count': self.corner_count,
            'air_temp': self.air_temp,
            'track_temp': self.track_temp,
            'track_length_km': self.track_length_km,
            'straight_line_ratio': self.straight_line_ratio,
            'avg_corner_speed': self.avg_corner_speed,
        }


def run_track_classification_analysis(
    features_dir: str = _JSON_DIR,
    n_clusters: int = 3,
    session: str = "FP3",
    validate: bool = True,
    save_output: bool = True,
) -> Dict[str, Any]:
    """
    Function 73 入口函數：賽道分類分析
    
    Parameters
    ----------
    features_dir : str
        特徵 JSON 檔案目錄（預設: json/）
    n_clusters : int
        聚類數量（預設: 3 = 高速/街道/混合）
    session : str
        會話類型（預設: FP3）
    validate : bool
        是否與公認分類對比驗證
    save_output : bool
        是否保存輸出檔案
    
    Returns
    -------
    Dict[str, Any]
        標準化結果字典
    """
    print("[INFO] 啟動 Function 73 - 賽道分類分析 (K-Means)")
    print(f"[INFO] 特徵目錄: {features_dir}")
    print(f"[INFO] 聚類數量: {n_clusters}")
    print(f"[INFO] 會話類型: {session}")
    
    # 步驟 1: 提取賽道特徵
    print("\n[步驟 1/5] 從 JSON 提取賽道特徵...")
    track_features = _extract_track_features(features_dir, session)
    
    if not track_features:
        return {
            "success": False,
            "message": "找不到足夠的賽道特徵數據",
            "function_id": "73",
            "data": None,
        }
    
    print(f"[INFO] 成功提取 {len(track_features)} 條賽道數據")
    
    # 步驟 2: 構建特徵矩陣
    print("\n[步驟 2/5] 構建特徵矩陣...")
    features_df = _build_features_dataframe(track_features)
    
    # 步驟 3: K-Means 聚類
    print(f"\n[步驟 3/5] 執行 K-Means 聚類 (k={n_clusters})...")
    classification_result = _perform_kmeans_clustering(features_df, n_clusters)
    
    # 步驟 4: 手動驗證（與公認分類對比）
    validation_result = None
    if validate:
        print("\n[步驟 4/5] 驗證分類結果...")
        validation_result = _validate_classification(classification_result)
    
    # 步驟 5: 保存輸出
    metadata = _build_metadata(n_clusters, session, len(track_features))
    
    result = {
        "success": True,
        "message": f"賽道分類完成，共 {len(track_features)} 條賽道",
        "function_id": "73",
        "data": {
            "metadata": metadata,
            "classification": classification_result,
            "validation": validation_result,
            "total_tracks": len(track_features),
        },
    }
    
    if save_output:
        print("\n[步驟 5/5] 保存分類結果...")
        output_paths = _save_classification_output(
            metadata, 
            classification_result, 
            validation_result,
            session=session  # ✅ 傳入 session 參數用於檔名
        )
        result["output_files"] = output_paths
        print(f"[INFO] 分類結果已保存: {output_paths['classification']}")
    
    return result


def _extract_track_features(features_dir: str, session: str) -> List[TrackFeatures]:
    """
    從 JSON 檔案提取賽道特徵
    
    JSON 檔案模式：
    - F48: all_drivers_straight_line_speed_{year}_{race}_{session}.json
    - F54: driver_throttle_ratio_{year}_{race}_{session}.json
    - F34: brake_performance_{year}_{race}_{session}.json
    - F47: all_drivers_cornering_analysis_{year}_{race}_{session}.json
    - F1:  enhanced_rain_analysis_{year}_{race}_{session}.json
    """
    features_list = []
    json_dir = Path(features_dir)
    
    # 搜索所有 F48 檔案作為基準（速度檔案最完整）
    speed_pattern = f"all_drivers_straight_line_speed_*_{session}.json"
    speed_files = list(json_dir.glob(speed_pattern))
    
    print(f"[DEBUG] 找到 {len(speed_files)} 個速度檔案")
    
    for speed_file in speed_files:
        # 解析檔名：all_drivers_straight_line_speed_2024_Japan_FP3.json
        parts = speed_file.stem.split('_')
        if len(parts) < 6:
            continue
            
        year = int(parts[-3])
        track_name = parts[-2]
        
        # 提取各類特徵
        features = TrackFeatures(track_name=track_name, year=year)
        
        # F48: 速度 + 賽道長度
        speed_data = _load_json_safe(speed_file)
        if speed_data:
            features.avg_speed = _extract_avg_speed(speed_data)
            features.max_speed = _extract_max_speed(speed_data)
            features.track_length_km = _extract_track_length(speed_data)  # 新增
        
        # F54: 油門 + 直線段比例
        throttle_file = json_dir / f"driver_throttle_ratio_{year}_{track_name}_{session}.json"
        throttle_data = _load_json_safe(throttle_file)
        if throttle_data:
            features.throttle_ratio = _extract_throttle_ratio(throttle_data)
            features.straight_line_ratio = _extract_straight_line_ratio(throttle_data)  # 新增
        
        # F34: 煞車
        brake_file = json_dir / f"brake_performance_{year}_{track_name}_{session}.json"
        brake_data = _load_json_safe(brake_file)
        if brake_data:
            features.brake_intensity = _extract_brake_intensity(brake_data)
        
        # F47: 彎道 + 平均彎道速度
        corner_file = json_dir / f"all_drivers_cornering_analysis_{year}_{track_name}_{session}.json"
        corner_data = _load_json_safe(corner_file)
        if corner_data:
            features.corner_count = _extract_corner_count(corner_data)
            features.avg_corner_speed = _extract_avg_corner_speed(corner_data)  # 新增
        
        # F1: 天氣
        weather_file = json_dir / f"enhanced_rain_analysis_{year}_{track_name}_{session}.json"
        weather_data = _load_json_safe(weather_file)
        if weather_data:
            features.air_temp, features.track_temp = _extract_temperature(weather_data)
        
        # 只保留有足夠特徵的賽道（至少 3 個特徵）
        valid_features = sum([
            features.avg_speed is not None,
            features.throttle_ratio is not None,
            features.brake_intensity is not None,
            features.corner_count is not None,
        ])
        
        if valid_features >= 3:
            features_list.append(features)
        else:
            print(f"[SKIP] {track_name} {year}: 特徵不足 ({valid_features}/4)")
    
    # 去重策略：每個賽道只保留最新年份數據
    deduplicated_features = _deduplicate_by_latest_year(features_list)
    print(f"[INFO] 去重後保留 {len(deduplicated_features)} 條賽道數據 (原始: {len(features_list)})")
    
    return deduplicated_features


def _load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """安全載入 JSON 檔案"""
    try:
        if not file_path.exists():
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARNING] 無法載入 {file_path.name}: {e}")
        return None


def _extract_avg_speed(speed_data: Dict[str, Any]) -> Optional[float]:
    """從 F48 JSON 提取平均速度"""
    try:
        drivers = speed_data.get('data', {}).get('driver_speeds', [])
        if not drivers:
            return None
        # F48 只有 max_speed_kmh，沒有 avg_speed，用所有車手的平均最大速度代替
        speeds = [d.get('max_speed_kmh') for d in drivers if d.get('max_speed_kmh')]
        return float(np.mean(speeds)) if speeds else None
    except Exception:
        return None


def _extract_max_speed(speed_data: Dict[str, Any]) -> Optional[float]:
    """從 F48 JSON 提取最大速度"""
    try:
        drivers = speed_data.get('data', {}).get('driver_speeds', [])
        if not drivers:
            return None
        speeds = [d.get('max_speed_kmh') for d in drivers if d.get('max_speed_kmh')]
        return float(np.max(speeds)) if speeds else None
    except Exception:
        return None


def _extract_throttle_ratio(throttle_data: Dict[str, Any]) -> Optional[float]:
    """從 F54 JSON 提取油門比例"""
    try:
        # 新格式：data.analysis.summary
        summary = throttle_data.get('data', {}).get('analysis', {}).get('summary')
        if summary and 'mean_full_throttle_ratio' in summary:
            return float(summary['mean_full_throttle_ratio'])
        
        # 舊格式：analysis.summary
        summary = throttle_data.get('analysis', {}).get('summary')
        if summary and 'mean_full_throttle_ratio' in summary:
            return float(summary['mean_full_throttle_ratio'])
        
        return None
    except Exception:
        return None


def _extract_brake_intensity(brake_data: Dict[str, Any]) -> Optional[float]:
    """從 F34 JSON 提取煞車強度"""
    try:
        drivers = brake_data.get('data', {}).get('driver_brakes', [])
        if not drivers:
            return None
        intensities = [d.get('max_deceleration_ms2') for d in drivers if d.get('max_deceleration_ms2')]
        return float(np.mean(intensities)) if intensities else None
    except Exception:
        return None


def _extract_corner_count(corner_data: Dict[str, Any]) -> Optional[int]:
    """從 F47 JSON 提取彎道數量"""
    try:
        # F47 結構：selected_corners = {'low_speed': [...], 'mid_speed': [...], 'high_speed': [...]}
        selected_corners = corner_data.get('selected_corners', {})
        if not selected_corners:
            return None
        
        # 計算所有類別的彎道總數
        total_corners = 0
        for category in ['low_speed', 'mid_speed', 'high_speed']:
            corners_in_category = selected_corners.get(category, [])
            total_corners += len(corners_in_category)
        
        return total_corners if total_corners > 0 else None
    except Exception:
        return None


def _extract_temperature(weather_data: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    """從 F1 JSON 提取溫度"""
    try:
        data = weather_data.get('data', {})
        air_temp = data.get('average_air_temp')
        track_temp = data.get('average_track_temp')
        return (float(air_temp) if air_temp else None, 
                float(track_temp) if track_temp else None)
    except Exception:
        return None, None


def _extract_track_length(speed_data: Dict[str, Any]) -> Optional[float]:
    """從 F48 JSON 提取賽道長度（方案 B 新增）"""
    try:
        # 嘗試從 metadata 獲取賽道長度
        metadata = speed_data.get('data', {}).get('metadata', {})
        track_length = metadata.get('track_length_km')
        if track_length:
            return float(track_length)
        
        # 如果 metadata 沒有，嘗試從 driver_speeds 推算
        # 使用最大 distance_m 作為賽道長度估計
        drivers = speed_data.get('data', {}).get('driver_speeds', [])
        if drivers:
            max_distances = [d.get('distance_m', 0) for d in drivers if d.get('distance_m')]
            if max_distances:
                # 賽道長度通常是最大 distance 的整數倍
                max_dist_km = max(max_distances) / 1000
                return round(max_dist_km, 3)
        
        return None
    except Exception:
        return None


def _extract_straight_line_ratio(throttle_data: Dict[str, Any]) -> Optional[float]:
    """從 F54 JSON 提取直線段比例（方案 B 新增）"""
    try:
        # 油門比例高 = 直線段多 = 高速賽道特徵
        # full_throttle_ratio 已經代表直線段比例
        summary = throttle_data.get('data', {}).get('analysis', {}).get('summary', {})
        if not summary:
            summary = throttle_data.get('analysis', {}).get('summary', {})
        
        full_throttle = summary.get('mean_full_throttle_ratio')
        if full_throttle:
            return float(full_throttle)
        
        return None
    except Exception:
        return None


def _extract_avg_corner_speed(corner_data: Dict[str, Any]) -> Optional[float]:
    """從 F47 JSON 提取平均彎道速度（方案 B 新增）"""
    try:
        selected_corners = corner_data.get('selected_corners', {})
        if not selected_corners:
            return None
        
        # 收集所有彎道的最小速度（彎道頂點速度）
        corner_speeds = []
        for category in ['low_speed', 'mid_speed', 'high_speed']:
            corners = selected_corners.get(category, [])
            for corner in corners:
                min_speed = corner.get('min_speed_kmh')
                if min_speed:
                    corner_speeds.append(float(min_speed))
        
        return float(np.mean(corner_speeds)) if corner_speeds else None
    except Exception:
        return None


def _deduplicate_by_latest_year(features_list: List[TrackFeatures]) -> List[TrackFeatures]:
    """去重：每個賽道只保留最新年份數據（方案 B 新增）"""
    # 按賽道名稱分組
    track_groups = {}
    for feature in features_list:
        track_name = feature.track_name
        if track_name not in track_groups:
            track_groups[track_name] = []
        track_groups[track_name].append(feature)
    
    # 每組只保留最新年份
    deduplicated = []
    for track_name, group in track_groups.items():
        # 按年份降序排序，取第一個（最新）
        latest = sorted(group, key=lambda x: x.year, reverse=True)[0]
        deduplicated.append(latest)
    
    return deduplicated


def _build_features_dataframe(track_features: List[TrackFeatures]) -> pd.DataFrame:
    """構建特徵矩陣 DataFrame（方案 B: 增強版）"""
    data = []
    for tf in track_features:
        data.append({
            'track_name': tf.track_name,
            'year': tf.year,
            # 原始特徵
            'avg_speed': tf.avg_speed or 0,
            'max_speed': tf.max_speed or 0,
            'throttle_ratio': tf.throttle_ratio or 0,
            'brake_intensity': tf.brake_intensity or 0,
            'corner_count': tf.corner_count or 0,
            # 新增特徵（方案 B）
            'track_length_km': tf.track_length_km or 5.0,  # 預設 5km
            'straight_line_ratio': tf.straight_line_ratio or tf.throttle_ratio or 0,
            'avg_corner_speed': tf.avg_corner_speed or 150.0,  # 預設 150 km/h
        })
    
    df = pd.DataFrame(data)
    print(f"[INFO] 特徵矩陣形狀: {df.shape} (包含 {len(df.columns)-2} 個特徵)")
    print(f"[INFO] 缺失值統計:\n{df.isnull().sum()}")
    
    return df


def _perform_kmeans_clustering(features_df: pd.DataFrame, n_clusters: int) -> Dict[str, Any]:
    """執行 K-Means 聚類（方案 B: 使用增強特徵 + 權重調整）"""
    # 選擇用於聚類的特徵（包含新特徵）
    feature_cols = [
        'avg_speed', 'max_speed', 'throttle_ratio', 'brake_intensity', 'corner_count',
        'track_length_km', 'straight_line_ratio', 'avg_corner_speed'  # 新增特徵
    ]
    
    # 特徵權重：強調高速賽道特徵
    feature_weights = {
        'avg_speed': 1.0,           # 基準
        'max_speed': 1.5,           # 提高：高速 vs 低速的關鍵
        'throttle_ratio': 1.0,      # 基準
        'brake_intensity': 1.0,     # 基準
        'corner_count': 0.8,        # 降低：差異不大
        'track_length_km': 1.3,     # 提高：街道賽識別
        'straight_line_ratio': 2.0, # 大幅提高：高速賽道最關鍵特徵
        'avg_corner_speed': 0.5,    # 降低：數據不準確
    }
    
    X = features_df[feature_cols].values
    
    # 標準化
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 應用特徵權重
    weights = np.array([feature_weights[col] for col in feature_cols])
    X_weighted = X_scaled * weights
    
    print(f"[INFO] 特徵權重: straight_line_ratio=2.0x, max_speed=1.5x, track_length=1.3x")
    
    # K-Means 聚類
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_weighted)
    
    # 添加標籤到 DataFrame
    features_df['cluster'] = labels
    
    # 計算聚類中心的原始值（需要反權重 + 反標準化）
    centers_weighted = kmeans.cluster_centers_
    centers_scaled = centers_weighted / weights  # 先移除權重
    centers_original = scaler.inverse_transform(centers_scaled)  # 再反標準化
    
    # 按聚類分組
    clusters = {}
    cluster_names = _assign_cluster_names(centers_original, feature_cols)
    
    for i in range(n_clusters):
        cluster_tracks = features_df[features_df['cluster'] == i]
        unique_tracks = cluster_tracks.groupby('track_name').size().reset_index(name='count')
        
        clusters[cluster_names[i]] = {
            'cluster_id': int(i),
            'tracks': unique_tracks['track_name'].tolist(),
            'track_count': len(unique_tracks),
            'center_features': {
                feature_cols[j]: float(centers_original[i][j])
                for j in range(len(feature_cols))
            }
        }
    
    print(f"\n[結果] 聚類完成:")
    for name, data in clusters.items():
        print(f"  {name}: {data['track_count']} 條賽道")
        print(f"    代表賽道: {', '.join(data['tracks'][:5])}")
    
    return clusters


def _assign_cluster_names(centers: np.ndarray, feature_cols: List[str]) -> List[str]:
    """根據聚類中心特徵自動命名"""
    names = []
    
    # 找出特徵索引
    speed_idx = feature_cols.index('avg_speed')
    brake_idx = feature_cols.index('brake_intensity')
    corner_idx = feature_cols.index('corner_count')
    
    for center in centers:
        avg_speed = center[speed_idx]
        brake_intensity = center[brake_idx]
        corner_count = center[corner_idx]
        
        # 根據特徵值判斷賽道類型
        if avg_speed > 220:  # 高速賽道
            names.append('high_speed')
        elif corner_count > 18 or brake_intensity < 15:  # 街道賽道
            names.append('street')
        else:  # 混合賽道
            names.append('mixed')
    
    # 確保名稱唯一
    if len(set(names)) < len(names):
        names = [f'cluster_{i}' for i in range(len(names))]
    
    return names


def _validate_classification(classification: Dict[str, Any]) -> Dict[str, Any]:
    """與公認分類對比驗證"""
    # F1 公認的賽道分類
    KNOWN_CLASSIFICATION = {
        'high_speed': ['Monza', 'Spa', 'Silverstone', 'Baku', 'Jeddah'],
        'street': ['Monaco', 'Singapore', 'Las Vegas'],
        'mixed': ['Suzuka', 'Barcelona', 'Austin', 'Interlagos', 'Spielberg'],
    }
    
    validation_results = {}
    total_matches = 0
    total_known = sum(len(tracks) for tracks in KNOWN_CLASSIFICATION.values())
    
    for category, known_tracks in KNOWN_CLASSIFICATION.items():
        predicted_category = None
        for cluster_name, cluster_data in classification.items():
            if any(track in cluster_data['tracks'] for track in known_tracks):
                predicted_category = cluster_name
                break
        
        matches = []
        mismatches = []
        
        for track in known_tracks:
            # 檢查是否在預測的類別中
            found_in_cluster = None
            for cluster_name, cluster_data in classification.items():
                if track in cluster_data['tracks']:
                    found_in_cluster = cluster_name
                    break
            
            if found_in_cluster == predicted_category:
                matches.append(track)
                total_matches += 1
            else:
                mismatches.append({
                    'track': track,
                    'expected': category,
                    'predicted': found_in_cluster or 'not_found'
                })
        
        validation_results[category] = {
            'predicted_cluster': predicted_category,
            'matches': matches,
            'mismatches': mismatches,
            'accuracy': len(matches) / len(known_tracks) if known_tracks else 0
        }
    
    overall_accuracy = total_matches / total_known if total_known > 0 else 0
    
    print(f"\n[驗證] 整體準確度: {overall_accuracy:.1%}")
    for category, result in validation_results.items():
        print(f"  {category}: {result['accuracy']:.1%} ({len(result['matches'])}/{len(result['matches']) + len(result['mismatches'])})")
    
    return {
        'overall_accuracy': overall_accuracy,
        'by_category': validation_results,
        'total_known_tracks': total_known,
        'total_matches': total_matches,
    }


def _build_metadata(n_clusters: int, session: str, total_tracks: int) -> Dict[str, Any]:
    """構建元數據（方案 B: 包含新特徵）"""
    return {
        'function_id': 73,
        'function_name': 'Track Classification Analysis (Enhanced)',
        'analysis_timestamp': datetime.utcnow().isoformat(),
        'n_clusters': n_clusters,
        'session': session,
        'total_tracks': total_tracks,
        'features_used': [
            'avg_speed', 'max_speed', 'throttle_ratio', 'brake_intensity', 'corner_count',
            'track_length_km', 'straight_line_ratio', 'avg_corner_speed'  # 方案 B 新增
        ],
        'algorithm': 'K-Means',
        'data_version': '2.0.0',  # 升級到 2.0
        'improvements': 'Added track length, straight line ratio, and corner speed features; implemented deduplication',
    }


def _save_classification_output(
    metadata: Dict[str, Any],
    classification: Dict[str, Any],
    validation: Optional[Dict[str, Any]],
    session: str = "FP3"
) -> Dict[str, str]:
    """保存分類結果到檔案"""
    # 創建輸出目錄
    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    os.makedirs(_REPORTS_DIR, exist_ok=True)
    
    # ✅ 使用標準命名格式：track_classification_{session}.json
    classification_filename = f'track_classification_{session}.json'
    classification_path = os.path.join(_OUTPUT_DIR, classification_filename)
    
    # 保存分類結果（供 Function 72 使用）
    with open(classification_path, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': metadata,
            'classification': classification,
        }, f, ensure_ascii=False, indent=2)
    
    # 保存驗證報告（詳細版，包含驗證細節）
    validation_filename = f'track_classification_validation_{session}.json'
    report_path = os.path.join(_REPORTS_DIR, validation_filename)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': metadata,
            'classification': classification,
            'validation': validation,
        }, f, ensure_ascii=False, indent=2)
    
    return {
        'classification': os.path.abspath(classification_path),
        'validation_report': os.path.abspath(report_path),
    }


__all__ = ['run_track_classification_analysis']
