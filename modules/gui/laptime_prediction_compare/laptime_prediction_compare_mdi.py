#!/usr/bin/env python3
"""
Laptime Prediction Compare MDI - 三曲線圈速對比模組

功能: 顯示 Real vs F57 vs F91 三條圈速曲線
數據源:
- Real: 2025 Abu Dhabi Race 實際圈速
- F57: combined_laptime_{year}_{race}_{session}.json
- F91: fp2_race_ml_prediction_v2_{year}_{race}.json

版本: 1.0.0
日期: 2025-12-13
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Matplotlib 整合
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class LaptimePredictionCompareMDI(QWidget):
    """圈速預測對比 MDI 視窗"""
    
    def __init__(self, year: int, race: str, driver: str = "1", parent=None):
        super().__init__(parent)
        self.year = year
        self.race = race
        self.driver = driver
        
        # 數據路徑
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.json_dir = self.project_root / "json"
        self.livef1_dir = self.json_dir / "LiveF1" / str(year)
        
        self.init_ui()
        self.load_and_display_data()
    
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout()
        
        # 標題
        title = QLabel(f"{self.year} {self.race} - 圈速預測對比")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 創建 Matplotlib 圖表
        self.figure = Figure(figsize=(12, 6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # 統計資訊
        self.info_label = QLabel("")
        self.info_label.setFont(QFont("Consolas", 10))
        layout.addWidget(self.info_label)
        
        # 重新載入按鈕
        reload_btn = QPushButton("重新載入")
        reload_btn.clicked.connect(self.load_and_display_data)
        layout.addWidget(reload_btn)
        
        self.setLayout(layout)
        self.setWindowTitle(f"圈速預測對比 - {self.race}")
    
    def load_and_display_data(self):
        """載入並顯示三條曲線"""
        try:
            # 載入 Real 數據
            real_data = self._load_real_laptimes()
            
            # 載入 F57 預測
            f57_data = self._load_f57_prediction()
            
            # 載入 F91 預測
            f91_data = self._load_f91_prediction()
            
            # 繪製三曲線
            self._draw_comparison_chart(real_data, f57_data, f91_data)
            
            # 更新統計
            self._update_statistics(real_data, f57_data, f91_data)
        
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"載入數據失敗: {e}")
    
    def _load_real_laptimes(self) -> Dict[int, float]:
        """載入實際圈速"""
        race_path = self.livef1_dir / f"{self.race}_Race"
        timing_file = race_path / "TimingData.json"
        
        if not timing_file.exists():
            raise FileNotFoundError(f"找不到 Race 數據: {timing_file}")
        
        with open(timing_file, 'r', encoding='utf-8') as f:
            timing_data = json.load(f)
        
        # 解析 LiveF1 格式
        lap_times = {}
        records = timing_data.get("records", [])
        
        for entry in records:
            lines = entry.get("data", {}).get("Lines", {})
            driver_data = lines.get(self.driver, {})
            
            last_lap = driver_data.get("LastLapTime", {})
            lap_time_str = last_lap.get("Value", "")
            lap_num = driver_data.get("NumberOfLaps")
            
            if lap_time_str and lap_num:
                lap_num = int(lap_num)
                if lap_num not in lap_times:
                    lap_times[lap_num] = self._convert_laptime(lap_time_str)
        
        return lap_times
    
    def _load_f57_prediction(self) -> Dict[int, float]:
        """載入 F57 預測數據"""
        # 尋找最新的 F57 檔案
        f57_files = list(self.json_dir.glob(f"combined_laptime_{self.year}_{self.race}_*.json"))
        
        if not f57_files:
            print(f"[WARNING] 找不到 F57 預測檔案: combined_laptime_{self.year}_{self.race}_*.json")
            return {}
        
        f57_file = sorted(f57_files)[-1]  # 最新的檔案
        print(f"[INFO] 載入 F57 檔案: {f57_file.name}")
        
        with open(f57_file, 'r', encoding='utf-8') as f:
            f57_data = json.load(f)
        
        # 提取車手的預測圈速
        predictions = {}
        
        # F57 新格式：drivers -> {driver_number} -> predictions
        drivers_data = f57_data.get("drivers", {})
        driver_data = drivers_data.get(self.driver, {})
        
        if driver_data:
            for lap_pred in driver_data.get("predictions", []):
                lap_num = lap_pred.get("lap_number")
                predicted_time = lap_pred.get("predicted_time")
                if lap_num and predicted_time:
                    predictions[int(lap_num)] = float(predicted_time)
        
        print(f"[INFO] F57 載入了 {len(predictions)} 個圈速預測")
        return predictions
    
    def _load_f91_prediction(self) -> Dict[int, float]:
        """載入 F91 預測數據"""
        # 尋找最新的 F91 檔案
        f91_files = list(self.json_dir.glob(f"fp2_race_ml_prediction_v2_{self.year}_{self.race}_*.json"))
        
        if not f91_files:
            raise FileNotFoundError("找不到 F91 預測檔案")
        
        f91_file = sorted(f91_files)[-1]  # 最新的檔案
        
        with open(f91_file, 'r', encoding='utf-8') as f:
            f91_data = json.load(f)
        
        # 提取車手的預測圈速
        predictions = {}
        driver_pred = f91_data.get("predictions", {}).get(self.driver, {})
        predicted_laps = driver_pred.get("predicted_laps", {})
        
        for lap_str, lap_time in predicted_laps.items():
            predictions[int(lap_str)] = float(lap_time)
        
        return predictions
    
    def _draw_comparison_chart(self, real: Dict, f57: Dict, f91: Dict):
        """繪製三曲線對比圖"""
        # 配置中文字體
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 清空之前的圖表
        self.figure.clear()
        
        # 創建子圖
        ax = self.figure.add_subplot(111)
        
        # 準備數據
        laps = sorted(set(list(real.keys()) + list(f57.keys()) + list(f91.keys())))
        
        real_times = [real.get(lap, None) for lap in laps]
        f57_times = [f57.get(lap, None) for lap in laps]
        f91_times = [f91.get(lap, None) for lap in laps]
        
        # 調試輸出
        print(f"\n[DEBUG] 數據統計:")
        print(f"  Real 數據點: {len([t for t in real_times if t is not None])}")
        print(f"  F57 數據點: {len([t for t in f57_times if t is not None])}")
        print(f"  F91 數據點: {len([t for t in f91_times if t is not None])}")
        
        # 繪製三條曲線
        if any(t is not None for t in real_times):
            ax.plot(laps, real_times, 'g-', linewidth=2, label='實際圈速 (Real)', marker='o', markersize=3)
        
        if any(t is not None for t in f57_times):
            ax.plot(laps, f57_times, 'b--', linewidth=2, label='燃油+輪胎模型 (F57)', marker='s', markersize=3)
        
        if any(t is not None for t in f91_times):
            ax.plot(laps, f91_times, 'r-.', linewidth=2, label='機器學習預測 (F91)', marker='^', markersize=3)
        
        # 獲取車手名稱
        driver_name = self._get_driver_name(self.driver)
        
        ax.set_xlabel('圈數', fontsize=12, fontproperties='Microsoft JhengHei')
        ax.set_ylabel('圈速 (秒)', fontsize=12, fontproperties='Microsoft JhengHei')
        ax.set_title(f'{self.year} {self.race} - 圈速預測對比 ({driver_name})', 
                     fontsize=14, fontweight='bold', fontproperties='Microsoft JhengHei')
        ax.legend(loc='best', fontsize=10, prop={'family': 'Microsoft JhengHei'})
        ax.grid(True, alpha=0.3)
        
        # 設置 Y 軸範圍
        all_times = [t for t in real_times + f57_times + f91_times if t is not None]
        if all_times:
            y_min = min(all_times) - 2
            y_max = max(all_times) + 2
            ax.set_ylim([y_min, y_max])
        
        # 刷新畫布
        self.canvas.draw()
    
    def _update_statistics(self, real: Dict, f57: Dict, f91: Dict):
        """更新統計資訊"""
        # 計算 MAE
        f57_mae = self._calculate_mae(real, f57)
        f91_mae = self._calculate_mae(real, f91)
        
        info_text = f"""
統計資訊:
  Real 圈數: {len(real)}
  F57 圈數: {len(f57)} | MAE: {f57_mae:.3f}s
  F91 圈數: {len(f91)} | MAE: {f91_mae:.3f}s
        """
        
        self.info_label.setText(info_text.strip())
    
    def _calculate_mae(self, real: Dict, pred: Dict) -> float:
        """計算平均絕對誤差"""
        errors = []
        for lap in real:
            if lap in pred and real[lap] is not None and pred[lap] is not None:
                errors.append(abs(real[lap] - pred[lap]))
        
        return sum(errors) / len(errors) if errors else 0.0
    
    def _get_driver_name(self, driver_number: str) -> str:
        """獲取車手名稱"""
        driver_map = {
            "1": "VER (Verstappen)",
            "4": "NOR (Norris)",
            "11": "PER (Perez)",
            "16": "LEC (Leclerc)",
            "55": "SAI (Sainz)",
            "63": "RUS (Russell)",
            "44": "HAM (Hamilton)",
            "81": "PIA (Piastri)",
        }
        return driver_map.get(driver_number, f"車手 {driver_number}")
    
    def _convert_laptime(self, time_str: str) -> float:
        """轉換圈速字串為秒"""
        if ":" in time_str:
            parts = time_str.split(":")
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        else:
            return float(time_str)
