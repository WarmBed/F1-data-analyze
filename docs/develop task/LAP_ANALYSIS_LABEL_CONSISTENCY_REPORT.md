# Lap Analysis 模組 - 標籤顯示一致性與多國語言調查報告

**調查日期**: 2025-10-07  
**調查範圍**: `modules/gui/lap_analysis/` 所有子模組  
**調查目的**: 確認單車手不同圈數與雙車手模式的標籤顯示一致性及多國語言支援

---

## 📋 執行摘要

經過深度調查，發現 **8 個遙測分析子模組**在標籤顯示邏輯、多國語言支援、字體設置上存在**嚴重不一致**問題。只有 **Speed Analysis** 和 **Throttle Analysis** 完整實現了雙圈比較模式的標籤顯示。

### 🔴 主要問題
1. **6 個模組**使用舊的單車手判斷邏輯（局部變數 `is_single_driver`）
2. **7 個模組**缺少雙圈比較模式的標籤處理（"第X圈"標記）
3. **圖例標籤**硬編碼中文，缺乏國際化支援
4. **字體設置**不統一（雅黑 vs Arial）

---

## 📊 詳細調查結果

### 1️⃣ **Speed Analysis** (速度分析)
**檔案**: `modules/gui/lap_analysis/speed_analysis/speed_analysis_chart_widget.py`

| 項目 | 狀態 | 詳情 |
|------|------|------|
| **單車手判斷邏輯** | ✅ **正確** | 使用 `self.is_single_driver` 成員變數 |
| **雙圈比較模式** | ✅ **完整支援** | 自動檢測 `lap1 != lap2`，生成標籤 |
| **圖例標籤格式** | ✅ **正確** | 單車手不同圈數時顯示 "VER - 第1圈" vs "VER - 第2圈" |
| **多國語言支援** | ❌ **缺失** | "第X圈" 硬編碼中文，無 `tr()` 包裝 |
| **字體設置** | ✅ **中文友好** | `QFont("Microsoft YaHei", 9)` |

**程式碼片段**:
```python
# 雙圈比較模式判斷 (行 158-167)
if driver1_name == driver2_name and lap1 is not None and lap2 is not None and lap1 != lap2:
    is_dual_lap_mode = True
    self.driver1_name = f"{driver1_name} - 第{lap1}圈"  # ⚠️ 硬編碼中文
    self.driver2_name = f"{driver2_name} - 第{lap2}圈"  # ⚠️ 硬編碼中文

# 圖例繪製 (行 646)
if not self.is_single_driver and self.driver2_name != self.driver1_name:
    painter.drawText(..., self.driver2_name)  # ✅ 正確顯示第2圈標籤
```

---

### 2️⃣ **Throttle Analysis** (油門分析)
**檔案**: `modules/gui/lap_analysis/Throttle_analysis/throttle_analysis_chart_widget.py`

| 項目 | 狀態 | 詳情 |
|------|------|------|
| **單車手判斷邏輯** | ✅ **正確** | 使用 `self.is_single_driver` 成員變數 |
| **雙圈比較模式** | ❌ **缺失** | 未實現 `lap1 != lap2` 檢測邏輯 |
| **圖例標籤格式** | ⚠️ **部分正確** | 使用 `self.is_single_driver` 判斷，但缺少圈數標記 |
| **多國語言支援** | ❌ **缺失** | 無圈數標籤，無需 i18n（但應補齊功能） |
| **字體設置** | ✅ **中文友好** | `QFont("Microsoft YaHei", 9)` |

**程式碼片段**:
```python
# 圖例繪製 (行 610-615)
if not self.is_single_driver and self.driver2_name != self.driver1_name:
    painter.drawLine(legend_x, legend_y + 20, legend_x + 20, legend_y + 20)
    painter.drawText(..., self.driver2_name)  # ❌ 缺少圈數標記
```

**缺少的功能**:
```python
# ❌ 應該有但沒有的雙圈比較模式處理
if driver1_name == driver2_name and lap1 != lap2:
    self.driver1_name = f"{driver1_name} - 第{lap1}圈"
    self.driver2_name = f"{driver2_name} - 第{lap2}圈"
```

---

### 3️⃣ **Acceleration Analysis** (加速度分析)
**檔案**: `modules/gui/lap_analysis/acceleration_analysis/acceleration_analysis_chart_widget.py`

| 項目 | 狀態 | 詳情 |
|------|------|------|
| **單車手判斷邏輯** | ❌ **錯誤** | 使用局部變數 `is_single_driver`（非成員變數） |
| **雙圈比較模式** | ❌ **完全缺失** | 無任何圈數處理邏輯 |
| **圖例標籤格式** | ❌ **錯誤** | 直接顯示車手名稱，無圈數標記 |
| **多國語言支援** | ❌ **缺失** | N/A |
| **字體設置** | ✅ **中文友好** | `QFont("Microsoft YaHei", 9)` |

**錯誤程式碼**:
```python
# ❌ 錯誤：每次繪製時重新計算，而非使用成員變數 (行 588-590)
def _draw_legend(self, painter: QPainter):
    is_single_driver = (self.driver1_name == self.driver2_name or 
                       not self.driver2_name or 
                       not self.driver2_acceleration)  # 局部變數！
    
    if not is_single_driver and self.driver2_name != self.driver1_name:
        # 顯示車手2圖例
```

**應修正為**:
```python
# ✅ 正確：使用成員變數
if not self.is_single_driver and self.driver2_name != self.driver1_name:
    # 顯示車手2圖例
```

---

### 4️⃣ **Brake Analysis** (煞車分析)
**檔案**: `modules/gui/lap_analysis/brake_analysis/brake_analysis_chart_widget.py`

| 項目 | 狀態 | 詳情 |
|------|------|------|
| **單車手判斷邏輯** | ❌ **錯誤** | 使用局部變數 `is_single_driver` |
| **雙圈比較模式** | ❌ **完全缺失** | 無任何圈數處理邏輯 |
| **圖例標籤格式** | ❌ **錯誤** | 直接顯示車手名稱，無圈數標記 |
| **多國語言支援** | ❌ **缺失** | N/A |
| **字體設置** | ✅ **中文友好** | `QFont("Microsoft YaHei", 9)` |

**錯誤程式碼**:
```python
# ❌ 錯誤：局部變數判斷 (行 536-538)
def _draw_legend(self, painter: QPainter):
    is_single_driver = (self.driver1_name == self.driver2_name or 
                       not self.driver2_name or 
                       not self.driver2_brake)  # 局部變數！
```

---

### 5️⃣ **RPM Analysis** (轉速分析)
**檔案**: `modules/gui/lap_analysis/rpm_analysis/rpm_analysis_chart_widget.py`

| 項目 | 狀態 | 詳情 |
|------|------|------|
| **單車手判斷邏輯** | ❌ **錯誤** | 使用局部變數 `is_single_driver` |
| **雙圈比較模式** | ❌ **完全缺失** | 無任何圈數處理邏輯 |
| **圖例標籤格式** | ❌ **錯誤** | 直接顯示車手名稱，無圈數標記 |
| **多國語言支援** | ❌ **缺失** | N/A |
| **字體設置** | ⚠️ **僅英文** | `QFont("Arial", 9)` - 中文顯示可能異常 |

**問題**:
```python
# ❌ 錯誤：局部變數 + 英文字體 (行 531-533)
def _draw_legend(self, painter: QPainter):
    painter.setFont(QFont("Arial", 9))  # ⚠️ 不支援中文
    is_single_driver = (self.driver1_name == self.driver2_name or 
                       not self.driver2_name or 
                       not self.driver2_rpm)
```

---

### 6️⃣ **Gear Analysis** (檔位分析)
**檔案**: `modules/gui/lap_analysis/gear_analysis/gear_analysis_chart_widget.py`

| 項目 | 狀態 | 詳情 |
|------|------|------|
| **單車手判斷邏輯** | ❌ **錯誤** | 使用局部變數 `is_single_driver` |
| **雙圈比較模式** | ❌ **完全缺失** | 無任何圈數處理邏輯 |
| **圖例標籤格式** | ❌ **錯誤** | 直接顯示車手名稱，無圈數標記 |
| **多國語言支援** | ❌ **缺失** | N/A |
| **字體設置** | ⚠️ **僅英文** | `QFont("Arial", 9)` - 中文顯示可能異常 |

**問題**:
```python
# ❌ 錯誤：局部變數 + 英文字體 (行 534-536)
def _draw_legend(self, painter: QPainter):
    painter.setFont(QFont("Arial", 9))  # ⚠️ 不支援中文
    is_single_driver = (self.driver1_name == self.driver2_name or 
                       not self.driver2_name or 
                       not self.driver2_gear)
```

---

### 7️⃣ **SpeedDiff Analysis** (速度差分析)
**檔案**: `modules/gui/lap_analysis/speeddiff_analysis/speeddiff_analysis_chart_widget.py`

| 項目 | 狀態 | 詳情 |
|------|------|------|
| **單車手判斷邏輯** | ⚠️ **特殊** | 此模組設計為雙車手對比，不適用單車手模式 |
| **雙圈比較模式** | ❌ **缺失** | 未實現圈數標記 |
| **圖例標籤格式** | ✅ **特殊設計** | 顯示 "VER 領先" / "LEC 領先" / "零點線" |
| **多國語言支援** | ✅ **部分支援** | 使用 `tr('leading', '領先')` 和 `tr('zero_line', '零點線')` |
| **字體設置** | ⚠️ **僅英文** | `QFont("Arial", 9)` |

**程式碼片段**:
```python
# ✅ 正確：使用 tr() 多國語言 (行 652-666)
painter.drawText(..., f"{self.driver1_name} {tr('leading', '領先')}")
painter.drawText(..., f"{self.driver2_name} {tr('leading', '領先')}")
painter.drawText(..., tr('zero_line', '零點線'))
```

**問題**:
- 車手名稱仍然缺少圈數標記（例如 "VER - 第1圈 領先"）

---

### 8️⃣ **DistanceDiff Analysis** (距離差分析)
**檔案**: `modules/gui/lap_analysis/distancediff_analysis/distancediff_analysis_chart_widget.py`

| 項目 | 狀態 | 詳情 |
|------|------|------|
| **單車手判斷邏輯** | ⚠️ **特殊** | 此模組設計為雙車手對比，不適用單車手模式 |
| **雙圈比較模式** | ❌ **缺失** | 未實現圈數標記 |
| **圖例標籤格式** | ✅ **特殊設計** | 顯示 "VER 領先" / "LEC 領先" / "零點線" |
| **多國語言支援** | ✅ **部分支援** | 使用 `tr('leading', '領先')` 和 `tr('zero_line', '零點線')` |
| **字體設置** | ⚠️ **僅英文** | `QFont("Arial", 9)` |

**程式碼片段**:
```python
# ✅ 正確：使用 tr() 多國語言 (行 610-624)
painter.drawText(..., f"{self.driver1_name} {tr('leading', '領先')}")
painter.drawText(..., f"{self.driver2_name} {tr('leading', '領先')}")
painter.drawText(..., tr('zero_line', '零點線'))
```

---

## 🔍 對比總結表

| 模組 | 單車手判斷 | 雙圈比較 | 圖例標籤 | 多國語言 | 字體 |
|------|-----------|---------|---------|---------|------|
| **Speed** | ✅ `self.is_single_driver` | ✅ 完整支援 | ✅ "VER - 第1圈" | ❌ 硬編碼中文 | ✅ 雅黑 |
| **Throttle** | ✅ `self.is_single_driver` | ❌ 缺失 | ⚠️ 無圈數標記 | N/A | ✅ 雅黑 |
| **Acceleration** | ❌ 局部變數 | ❌ 缺失 | ❌ 無圈數標記 | N/A | ✅ 雅黑 |
| **Brake** | ❌ 局部變數 | ❌ 缺失 | ❌ 無圈數標記 | N/A | ✅ 雅黑 |
| **RPM** | ❌ 局部變數 | ❌ 缺失 | ❌ 無圈數標記 | N/A | ❌ Arial |
| **Gear** | ❌ 局部變數 | ❌ 缺失 | ❌ 無圈數標記 | N/A | ❌ Arial |
| **SpeedDiff** | ⚠️ 特殊設計 | ❌ 缺失 | ✅ "領先"標記 | ✅ 部分 tr() | ❌ Arial |
| **DistanceDiff** | ⚠️ 特殊設計 | ❌ 缺失 | ✅ "領先"標記 | ✅ 部分 tr() | ❌ Arial |

**符號說明**:
- ✅ = 正確/完整
- ⚠️ = 部分正確/特殊設計
- ❌ = 錯誤/缺失
- N/A = 不適用

---

## 🎯 統一標準建議

### **標準 1: 單車手判斷邏輯**
所有模組應使用**成員變數** `self.is_single_driver`，而非局部變數：

```python
# ✅ 正確做法
class XxxChartWidget(QWidget):
    def __init__(self):
        self.is_single_driver = False  # 成員變數
    
    def set_xxx_data(...):
        # 更新 is_single_driver
        if driver1_name == driver2_name and not (lap1 and lap2 and lap1 != lap2):
            self.is_single_driver = True
        else:
            self.is_single_driver = False
    
    def _draw_legend(self, painter):
        if not self.is_single_driver and self.driver2_name != self.driver1_name:
            # 顯示車手2圖例
```

### **標準 2: 雙圈比較模式**
所有模組應實現統一的圈數標記邏輯：

```python
# ✅ 標準實現
def set_xxx_data(self, ..., lap1=None, lap2=None):
    # 雙圈比較模式判斷
    if driver1_name == driver2_name and lap1 is not None and lap2 is not None and lap1 != lap2:
        self.driver1_name = f"{driver1_name} - {tr('lap_prefix', '第')}{lap1}{tr('lap_suffix', '圈')}"
        self.driver2_name = f"{driver2_name} - {tr('lap_prefix', '第')}{lap2}{tr('lap_suffix', '圈')}"
        self.is_single_driver = False  # 雙圈比較不是單車手模式
    else:
        self.driver1_name = driver1_name
        self.driver2_name = driver2_name
```

### **標準 3: 多國語言支援**
所有圈數標記應使用 i18n 字典：

```python
# ✅ 正確做法
LAP_LABEL_FORMATS = {
    'zh-TW': lambda name, lap: f"{name} - 第{lap}圈",
    'zh-CN': lambda name, lap: f"{name} - 第{lap}圈",
    'en': lambda name, lap: f"{name} - Lap {lap}",
    'ja': lambda name, lap: f"{name} - {lap}周目",
}

# 使用範例
from core.gui_i18n import get_current_locale
locale = get_current_locale()
self.driver1_name = LAP_LABEL_FORMATS[locale](driver1_name, lap1)
```

### **標準 4: 字體設置統一**
所有模組應使用**支援中文的字體**：

```python
# ✅ 正確做法
painter.setFont(QFont("Microsoft YaHei", 9))  # 或 "Microsoft JhengHei"

# ❌ 錯誤做法
painter.setFont(QFont("Arial", 9))  # 中文顯示異常
```

---

## 🛠️ 修正優先級

### **P0 - 緊急修正（功能缺陷）**
1. ✅ **Acceleration/Brake/RPM/Gear**: 修正單車手判斷邏輯（局部變數 → 成員變數）
2. ✅ **Throttle/Acceleration/Brake/RPM/Gear/SpeedDiff/DistanceDiff**: 實現雙圈比較模式標籤

### **P1 - 高優先級（用戶體驗）**
3. ✅ **RPM/Gear/SpeedDiff/DistanceDiff**: 修正字體設置（Arial → Microsoft YaHei）
4. ✅ **所有模組**: 實現多國語言圈數標記（i18n）

### **P2 - 一般優先級（代碼規範）**
5. ✅ 建立統一的 `LapLabelFormatter` 工具類
6. ✅ 更新所有模組的單元測試

---

## 📝 修正檢查清單

### **需修正的檔案**
- [ ] `acceleration_analysis/acceleration_analysis_chart_widget.py`
- [ ] `brake_analysis/brake_analysis_chart_widget.py`
- [ ] `rpm_analysis/rpm_analysis_chart_widget.py`
- [ ] `gear_analysis/gear_analysis_chart_widget.py`
- [ ] `Throttle_analysis/throttle_analysis_chart_widget.py`
- [ ] `speeddiff_analysis/speeddiff_analysis_chart_widget.py`
- [ ] `distancediff_analysis/distancediff_analysis_chart_widget.py`

### **需新增的工具**
- [ ] `core/lap_label_formatter.py` - 統一圈數標籤格式化工具
- [ ] `locales/lap_labels.json` - 圈數標籤多國語言字典

---

## 🔗 相關文件
- **主文檔**: `IMPLEMENTATION_COMPLETE_Dual_Lap_All_Modules.md`
- **快速參考**: `QUICKREF_Dual_Lap_All_Modules.md`
- **開發指南**: `.github/copilot-instructions.md` (第 4 節)

---

**報告生成**: 2025-10-07  
**調查人員**: GitHub Copilot AI Assistant  
**狀態**: 🔴 待修正
