# 🎯 Lap Analysis 時間軸功能 - 完整任務清單與代碼規劃

**項目代號**：TIME-AXIS-UNIFICATION  
**開始日期**：2025-10-11  
**預估完成**：2025-10-13  
**負責人**：AI Assistant  

---

## 📊 項目概述

### 目標
為所有 `lap_analysis` 模組添加**時間序列 X 軸切換**功能，允許用戶在「距離」和「時間」兩種 X 軸模式之間切換。

### 影響範圍
```
modules/gui/lap_analysis/
├── ✅ speed_analysis/          # 速度分析
├── ✅ throttle_analysis/       # 油門分析  
├── ✅ rpm_analysis/            # RPM 分析
├── ✅ gear_analysis/           # 檔位分析
├── ✅ brake_analysis/          # 煞車分析
├── ✅ acceleration_analysis/  # 加速度分析
├── ⚠️ speeddiff_analysis/     # 速度差分析（特殊）
└── ⚠️ distancediff_analysis/  # 距離差分析（特殊）

總計：8 個模組
標準模組：6 個（需要完整實現）
特殊模組：2 個（需要特別處理）
```

---

## 🏗️ 架構設計

### 設計原則

#### 原則 1：統一基類方案
- ✅ 修改 `TelemetryChartWidgetBase`（如果存在）
- ✅ 所有模組繼承統一實現
- ✅ 減少代碼重複

#### 原則 2：向後兼容
- ✅ 不破壞現有功能
- ✅ 距離軸為預設模式
- ✅ 時間軸為可選功能

#### 原則 3：數據分離
- ✅ 時間數據獨立儲存
- ✅ 從 JSON `time_series` 提取
- ✅ 與距離數據同步

### 核心組件設計

#### 1️⃣ **數據結構擴展**
```python
# 現有結構
class ChartWidget:
    distance_data: List[float]     # X 軸：距離
    driver1_values: List[float]    # Y 軸：數值
    driver2_values: List[float]    # Y 軸：數值

# 新增結構
class ChartWidget:
    distance_data: List[float]     # X 軸：距離（保留）
    time_data: List[float]         # X 軸：時間（新增）
    driver1_values: List[float]    # Y 軸：數值
    driver2_values: List[float]    # Y 軸：數值
    use_time_axis: bool = False    # 軸模式切換標記
```

#### 2️⃣ **UI 組件設計**
```python
# 控制面板擴展
class AnalysisChartWidget:
    def _create_status_info_widget(self):
        # ... 現有控制項 ...
        
        # 新增：時間軸切換 Checkbox
        time_axis_container = QWidget()
        time_axis_layout = QHBoxLayout(time_axis_container)
        
        self.time_axis_checkbox = QCheckBox(tr("use_time_axis", "使用時間軸"))
        self.time_axis_checkbox.setChecked(False)  # 預設：距離軸
        self.time_axis_checkbox.stateChanged.connect(self._on_time_axis_toggled)
        
        time_axis_layout.addWidget(self.time_axis_checkbox)
        layout.addWidget(time_axis_container)
```

#### 3️⃣ **繪圖邏輯修改**
```python
def paintEvent(self, event):
    # 選擇 X 軸數據源
    if self.use_time_axis and len(self.time_data) > 0:
        x_data = self.time_data
        x_label = tr("time_seconds", "時間 (秒)")
        x_min, x_max = self.view_min_time, self.view_max_time
    else:
        x_data = self.distance_data
        x_label = tr("distance_meters", "距離 (公尺)")
        x_min, x_max = self.view_min_distance, self.view_max_distance
    
    # 現有繪圖邏輯保持不變
    # 只需將所有 self.distance_data 替換為 x_data
```

#### 4️⃣ **數據載入器擴展**
```python
class TelemetryDataLoader:
    def _transform_data_for_display(self, raw_data: dict) -> dict:
        transformed = {
            'telemetry_data': {...},
            'metadata': {...}
        }
        
        # 新增：提取時間序列數據
        if 'time_series' in raw_data:
            time_series = raw_data['time_series']
            driver1_ch = time_series['driver1']['channels']
            
            # 獲取第一個可用通道的時間數據
            for channel_name, channel_data in driver1_ch.items():
                if 'time_seconds' in channel_data:
                    transformed['time_data'] = channel_data['time_seconds']
                    break
        
        return transformed
```

---

## 📋 詳細任務清單

### Phase 1：基礎設施準備（優先級：🔴 最高）

#### Task 1.1：檢查基類是否存在
- [ ] 檢查 `TelemetryChartWidgetBase` 是否存在
- [ ] 分析基類的方法和屬性
- [ ] 確定是否可以在基類統一實現

**檔案**：`modules/gui/base/universal_chart_widget_base.py`  
**預估時間**：30 分鐘  
**依賴**：無

#### Task 1.2：設計統一接口
- [ ] 定義 `set_time_data()` 方法
- [ ] 定義 `toggle_time_axis()` 方法
- [ ] 定義時間軸相關屬性

**輸出**：接口文檔  
**預估時間**：1 小時  
**依賴**：Task 1.1

#### Task 1.3：創建測試數據
- [ ] 準備包含時間序列的 JSON 測試檔案
- [ ] 驗證 CLI 功能13輸出正確

**預估時間**：30 分鐘  
**依賴**：無

---

### Phase 2：單一模組實現（優先級：🟠 高）

#### Task 2.1：Speed Analysis 完整實現
**目標**：作為其他模組的範本

##### Subtask 2.1.1：UI 組件修改
- [ ] 修改 `speed_analysis_chart_widget.py`
- [ ] 在 `_create_status_info_widget()` 添加 Checkbox
- [ ] 實現 `_on_time_axis_toggled()` 回調

**檔案**：`modules/gui/lap_analysis/speed_analysis/speed_analysis_chart_widget.py`  
**修改行數**：約 50 行  
**預估時間**：1 小時

##### Subtask 2.1.2：數據結構擴展
- [ ] 在 `SpeedChartWidget` 添加 `time_data` 屬性
- [ ] 修改 `set_speed_data()` 方法接受時間數據
- [ ] 添加 `use_time_axis` 屬性

**檔案**：同上  
**修改行數**：約 30 行  
**預估時間**：1 小時

##### Subtask 2.1.3：繪圖邏輯修改
- [ ] 修改 `paintEvent()` 方法
- [ ] 實現 X 軸數據源切換
- [ ] 更新 X 軸標籤和範圍

**檔案**：同上  
**修改行數**：約 80 行  
**預估時間**：2 小時

##### Subtask 2.1.4：數據載入器修改
- [ ] 修改 `speed_analysis_data_loader.py`
- [ ] 在 `_transform_data_for_display()` 提取時間數據
- [ ] 傳遞時間數據到 Chart Widget

**檔案**：`modules/gui/lap_analysis/speed_analysis/speed_analysis_data_loader.py`  
**修改行數**：約 40 行  
**預估時間**：1.5 小時

##### Subtask 2.1.5：測試和調試
- [ ] 載入測試數據
- [ ] 驗證距離軸模式（預設）
- [ ] 驗證時間軸模式切換
- [ ] 測試連動功能
- [ ] 測試縮放和拖拉

**預估時間**：2 小時

**Task 2.1 總時間**：7.5 小時

---

### Phase 3：批次模組實現（優先級：🟡 中）

#### Task 3.1：Throttle Analysis
- [ ] 複製 Speed Analysis 的實現模式
- [ ] 修改 `throttle_analysis_chart_widget.py`
- [ ] 修改數據載入器
- [ ] 測試

**預估時間**：4 小時

#### Task 3.2：RPM Analysis
- [ ] 同 Task 3.1 流程
- [ ] 特別注意 RPM 的數值範圍

**預估時間**：4 小時

#### Task 3.3：Gear Analysis
- [ ] 同 Task 3.1 流程
- [ ] 檔位為整數值，需要特別處理

**預估時間**：4 小時

#### Task 3.4：Brake Analysis
- [ ] 同 Task 3.1 流程
- [ ] 煞車為百分比值

**預估時間**：4 小時

#### Task 3.5：Acceleration Analysis
- [ ] 同 Task 3.1 流程
- [ ] 加速度可能有負值

**預估時間**：4 小時

**Phase 3 總時間**：20 小時

---

### Phase 4：特殊模組處理（優先級：🟢 低）

#### Task 4.1：SpeedDiff Analysis
**特殊性**：本身是「差值」分析，X 軸切換意義不同

- [ ] 評估是否需要時間軸
- [ ] 如果需要，實現特殊邏輯
- [ ] 測試

**預估時間**：3 小時（待評估）

#### Task 4.2：DistanceDiff Analysis
**特殊性**：分析「距離差」，時間軸可能更有意義

- [ ] 評估實現方式
- [ ] 實現時間軸切換
- [ ] 測試

**預估時間**：3 小時（待評估）

**Phase 4 總時間**：6 小時

---

### Phase 5：基類重構（優先級：🔵 最低，可選）

#### Task 5.1：提取共用邏輯到基類
- [ ] 分析所有模組的共同模式
- [ ] 在 `TelemetryChartWidgetBase` 實現統一方法
- [ ] 所有模組繼承基類實現

**預估時間**：6 小時  
**依賴**：Phase 2, 3, 4 全部完成

#### Task 5.2：代碼清理和優化
- [ ] 刪除重複代碼
- [ ] 統一命名規範
- [ ] 添加文檔註釋

**預估時間**：4 小時

**Phase 5 總時間**：10 小時

---

### Phase 6：測試和文檔（優先級：🔴 最高）

#### Task 6.1：全面測試
- [ ] 所有模組的距離軸模式
- [ ] 所有模組的時間軸模式
- [ ] 切換功能正常
- [ ] 連動功能正常
- [ ] 縮放和拖拉正常
- [ ] 數據準確性驗證

**預估時間**：4 小時

#### Task 6.2：創建使用者文檔
- [ ] 編寫功能說明
- [ ] 創建操作指南
- [ ] 添加螢幕截圖

**預估時間**：2 小時

#### Task 6.3：開發者文檔
- [ ] API 文檔
- [ ] 架構說明
- [ ] 擴展指南

**預估時間**：2 小時

**Phase 6 總時間**：8 小時

---

## 📊 時間估算總結

| Phase | 任務內容 | 預估時間 | 優先級 |
|-------|---------|---------|--------|
| Phase 1 | 基礎設施準備 | 2 小時 | 🔴 最高 |
| Phase 2 | Speed Analysis 實現 | 7.5 小時 | 🟠 高 |
| Phase 3 | 批次模組實現 (5個) | 20 小時 | 🟡 中 |
| Phase 4 | 特殊模組處理 (2個) | 6 小時 | 🟢 低 |
| Phase 5 | 基類重構（可選） | 10 小時 | 🔵 最低 |
| Phase 6 | 測試和文檔 | 8 小時 | 🔴 最高 |
| **總計** | | **53.5 小時** | |

### 最小可行產品 (MVP)
**Phase 1 + 2 + 6（部分）** = **12 小時**（1.5 個工作日）

### 完整實現（不含基類重構）
**Phase 1-4 + 6** = **43.5 小時**（5.5 個工作日）

### 完整實現（含基類重構）
**Phase 1-6** = **53.5 小時**（6.5 個工作日）

---

## 🎯 執行策略

### 建議執行順序

#### 第一天：基礎 + Speed Analysis
1. ✅ Phase 1：基礎設施（2h）
2. ✅ Phase 2：Speed Analysis（7.5h）
3. ✅ 簡單測試（0.5h）

**Day 1 總計**：10 小時

#### 第二天：批次實現（前3個）
1. ✅ Task 3.1：Throttle（4h）
2. ✅ Task 3.2：RPM（4h）
3. ✅ Task 3.3：Gear（開始，2h）

**Day 2 總計**：10 小時

#### 第三天：批次實現（後2個）+ 測試
1. ✅ Task 3.3：Gear（完成，2h）
2. ✅ Task 3.4：Brake（4h）
3. ✅ Task 3.5：Acceleration（4h）
4. ✅ 初步測試（2h）

**Day 3 總計**：12 小時

---

## 📝 代碼規範

### 命名規範
```python
# 屬性命名
self.time_data: List[float]           # 時間數據
self.use_time_axis: bool              # 軸模式標記
self.time_axis_checkbox: QCheckBox    # UI 組件

# 方法命名
def set_time_data(self, time_data: List[float])  # 設置時間數據
def _on_time_axis_toggled(self, state: int)      # 切換回調
def toggle_time_axis(self, enabled: bool)        # 公開方法
```

### 國際化要求
所有用戶可見字串必須使用 `tr()` 函數：
```python
# ✅ 正確
self.time_axis_checkbox = QCheckBox(tr("use_time_axis", "使用時間軸"))
x_label = tr("time_seconds", "時間 (秒)")

# ❌ 錯誤
self.time_axis_checkbox = QCheckBox("使用時間軸")
```

### 註釋要求
```python
def set_time_data(self, time_data: List[float]):
    """
    設置時間序列數據
    
    Args:
        time_data: 時間數據數組（秒），與距離數據長度對應
        
    Note:
        - 時間數據來自 JSON 的 time_series.driver1.channels[param].time_seconds
        - 如果沒有時間數據，將禁用時間軸 Checkbox
    """
```

---

## ✅ 驗收標準

### 功能要求
- [ ] 所有標準模組支援時間/距離軸切換
- [ ] Checkbox 位置統一（控制面板右側）
- [ ] 預設為距離軸模式
- [ ] 切換時圖表立即更新
- [ ] 無需重新載入數據

### 性能要求
- [ ] 切換延遲 < 100ms
- [ ] 繪圖性能與原版相同
- [ ] 記憶體使用增加 < 5%

### 相容性要求
- [ ] 不破壞現有功能
- [ ] 連動功能正常
- [ ] 縮放和拖拉正常
- [ ] 固定線功能正常

### 代碼品質要求
- [ ] 遵循反幻覺編碼四原則
- [ ] 所有字串使用 `tr()` 國際化
- [ ] 禁止 emoji
- [ ] 完整的類型提示
- [ ] 充分的註釋

---

## 🚨 風險評估

### 高風險項目
1. **連動功能兼容性** (風險：🔴 高)
   - **問題**：時間軸模式下連動可能失效
   - **緩解**：優先測試連動功能

2. **數據同步問題** (風險：🟠 中)
   - **問題**：時間數據和距離數據長度可能不一致
   - **緩解**：在數據載入時驗證長度

### 中風險項目
1. **UI 佈局適應** (風險：🟡 中低)
   - **問題**：Checkbox 可能擠壓現有控件
   - **緩解**：使用彈性佈局

2. **特殊模組適配** (風險：🟡 中低)
   - **問題**：SpeedDiff/DistanceDiff 可能需要特殊處理
   - **緩解**：Phase 4 單獨評估

---

## 📦 交付物清單

### 代碼交付
- [ ] 6 個標準模組的修改版本
- [ ] 2 個特殊模組的修改版本（如適用）
- [ ] 基類的修改版本（如適用）
- [ ] 數據載入器的修改版本

### 文檔交付
- [ ] 任務執行報告
- [ ] 使用者操作指南
- [ ] 開發者 API 文檔
- [ ] 測試報告

### 測試交付
- [ ] 測試用例清單
- [ ] 測試數據檔案
- [ ] 螢幕截圖/錄影

---

## 🎬 下一步行動

準備好開始執行了嗎？我建議按照以下步驟進行：

### 立即行動（現在）
1. ✅ 創建任務追蹤檔案：`tasks/TIME_AXIS_TASK.md`
2. ✅ 檢查基類結構
3. ✅ 準備測試數據

### Phase 1 啟動（接下來）
1. 🚀 Task 1.1：檢查基類
2. 🚀 Task 1.2：設計接口
3. 🚀 Task 1.3：準備測試數據

### 請確認
- [ ] 任務清單是否清楚？
- [ ] 時間估算是否合理？
- [ ] 執行順序是否同意？
- [ ] 現在開始 Phase 1？

**我已經完全準備好！隨時可以開始編碼！** 🚀
