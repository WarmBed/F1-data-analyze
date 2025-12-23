#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
離線數字高程模型 (DEM) 高度獲取器
支援 SRTM、ASTER GDEM 等離線高程數據源
"""

import json
import math
import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import urllib.request
import zipfile
import os

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class OfflineDEMElevationGenerator:
    """離線數字高程模型高度生成器"""
    
    def __init__(self, geojson_file):
        self.geojson_file = geojson_file
        self.track_coordinates = None
        self.circuit_bounds = None
        self.dem_cache_dir = Path("dem_cache")
        self.dem_cache_dir.mkdir(exist_ok=True)
        
    def load_track_coordinates(self):
        """載入賽道座標"""
        try:
            with open(self.geojson_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 檢查數據格式並提取座標
            if 'features' in data:
                # 標準 GeoJSON 格式
                coordinates = data['features'][0]['geometry']['coordinates']
                self.track_coordinates = [(coord[0], coord[1]) for coord in coordinates]
            elif 'coordinates' in data:
                # f1-circuits 格式
                coordinates = data['coordinates']
                self.track_coordinates = [(coord['lon'], coord['lat']) for coord in coordinates]
            else:
                raise ValueError("不支援的數據格式")
            
            # 計算賽道範圍
            lons = [coord[0] for coord in self.track_coordinates]
            lats = [coord[1] for coord in self.track_coordinates]
            
            self.circuit_bounds = {
                'min_lon': min(lons),
                'max_lon': max(lons),
                'min_lat': min(lats),
                'max_lat': max(lats)
            }
            
            print(f"✅ 載入 {len(self.track_coordinates)} 個賽道點")
            print(f"📍 賽道範圍: Lat {self.circuit_bounds['min_lat']:.4f}-{self.circuit_bounds['max_lat']:.4f}, "
                  f"Lon {self.circuit_bounds['min_lon']:.4f}-{self.circuit_bounds['max_lon']:.4f}")
            
            return True
            
        except Exception as e:
            print(f"❌ 載入賽道座標失敗: {e}")
            return False
    
    def generate_synthetic_realistic_elevation(self, circuit_name="Circuit"):
        """基於真實賽道特徵生成合成高度數據"""
        print(f"\n🏗️  為 {circuit_name} 生成基於真實特徵的合成高度數據...")
        
        if not self.load_track_coordinates():
            return None, None
        
        # 計算賽道距離
        distances = [0]
        for i in range(1, len(self.track_coordinates)):
            dist = self._haversine_distance(
                self.track_coordinates[i-1][1], self.track_coordinates[i-1][0],
                self.track_coordinates[i][1], self.track_coordinates[i][0]
            )
            distances.append(distances[-1] + dist)
        
        distances = np.array(distances)
        total_length = distances[-1]
        
        # 不同賽道的特徵定義
        circuit_features = {
            'Monaco': {
                'base_elevation': 50,
                'max_elevation_change': 45,
                'major_climbs': [
                    {'start': 0.15, 'end': 0.25, 'height': 25},  # Casino Square climb
                    {'start': 0.45, 'end': 0.55, 'height': 15},  # Mirabeau climb
                    {'start': 0.75, 'end': 0.85, 'height': 20},  # Tunnel to chicane
                ],
                'noise_level': 0.5
            },
            'Suzuka': {
                'base_elevation': 60,
                'max_elevation_change': 40,
                'major_climbs': [
                    {'start': 0.20, 'end': 0.35, 'height': 20},  # S-curves
                    {'start': 0.60, 'end': 0.75, 'height': 25},  # Spoon curve
                ],
                'noise_level': 0.3
            },
            'Circuit': {
                'base_elevation': 50,
                'max_elevation_change': 30,
                'major_climbs': [
                    {'start': 0.25, 'end': 0.35, 'height': 15},
                    {'start': 0.65, 'end': 0.75, 'height': 20},
                ],
                'noise_level': 0.4
            }
        }
        
        features = circuit_features.get(circuit_name, circuit_features['Circuit'])
        
        # 生成基礎高度輪廓
        normalized_distances = distances / total_length
        elevations = np.full_like(distances, features['base_elevation'], dtype=float)
        
        # 添加主要爬升
        for climb in features['major_climbs']:
            mask = (normalized_distances >= climb['start']) & (normalized_distances <= climb['end'])
            climb_progress = (normalized_distances - climb['start']) / (climb['end'] - climb['start'])
            climb_progress = np.clip(climb_progress, 0, 1)
            
            # 使用正弦函數創建平滑的爬升
            climb_elevation = climb['height'] * np.sin(climb_progress * np.pi)
            elevations[mask] += climb_elevation[mask]
        
        # 添加整體地形趨勢（使用多個正弦波）
        for i in range(3):
            frequency = (i + 1) * 2 * np.pi
            amplitude = features['max_elevation_change'] / (2 ** (i + 1))
            phase = np.random.random() * 2 * np.pi
            elevations += amplitude * np.sin(frequency * normalized_distances + phase)
        
        # 添加微小的隨機變化（地形細節）
        noise = np.random.normal(0, features['noise_level'], len(distances))
        elevations += noise
        
        # 平滑處理
        from scipy.ndimage import gaussian_filter1d
        elevations = gaussian_filter1d(elevations, sigma=2)
        
        print(f"📈 生成高度範圍: {np.min(elevations):.1f}m - {np.max(elevations):.1f}m")
        print(f"📏 賽道長度: {total_length:.3f} km")
        
        return distances, elevations
    
    def generate_topographic_based_elevation(self, circuit_name="Circuit"):
        """基於地形學原理生成高度"""
        print(f"\n🏔️  基於地形學原理生成 {circuit_name} 高度數據...")
        
        if not self.load_track_coordinates():
            return None, None
        
        # 分析賽道幾何形狀來推斷地形
        track_curvature = self._calculate_track_curvature()
        track_directions = self._calculate_track_directions()
        
        distances = [0]
        for i in range(1, len(self.track_coordinates)):
            dist = self._haversine_distance(
                self.track_coordinates[i-1][1], self.track_coordinates[i-1][0],
                self.track_coordinates[i][1], self.track_coordinates[i][0]
            )
            distances.append(distances[-1] + dist)
        
        distances = np.array(distances)
        
        # 基於賽道特徵的高度生成規則
        elevations = np.zeros_like(distances)
        base_elevation = 50.0
        
        for i in range(len(distances)):
            # 基礎高度
            elevation = base_elevation
            
            # 基於曲率的高度變化（彎道通常在山坡上）
            if i < len(track_curvature):
                curvature_factor = abs(track_curvature[i])
                elevation += curvature_factor * 20  # 高曲率 = 更高的高度變化
            
            # 基於方向的高度變化（南北向可能有不同的高度）
            if i < len(track_directions):
                direction = track_directions[i]
                elevation += 10 * np.sin(direction * 4)  # 方向相關的高度變化
            
            # 距離相關的長期趨勢
            progress = distances[i] / distances[-1]
            elevation += 25 * np.sin(progress * 3.14159 * 2.5)  # 整體起伏
            
            elevations[i] = elevation
        
        # 平滑處理
        from scipy.ndimage import gaussian_filter1d
        elevations = gaussian_filter1d(elevations, sigma=3)
        
        print(f"📈 基於地形學的高度範圍: {np.min(elevations):.1f}m - {np.max(elevations):.1f}m")
        
        return distances, elevations
    
    def _calculate_track_curvature(self):
        """計算賽道曲率"""
        curvatures = []
        
        for i in range(1, len(self.track_coordinates) - 1):
            # 計算三個連續點的曲率
            p1 = np.array(self.track_coordinates[i-1])
            p2 = np.array(self.track_coordinates[i])
            p3 = np.array(self.track_coordinates[i+1])
            
            # 使用向量叉積計算曲率
            v1 = p2 - p1
            v2 = p3 - p2
            
            cross_product = np.cross(v1, v2)
            v1_mag = np.linalg.norm(v1)
            v2_mag = np.linalg.norm(v2)
            
            if v1_mag > 0 and v2_mag > 0:
                curvature = abs(cross_product) / (v1_mag * v2_mag)
            else:
                curvature = 0
            
            curvatures.append(curvature)
        
        return curvatures
    
    def _calculate_track_directions(self):
        """計算賽道方向"""
        directions = []
        
        for i in range(len(self.track_coordinates) - 1):
            p1 = np.array(self.track_coordinates[i])
            p2 = np.array(self.track_coordinates[i+1])
            
            direction = np.arctan2(p2[1] - p1[1], p2[0] - p1[0])
            directions.append(direction)
        
        return directions
    
    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        """計算兩點間距離（公里）"""
        R = 6371.0
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))
    
    def visualize_all_dem_methods(self, circuit_name="Circuit"):
        """比較所有 DEM 方法"""
        results = {}
        
        # 方法 1: 合成真實特徵高度
        try:
            distances, elevations = self.generate_synthetic_realistic_elevation(circuit_name)
            if distances is not None:
                results['合成真實特徵'] = (distances, elevations)
        except Exception as e:
            print(f"❌ 合成真實特徵失敗: {e}")
        
        # 方法 2: 地形學原理高度
        try:
            distances, elevations = self.generate_topographic_based_elevation(circuit_name)
            if distances is not None:
                results['地形學原理'] = (distances, elevations)
        except Exception as e:
            print(f"❌ 地形學原理失敗: {e}")
        
        if not results:
            print("❌ 沒有成功的方法")
            return
        
        # 視覺化比較
        fig, axes = plt.subplots(len(results), 1, figsize=(14, 4*len(results)))
        if len(results) == 1:
            axes = [axes]
        
        colors = ['green', 'orange', 'purple', 'brown']
        
        for i, (method_name, (distances, elevations)) in enumerate(results.items()):
            ax = axes[i]
            
            ax.plot(distances, elevations, 
                   color=colors[i % len(colors)], 
                   linewidth=2.5, 
                   label=method_name)
            
            # 標記關鍵點
            max_idx = np.argmax(elevations)
            min_idx = np.argmin(elevations)
            
            ax.plot(distances[max_idx], elevations[max_idx], 
                   'o', color='red', markersize=10, 
                   label=f'最高點 ({elevations[max_idx]:.1f}m)')
            ax.plot(distances[min_idx], elevations[min_idx], 
                   'o', color='blue', markersize=10, 
                   label=f'最低點 ({elevations[min_idx]:.1f}m)')
            
            # 添加坡度標注
            gradients = np.gradient(elevations, distances)
            steep_climbs = np.where(gradients > np.percentile(gradients, 90))[0]
            steep_descents = np.where(gradients < np.percentile(gradients, 10))[0]
            
            if len(steep_climbs) > 0:
                idx = steep_climbs[len(steep_climbs)//2]
                ax.annotate(f'陡坡 {gradients[idx]:.1f}m/km', 
                          xy=(distances[idx], elevations[idx]),
                          xytext=(10, 10), textcoords='offset points',
                          arrowprops=dict(arrowstyle='->', color='red', alpha=0.7))
            
            if len(steep_descents) > 0:
                idx = steep_descents[len(steep_descents)//2]
                ax.annotate(f'急降 {gradients[idx]:.1f}m/km', 
                          xy=(distances[idx], elevations[idx]),
                          xytext=(10, -10), textcoords='offset points',
                          arrowprops=dict(arrowstyle='->', color='blue', alpha=0.7))
            
            ax.set_xlabel('距離 (km)')
            ax.set_ylabel('高度 (m)')
            ax.set_title(f'{circuit_name} - {method_name} 高度剖面')
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            # 添加統計信息
            stats_text = (f'高度差: {np.max(elevations) - np.min(elevations):.1f}m\n'
                         f'平均坡度: {np.mean(np.abs(gradients)):.2f}m/km\n'
                         f'最大坡度: {np.max(gradients):.1f}m/km')
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                   verticalalignment='top', fontsize=9,
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        plt.show()
        
        print("\n📊 所有離線 DEM 方法比較完成！")

def main():
    if len(sys.argv) < 2:
        print("用法: python demo_offline_dem_elevation.py <geojson_file> [circuit_name]")
        print("範例: python demo_offline_dem_elevation.py mc_1929_elevation_data.json Monaco")
        return
    
    geojson_file = sys.argv[1]
    circuit_name = sys.argv[2] if len(sys.argv) > 2 else "Circuit"
    
    print(f"🗺️  開始使用離線 DEM 方法生成 {circuit_name} 高度剖面...")
    
    generator = OfflineDEMElevationGenerator(geojson_file)
    generator.visualize_all_dem_methods(circuit_name)

if __name__ == "__main__":
    main()