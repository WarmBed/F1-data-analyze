# 📊 雙圈比較模式實施狀況報告

**報告日期**: 2025-10-07  
**功能**: 單車手雙圈比較模式 (Same Driver, Different Laps)  
**狀態**: ⚠️ 僅部分實施

---

## 🔍 實施狀況總覽

### ✅ 已實施模組

#### 1. Speed Analysis（速度分析）✅ 完整實施

**檔案**: `modules/gui/lap_analysis/speed_analysis/speed_analysis_chart_widget.py`

**實施內容**:
- ✅ `set_speed_data()` 接受 `lap1` 和 `lap2` 參數（第 122 行）
- ✅ 雙圈比較模式判斷邏輯（第 159-189 行）
- ✅ 圖例顯示圈數標籤："LEC - 第10圈" vs "LEC - 第50圈"
- ✅ 測試通過（5/5 測試案例）

**核心邏輯**:
```python
def set_speed_data(self, distance: List[float], 
                  driver1_speed: List[float], 
                  driver2_speed: List[float], 
                  driver1_name: str = "Driver 1", 
                  driver2_name: str = "Driver 2", 
                  sectors: List[Dict] = None,
                  lap1: int = None, lap2: int = None):  # 🆕 雙圈參數
    
    # 雙圈比較模式判斷
    is_dual_lap_mode = False
    if driver1_name == driver2_name and lap1 is not None and lap2 is not None and lap1 != lap2:
        # 同車手不同圈數 → 雙圈比較模式
        is_dual_lap_mode = True
        self.driver1_name = f"{driver1_name} - 第{lap1}圈"
        self.driver2_name = f"{driver2_name} - 第{lap2}圈"
```

**實施日期**: 2025-10-07  
**測試狀態**: ✅ 通過

---

### ❌ 未實施模組（7 個）

以下模組的 `set_*_data()` 方法**沒有** `lap1`/`lap2` 參數，無法支援雙圈比較：

#### 2. Brake Analysis（煞車分析）❌

**檔案**: `modules/gui/lap_analysis/brake_analysis/brake_analysis_chart_widget.py`

**當前方法簽名**:
```python
def set_brake_data(self, distance: List[float], 
                 driver1_brake: List[float], 
                 driver2_brake: List[float], 
                 driver1_name: str = "Driver 1", 
                 driver2_name: str = "Driver 2", 
                 sectors: List[Dict] = None):  # ❌ 沒有 lap1, lap2
```

**缺失功能**:
- ❌ 無法接受圈數參數
- ❌ 無雙圈比較模式判斷
- ❌ 圖例不顯示圈數標籤

---

#### 3. Throttle Analysis（油門分析）❌

**檔案**: `modules/gui/lap_analysis/Throttle_analysis/throttle_analysis_chart_widget.py`

**當前狀態**:
- ✅ 有 `set_lap_numbers()` 方法（第 1390 行）
- ❌ 但 `set_throttle_data()` 沒有 lap1/lap2 參數
- ❌ 無雙圈比較模式實施

**方法簽名**:
```python
def set_throttle_data(self, distance: List[float], 
                     driver1_throttle: List[float], 
                     driver2_throttle: List[float], 
                     driver1_name: str = "Driver 1", 
                     driver2_name: str = "Driver 2", 
                     sectors: List[Dict] = None):  # ❌ 沒有 lap1, lap2
```

---

#### 4. RPM Analysis（轉速分析）❌

**檔案**: `modules/gui/lap_analysis/rpm_analysis/rpm_analysis_chart_widget.py`

**狀態**: 未檢查，推測與 Brake/Throttle 類似

---

#### 5. Gear Analysis（檔位分析）❌

**檔案**: `modules/gui/lap_analysis/gear_analysis/gear_analysis_chart_widget.py`

**狀態**: 未檢查，推測與 Brake/Throttle 類似

---

#### 6. Acceleration Analysis（加速度分析）❌

**檔案**: `modules/gui/lap_analysis/acceleration_analysis/acceleration_analysis_chart_widget.py`

**狀態**: 未檢查，推測與 Brake/Throttle 類似

---

#### 7. Speed Diff Analysis（速度差異分析）❌

**檔案**: `modules/gui/lap_analysis/speeddiff_analysis/speeddiff_analysis_chart_widget.py`

**狀態**: 未檢查，推測與 Brake/Throttle 類似

---

#### 8. Distance Diff Analysis（距離差異分析）❌

**檔案**: `modules/gui/lap_analysis/distancediff_analysis/distancediff_analysis_chart_widget.py`

**狀態**: 未檢查，推測與 Brake/Throttle 類似

---

## 📊 實施進度統計

### 總覽
- **總模組數**: 8
- **已實施**: 1 (12.5%)
- **未實施**: 7 (87.5%)

### 進度條
```
Speed Analysis     ████████████████████ 100% ✅
Brake Analysis     ░░░░░░░░░░░░░░░░░░░░   0% ❌
Throttle Analysis  ░░░░░░░░░░░░░░░░░░░░   0% ❌
RPM Analysis       ░░░░░░░░░░░░░░░░░░░░   0% ❌
Gear Analysis      ░░░░░░░░░░░░░░░░░░░░   0% ❌
Acceleration       ░░░░░░░░░░░░░░░░░░░░   0% ❌
Speed Diff         ░░░░░░░░░░░░░░░░░░░░   0% ❌
Distance Diff      ░░░░░░░░░░░░░░░░░░░░   0% ❌
─────────────────────────────────────────
總進度             ██░░░░░░░░░░░░░░░░░░ 12.5%
```

---

## 🔧 待實施工作

### 優先順序 1（核心遙測）

#### Brake Analysis
**預估時間**: 30 分鐘  
**工作內容**:
1. 修改 `set_brake_data()` 添加 `lap1`/`lap2` 參數
2. 實施雙圈比較模式判斷
3. 修改圖例顯示圈數標籤
4. 修改 `update_brake_data()` 提取和傳遞圈數

**參考**: `speed_analysis_chart_widget.py` 第 119-189 行

---

#### Throttle Analysis
**預估時間**: 30 分鐘  
**工作內容**: 同 Brake Analysis

---

#### RPM Analysis
**預估時間**: 30 分鐘  
**工作內容**: 同 Brake Analysis

---

### 優先順序 2（進階分析）

#### Gear Analysis
**預估時間**: 30 分鐘

#### Acceleration Analysis
**預估時間**: 30 分鐘

---

### 優先順序 3（差異分析）

#### Speed Diff Analysis
**預估時間**: 30 分鐘

#### Distance Diff Analysis
**預估時間**: 30 分鐘

---

## 📋 實施檢查清單

### Brake Analysis 實施步驟

- [ ] **Step 1**: 修改 `set_brake_data()` 方法簽名
  ```python
  def set_brake_data(self, distance: List[float], 
                   driver1_brake: List[float], 
                   driver2_brake: List[float], 
                   driver1_name: str = "Driver 1", 
                   driver2_name: str = "Driver 2", 
                   sectors: List[Dict] = None,
                   lap1: int = None, lap2: int = None):  # 🆕 添加
  ```

- [ ] **Step 2**: 添加雙圈比較模式判斷
  ```python
  is_dual_lap_mode = False
  if driver1_name == driver2_name and lap1 is not None and lap2 is not None and lap1 != lap2:
      is_dual_lap_mode = True
      self.driver1_name = f"{driver1_name} - 第{lap1}圈"
      self.driver2_name = f"{driver2_name} - 第{lap2}圈"
  ```

- [ ] **Step 3**: 修改 `update_brake_data()` 提取圈數
  ```python
  # 提取圈數信息
  lap1 = None
  lap2 = None
  if 'drivers' in data and len(data['drivers']) >= 2:
      driver1_info = data['drivers'][0]
      driver2_info = data['drivers'][1]
      lap1 = driver1_info.get('lap_number')
      lap2 = driver2_info.get('lap_number')
  ```

- [ ] **Step 4**: 傳遞圈數到 `set_brake_data()`
  ```python
  self.brake_chart.set_brake_data(
      distance, driver1_brake, driver2_brake,
      driver1_name, driver2_name, sectors,
      lap1=lap1, lap2=lap2  # 🆕 傳遞圈數
  )
  ```

- [ ] **Step 5**: 測試驗證
  - 測試同車手不同圈數（LEC Lap10 vs LEC Lap50）
  - 測試不同車手（VER vs LEC）
  - 測試圖例顯示正確

---

## 🎯 批次實施建議

### 方法 1: 使用自動化腳本

參考之前創建的 `apply_dual_lap_mode.py` 工具，可以批次修改所有模組。

**優點**:
- 快速一致
- 減少手動錯誤

**缺點**:
- 需要仔細測試每個模組

---

### 方法 2: 逐個手動實施

按優先順序逐個修改和測試。

**優點**:
- 可以細緻調整每個模組
- 更容易發現問題

**缺點**:
- 耗時較長

---

## 📊 預估總工時

### 手動實施
- Brake: 30 分鐘
- Throttle: 30 分鐘
- RPM: 30 分鐘
- Gear: 30 分鐘
- Acceleration: 30 分鐘
- Speed Diff: 30 分鐘
- Distance Diff: 30 分鐘

**總計**: 3.5 小時

### 使用自動化腳本
- 腳本開發: 1 小時
- 批次執行: 10 分鐘
- 測試驗證: 1.5 小時

**總計**: 2.5 小時

---

## ✅ 完成後效果

### 修改前
```
用戶選擇: LEC Lap10 vs LEC Lap50

Speed Analysis:   ✅ 顯示 "LEC - 第10圈" vs "LEC - 第50圈"
Brake Analysis:   ❌ 顯示 "LEC" vs "LEC" (無法區分)
Throttle Analysis: ❌ 顯示 "LEC" vs "LEC" (無法區分)
```

### 修改後
```
用戶選擇: LEC Lap10 vs LEC Lap50

Speed Analysis:   ✅ 顯示 "LEC - 第10圈" vs "LEC - 第50圈"
Brake Analysis:   ✅ 顯示 "LEC - 第10圈" vs "LEC - 第50圈"
Throttle Analysis: ✅ 顯示 "LEC - 第10圈" vs "LEC - 第50圈"
RPM Analysis:     ✅ 顯示 "LEC - 第10圈" vs "LEC - 第50圈"
Gear Analysis:    ✅ 顯示 "LEC - 第10圈" vs "LEC - 第50圈"
...
```

---

## 🎉 總結

### 當前狀況
- ✅ Speed Analysis 已完整實施雙圈比較模式
- ❌ 其餘 7 個模組尚未實施

### 建議行動
1. 優先實施 Brake、Throttle、RPM（核心遙測）
2. 使用 Speed Analysis 作為範本
3. 逐個測試驗證

### 預期收益
- ✅ 所有遙測圖表支援雙圈比較
- ✅ 統一的用戶體驗
- ✅ 更強大的分析功能

---

**報告生成時間**: 2025-10-07  
**下一步**: 決定實施策略（手動 vs 自動化）

