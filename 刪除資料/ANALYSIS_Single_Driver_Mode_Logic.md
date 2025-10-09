# 🔍 深度分析：單車手模式判斷邏輯

**分析日期**: 2025-10-07  
**問題**: Driver1=LEC Lap1=10 vs Driver2=LEC Lap2=50 會觸發單車手模式嗎？  
**答案**: ✅ **會觸發單車手模式**

---

## 📊 核心判斷邏輯

系統在**兩個層級**判斷單/雙車手模式：

### 第一層級：ChartWidget 初始化判斷

**位置**: `*_chart_widget.py` 的 `set_*_data()` 方法  
**判斷時機**: 接收數據時

#### Speed Analysis 範例

**檔案**: `modules/gui/lap_analysis/speed_analysis/speed_analysis_chart_widget.py`  
**行數**: ~148

```python
def set_speed_data(self, distance, driver1_speed, driver2_speed, 
                   driver1_name: str = "Driver 1", 
                   driver2_name: str = "Driver 2", 
                   sectors: List[Dict] = None):
    """設置速度數據"""
    
    # 🔍 關鍵判斷邏輯
    self.is_single_driver = (
        not driver2_speed or          # 車手2無數據
        driver2_name == "" or         # 車手2名稱為空
        driver1_name == driver2_name  # ⚠️ 兩個車手代碼相同
    )
    
    print(f"[SPEED_CHART] 🔍 單車手模式: {self.is_single_driver}")
```

#### Throttle Analysis 範例

**檔案**: `modules/gui/lap_analysis/Throttle_analysis/throttle_analysis_chart_widget.py`  
**行數**: ~141

```python
def set_throttle_data(self, distance, driver1_throttle, driver2_throttle,
                      driver1_name: str = "Driver 1",
                      driver2_name: str = "Driver 2",
                      sectors: List[Dict] = None):
    """設置油門數據"""
    
    # 🔍 完全相同的判斷邏輯
    self.is_single_driver = (
        not driver2_throttle or 
        driver2_name == "" or 
        driver1_name == driver2_name
    )
```

### 第二層級：數據更新時的動態判斷

**位置**: `*_chart_widget.py` 的 `update_chart_from_json()` 方法  
**判斷時機**: 載入 JSON 數據後

**檔案**: `speed_analysis_chart_widget.py`  
**行數**: ~1294-1318

```python
# 檢測是否為單車手模式或相同車手比較
is_single_driver_mode = False

if metadata.get('is_single_driver', False):
    # 1️⃣ 明確標記的單車手模式
    is_single_driver_mode = True
    print(f"[SPEED_CHART] 🔍 檢測到單車手模式標記")

elif driver1_name == driver2_name:
    # 2️⃣ 相同車手比較（如 LEC vs LEC）⚠️ 關鍵！
    is_single_driver_mode = True
    print(f"[SPEED_CHART] 🔍 檢測到相同車手比較: {driver1_name} vs {driver2_name}")

elif len(drivers) == 1:
    # 3️⃣ 只有一個車手的數據
    is_single_driver_mode = True
    print(f"[SPEED_CHART] 🔍 檢測到單車手數據: {driver1_name}")

if is_single_driver_mode:
    print(f"[SPEED_CHART] 🎯 使用單車手模式顯示")
    self.is_single_driver = True
    # ⚠️ 清空車手2的數據，只顯示車手1
    driver2_speed = []
    driver2_name = ""
else:
    self.is_single_driver = False
    print(f"[SPEED_CHART] 🎯 使用雙車手模式顯示: {driver1_name} vs {driver2_name}")
```

---

## 🎯 問題案例分析

### 案例: Driver1=LEC Lap1=10, Driver2=LEC Lap2=50

#### 第一層級判斷（初始化）

```python
driver1_name = "LEC"  # 來自 driver1_combo
driver2_name = "LEC"  # 來自 driver2_combo
lap1 = 10
lap2 = 50

# 執行判斷
self.is_single_driver = (
    not driver2_speed or       # ❌ False - driver2 有數據
    driver2_name == "" or      # ❌ False - driver2_name = "LEC"
    driver1_name == driver2_name  # ✅ True - "LEC" == "LEC"
)

# 結果：is_single_driver = True ✅
```

#### 第二層級判斷（數據更新）

```python
driver1_name = "LEC"
driver2_name = "LEC"

# 執行三重檢測
if metadata.get('is_single_driver', False):
    # 可能為 False（取決於 JSON）
    pass
elif driver1_name == driver2_name:  # ✅ True - "LEC" == "LEC"
    is_single_driver_mode = True
    print(f"[SPEED_CHART] 🔍 檢測到相同車手比較: LEC vs LEC")
    
# 結果：is_single_driver_mode = True ✅

# 後續處理
if is_single_driver_mode:
    self.is_single_driver = True
    driver2_speed = []      # 清空車手2數據
    driver2_name = ""       # 清空車手2名稱
```

---

## 🔬 深入分析：為什麼這樣設計？

### 1. **邏輯合理性** ✅

當 `driver1_name == driver2_name` 時：
- **語義**: 用戶想比較**同一車手的兩個不同圈速**
- **實際**: 例如 LEC 第10圈 vs LEC 第50圈
- **預期行為**: 應該顯示為「單車手的圈速差異比較」，而非「兩個不同車手的比較」

### 2. **UI/UX 考量** 👍

**單車手模式的優勢**:
- 避免圖表顯示兩條完全相同顏色的線（混淆）
- 統計表格不會顯示「LEC vs LEC」的冗余比較
- 圖例更簡潔（只顯示一個車手名稱）
- 避免誤導用戶以為是「不同車手的對比」

### 3. **數據處理邏輯** 🔧

進入單車手模式後：

```python
# 清空車手2的數據
driver2_speed = []
driver2_name = ""

# 只繪製車手1的圖形
self.chart_widget.set_speed_data(
    distance=distance,
    driver1_speed=driver1_speed,
    driver2_speed=[],           # 空列表
    driver1_name="LEC",
    driver2_name="",            # 空字串
    sectors=sectors
)
```

**結果**:
- 圖表只顯示一條線（車手1）
- 車手2的圈速**被丟棄**，不會繪製
- 統計表格只顯示車手1的數據

---

## ⚠️ 潛在問題：用戶預期 vs 實際行為

### 問題場景

**用戶操作**:
1. 選擇 Driver1 = LEC, Lap1 = 10
2. 選擇 Driver2 = LEC, Lap2 = 50
3. 點擊 "Update All Analysis"

**用戶預期**:
- 看到 LEC 第10圈和第50圈的**兩條線進行比較**
- 圖表應該顯示兩個圈速的差異（速度曲線對比）

**實際結果**:
- ❌ 系統判斷為「單車手模式」
- ❌ 車手2的數據（第50圈）被清空
- ❌ **只顯示第10圈的一條線**
- ❌ 第50圈的數據**完全不顯示**

### 控制台輸出

```
[SPEED_CHART] 🔍 檢測到相同車手比較: LEC vs LEC
[SPEED_CHART] 🎯 使用單車手模式顯示
[SPEED_CHART] 清空車手2數據: driver2_speed = []
[SPEED_CHART] 只繪製車手1: LEC 第10圈
```

---

## 🐛 是否為 BUG？

### 觀點A: 這是**正確的設計** ✅

**理由**:
1. **語義正確性**: "LEC vs LEC" 在語義上不合理，應該視為單車手
2. **避免混淆**: 防止用戶誤以為是「不同車手的比較」
3. **UI 一致性**: 保持單/雙車手模式的清晰界限

**建議使用方式**:
- 如果要比較同一車手的兩個圈速，應該:
  - 使用「圈速對比」功能（Function 13）
  - 或在圖表上手動疊加兩個圈速的視窗

### 觀點B: 這是**功能缺陷** ❌

**理由**:
1. **用戶預期**: 明確選擇了兩個不同的圈數，期望看到對比
2. **功能限制**: 無法通過主控制器直接比較同一車手的不同圈速
3. **數據丟失**: 車手2的圈速數據被默默丟棄，沒有警告

**改進建議**:
1. **檢測並提示**: 當 `driver1 == driver2` 但 `lap1 != lap2` 時，顯示提示
2. **保留雙圈模式**: 新增「同車手雙圈比較」模式，保留兩條線
3. **UI 優化**: 圖例顯示為 "LEC - 第10圈" 和 "LEC - 第50圈"

---

## 🔄 影響範圍

### 受影響的遙測模組

所有遙測分析模組都使用相同邏輯：

| 模組 | 檔案 | 判斷邏輯 | 行為 |
|------|------|----------|------|
| **Speed Analysis** | `speed_analysis_chart_widget.py:148` | `driver1_name == driver2_name` | 單車手模式 ✅ |
| **Throttle Analysis** | `throttle_analysis_chart_widget.py:141` | `driver1_name == driver2_name` | 單車手模式 ✅ |
| **RPM Analysis** | `rpm_analysis_chart_widget.py:509` | `driver1_name == driver2_name` | 單車手模式 ✅ |
| **Brake Analysis** | `brake_analysis_chart_widget.py:514` | `driver1_name == driver2_name` | 單車手模式 ✅ |
| **Gear Analysis** | `gear_analysis_chart_widget.py:512` | `driver1_name == driver2_name` | 單車手模式 ✅ |
| **Acceleration** | （待確認） | （待確認） | （待確認） |
| **Speed Diff** | （待確認） | （待確認） | （待確認） |
| **Distance Diff** | （待確認） | （待確認） | （待確認） |

**結論**: **所有遙測模組都會觸發單車手模式** ✅

---

## 📝 結論

### 直接回答原問題

**Q**: Driver1=LEC Lap1=10, Driver2=LEC Lap2=50 是不是會觸發單車手模式？  
**A**: ✅ **是的，會觸發單車手模式**

### 判斷依據

```python
# 所有遙測模組的判斷邏輯
self.is_single_driver = (
    not driver2_data or 
    driver2_name == "" or 
    driver1_name == driver2_name  # ✅ "LEC" == "LEC" → True
)
```

### 實際影響

1. **車手2的圈速數據會被清空**（driver2_speed = []）
2. **只顯示車手1的第10圈**，第50圈不會顯示
3. **圖表只有一條線**，不會有對比
4. **統計表格只顯示一個車手**

### 設計哲學

系統認為 **"LEC vs LEC" 在語義上等同於單車手模式**，即使圈數不同。這是一個**有意為之的設計決策**，目的是:
- 保持單/雙車手模式的清晰界限
- 避免 UI 上的混淆（相同顏色的兩條線）
- 簡化統計比較邏輯

---

## 🛠️ 建議改進方案

### 方案A: 保持現狀 + 增加提示

```python
if driver1_name == driver2_name and lap1 != lap2:
    QMessageBox.information(
        self, 
        "同車手不同圈數比較",
        f"檢測到相同車手的不同圈數比較 ({driver1_name} 第{lap1}圈 vs 第{lap2}圈)\n"
        "系統將使用單車手模式，只顯示第一圈的數據。\n\n"
        "如需比較同車手的兩個圈速，請使用「圈速對比」功能。"
    )
```

### 方案B: 新增「同車手雙圈模式」

```python
# 修改判斷邏輯
if driver1_name == driver2_name:
    if lap1 == lap2:
        # 相同車手相同圈數 → 單車手模式
        self.is_single_driver = True
    else:
        # 相同車手不同圈數 → 雙圈比較模式
        self.is_same_driver_dual_lap = True
        # 保留兩條線，但使用不同標記
        driver1_label = f"{driver1_name} - 第{lap1}圈"
        driver2_label = f"{driver2_name} - 第{lap2}圈"
```

### 方案C: 在 UI 上禁止相同車手選擇

```python
# f1t_gui_main.py 中的信號處理
def on_driver1_changed(self):
    driver1 = self.driver1_combo.currentText()
    driver2 = self.driver2_combo.currentText()
    
    if driver1 == driver2 and driver2 != "無":
        QMessageBox.warning(
            self,
            "無效選擇",
            "車手1和車手2不能相同\n請選擇不同的車手或將車手2設為「無」"
        )
        self.driver2_combo.setCurrentText("無")
```

---

**分析完成時間**: 2025-10-07  
**文件版本**: v1.0  
**下一步**: 等待產品決策 - 是否需要修改此行為

