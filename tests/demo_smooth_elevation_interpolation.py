#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高階插值法改善賽道高度視覺化
使用三次樣條、多項式擬合等方法平滑化 GeoJSON 高度數據
"""

import json
import math
import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate
from scipy.optimize import curve_fit
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class SmoothElevationGenerator:
    """平滑高度生成器"""
    
    def __init__(self, geojson_file):
        self.geojson_file = geojson_file
        self.track_data = None
        self.raw_elevations = None
        self.distances = None
        
    def load_geojson_data(self):
        """載入 GeoJSON 數據"""
        try:
            with open(self.geojson_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 檢查數據格式並提取座標和高度數據
            coords = []
            elevations = []
            
            if 'features' in data:
                # 標準 GeoJSON 格式
                coordinates = data['features'][0]['geometry']['coordinates']
                for coord in coordinates:
                    lon, lat, elev = coord[0], coord[1], coord[2]
                    coords.append([lon, lat])
                    elevations.append(elev)
            elif 'coordinates' in data:
                # f1-circuits 格式
                coordinates = data['coordinates']
                for coord in coordinates:
                    lon, lat, elev = coord['lon'], coord['lat'], coord['elevation']
                    coords.append([lon, lat])
                    elevations.append(elev)
            else:
                raise ValueError("不支援的數據格式")
            
            # 計算距離
            distances = [0]
            for i in range(1, len(coords)):
                dist = self._haversine_distance(
                    coords[i-1][1], coords[i-1][0],
                    coords[i][1], coords[i][0]
                )
                distances.append(distances[-1] + dist)
            
            self.track_data = coords
            self.raw_elevations = np.array(elevations)
            self.distances = np.array(distances)
            
            print(f"✅ 載入 {len(coordinates)} 個數據點")
            print(f"📏 賽道總長度: {distances[-1]:.3f} km")
            print(f"🏔️  原始高度範圍: {min(elevations):.1f}m - {max(elevations):.1f}m")
            
            return True
            
        except Exception as e:
            print(f"❌ 載入 GeoJSON 失敗: {e}")
            return False
    
    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        """計算兩點間距離（公里）"""
        R = 6371.0
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))
    
    def generate_cubic_spline_elevation(self, smoothing_factor=0):
        """使用三次樣條插值生成平滑高度"""
        print("\n🔄 執行三次樣條插值...")
        
        # 創建三次樣條插值器
        spline = interpolate.UnivariateSpline(
            self.distances, 
            self.raw_elevations, 
            s=smoothing_factor  # 平滑因子
        )
        
        # 生成更密集的數據點
        dense_distances = np.linspace(0, self.distances[-1], len(self.distances) * 10)
        smooth_elevations = spline(dense_distances)
        
        return dense_distances, smooth_elevations
    
    def generate_polynomial_elevation(self, degree=6):
        """使用多項式擬合生成平滑高度"""
        print(f"\n🔄 執行 {degree} 階多項式擬合...")
        
        # 多項式特徵轉換
        poly_features = PolynomialFeatures(degree=degree)
        X_poly = poly_features.fit_transform(self.distances.reshape(-1, 1))
        
        # 線性回歸擬合
        poly_reg = LinearRegression()
        poly_reg.fit(X_poly, self.raw_elevations)
        
        # 生成平滑曲線
        dense_distances = np.linspace(0, self.distances[-1], len(self.distances) * 10)
        X_dense_poly = poly_features.transform(dense_distances.reshape(-1, 1))
        smooth_elevations = poly_reg.predict(X_dense_poly)
        
        return dense_distances, smooth_elevations
    
    def generate_fourier_elevation(self, n_harmonics=10):
        """使用傅立葉級數重構高度"""
        print(f"\n🔄 執行傅立葉級數重構 (前 {n_harmonics} 項)...")
        
        # 傅立葉級數參數
        N = len(self.raw_elevations)
        L = self.distances[-1]
        
        # 計算傅立葉係數
        a0 = np.mean(self.raw_elevations)
        
        def fourier_series(x):
            result = a0
            for n in range(1, n_harmonics + 1):
                # 計算 an 和 bn 係數
                an = 2/N * np.sum(self.raw_elevations * np.cos(2*np.pi*n*self.distances/L))
                bn = 2/N * np.sum(self.raw_elevations * np.sin(2*np.pi*n*self.distances/L))
                
                result += an * np.cos(2*np.pi*n*x/L) + bn * np.sin(2*np.pi*n*x/L)
            
            return result
        
        # 生成平滑曲線
        dense_distances = np.linspace(0, self.distances[-1], len(self.distances) * 10)
        smooth_elevations = np.array([fourier_series(d) for d in dense_distances])
        
        return dense_distances, smooth_elevations
    
    def generate_gaussian_smoothed_elevation(self, sigma=0.1):
        """使用高斯平滑濾波器"""
        print(f"\n🔄 執行高斯平滑 (σ={sigma})...")
        
        from scipy.ndimage import gaussian_filter1d
        
        # 應用高斯濾波
        smooth_raw = gaussian_filter1d(self.raw_elevations, sigma=sigma*len(self.raw_elevations))
        
        # 使用插值增加密度
        spline = interpolate.interp1d(self.distances, smooth_raw, kind='cubic')
        dense_distances = np.linspace(0, self.distances[-1], len(self.distances) * 10)
        smooth_elevations = spline(dense_distances)
        
        return dense_distances, smooth_elevations
    
    def visualize_all_methods(self, circuit_name="Circuit"):
        """比較所有平滑化方法"""
        if not self.load_geojson_data():
            return
        
        # 生成不同方法的結果
        methods_results = {}
        
        # 1. 原始數據
        methods_results['原始數據'] = (self.distances, self.raw_elevations)
        
        # 2. 三次樣條
        try:
            methods_results['三次樣條'] = self.generate_cubic_spline_elevation(smoothing_factor=0.5)
        except:
            print("⚠️  三次樣條插值失敗")
        
        # 3. 多項式擬合
        try:
            methods_results['多項式擬合'] = self.generate_polynomial_elevation(degree=8)
        except:
            print("⚠️  多項式擬合失敗")
        
        # 4. 傅立葉級數
        try:
            methods_results['傅立葉級數'] = self.generate_fourier_elevation(n_harmonics=15)
        except:
            print("⚠️  傅立葉級數重構失敗")
        
        # 5. 高斯平滑
        try:
            methods_results['高斯平滑'] = self.generate_gaussian_smoothed_elevation(sigma=0.05)
        except:
            print("⚠️  高斯平滑失敗")
        
        # 創建比較圖
        fig, axes = plt.subplots(len(methods_results), 1, figsize=(12, 3*len(methods_results)))
        if len(methods_results) == 1:
            axes = [axes]
        
        colors = ['red', 'blue', 'green', 'orange', 'purple']
        
        for i, (method_name, (distances, elevations)) in enumerate(methods_results.items()):
            ax = axes[i]
            
            # 應用 F1 官方高度修正
            if method_name == '原始數據':
                corrected_elevations = self._apply_f1_elevation_correction(elevations, circuit_name)
            else:
                corrected_elevations = self._apply_f1_elevation_correction(elevations, circuit_name)
            
            ax.plot(distances, corrected_elevations, 
                   color=colors[i % len(colors)], 
                   linewidth=2, 
                   label=method_name)
            
            # 標記最高點和最低點
            max_idx = np.argmax(corrected_elevations)
            min_idx = np.argmin(corrected_elevations)
            
            ax.plot(distances[max_idx], corrected_elevations[max_idx], 
                   'o', color='red', markersize=8, label=f'最高點 ({corrected_elevations[max_idx]:.1f}m)')
            ax.plot(distances[min_idx], corrected_elevations[min_idx], 
                   'o', color='blue', markersize=8, label=f'最低點 ({corrected_elevations[min_idx]:.1f}m)')
            
            ax.set_xlabel(f'距離 (km)')
            ax.set_ylabel('高度 (m)')
            ax.set_title(f'{circuit_name} - {method_name} 高度剖面')
            ax.grid(True, alpha=0.3)
            ax.legend()
        
        plt.tight_layout()
        plt.show()
        
        print("\n📊 所有平滑化方法比較完成！")
    
    def _apply_f1_elevation_correction(self, elevations, circuit_name):
        """應用 F1 官方高度修正"""
        # F1 官方高度範圍 (根據賽道)
        f1_elevation_ranges = {
            'Monaco': (47.5, 89.5),    # F1 官方：42m 高度差，Monaco 海拔約 47.5m-89.5m
            'Suzuka': (45.0, 100.0),   # Suzuka 實際海拔範圍
            'Circuit': (0.0, 100.0)    # 默認範圍
        }
        
        target_range = f1_elevation_ranges.get(circuit_name, f1_elevation_ranges['Circuit'])
        
        # 正規化到 0-1，然後縮放到目標範圍
        min_elev, max_elev = np.min(elevations), np.max(elevations)
        normalized = (elevations - min_elev) / (max_elev - min_elev)
        corrected = normalized * (target_range[1] - target_range[0]) + target_range[0]
        
        return corrected

def main():
    if len(sys.argv) < 2:
        print("用法: python demo_smooth_elevation_interpolation.py <geojson_file> [circuit_name]")
        print("範例: python demo_smooth_elevation_interpolation.py mc_1929_elevation_data.json Monaco")
        return
    
    geojson_file = sys.argv[1]
    circuit_name = sys.argv[2] if len(sys.argv) > 2 else "Circuit"
    
    print(f"🏁 開始生成 {circuit_name} 的平滑高度剖面...")
    
    generator = SmoothElevationGenerator(geojson_file)
    generator.visualize_all_methods(circuit_name)

if __name__ == "__main__":
    main()