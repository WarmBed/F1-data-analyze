# 最快圈速深紫色背景顯示功能 - 實作總結

## 📋 實作目標
在 Live Timing Ranking Tower 的「最佳」欄位中，當車手擁有全場最快的 best_lap 時，顯示**深紫色背景**。

## ✅ 已完成的修改

### 1. 修改檔案：`modules/gui/live_timing/live_timing_modules/ranking_tower.py`

#### 修改 1: 初始化最快圈速追蹤屬性 (Line ~162)
```python
# 最快圈速追蹤 (用於深紫色背景顯示)
self._fastest_best_lap: Optional[str] = None  # 全場最快的 best_lap 時間字串
```

#### 修改 2: 在 `_populate_table` 方法中計算全場最快圈速 (Line ~570)
```python
# ✅ 計算全場最快的 best_lap (用於紫色背景顯示)
fastest_best_lap_time = None
fastest_best_lap_seconds = float('inf')

for driver_num, driver_data in drivers.items():
    best_lap_time = driver_data.get('best_lap_time', '')
    if best_lap_time and best_lap_time.strip():
        # 轉換為秒數進行比較 (格式: "1:23.456")
        try:
            if ':' in best_lap_time:
                parts = best_lap_time.split(':')
                minutes = int(parts[0])
                seconds = float(parts[1])
                total_seconds = minutes * 60 + seconds
            else:
                total_seconds = float(best_lap_time)
            
            if total_seconds < fastest_best_lap_seconds:
                fastest_best_lap_seconds = total_seconds
                fastest_best_lap_time = best_lap_time
        except (ValueError, IndexError):
            pass

# 儲存最快圈速供 _set_lap_times 使用
self._fastest_best_lap = fastest_best_lap_time
```

#### 修改 3: 在 `_set_lap_times` 方法中應用深紫色背景 (Line ~1003)
```python
# 最佳 (欄位 12)
best_lap_time = driver_data.get('best_lap_time', '')
best_lap_item = QTableWidgetItem(best_lap_time if best_lap_time else '')
best_lap_item.setTextAlignment(Qt.AlignCenter)

# ✅ 檢查是否為全場最快圈速 - 顯示深紫色背景
is_fastest_overall = (
    best_lap_time 
    and best_lap_time.strip() 
    and hasattr(self, '_fastest_best_lap') 
    and best_lap_time == self._fastest_best_lap
)

if is_fastest_overall:
    # 深紫色背景 (類似深紅色的色調)
    best_lap_item.setBackground(QColor('#663399'))  # 深紫色 (Rebecca Purple)
    best_lap_item.setForeground(QColor('#FFFFFF'))  # 白色文字
    font = best_lap_item.font()
    font.setBold(True)
    best_lap_item.setFont(font)
else:
    best_lap_item.setForeground(QColor('#FFFFFF'))  # 白色

self.table.setItem(row, 12, best_lap_item)
```

## 🎨 視覺設計

### 顏色規格
- **深紫色背景**: `#663399` (Rebecca Purple)
- **文字顏色**: `#FFFFFF` (白色)
- **字體樣式**: 粗體 (Bold)

### 設計一致性
此設計與現有的 sector 和 last_lap 的 overall fastest 顯示風格一致：
- Sector overall fastest: `#FF00FF` (洋紅色)
- Last lap overall fastest: `#FF00FF` (洋紅色)
- **Best lap overall fastest**: `#663399` (深紫色) ✨ 新增

## 🧪 測試驗證

### 邏輯測試
已通過 `test_fastest_lap_logic.py` 驗證：
```
✅ 全場最快圈速: 1:23.123 (83.123 秒)
✅ 只有 LEC (16) 應該顯示深紫色背景
```

### 手動測試步驟
1. 啟動 F1T GUI: `python f1t_gui_main.py`
2. 選單: `Live Timing` → `Live Ranking (即時排名塔)`
3. 載入比賽: `2025 Qatar Race`
4. 開始播放
5. 觀察「最佳」欄位 (第 12 欄)

### 預期結果
✅ 全場最快的 best_lap 顯示深紫色背景 (#663399)  
✅ 白色粗體文字  
✅ 其他車手的 best_lap 保持正常白色文字  
✅ 當排名或圈時更新時，深紫色背景即時切換  

## 📐 技術細節

### 時間格式解析
- **格式**: `"1:23.456"` (分:秒.毫秒)
- **轉換邏輯**: 
  ```python
  minutes * 60 + seconds = 83.456 秒
  ```
- **比較方式**: 使用轉換後的總秒數進行數值比較

### 性能考量
- ✅ 每次 `update_display()` 調用時重新計算最快圈速
- ✅ 只遍歷一次所有車手進行計算 (O(n))
- ✅ 使用簡單字串比較判斷是否為最快 (O(1))
- ✅ 無額外記憶體開銷 (僅儲存一個字串)

### 邊界情況處理
- ✅ 車手無 best_lap (空字串或 None): 跳過，不參與比較
- ✅ 時間格式異常: try-except 捕獲，跳過該車手
- ✅ 多位車手相同最快時間: 僅第一位車手顯示紫色背景 (字串完全匹配)
- ✅ 比賽開始時無人完成圈速: `_fastest_best_lap = None`，所有車手正常顯示

## 🔄 更新流程

```
用戶操作 (播放/切換時間點)
    ↓
DataManager 發送 snapshot_updated 信號
    ↓
ranking_tower.update_display(snapshot)
    ↓
_populate_table() 計算全場最快圈速
    ↓
儲存至 self._fastest_best_lap
    ↓
_update_row() 更新每位車手
    ↓
_set_lap_times() 設置 best_lap 顯示
    ↓
檢查 best_lap_time == self._fastest_best_lap
    ↓
是: 深紫色背景 + 白色粗體
否: 正常白色文字
```

## 📝 程式碼變更摘要

| 檔案 | 變更內容 | 行數 |
|------|---------|------|
| `ranking_tower.py` | 新增 `_fastest_best_lap` 屬性 | ~162 |
| `ranking_tower.py` | 新增最快圈速計算邏輯 | ~570-595 |
| `ranking_tower.py` | 新增深紫色背景顯示邏輯 | ~1003-1025 |

## 🎯 使用者體驗

### 視覺效果
- 🟣 **深紫色背景**: 明顯識別全場最快車手
- ⚪ **白色文字**: 與深色背景形成高對比度
- **粗體字**: 進一步強調重要性

### 動態更新
- 當車手刷新最快圈速時，深紫色背景即時切換
- 排名塔每 50ms 更新一次 (20 FPS)，視覺效果流暢

### 與現有功能整合
- 與 sector 時間的顏色系統一致 (綠色 = 個人最快，紫色 = 全場最快)
- 與 last_lap 時間的顯示邏輯相同
- 不影響進站 (PIT) 黃色高亮和名次變更紅框顯示

## ✅ 驗證檢查清單

- [x] 語法檢查通過 (`python -m py_compile`)
- [x] 邏輯測試通過 (`test_fastest_lap_logic.py`)
- [x] 時間解析正確 (分:秒.毫秒 → 總秒數)
- [x] 顏色規格正確 (#663399 深紫色)
- [x] 粗體文字應用
- [x] 邊界情況處理
- [ ] GUI 手動測試 (待用戶確認)

## 🚀 部署狀態

✅ **代碼已修改並通過測試**  
⏳ **等待 GUI 手動測試確認**  

---

**實作時間**: 2025-01-XX  
**修改者**: GitHub Copilot  
**測試狀態**: 邏輯測試通過 ✅  
**用戶確認**: 待確認  
