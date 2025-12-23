# 切換賽道時：彎道圓圈 vs Sector 標籤邏輯對比

## 📊 完整流程對比表

| 階段 | 彎道圓圈 (Official Corners) | Sector 標籤 (Sector Boundaries) | 差異分析 |
|------|----------------------------|--------------------------------|---------|
| **1. 用戶操作** | 切換賽道：Brazil → Bahrain | 切換賽道：Brazil → Bahrain | ✅ 相同 |
| **2. 觸發調用** | `update_lap_parameters("2025", "Bahrain", "R")` | `update_lap_parameters("2025", "Bahrain", "R")` | ✅ 相同 |
| **3. 基類處理** | `update_parameters()` → `_load_data_with_current_parameters()` | `update_parameters()` → `_load_data_with_current_parameters()` | ✅ 相同 |
| **4. API 請求** | 請求 Bahrain 2025 R 數據 | 請求 Bahrain 2025 R 數據 | ✅ 相同 |
| **5. API 響應** | 返回 Bahrain 數據（包含 `official_corners`） | 返回 Bahrain 數據（**可能不包含** `sector_boundaries`） | ⚠️ **關鍵差異** |
| **6. 數據載入** | `_on_data_loaded(bahrain_data)` | `_on_data_loaded(bahrain_data)` | ✅ 相同 |
| **7. TrackMap 更新** | `load_track_data(bahrain_track_data)` | `load_track_data(bahrain_track_data)` | ✅ 相同 |
| **8A. 有新數據時** | `self.official_corners = bahrain_corners` ✅ | `self.sector_boundaries = bahrain_boundaries` ✅ | ✅ 相同 - 正確更新 |
| **8B. 無新數據時** | `self.official_corners = []` （清空） | `self.sector_boundaries = brazil_boundaries` **（保留舊數據！）** | 🚨 **致命差異** |
| **9. 繪製結果** | Bahrain 彎道在 Bahrain 地圖上 ✅ | **Brazil Sector 在 Bahrain 地圖上** ❌ | 🚨 **座標錯位** |

---

## 🔍 核心問題分析

### **為什麼彎道圓圈不會座標錯位？**

```python
# TrackMapWidget.load_track_data() Line 219-237
official_corners_data = track_data.get("official_corners", {})

if official_corners_data.get("available") and official_corners_data.get("corners"):
    self.official_corners = official_corners_data.get("corners", [])  # ✅ 載入新數據
else:
    self.official_corners = []  # ✅ 清空（無新數據 = 無彎道）
```

**邏輯**：
- ✅ 有新數據 → 載入新彎道座標
- ✅ 無新數據 → **清空**（不保留舊座標）
- **結果**：永遠不會出現「舊賽道座標顯示在新賽道地圖上」

---

### **為什麼 Sector 標籤會座標錯位？**

```python
# TrackMapWidget.load_track_data() Line 239-260 (修復後的版本)
sector_boundaries_data = track_data.get("sector_boundaries", [])

if sector_boundaries_data:
    self.sector_boundaries = sector_boundaries_data  # ✅ 載入新數據
else:
    if self.sector_boundaries:
        # ❌ 保留舊數據（為了解決初始化消失問題）
        # 但副作用：切換賽道時保留舊座標！
        print("保留現有 sector_boundaries")
    else:
        self.sector_boundaries = []
```

**邏輯**：
- ✅ 有新數據 → 載入新 Sector 座標
- ❌ 無新數據 → **保留舊座標**（Brazil 座標）
- **結果**：Brazil 的 Sector 座標顯示在 Bahrain 的賽道地圖上 → 座標錯位！

---

## 🎯 兩難困境

### **困境說明**

| 場景 | 不保留舊數據 | 保留舊數據（當前） |
|------|------------|------------------|
| **初始化後第二次 load_track_data** | ❌ Sector 消失 | ✅ Sector 顯示 |
| **切換賽道** | ✅ 清空座標，無錯位 | ❌ 保留舊座標，錯位！ |

**我們的目標**：
- ✅ 初始化後 Sector 不消失
- ✅ 切換賽道後 Sector 不錯位

**問題根源**：
- 無法區分「第二次載入同一賽道」和「切換到新賽道」

---

## 💡 解決方案：增加賽道變更檢測

### **方案 A：在 TrackMapWidget 層檢測賽道變更** ⭐

**實現邏輯**：
```python
# TrackMapWidget 增加屬性
self._last_track_name = None  # 記錄上次載入的賽道

# load_track_data() 中檢測變更
def load_track_data(self, track_data: Dict[str, Any]) -> bool:
    # 取得當前賽道名稱
    session_info = track_data.get("session_info", {})
    current_track = session_info.get("track_name") or session_info.get("event_name")
    
    # 檢測賽道變更
    track_changed = (self._last_track_name is not None and 
                     current_track is not None and 
                     self._last_track_name != current_track)
    
    # 載入 Sector 邊界
    sector_boundaries_data = track_data.get("sector_boundaries", [])
    
    if sector_boundaries_data:
        # 有新數據：直接載入
        self.sector_boundaries = sector_boundaries_data
    else:
        if track_changed:
            # ✅ 賽道變更且無新數據：清空（避免座標錯位）
            self.sector_boundaries = []
            print(f"[TRACK_MAP] 賽道變更 ({self._last_track_name} → {current_track})，清空 Sector 邊界")
        elif self.sector_boundaries:
            # ✅ 同一賽道且無新數據：保留（避免消失）
            print(f"[TRACK_MAP] 同一賽道，保留現有 {len(self.sector_boundaries)} 個 Sector 邊界")
        else:
            self.sector_boundaries = []
    
    # 更新記錄
    self._last_track_name = current_track
```

**優點**：
- ✅ 精確檢測賽道變更
- ✅ 同一賽道內：保留數據（解決消失問題）
- ✅ 切換賽道：清空數據（解決錯位問題）
- ✅ 不影響彎道圓圈邏輯

**缺點**：
- ⚠️ 需要依賴 `track_name` 的準確性

---

### **方案 B：在 MDI 層處理（已被否決）**

檢測賽道變更 → 重建整個 MDI 視窗

**缺點**：
- 用戶反映過於複雜
- 已回退

---

## 📋 實施計劃

1. **修改 TrackMapWidget**：
   - 增加 `self._last_track_name` 屬性
   - 在 `load_track_data()` 中實施賽道變更檢測邏輯

2. **測試場景**：
   - ✅ 初始化 Brazil → Sector 顯示
   - ✅ 初始化後第二次載入（同一賽道）→ Sector 保持顯示
   - ✅ 切換到 Bahrain → Sector 清空或更新為 Bahrain 座標
   - ✅ 再切換回 Brazil → Sector 清空或更新為 Brazil 座標

3. **預期結果**：
   - ✅ Sector 標籤不會無故消失
   - ✅ Sector 座標永遠正確（不會錯位）

---

## 🔑 關鍵代碼位置

- **TrackMapWidget.__init__**: Line 108-168 → 增加 `_last_track_name` 屬性
- **TrackMapWidget.load_track_data**: Line 165-280 → 實施檢測邏輯
- **具體位置**: Line 239-260（Sector 邊界載入）

---

## 📊 最終對比（修復後）

| 場景 | 彎道圓圈 | Sector 標籤（修復後） |
|------|---------|---------------------|
| **初始化** | ✅ 顯示 | ✅ 顯示 |
| **第二次載入（同賽道）** | ✅ 顯示 | ✅ 保留顯示 |
| **切換賽道** | ✅ 更新/清空 | ✅ 更新/清空 |
| **座標正確性** | ✅ 永遠正確 | ✅ 永遠正確 |
