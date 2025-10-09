# 🔄 雙圈比較模式實施報告

**實施日期**: 2025-10-07  
**功能**: 同車手不同圈數雙圈比較模式  
**狀態**: ✅ 已完成並測試通過

---

## 📋 需求概述

### 問題
用戶輸入 **Driver1=LEC Lap1=10** vs **Driver2=LEC Lap2=50** 時，系統原本會判斷為「單車手模式」，導致：
- ❌ 車手2的第50圈數據被清空
- ❌ 只顯示第10圈的一條線
- ❌ 無法比較同一車手的兩個不同圈速

### 解決方案
實施**方案2：新增雙圈比較模式**
- ✅ 當 `driver1 == driver2` 且 `lap1 != lap2` 時，使用雙車手比較模式
- ✅ 保留兩條線，分別顯示第10圈和第50圈
- ✅ 圖例標籤改為 **"LEC - 第10圈"** vs **"LEC - 第50圈"**

---

## 🔧 技術實施

### 修改文件
- **檔案**: `modules/gui/lap_analysis/speed_analysis/speed_analysis_chart_widget.py`
- **總修改**: 3 處關鍵變更

### 變更 1: 修改 `set_speed_data()` 方法簽名

**位置**: 第 119-145 行

#### 變更前
```python
def set_speed_data(self, distance: List[float], driver1_speed: List[float], 
                  driver2_speed: List[float], driver1_name: str = "Driver 1", 
                  driver2_name: str = "Driver 2", sectors: List[Dict] = None):
    """設置速度數據"""
```

#### 變更後
```python
def set_speed_data(self, distance: List[float], driver1_speed: List[float], 
                  driver2_speed: List[float], driver1_name: str = "Driver 1", 
                  driver2_name: str = "Driver 2", sectors: List[Dict] = None,
                  lap1: int = None, lap2: int = None):
    """
    設置速度數據
    
    Parameters:
        ...
        lap1: 車手1圈數（用於雙圈比較模式）
        lap2: 車手2圈數（用於雙圈比較模式）
    """
```

**說明**: 新增 `lap1` 和 `lap2` 參數，用於判斷雙圈比較模式

---

### 變更 2: 修改單/雙車手模式判斷邏輯

**位置**: 第 154-189 行

#### 變更前（舊邏輯）
```python
# 判斷單車手模式：空的 driver2_speed 或空的 driver2_name 表示單車手模式
self.is_single_driver = (
    not driver2_speed or 
    driver2_name == "" or 
    driver1_name == driver2_name  # ❌ 只要車手相同就是單車手模式
)
```

#### 變更後（新邏輯）
```python
# 🆕 雙圈比較模式：判斷是否為同車手不同圈數比較
is_dual_lap_mode = False
if driver1_name == driver2_name and lap1 is not None and lap2 is not None and lap1 != lap2:
    # 同車手不同圈數 → 雙圈比較模式
    is_dual_lap_mode = True
    self.driver1_name = f"{driver1_name} - 第{lap1}圈"
    self.driver2_name = f"{driver2_name} - 第{lap2}圈"
    print(f"[SPEED_CHART] 🔄 雙圈比較模式: {self.driver1_name} vs {self.driver2_name}")
else:
    # 正常模式：直接使用車手名稱
    self.driver1_name = driver1_name
    self.driver2_name = driver2_name

# 判斷單車手模式：
if not driver2_speed or driver2_name == "":
    self.is_single_driver = True
elif driver1_name == driver2_name:
    if lap1 is not None and lap2 is not None and lap1 != lap2:
        # 同車手不同圈數 → 雙圈比較模式（不是單車手模式）✅
        self.is_single_driver = False
        print(f"[SPEED_CHART] 🔍 雙圈比較模式（同車手不同圈數）")
    else:
        # 同車手相同圈數或無圈數信息 → 單車手模式
        self.is_single_driver = True
        print(f"[SPEED_CHART] 🔍 單車手模式（同車手相同圈數）")
else:
    # 不同車手 → 雙車手比較模式
    self.is_single_driver = False
```

**核心改進**:
1. 新增 `is_dual_lap_mode` 標記
2. 當檢測到同車手不同圈數時：
   - 設置 `is_single_driver = False` (使用雙車手模式)
   - 修改標籤為 `"車手代碼 - 第X圈"` 格式
3. 只有同車手相同圈數才觸發單車手模式

---

### 變更 3: 修改 `update_speed_data()` 方法

**位置**: 第 1315-1370 行

#### 變更：提取圈數信息

```python
# 如果有車手信息，使用車手代碼作為名稱
lap1 = None
lap2 = None
if len(drivers) >= 2:
    driver1_name = drivers[0].get('code', driver1_name)
    driver2_name = drivers[1].get('code', driver2_name)
    # 🆕 提取圈數信息（用於雙圈比較模式判斷）
    lap1 = drivers[0].get('lap_number')
    lap2 = drivers[1].get('lap_number')
    print(f"[SPEED_CHART_WIDGET] 🔢 提取圈數: lap1={lap1}, lap2={lap2}")
elif len(drivers) == 1:
    driver1_name = drivers[0].get('code', driver1_name)
    lap1 = drivers[0].get('lap_number')
```

#### 變更：更新判斷邏輯

```python
# 🆕 雙圈比較模式判斷邏輯
is_single_driver_mode = False
is_dual_lap_mode = False

if metadata.get('is_single_driver', False):
    is_single_driver_mode = True
elif driver1_name == driver2_name:
    # 相同車手：需要進一步判斷
    if lap1 is not None and lap2 is not None and lap1 != lap2:
        # 🆕 同車手不同圈數 → 雙圈比較模式
        is_dual_lap_mode = True
        is_single_driver_mode = False
        print(f"[SPEED_CHART] 🔄 檢測到雙圈比較模式: {driver1_name} 第{lap1}圈 vs 第{lap2}圈")
    else:
        # 同車手相同圈數或無圈數信息 → 單車手模式
        is_single_driver_mode = True
elif len(drivers) == 1:
    is_single_driver_mode = True

if is_single_driver_mode:
    # 單車手模式：清空車手2數據
    driver2_speed = []
    driver2_name = ""
    lap2 = None
elif is_dual_lap_mode:
    # 雙圈比較模式：保持車手2數據
    print(f"[SPEED_CHART] 🔄 使用雙圈比較模式顯示")
    self.is_single_driver = False
else:
    # 雙車手模式：正常顯示
    self.is_single_driver = False
```

#### 變更：傳遞圈數參數

```python
# 更新圖表
self.chart_widget.set_speed_data(
    distance=distance,
    driver1_speed=driver1_speed,
    driver2_speed=driver2_speed,
    driver1_name=driver1_name,
    driver2_name=driver2_name,
    sectors=sectors,
    lap1=lap1,  # 🆕 傳遞圈數信息
    lap2=lap2   # 🆕 傳遞圈數信息
)
```

---

## 🧪 測試結果

### 測試腳本
**檔案**: `test_dual_lap_mode.py`

### 測試案例

| 案例 | Driver1 | Lap1 | Driver2 | Lap2 | 預期模式 | 預期標籤 | 結果 |
|------|---------|------|---------|------|----------|----------|------|
| 1 | LEC | 10 | LEC | 50 | 雙圈比較 | "LEC - 第10圈" vs "LEC - 第50圈" | ✅ 通過 |
| 2 | LEC | 10 | LEC | 10 | 單車手 | "LEC" | ✅ 通過 |
| 3 | VER | 10 | LEC | 15 | 雙車手 | "VER" vs "LEC" | ✅ 通過 |
| 4 | LEC | None | LEC | None | 單車手 | "LEC" | ✅ 通過 |
| 5 | VER | 10 | "" | None | 單車手 | "VER" | ✅ 通過 |

### 測試輸出

```
================================================================================
🧪 雙圈比較模式測試
================================================================================

測試案例 1: Driver1=LEC Lap1=10 vs Driver2=LEC Lap2=50
[MOCK_CHART] 🔄 雙圈比較模式: LEC - 第10圈 vs LEC - 第50圈
[MOCK_CHART] 🔍 雙圈比較模式（同車手不同圈數）
[MOCK_CHART] 🔍 is_single_driver: False
✅ 測試案例 1 通過

...（其他案例）...

🎉 所有測試通過！
```

---

## 📊 行為對比表

### 案例：Driver1=LEC Lap1=10 vs Driver2=LEC Lap2=50

| 項目 | 舊行為（修改前） | 新行為（修改後） |
|------|------------------|------------------|
| **模式判斷** | 單車手模式 | 雙圈比較模式 |
| **is_single_driver** | `True` | `False` |
| **車手2數據** | 清空（[]） | 保留（第50圈數據） |
| **圖表顯示** | 只顯示一條線（第10圈） | 顯示兩條線（第10圈 + 第50圈） |
| **driver1_name** | "LEC" | **"LEC - 第10圈"** ✨ |
| **driver2_name** | "" (空) | **"LEC - 第50圈"** ✨ |
| **圖例** | "LEC" | "LEC - 第10圈" 和 "LEC - 第50圈" |
| **統計表格** | 只顯示一個車手 | 顯示兩個圈速的比較 |

---

## 🎯 判斷邏輯流程圖

```
用戶輸入參數
    ↓
driver1 == driver2 ?
    ├─ No → 雙車手比較模式（不同車手）
    │       標籤: "VER" vs "LEC"
    │
    └─ Yes → 檢查圈數
            ↓
        lap1 != lap2 ?
            ├─ Yes → 🆕 雙圈比較模式（同車手不同圈）
            │        is_single_driver = False
            │        標籤: "LEC - 第10圈" vs "LEC - 第50圈"
            │        保留兩條線 ✅
            │
            └─ No → 單車手模式（同車手相同圈或無圈數）
                    is_single_driver = True
                    標籤: "LEC"
                    只顯示一條線
```

---

## 💡 關鍵設計決策

### 1. **為什麼修改標籤而不是判斷邏輯？**
- **原因**: 保持系統架構簡潔，利用現有的雙車手比較模式
- **優勢**: 
  - 不需要新增第三種模式
  - 複用現有的圖表繪製邏輯
  - 只需修改標籤生成即可區分

### 2. **為什麼需要 lap1 和 lap2 參數？**
- **原因**: 原本只判斷 `driver1_name == driver2_name`，無法區分是否為同圈
- **解決**: 新增圈數信息後，可以精確判斷 `lap1 != lap2`

### 3. **為什麼在兩個地方都修改判斷邏輯？**
- **set_speed_data()**: 圖表層級的判斷（接收外部數據時）
- **update_speed_data()**: 數據載入層級的判斷（從 JSON 載入時）
- **原因**: 確保兩個入口點的邏輯一致

---

## 🔍 調試輸出範例

### 雙圈比較模式（新功能）

```
[SPEED_CHART] ========== set_speed_data 被調用 ==========
[SPEED_CHART] 👤 driver1_name: LEC
[SPEED_CHART] 👤 driver2_name: LEC
[SPEED_CHART] 🔢 lap1: 10, lap2: 50
[SPEED_CHART] 🔄 雙圈比較模式: LEC - 第10圈 vs LEC - 第50圈
[SPEED_CHART] 🔍 雙圈比較模式（同車手不同圈數）
[SPEED_CHART] 🔍 is_single_driver: False
[SPEED_CHART] 📝 最終標籤: driver1='LEC - 第10圈', driver2='LEC - 第50圈'
```

### 單車手模式（保持原邏輯）

```
[SPEED_CHART] ========== set_speed_data 被調用 ==========
[SPEED_CHART] 👤 driver1_name: LEC
[SPEED_CHART] 👤 driver2_name: LEC
[SPEED_CHART] 🔢 lap1: 10, lap2: 10
[SPEED_CHART] 🔍 單車手模式（同車手相同圈數）
[SPEED_CHART] 🔍 is_single_driver: True
```

---

## 📝 後續工作

### 已完成 ✅
- [x] Speed Analysis 模組實施
- [x] 單元測試通過
- [x] 文檔撰寫

### 待辦事項 📋

#### 1. 應用到其他遙測模組
需要對以下模組進行相同的修改：

| 模組 | 檔案路徑 | 優先級 |
|------|----------|--------|
| **Throttle Analysis** | `modules/gui/lap_analysis/Throttle_analysis/throttle_analysis_chart_widget.py` | 🔴 高 |
| **RPM Analysis** | `modules/gui/lap_analysis/rpm_analysis/rpm_analysis_chart_widget.py` | 🔴 高 |
| **Brake Analysis** | `modules/gui/lap_analysis/brake_analysis/brake_analysis_chart_widget.py` | 🟡 中 |
| **Gear Analysis** | `modules/gui/lap_analysis/gear_analysis/gear_analysis_chart_widget.py` | 🟡 中 |
| **Acceleration Analysis** | `modules/gui/lap_analysis/acceleration_analysis/*.py` | 🟢 低 |
| **Speed Diff** | `modules/gui/lap_analysis/speed_diff_analysis/*.py` | 🟢 低 |
| **Distance Diff** | `modules/gui/lap_analysis/distance_diff_analysis/*.py` | 🟢 低 |

**修改模板**（適用於所有模組）：
1. 在 `set_*_data()` 方法簽名中添加 `lap1` 和 `lap2` 參數
2. 修改判斷邏輯（與 Speed Analysis 相同）
3. 在 `update_*_data()` 方法中提取圈數並傳遞

#### 2. GUI 整合測試
- [ ] 在實際 F1T GUI 中測試雙圈比較模式
- [ ] 驗證圖例顯示正確
- [ ] 驗證統計表格正常運作
- [ ] 檢查工具欄狀態更新

#### 3. 用戶提示優化（可選）
當用戶選擇同車手不同圈時，可以考慮增加提示：

```python
if is_dual_lap_mode:
    QMessageBox.information(
        self,
        "雙圈比較模式",
        f"檢測到 {driver1_name} 第{lap1}圈 vs 第{lap2}圈\n"
        "系統將使用雙圈比較模式顯示兩個圈速。"
    )
```

#### 4. 文檔更新
- [ ] 更新 `DEEP_DIVE_Lap_Analysis_Architecture.md`
- [ ] 更新 `ANALYSIS_Single_Driver_Mode_Logic.md`
- [ ] 創建用戶手冊說明雙圈比較功能

---

## 🎉 總結

### 成果
✅ **成功實施雙圈比較模式**
- 同車手不同圈數現在可以正常比較
- 圖例標籤清晰顯示 "車手 - 第X圈"
- 保留兩條線和完整數據
- 所有測試案例通過

### 影響
- **Speed Analysis**: ✅ 已實施
- **其他遙測模組**: ⏳ 待實施
- **向後兼容性**: ✅ 完全兼容（新增參數為可選）

### 下一步
建議優先實施 **Throttle Analysis** 和 **RPM Analysis**，因為這兩個模組使用頻率較高。

---

**實施者**: GitHub Copilot  
**審核者**: F1T Team  
**狀態**: ✅ Speed Analysis 完成，待擴展至其他模組

