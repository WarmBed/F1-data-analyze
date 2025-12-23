#!/usr/bin/env python3
"""
PyQt5 Heatmap Widget - Standalone Test Script
==============================================

快速測試 IdealLapSectorHeatmapWidget (Pure PyQt5 Version)

執行方式：
    python test_pyqt5_heatmap_widget.py

測試項目：
    1. Widget 初始化
    2. 數據載入（模擬數據）
    3. 熱力圖繪製
    4. 互動功能（懸停、點擊）
    5. 排序功能
    6. 高亮選項
    7. 匯出圖片

Author: F1T Team
Date: 2025-10-11
"""

from __future__ import annotations

import sys
from pathlib import Path

# 確保可以導入專案模組
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QPushButton,
    QCheckBox,
    QLabel,
    QMessageBox,
)
from PyQt5.QtCore import Qt


def create_test_data(num_drivers: int = 10) -> dict:
    """
    建立測試數據
    
    Args:
        num_drivers: 車手數量（預設 10）
    
    Returns:
        符合 IdealLapSectorHeatmapWidget 格式的 payload
    """
    print(f"[TEST] 建立測試數據（{num_drivers} 位車手）...")
    
    drivers = [f"D{i:02d}" for i in range(num_drivers)]
    sectors = ["S1", "S2", "S3"]
    
    # 生成隨機分段時間（15-30 秒）
    np.random.seed(42)  # 固定隨機種子以便重現
    
    data = {}
    for sector in sectors:
        data[sector] = {driver: np.random.uniform(15, 30) for driver in drivers}
    
    df = pd.DataFrame(data).T
    
    # 建立 cell_details
    cell_details = {}
    for sector in sectors:
        for driver in drivers:
            time_val = df.loc[sector, driver]
            cell_details[(sector, driver)] = {
                "time": time_val,
                "lap": np.random.randint(1, 60),
                "team": f"Team {driver}",
                "sector_rank": None,  # 稍後計算
                "delta_to_fastest": None,  # 稍後計算
            }
    
    # 建立 sector_summary
    sector_summary = {}
    for sector in sectors:
        sector_times = df.loc[sector]
        fastest_driver = sector_times.idxmin()
        fastest_time = sector_times.min()
        slowest_time = sector_times.max()
        
        sector_summary[sector] = {
            "fastest_driver": fastest_driver,
            "fastest_time": fastest_time,
            "slowest_time": slowest_time,
            "average_time": sector_times.mean(),
            "time_range": slowest_time - fastest_time,
        }
        
        # 計算 sector_rank 和 delta_to_fastest
        sorted_drivers = sector_times.sort_values().index
        for rank, driver in enumerate(sorted_drivers, start=1):
            cell_key = (sector, driver)
            cell_details[cell_key]["sector_rank"] = rank
            cell_details[cell_key]["delta_to_fastest"] = sector_times[driver] - fastest_time
    
    # 建立 driver_best_map（每位車手的最佳分段）
    driver_best_map = {}
    for driver in drivers:
        driver_times = df[driver]
        best_sector = driver_times.idxmin()
        driver_best_map[driver] = best_sector
    
    payload = {
        "sector_matrix": df,
        "sector_summary": sector_summary,
        "cell_details": cell_details,
        "driver_best_map": driver_best_map,
        "driver_order": drivers,
    }
    
    print("[TEST] ✅ 測試數據建立完成")
    return payload


class HeatmapTestWindow(QMainWindow):
    """測試視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 Heatmap Widget - Test Window")
        self.resize(1200, 800)
        
        # 建立主 Widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        main_layout = QVBoxLayout(main_widget)
        
        # 標題
        title = QLabel("IdealLapSectorHeatmapWidget - Pure PyQt5 Test")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16pt; font-weight: bold; padding: 10px;")
        main_layout.addWidget(title)
        
        # 控制面板
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)
        
        # 熱力圖 Widget（這裡需要導入實際實現）
        try:
            from modules.gui.ideal_lap_sector_heatmap.ideal_lap_sector_heatmap_widget import (
                IdealLapSectorHeatmapWidget,
            )
            
            self.heatmap_widget = IdealLapSectorHeatmapWidget()
            self.heatmap_widget.cell_clicked.connect(self._on_cell_clicked)
            main_layout.addWidget(self.heatmap_widget, stretch=1)
            
            print("[TEST] ✅ IdealLapSectorHeatmapWidget 初始化成功")
        
        except Exception as exc:
            print(f"[TEST] ❌ IdealLapSectorHeatmapWidget 初始化失敗: {exc}")
            error_label = QLabel(f"⚠️ Widget 初始化失敗\n{exc}")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("color: red; font-size: 12pt;")
            main_layout.addWidget(error_label, stretch=1)
            self.heatmap_widget = None
        
        # 狀態列
        self.statusBar().showMessage("就緒")
    
    def _create_control_panel(self) -> QWidget:
        """建立控制面板"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        
        # 數據載入按鈕
        btn_load_10 = QPushButton("載入數據（10 車手）")
        btn_load_10.clicked.connect(lambda: self._load_data(10))
        layout.addWidget(btn_load_10)
        
        btn_load_20 = QPushButton("載入數據（20 車手）")
        btn_load_20.clicked.connect(lambda: self._load_data(20))
        layout.addWidget(btn_load_20)
        
        # 分隔線
        layout.addWidget(QLabel("|"))
        
        # 排序按鈕
        btn_sort_s1 = QPushButton("排序：S1")
        btn_sort_s1.clicked.connect(lambda: self._sort_by_sector("S1"))
        layout.addWidget(btn_sort_s1)
        
        btn_sort_s2 = QPushButton("排序：S2")
        btn_sort_s2.clicked.connect(lambda: self._sort_by_sector("S2"))
        layout.addWidget(btn_sort_s2)
        
        btn_sort_s3 = QPushButton("排序：S3")
        btn_sort_s3.clicked.connect(lambda: self._sort_by_sector("S3"))
        layout.addWidget(btn_sort_s3)
        
        # 分隔線
        layout.addWidget(QLabel("|"))
        
        # 高亮選項
        self.chk_global = QCheckBox("顯示全局最快")
        self.chk_global.setChecked(True)
        self.chk_global.stateChanged.connect(self._update_highlight)
        layout.addWidget(self.chk_global)
        
        self.chk_personal = QCheckBox("顯示個人最佳")
        self.chk_personal.setChecked(False)
        self.chk_personal.stateChanged.connect(self._update_highlight)
        layout.addWidget(self.chk_personal)
        
        # 分隔線
        layout.addWidget(QLabel("|"))
        
        # 匯出按鈕
        btn_export = QPushButton("匯出圖片")
        btn_export.clicked.connect(self._export_image)
        layout.addWidget(btn_export)
        
        # 清除按鈕
        btn_clear = QPushButton("清除數據")
        btn_clear.clicked.connect(self._clear_data)
        layout.addWidget(btn_clear)
        
        layout.addStretch()
        
        return panel
    
    def _load_data(self, num_drivers: int):
        """載入測試數據"""
        if not self.heatmap_widget:
            self.statusBar().showMessage("❌ Widget 未初始化")
            return
        
        try:
            import time
            
            self.statusBar().showMessage(f"載入中... ({num_drivers} 車手)")
            
            # 建立數據
            start = time.time()
            data = create_test_data(num_drivers)
            end = time.time()
            
            print(f"[TEST] 數據建立時間: {(end - start) * 1000:.2f} ms")
            
            # 載入到 Widget
            start = time.time()
            self.heatmap_widget.set_data(data)
            end = time.time()
            
            print(f"[TEST] Widget 繪製時間: {(end - start) * 1000:.2f} ms")
            
            self.statusBar().showMessage(
                f"✅ 已載入 {num_drivers} 位車手的數據 "
                f"(繪製時間: {(end - start) * 1000:.1f} ms)"
            )
        
        except Exception as exc:
            print(f"[TEST] ❌ 載入數據失敗: {exc}")
            import traceback
            traceback.print_exc()
            self.statusBar().showMessage(f"❌ 載入失敗: {exc}")
    
    def _sort_by_sector(self, sector: str):
        """按分段排序"""
        if not self.heatmap_widget:
            return
        
        try:
            current_data = self.heatmap_widget.get_current_data()
            df = current_data.get("sector_matrix")
            
            if df is None or df.empty:
                self.statusBar().showMessage("⚠️ 無數據")
                return
            
            # 按該分段時間排序
            sector_times = df.loc[sector]
            sorted_drivers = sector_times.sort_values().index.tolist()
            
            self.heatmap_widget.render_heatmap(sorted_drivers)
            self.statusBar().showMessage(f"✅ 已按 {sector} 排序")
        
        except Exception as exc:
            print(f"[TEST] ❌ 排序失敗: {exc}")
            self.statusBar().showMessage(f"❌ 排序失敗: {exc}")
    
    def _update_highlight(self):
        """更新高亮選項"""
        if not self.heatmap_widget:
            return
        
        try:
            self.heatmap_widget.set_highlight_options(
                show_global_fastest=self.chk_global.isChecked(),
                show_personal_best=self.chk_personal.isChecked(),
            )
            self.statusBar().showMessage("✅ 高亮選項已更新")
        
        except Exception as exc:
            print(f"[TEST] ❌ 更新高亮失敗: {exc}")
    
    def _export_image(self):
        """匯出圖片"""
        if not self.heatmap_widget:
            return
        
        try:
            file_path = "test_heatmap_export.png"
            success = self.heatmap_widget.save_plot(file_path)
            
            if success:
                self.statusBar().showMessage(f"✅ 已匯出: {file_path}")
                QMessageBox.information(
                    self,
                    "匯出成功",
                    f"圖片已儲存至:\n{file_path}"
                )
            else:
                self.statusBar().showMessage("❌ 匯出失敗")
        
        except Exception as exc:
            print(f"[TEST] ❌ 匯出失敗: {exc}")
            self.statusBar().showMessage(f"❌ 匯出失敗: {exc}")
    
    def _clear_data(self):
        """清除數據"""
        if not self.heatmap_widget:
            return
        
        try:
            self.heatmap_widget.clear_data()
            self.statusBar().showMessage("✅ 已清除數據")
        
        except Exception as exc:
            print(f"[TEST] ❌ 清除失敗: {exc}")
    
    def _on_cell_clicked(self, driver: str, sector: str):
        """儲存格點擊事件"""
        self.statusBar().showMessage(f"🖱️ 點擊: {driver} - {sector}")
        print(f"[TEST] Cell clicked: driver={driver}, sector={sector}")


def main():
    """主程式"""
    print("[TEST] 啟動 PyQt5 Heatmap Widget 測試...")
    
    app = QApplication(sys.argv)
    
    window = HeatmapTestWindow()
    window.show()
    
    print("[TEST] 測試視窗已開啟")
    print("[TEST] 請點擊按鈕測試功能")
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
