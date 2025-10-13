# 📊 Speed Analysis 時間軸切換功能 - 可行性調查報告

## 🎯 調查目標
在 `lap_analysis` 模組（speed, throttle, RPM, gear, brake, acceleration）中添加**時間序列 X 軸切換**功能。

---

## ✅ 調查結論：**完全可行！**

### 1. **現有架構分析**

#### 📂 模組結構
```
modules/gui/lap_analysis/
├── speed_analysis/
│   ├── speed_analysis_mdi.py          # MDI 視窗管理器
│   ├── speed_analysis_chart_widget.py  # 圖表組件（包含控制面板）
│   └── speed_analysis_data_loader.py   # 數據載入器
├── throttle_analysis/
├── rpm_analysis/
├── gear_analysis/
├── brake_analysis/
└── acceleration_analysis/
```

#### 🎨 控制面板位置
**發現地點**：`SpeedAnalysisChartWidget` 類（speed_analysis_chart_widget.py:909）

**現有控制項**：
- ✅ 圈數顯示：`lap1_display`, `lap2_display`（只讀 QLabel）
- ✅ 統計面板切換按鈕：`toggle_button`
- ✅ 狀態信息欄：顯示圈時間、輪胎配方等

**控制面板位置**：在 `_create_status_info_widget()` 方法中創建（第 1066 行）

---

### 2. **數據來源分析**

#### 📊 當前數據流
```
CLI (f13) → JSON 檔案 → DataLoader → ChartWidget → 繪圖
                ↓
        comparison_telemetry_*.json
```

#### 🔍 JSON 數據結構（已確認包含時間序列）
```json
{
  "time_series": {
    "driver1": {
      "channels": {
        "Speed": {
          "distance_meters": [0, 10, 20, ...],  // ✅ 距離數據
          "time_seconds": [0, 0.5, 1.0, ...],   // ✅ 時間數據（新增！）
          "values": [100, 120, 140, ...]
        }
      }
    }
  }
}
```

**✅ 時間序列數據已完整實現！** （剛才在 CLI 中添加）

---

### 3. **圖表繪製分析**

#### 🎨 當前繪圖方式
**類別**：`SpeedChartWidget` (speed_analysis_chart_widget.py:39)

**X 軸數據**：
```python
self.distance_data = []  # 當前使用距離作為 X 軸
```

**繪圖方法**：
- `set_speed_data()` - 接收距離和速度數據
- `paintEvent()` - 使用 QPainter 繪製圖表
- 座標轉換：將距離映射到螢幕像素

---

### 4. **實現方案設計**

#### 🎯 目標功能
1. 添加 **Checkbox** 切換「距離」/「時間」X 軸
2. 動態切換時**無需重新載入數據**（使用緩存的 time_series）
3. 保持現有功能不變（連動、縮放、固定線等）

#### 📋 具體實現步驟

##### **步驟 1：修改控制面板**（✅ 可行）
**檔案**：`speed_analysis_chart_widget.py`
**位置**：`_create_status_info_widget()` 方法

```python
# 在 tyre_life_container 之後添加
time_axis_container = QWidget()
time_axis_layout = QHBoxLayout(time_axis_container)

# Checkbox
self.time_axis_checkbox = QCheckBox(tr("use_time_axis", "使用時間軸"))
self.time_axis_checkbox.setStyleSheet("font-size: 11px;")
self.time_axis_checkbox.stateChanged.connect(self._on_time_axis_toggled)
time_axis_layout.addWidget(self.time_axis_checkbox)

layout.addWidget(time_axis_container)
```

##### **步驟 2：擴展數據儲存**（✅ 可行）
**檔案**：`speed_analysis_chart_widget.py`
**類別**：`SpeedChartWidget`

```python
# 添加時間序列數據儲存
self.time_data = []          # 新增：時間數據
self.use_time_axis = False   # 新增：是否使用時間軸

def set_speed_data(self, distance, driver1_speed, driver2_speed, 
                  time_data=None, ...):  # 添加 time_data 參數
    self.distance_data = distance
    self.time_data = time_data if time_data else []
    # ...
```

##### **步驟 3：修改繪圖邏輯**（✅ 可行）
**檔案**：`speed_analysis_chart_widget.py`
**方法**：`paintEvent()`

```python
def paintEvent(self, event):
    # 選擇 X 軸數據源
    if self.use_time_axis and self.time_data:
        x_data = self.time_data
        x_label = tr("time_seconds", "時間 (秒)")
    else:
        x_data = self.distance_data
        x_label = tr("distance_meters", "距離 (公尺)")
    
    # 現有的繪圖邏輯保持不變，只是 x_data 來源改變
    # ...
```

##### **步驟 4：擴展數據載入器**（✅ 可行）
**檔案**：`speed_analysis_data_loader.py`
**目標**：從 JSON 提取時間序列數據

```python
def _transform_data_for_display(self, raw_data: dict) -> dict:
    # 現有的轉換邏輯
    transformed = super()._transform_data_for_display(raw_data)
    
    # 添加時間序列提取
    if 'time_series' in raw_data:
        time_series = raw_data['time_series']
        driver1_ch = time_series['driver1']['channels'].get('Speed', {})
        
        transformed['time_data'] = driver1_ch.get('time_seconds', [])
    
    return transformed
```

---

### 5. **技術風險評估**

#### ✅ 低風險項目
1. **控制面板擴展** - 已有類似實現（圈數顯示）
2. **數據儲存** - 只需添加一個變數
3. **JSON 數據** - 已完整實現時間序列
4. **繪圖切換** - 只需改變 X 軸數據源

#### ⚠️ 需要注意的點
1. **其他模組同步**：Throttle, RPM, Gear, Brake, Acceleration 也需要相同修改
2. **連動功能**：確保時間軸模式下連動仍然正常工作
3. **座標轉換**：時間軸和距離軸的範圍可能不同
4. **UI 一致性**：所有遙測模組的 Checkbox 位置應統一

---

### 6. **擴展性分析**

#### 🔄 統一基類方案（推薦）
**檔案**：`modules/gui/base/universal_chart_widget_base.py`
**類別**：`TelemetryChartWidgetBase`

**優點**：
- 一次修改，所有遙測模組受益
- 保持架構一致性
- 減少代碼重複

**實現**：
```python
class TelemetryChartWidgetBase(QWidget):
    def __init__(self):
        # 統一的時間軸切換邏輯
        self.time_axis_enabled = False
        self.x_data = []  # 統一的 X 軸數據
        
    def toggle_time_axis(self, enabled: bool):
        # 所有子類繼承此方法
        pass
```

---

## 🎯 實施建議

### Phase 1：單一模組驗證（1-2天）
1. ✅ 在 `speed_analysis` 中實現完整功能
2. ✅ 測試距離/時間切換
3. ✅ 驗證連動功能

### Phase 2：擴展到其他模組（2-3天）
1. ✅ Throttle Analysis
2. ✅ RPM Analysis
3. ✅ Gear Analysis
4. ✅ Brake Analysis
5. ✅ Acceleration Analysis

### Phase 3：統一基類重構（1-2天）
1. ✅ 提取共用邏輯到 `TelemetryChartWidgetBase`
2. ✅ 所有模組繼承統一實現
3. ✅ 測試全面

---

## 🚀 總結

### ✅ **完全可行！**

**關鍵優勢**：
1. 時間序列數據已在 CLI 中完整實現
2. 控制面板有明確的擴展點
3. 圖表繪製邏輯簡單直接
4. 數據載入器容易擴展

**預估工作量**：
- **單一模組**：4-6 小時
- **所有模組**：2-3 天
- **測試和優化**：1-2 天

**建議開始點**：從 `speed_analysis` 開始，作為範本！

---

## 📝 下一步

準備好開始實現了嗎？我可以：
1. 🚀 立即開始修改 `speed_analysis`
2. 📋 先創建詳細的任務清單
3. 🔍 繼續深入調查其他細節

**你的選擇？**
