# Sector 標籤 vs 彎道圓圈：顯示機制比較

## 📊 核心差異對照表

| 特性 | 彎道圓圈 (Official Corners) | Sector 標籤 (Sector Boundaries) |
|------|---------------------------|--------------------------------|
| **數據來源** | FastF1 API (`official_corners`) | CLI Function 100 計算 (`sector_boundaries`) |
| **數據結構** | `[{number, x, y, angle, distance}, ...]` | `[{sector, name, distance_m, position_x, position_y, elevation, sector_time}, ...]` |
| **載入方式** | `load_track_data(track_data)` | `set_sector_boundaries(boundaries)` |
| **儲存位置** | `self.official_corners` (List[Dict]) | `self.sector_boundaries` (List[Dict]) |
| **控制開關** | `self.show_official_corners` (布林值) | `self.show_sector_boundaries` (布林值) |
| **繪製方法** | `_draw_official_corners(painter)` | `_draw_sector_boundaries(painter)` |
| **繪製位置** | `paintEvent()` Line 457-465 | `paintEvent()` Line 467-476 |
| **視覺樣式** | 圓圈 + 數字 (T1, T2, ...) | 黑色虛線 + 標籤 (S1, S2, S3) |
| **顏色編碼** | 白色/黃色/紅色/淺紫色（旗幟危險度） | 黑色虛線 + 白底黑字標籤 |
| **數量** | 可變（賽道彎道數量，例如 15-21 個） | 固定 3 個 (S1/S2/S3) |
| **持久性** | ✅ 穩定 | ❌ **問題：初始化後消失** |

---

## 🔍 問題診斷：為什麼 Sector 標籤會消失？

### **正常流程（彎道圓圈 - 運作正常）**

```python
initialize_module()
    ↓
load_initial_data()  # 啟動 API Worker
    ↓
API Worker 完成 → _on_api_success() → _on_data_loaded(gui_data)
    ↓
track_map.load_track_data(track_data)  # 包含 official_corners
    ↓
self.official_corners = track_data.get("official_corners", [])  # ✅ 數據載入
    ↓
self.show_official_corners = True  # ✅ 啟用顯示
    ↓
paintEvent() 每次重繪時檢查：
    if self.show_official_corners and self.official_corners:
        _draw_official_corners(painter)  # ✅ 持續顯示
```

### **問題流程（Sector 標籤 - 一瞬間消失）**

```python
initialize_module()
    ↓
load_initial_data()  # 啟動 API Worker
    ↓
API Worker 完成 → _on_api_success() → _on_data_loaded(gui_data)
    ↓
track_map.set_sector_boundaries(sector_boundaries)
    ↓
self.sector_boundaries = sector_boundaries  # ✅ 數據載入
self.show_sector_boundaries = True  # ✅ 啟用顯示
    ↓
paintEvent() 觸發 → 顯示 Sector 標籤 ✅ (一瞬間)
    ↓
⚠️  **問題點：主視窗又調用 update_lap_parameters()**
    ↓
f1t_gui_main.py Line 13915:
    module.update_lap_parameters(current_year, current_race, current_session)
    ↓
update_lap_parameters() → super().update_parameters()
    ↓
基類 update_parameters() → _load_data_with_current_parameters()
    ↓
⚠️  **第二次載入數據** → 可能返回不完整的 track_data
    ↓
track_map.load_track_data(incomplete_track_data)  # 沒有 sector_boundaries
    ↓
TrackMapWidget Line 239-257:
    sector_boundaries_data = track_data.get("sector_boundaries", [])
    if sector_boundaries_data:
        self.sector_boundaries = sector_boundaries_data  # ❌ 空列表
    else:
        self.sector_boundaries = []  # ❌ 清空！
    ↓
paintEvent() 再次觸發：
    if self.show_sector_boundaries and self.sector_boundaries:
        # ❌ self.sector_boundaries 已被清空，跳過繪製
```

---

## 🐛 根本原因分析

### **問題 1：重複載入數據**

主視窗在 `initialize_module()` 完成後又調用 `update_lap_parameters()`，導致數據被載入兩次：

```python
# f1t_gui_main.py Line 13911-13915
if module.initialize_module():  # 第一次載入（成功）
    print(f"[OK] [MODULE_FACTORY] 歷年賽道旗幟統計模組初始化成功")
    
    # ❌ 問題：又載入一次
    module.update_lap_parameters(current_year, current_race, current_session)
```

### **問題 2：數據持久性差異**

- **彎道圓圈** (`official_corners`)：透過 `load_track_data()` 載入，**每次都包含在 track_data** 中
- **Sector 標籤** (`sector_boundaries`)：透過 `set_sector_boundaries()` 設置，**但第二次載入時 track_data 可能不包含**

### **問題 3：TrackMapWidget 的保護邏輯不足**

TrackMapWidget 在 `load_track_data()` 中會**無條件覆蓋** `self.sector_boundaries`：

```python
# 原始邏輯（已被我簡化）
if sector_boundaries_data and isinstance(sector_boundaries_data, list):
    self.sector_boundaries = sector_boundaries_data  # 載入新數據
else:
    self.sector_boundaries = []  # ❌ 清空！（沒有保護）
```

**對比**：彎道圓圈沒有這個問題，因為 `official_corners` 總是存在於 `track_data` 中。

---

## 💡 解決方案

### **方案 A：移除重複調用（推薦）** ⭐

修改主視窗，移除 `initialize_module()` 後的 `update_lap_parameters()` 調用：

```python
# f1t_gui_main.py Line 13911-13918
if module.initialize_module():
    print(f"[OK] [MODULE_FACTORY] 歷年賽道旗幟統計模組初始化成功")
    
    # ❌ 移除這行（重複調用）
    # module.update_lap_parameters(current_year, current_race, current_session)
    
    return self._mark_module_factory_type(module, module_type)
```

**優點**：
- ✅ 最簡單
- ✅ 不破壞現有流程
- ✅ 避免重複載入

**缺點**：
- ⚠️  需要確認移除後不會影響其他模組

---

### **方案 B：TrackMapWidget 保護邏輯（備用）**

如果無法移除重複調用，增強 TrackMapWidget 的保護邏輯：

```python
# track_map_widget.py Line 239-257
sector_boundaries_data = track_data.get("sector_boundaries", [])

if sector_boundaries_data and isinstance(sector_boundaries_data, list):
    self.sector_boundaries = sector_boundaries_data
    print(f"[TRACK_MAP] ✅ 成功載入 {len(self.sector_boundaries)} 個 Sector 邊界")
else:
    # 🛡️  保護邏輯：如果新數據沒有，保留現有數據（不清空）
    if self.sector_boundaries:
        print(f"[TRACK_MAP] ⚠️  新數據無 Sector 邊界，保留現有 {len(self.sector_boundaries)} 個")
    else:
        self.sector_boundaries = []
        print(f"[TRACK_MAP] ❌ 新數據無 Sector 邊界且當前為空，設置為空列表")
```

**優點**：
- ✅ 不需修改主視窗
- ✅ 增強容錯性

**缺點**：
- ⚠️  可能在賽道切換時保留舊賽道的 Sector 座標（座標污染）
- ⚠️  這就是之前我們遇到的問題！

---

## 🎯 建議實施

### **第一步：移除重複調用（方案 A）**

修改 `f1t_gui_main.py` Line 13915，註釋掉重複的 `update_lap_parameters()` 調用。

### **第二步：驗證**

1. 啟動 GUI
2. 開啟「歷年賽道旗幟統計」
3. 觀察 Sector 標籤是否持續顯示
4. 切換賽道，確認新賽道的 Sector 座標正確

### **第三步：如果方案 A 失敗**

回退到方案 B，但需要額外處理賽道切換時的座標污染問題（已實現的 MDI 重建機制）。

---

## 📋 總結

**為什麼彎道圓圈正常，Sector 標籤消失？**

1. **數據來源穩定性**：彎道圓圈來自 FastF1 固定 API，每次 `load_track_data()` 都包含；Sector 標籤需要 CLI 計算，第二次載入時可能缺失
2. **載入機制差異**：彎道圓圈透過 `load_track_data()` 統一載入；Sector 標籤需要額外調用 `set_sector_boundaries()`
3. **重複載入**：主視窗的重複 `update_lap_parameters()` 調用導致數據被覆蓋
4. **保護不足**：TrackMapWidget 沒有保護現有的 Sector 數據，直接清空

**解決方向**：移除重複調用，確保數據只載入一次。
