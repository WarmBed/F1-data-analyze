# Historical Track Map vs Demo 功能比對表

## 📋 比對基準
- **參考實現**: `demo_japan_circuit_with_elevation.py`
- **當前實現**: `modules/gui/Historical_track_map/historical_track_map_mdi.py`
- **比對日期**: 2025-11-11

---

## 🎯 功能完整性比對

### 1. **賽道地圖顯示功能**

| 功能項目 | Demo 實現 | Historical Track Map | 狀態 | 缺失原因 |
|---------|-----------|---------------------|------|----------|
| 賽道輪廓繪製 | ✅ 完整實現 | ✅ 已實現 | ✅ 正常 | - |
| 彎道編號標註 | ✅ 完整實現 | ❌ **缺失** | ❌ 違反原則2 | 未檢查參考實現 |
| 彎道位置圓圈 | ✅ 完整實現 | ❌ **缺失** | ❌ 違反原則2 | 未檢查參考實現 |
| 彎道 Tooltip | ✅ 完整實現 | ❌ **缺失** | ❌ 違反原則2 | 未檢查參考實現 |
| 彎道點擊固定 | ✅ 完整實現 | ❌ **缺失** | ❌ 違反原則2 | 未檢查參考實現 |
| 切換彎道顯示 | ✅ 按鈕控制 | ❌ **缺失** | ❌ 違反原則2 | 未檢查參考實現 |

**Demo 彎道標註實現**：
```python
# ElevationProfileWidget.plot_elevation()
if official_corners:
    for corner in official_corners:
        corner_dist = corner.get('mapped_distance', 0) / 1000  # km
        corner_num = corner.get('number', 0)
        
        # 找到最接近的高程值
        closest_idx = min(range(len(distances)), 
                         key=lambda i: abs(distances[i] - corner_dist))
        corner_elev = elevations[closest_idx]
        
        # 繪製彎道標記
        ax.plot(corner_dist, corner_elev, 'ro', markersize=6)
        ax.text(corner_dist, corner_elev + 2, f'T{corner_num}',
               ha='center', va='bottom', fontsize=8, color='red')
```

### 2. **高程圖表功能**

| 功能項目 | Demo 實現 | Historical Track Map | 狀態 | 缺失原因 |
|---------|-----------|---------------------|------|----------|
| 高程剖面繪製 | ✅ 完整實現 | ✅ 已實現 | ✅ 正常 | - |
| 距離軸標註 (km) | ✅ **完整實現** | ❌ **缺失** | ❌ 違反原則1 | 假設有距離軸 |
| 高程軸標註 (m) | ✅ 完整實現 | ✅ 已實現 | ✅ 正常 | - |
| 彎道位置標記 | ✅ **完整實現** | ❌ **缺失** | ❌ 違反原則2 | 未檢查參考實現 |
| 彎道編號標註 | ✅ **完整實現** | ❌ **缺失** | ❌ 違反原則2 | 未檢查參考實現 |
| 網格線 | ✅ 完整實現 | ✅ 已實現 | ✅ 正常 | - |
| 圖例 | ✅ 完整實現 | ❌ **缺失** | ❌ 違反原則2 | 未檢查參考實現 |

**Demo 高程圖實現**：
```python
# 繪製高程剖面
ax.plot(distances, elevations, 'b-', linewidth=2, label='Track Elevation')
ax.fill_between(distances, elevations, alpha=0.3, color='lightblue')

# 標註彎道位置
if official_corners:
    for corner in official_corners:
        corner_dist = corner.get('mapped_distance', 0) / 1000  # km
        corner_num = corner.get('number', 0)
        
        # 繪製彎道標記
        ax.plot(corner_dist, corner_elev, 'ro', markersize=6)
        ax.text(corner_dist, corner_elev + 2, f'T{corner_num}',
               ha='center', va='bottom', fontsize=8, color='red')

# 設置軸標籤
ax.set_xlabel('Distance (km)', fontsize=10)
ax.set_ylabel('Elevation (m)', fontsize=10)
ax.legend(loc='upper right')
```

### 3. **聯動功能**

| 功能項目 | Demo 實現 | Historical Track Map | 狀態 | 缺失原因 |
|---------|-----------|---------------------|------|----------|
| 點擊地圖 → 高程圖高亮 | ❌ 未實現 | ❌ 未實現 | ⚠️ 可選 | Demo 也沒有 |
| 點擊高程圖 → 地圖高亮 | ❌ 未實現 | ❌ 未實現 | ⚠️ 可選 | Demo 也沒有 |
| 彎道懸停 Tooltip | ✅ **完整實現** | ❌ **缺失** | ❌ 違反原則2 | 未檢查參考實現 |
| 彎道點擊固定 Tooltip | ✅ **完整實現** | ❌ **缺失** | ❌ 違反原則2 | 未檢查參考實現 |

**TrackMapWidget 彎道點擊實現**：
```python
def mousePressEvent(self, event):
    if event.button() == Qt.LeftButton:
        # 檢查是否點擊彎道圓圈
        clicked_corner = self._get_corner_at_position(event.x(), event.y())
        
        if clicked_corner:
            # 固定該彎道的 tooltip
            self.pinned_corner = clicked_corner
            self.pinned_tooltip_pos = event.globalPos()
            tooltip_text = self._format_corner_tooltip(clicked_corner)
            if tooltip_text:
                QToolTip.showText(self.pinned_tooltip_pos, tooltip_text, self)
```

### 4. **控制按鈕**

| 功能項目 | Demo 實現 | Historical Track Map | 狀態 | 缺失原因 |
|---------|-----------|---------------------|------|----------|
| 切換彎道顯示 | ✅ "🎯 切換彎道" | ❌ **缺失** | ❌ 違反原則2 | 未檢查參考實現 |
| 重置視圖 | ✅ "🔄 重置視圖" | ❌ **缺失** | ❌ 違反原則2 | 未檢查參考實現 |
| 重繪高程圖 | ✅ "📊 重繪高程" | ❌ **缺失** | ❌ 違反原則2 | 未檢查參考實現 |

**Demo 控制按鈕實現**：
```python
toggle_corners_btn = QPushButton("🎯 切換彎道")
toggle_corners_btn.clicked.connect(self._toggle_corners)

fit_view_btn = QPushButton("🔄 重置視圖")
fit_view_btn.clicked.connect(self._fit_view)

refresh_elev_btn = QPushButton("📊 重繪高程")
refresh_elev_btn.clicked.connect(self._refresh_elevation)
```

### 5. **佈局結構**

| 功能項目 | Demo 實現 | Historical Track Map | 狀態 | 缺失原因 |
|---------|-----------|---------------------|------|----------|
| QSplitter 分割 | ✅ 垂直分割 | ❌ **缺失** | ❌ 違反原則2 | 使用 QVBoxLayout |
| 可調整比例 | ✅ 可拖曳分隔線 | ❌ **固定比例** | ❌ 違反原則2 | 未檢查參考實現 |
| TrackMap 佔 70% | ✅ `setStretchFactor(0, 7)` | ❌ **等比例** | ❌ 違反原則2 | 未檢查參考實現 |
| Elevation 佔 30% | ✅ `setStretchFactor(1, 3)` | ❌ **等比例** | ❌ 違反原則2 | 未檢查參考實現 |

**Demo 佈局實現**：
```python
# 使用 QSplitter 分割 TrackMap 和 Elevation
splitter = QSplitter(Qt.Vertical)

self.track_map = TrackMapWidget()
splitter.addWidget(self.track_map)

self.elevation_widget = ElevationProfileWidget()
splitter.addWidget(self.elevation_widget)

# 設定初始比例（TrackMap 佔 70%，Elevation 佔 30%）
splitter.setStretchFactor(0, 7)
splitter.setStretchFactor(1, 3)
```

### 6. **資訊顯示**

| 功能項目 | Demo 實現 | Historical Track Map | 狀態 | 缺失原因 |
|---------|-----------|---------------------|------|----------|
| 頂部資訊面板 | ✅ HTML 格式 | ✅ 已實現 | ✅ 正常 | - |
| 賽道距離 (km) | ✅ 完整實現 | ❌ **缺失** | ❌ 違反原則2 | 未檢查參考實現 |
| 高程範圍 | ✅ 完整實現 | ✅ 已實現 | ✅ 正常 | - |
| 高程變化 (Δ) | ✅ 完整實現 | ❌ **缺失** | ❌ 違反原則2 | 未檢查參考實現 |
| 底部統計資訊 | ✅ 完整實現 | ❌ **缺失** | ❌ 違反原則2 | 未檢查參考實現 |

**Demo 資訊顯示實現**：
```python
info_html = f"""
<b>🏁 {metadata.get('race', 'N/A')}</b> | 
{metadata.get('year', 'N/A')} | 
Distance: {metadata.get('total_distance_m', 0)/1000:.2f} km | 
Elevation: {elev_profile.get('min_elevation', 0):.0f}m ~ {elev_profile.get('max_elevation', 0):.0f}m 
(Δ{elev_profile.get('elevation_change', 0):.0f}m)
"""

self.stats_label.setText(
    f"賽道輪廓: {outline_count} 點 | 官方彎道: {corners_count} 個 | "
    f"座標系統: FastF1 (X/Y) + GeoJSON (Elevation)"
)
```

---

## 📊 統計總結

### 缺失功能統計

| 類別 | Demo 功能數 | 已實現 | 缺失 | 實現率 |
|------|------------|--------|------|--------|
| 賽道地圖 | 6 | 1 | 5 | 16.7% |
| 高程圖表 | 7 | 3 | 4 | 42.9% |
| 聯動功能 | 4 | 0 | 4 | 0% |
| 控制按鈕 | 3 | 0 | 3 | 0% |
| 佈局結構 | 4 | 0 | 4 | 0% |
| 資訊顯示 | 6 | 2 | 4 | 33.3% |
| **總計** | **30** | **6** | **24** | **20%** |

### 違反開發原則統計

| 原則 | 違反次數 | 說明 |
|------|----------|------|
| **原則 1** | 1 次 | 假設高程圖有距離軸，未驗證 |
| **原則 2** | 23 次 | 未檢查 Demo 參考實現，導致 23 個功能缺失 |

---

## 🔧 必須修復的關鍵功能

### 優先級 P0（必須實現）
1. ✅ **高程圖彎道標記** - 紅點 + 編號標註
2. ✅ **高程圖距離軸** - 使用 distance_m 數據
3. ✅ **QSplitter 佈局** - 可調整比例
4. ✅ **切換彎道按鈕** - 控制彎道顯示

### 優先級 P1（高優先）
5. ✅ **賽道地圖彎道標註** - 完整複製 TrackMapWidget 功能
6. ✅ **底部統計資訊** - 點數、彎道數、座標系統
7. ✅ **資訊面板完整** - 賽道距離、高程變化

### 優先級 P2（建議實現）
8. ⚠️ **重置視圖按鈕** - 重置地圖縮放
9. ⚠️ **重繪高程按鈕** - 強制重繪圖表
10. ⚠️ **彎道 Tooltip** - 懸停顯示彎道資訊

---

## 💡 修復建議

### 1. 高程圖彎道標記（最關鍵）
```python
# elevation_chart_widget.py
def plot_elevation(self, track_outline: list, corners: list):
    # 提取距離和高程
    distances = [p.get('distance_m', 0) / 1000 for p in track_outline]  # km
    elevations = [p.get('elevation', 0) / 10 for p in track_outline]   # FastF1 除以 10
    
    # 繪製高程剖面
    ax.plot(distances, elevations, 'b-', linewidth=2, label='Track Elevation')
    ax.fill_between(distances, elevations, alpha=0.3, color='lightblue')
    
    # 標註彎道位置
    if corners:
        for corner_num in corners:
            # 找到彎道對應的距離和高程
            # （需要從 corner_analysis 提取 mapped_distance）
            ax.plot(corner_dist, corner_elev, 'ro', markersize=6)
            ax.text(corner_dist, corner_elev + 2, f'T{corner_num}',
                   ha='center', va='bottom', fontsize=8, color='red')
    
    # 設置軸標籤
    ax.set_xlabel('Distance (km)', fontsize=10)
    ax.set_ylabel('Elevation (m)', fontsize=10)
```

### 2. QSplitter 佈局替換
```python
# historical_track_map_mdi.py
from PyQt5.QtWidgets import QSplitter

# 替換原有的 QVBoxLayout
splitter = QSplitter(Qt.Vertical)
splitter.addWidget(self.track_map)
splitter.addWidget(self.elevation_chart)
splitter.setStretchFactor(0, 7)  # TrackMap 70%
splitter.setStretchFactor(1, 3)  # Elevation 30%
```

### 3. 控制按鈕添加
```python
toggle_corners_btn = QPushButton("🎯 切換彎道")
toggle_corners_btn.clicked.connect(self._toggle_corners)

def _toggle_corners(self):
    self.track_map.show_official_corners = not self.track_map.show_official_corners
    self.track_map.update()
```

---

## ⚠️ 結論

**當前實現僅完成 Demo 功能的 20%**，嚴重違反開發原則 2（模組資料夾優先 - 複用現有功能）。

**主要問題**：
1. ❌ 未檢查 Demo 參考實現
2. ❌ 未複用 TrackMapWidget 的完整功能
3. ❌ 未實現高程圖的彎道標記和距離軸
4. ❌ 未使用 QSplitter 可調整佈局

**必須立即修復**以符合開發原則和用戶期望。
