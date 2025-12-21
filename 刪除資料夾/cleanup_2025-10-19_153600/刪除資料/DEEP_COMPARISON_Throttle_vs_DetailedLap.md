# 🔍 深度對比檢查：Throttle Line Chart vs Detailed Lap Analysis

**日期**: 2025-10-08  
**目的**: 逐項對比每一個 UI 細節，確保完全一致

---

## 1️⃣ **車手選擇器 (DriverSelectionWidget)**

### ✅ 已對齊項目

| 項目 | Detailed Lap Analysis | Throttle Line Chart | 狀態 |
|------|----------------------|---------------------|------|
| **下拉選單數量** | 5 個 | 5 個 | ✅ 一致 |
| **最小寬度** | `setMinimumWidth(50)` | `setMinimumWidth(50)` | ✅ 已修正 |
| **最大寬度** | `setMaximumWidth(120)` | `setMaximumWidth(120)` | ✅ 已修正 |
| **間距** | `driver_layout.setSpacing(10)` | `driver_layout.setSpacing(10)` | ✅ 已修正 |
| **Clear 按鈕寬度** | `setMaximumWidth(60)` | `setMaximumWidth(60)` | ✅ 已修正 |
| **自動選擇** | 前 3 位車手 | 前 3 位車手 | ✅ 已修正 |
| **信號名稱** | `drivers_selected = pyqtSignal(list)` | `drivers_selected = pyqtSignal(list)` | ✅ 已修正 |
| **佔位符文字** | `f"-- {tr('please_select', '請選擇')} --"` | `f"-- {tr('please_select', '請選擇')} --"` | ✅ 一致 |
| **重複選擇過濾** | `if driver not in selected` | `if driver not in selected` | ✅ 一致 |
| **blockSignals** | 更新時暫停信號 | 更新時暫停信號 | ✅ 已修正 |

### ❌ 差異項目

| 項目 | Detailed Lap Analysis | Throttle Line Chart | 狀態 |
|------|----------------------|---------------------|------|
| **時間差標籤** | ✅ 有 `time_diff_label` | ❌ 無 | ⚠️ **需要添加**（可選功能） |

---

## 2️⃣ **圖表主題 (ChartTheme / ThrottleChartTheme)**

### ✅ 已對齊項目

| 項目 | Detailed Lap Analysis | Throttle Line Chart | 狀態 |
|------|----------------------|---------------------|------|
| **DRIVER1_COLOR** | `QColor(220, 53, 69)` 紅色 | `QColor(220, 53, 69)` | ✅ 一致 |
| **DRIVER2_COLOR** | `QColor(0, 123, 255)` 藍色 | `QColor(0, 123, 255)` | ✅ 一致 |
| **DRIVER3_COLOR** | `QColor(40, 167, 69)` 綠色 | `QColor(40, 167, 69)` | ✅ 一致 |
| **DRIVER4_COLOR** | `QColor(255, 193, 7)` 黃色 | `QColor(255, 193, 7)` | ✅ 一致 |
| **DRIVER5_COLOR** | `QColor(108, 117, 125)` 灰色 | `QColor(108, 117, 125)` | ✅ 一致 |
| **BACKGROUND** | `QColor(255, 255, 255)` 白色 | `QColor(255, 255, 255)` | ✅ 一致 |
| **GRID_COLOR** | `QColor(200, 200, 200)` | `QColor(200, 200, 200)` | ✅ 一致 |
| **TEXT_COLOR** | `QColor(0, 0, 0)` 黑色 | `QColor(0, 0, 0)` | ✅ 一致 |

---

## 3️⃣ **圖表組件 (LaptimeChartWidget / ThrottleChartWidget)**

### 字體設定

| 用途 | Detailed Lap Analysis | Throttle Line Chart | 狀態 |
|------|----------------------|---------------------|------|
| **無數據提示字體** | `font.setPointSize(8)` | ❓ 需要檢查 | ⚠️ **需確認** |
| **Y 軸標籤字體** | `font.setPointSize(8)` | ❓ 需要檢查 | ⚠️ **需確認** |
| **X 軸標籤字體** | `font.setPointSize(8)` | ❓ 需要檢查 | ⚠️ **需確認** |
| **圖例標題字體** | `title_font.setPointSize(9)`, `title_font.setBold(True)` | ❓ 需要檢查 | ⚠️ **需確認** |
| **圖例內容字體** | `content_font.setPointSize(8)` | ❓ 需要檢查 | ⚠️ **需確認** |
| **Tooltip 字體** | `font.setPointSize(8)` | ❓ 需要檢查 | ⚠️ **需確認** |

### 邊距設定

| 項目 | Detailed Lap Analysis | Throttle Line Chart | 狀態 |
|------|----------------------|---------------------|------|
| **動態邊距計算** | `base_margin = min(width, height) * 0.08` | ❓ 需要檢查 | ⚠️ **需確認** |
| **最小/最大邊距** | `max(20, min(60, int(base_margin)))` | ❓ 需要檢查 | ⚠️ **需確認** |
| **左側邊距** | `max(95, int(width * 0.12))` | ❓ 需要檢查 | ⚠️ **需確認** |

### 最小尺寸

| 項目 | Detailed Lap Analysis | Throttle Line Chart | 狀態 |
|------|----------------------|---------------------|------|
| **setMinimumSize** | `(200, 100)` | ❓ 需要檢查 | ⚠️ **需確認** |

### 邊框樣式

| 項目 | Detailed Lap Analysis | Throttle Line Chart | 狀態 |
|------|----------------------|---------------------|------|
| **setStyleSheet** | `"border: 1px solid #ccc;"` | ❓ 需要檢查 | ⚠️ **需確認** |

### 折線繪製

| 項目 | Detailed Lap Analysis | Throttle Line Chart | 狀態 |
|------|----------------------|---------------------|------|
| **折線寬度** | `line_width=2` | ❓ 需要檢查 | ⚠️ **需確認** |
| **數據點大小** | 無顯示數據點 | ❓ 需要檢查 | ⚠️ **需確認** |
| **抗鋸齒** | `painter.setRenderHint(QPainter.Antialiasing)` | ❓ 需要檢查 | ⚠️ **需確認** |

### 網格線

| 項目 | Detailed Lap Analysis | Throttle Line Chart | 狀態 |
|------|----------------------|---------------------|------|
| **主網格線間距** | 每 5 圈 | ❓ 需要檢查 | ⚠️ **需確認** |
| **次網格線間距** | 每 1 圈 | ❓ 需要檢查 | ⚠️ **需確認** |
| **主網格線寬度** | 1px | ❓ 需要檢查 | ⚠️ **需確認** |
| **次網格線寬度** | 0.5px | ❓ 需要檢查 | ⚠️ **需確認** |

### 圖例

| 項目 | Detailed Lap Analysis | Throttle Line Chart | 狀態 |
|------|----------------------|---------------------|------|
| **可拖移** | ✅ 支援 | ❓ 需要檢查 | ⚠️ **需確認** |
| **顏色方塊大小** | 12x12 | ❓ 需要檢查 | ⚠️ **需確認** |
| **文字間距** | 5px | ❓ 需要檢查 | ⚠️ **需確認** |
| **背景色** | 半透明白色 | ❓ 需要檢查 | ⚠️ **需確認** |
| **邊框** | `QPen(QColor(0, 0, 0), 1)` | ❓ 需要檢查 | ⚠️ **需確認** |

### Tooltip

| 項目 | Detailed Lap Analysis | Throttle Line Chart | 狀態 |
|------|----------------------|---------------------|------|
| **Hover 顯示** | ✅ 支援 | ❓ 需要檢查 | ⚠️ **需確認** |
| **固定點數量** | 最多 2 個 | ❓ 需要檢查 | ⚠️ **需確認** |
| **左鍵固定** | ✅ 支援 | ❓ 需要檢查 | ⚠️ **需確認** |
| **右鍵清除** | ✅ 支援 | ❓ 需要檢查 | ⚠️ **需確認** |
| **時間差計算** | ✅ 支援 | ❌ 不適用（油門秒數） | ✅ 正確 |

### 縮放功能

| 項目 | Detailed Lap Analysis | Throttle Line Chart | 狀態 |
|------|----------------------|---------------------|------|
| **滾輪縮放** | ✅ 支援 | ❓ 需要檢查 | ⚠️ **需確認** |
| **縮放軸** | Y 軸 | ❓ 需要檢查 | ⚠️ **需確認** |

---

## 4️⃣ **主組件 (driverLapAnalysisChartWidget / ThrottleMultiDriverChartWidget)**

### 布局結構

| 項目 | Detailed Lap Analysis | Throttle Line Chart | 狀態 |
|------|----------------------|---------------------|------|
| **主布局** | `QVBoxLayout` | ❓ 需要檢查 | ⚠️ **需確認** |
| **車手選擇 stretch** | 0 | ❓ 需要檢查 | ⚠️ **需確認** |
| **圖表 stretch** | 1 | ❓ 需要檢查 | ⚠️ **需確認** |

### 信號定義

| 項目 | Detailed Lap Analysis | Throttle Line Chart | 狀態 |
|------|----------------------|---------------------|------|
| **driver_selected** | `pyqtSignal(str)` | ❓ 需要檢查 | ⚠️ **需確認** |
| **lap_selected** | `pyqtSignal(int, str, dict)` | ❌ 不適用（油門分析） | ✅ 正確 |

---

## 5️⃣ **數據結構**

### Detailed Lap Analysis

```python
class ChartDataPoint:
    def __init__(self, x, y, metadata=None):
        self.x = x  # 圈數
        self.y = y  # 圈速 (秒)
        self.metadata = metadata or {}

class ChartSeries:
    def __init__(self, name, data, color, line_width=2, style='line'):
        self.name = name  # 車手代碼
        self.data = data  # List[ChartDataPoint]
        self.color = color
        self.line_width = line_width
        self.style = style
```

### Throttle Line Chart

| 項目 | 狀態 |
|------|------|
| **ThrottleDataPoint** | ⚠️ **需確認結構** |
| **ThrottleDataSeries** | ⚠️ **需確認結構** |
| **數據格式** | `x=圈數, y=油門秒數` | ✅ 正確 |

---

## 6️⃣ **交互功能**

### 滑鼠事件

| 事件 | Detailed Lap Analysis | Throttle Line Chart | 狀態 |
|------|----------------------|---------------------|------|
| **mouseMoveEvent** | ✅ Hover + 圖例拖移 | ❓ 需要檢查 | ⚠️ **需確認** |
| **mousePressEvent** | ✅ 固定點 + 圖例拖移 | ❓ 需要檢查 | ⚠️ **需確認** |
| **mouseReleaseEvent** | ✅ 結束拖移 | ❓ 需要檢查 | ⚠️ **需確認** |
| **wheelEvent** | ✅ 縮放 | ❓ 需要檢查 | ⚠️ **需確認** |

---

## 📋 **待檢查清單（優先級排序）**

### 🔴 高優先級（影響 UI 顯示）

1. **字體大小統一**：
   - [ ] 檢查所有文字是否使用 `font.setPointSize(8)`
   - [ ] 檢查圖例標題是否使用 `setPointSize(9) + setBold(True)`

2. **邊距計算**：
   - [ ] 實現動態邊距：`base_margin = min(width, height) * 0.08`
   - [ ] 左側邊距：`max(95, int(width * 0.12))`

3. **最小尺寸**：
   - [ ] 設定 `setMinimumSize(200, 100)`

4. **邊框樣式**：
   - [ ] 設定 `setStyleSheet("border: 1px solid #ccc;")`

### 🟡 中優先級（影響功能）

5. **折線繪製**：
   - [ ] 確認折線寬度為 2px
   - [ ] 啟用抗鋸齒：`painter.setRenderHint(QPainter.Antialiasing)`

6. **網格線**：
   - [ ] 主網格線：每 5 圈，寬度 1px
   - [ ] 次網格線：每 1 圈，寬度 0.5px

7. **圖例**：
   - [ ] 顏色方塊：12x12
   - [ ] 文字間距：5px
   - [ ] 背景：半透明白色
   - [ ] 邊框：黑色 1px

### 🟢 低優先級（細節優化）

8. **Tooltip**：
   - [ ] Hover 提示實現
   - [ ] 固定點功能（最多 2 個）
   - [ ] 右鍵清除

9. **縮放功能**：
   - [ ] 滾輪縮放 Y 軸

10. **時間差標籤**（可選）：
    - [ ] 添加 `time_diff_label`（如需要）

---

## 🎯 **下一步行動**

1. **立即檢查**: 讀取 `throttle_multi_driver_chart_widget.py` 的圖表繪製部分
2. **逐項對比**: 對照上述清單修正每一項
3. **測試驗證**: 重啟 GUI，視覺對比兩個模組

---

**狀態**: ⏳ 深度對比進行中  
**目標**: 100% UI 和邏輯一致性  
**負責人**: AI Assistant
