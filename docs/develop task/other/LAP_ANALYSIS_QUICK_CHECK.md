# Lap Analysis 標籤顯示快速檢查表

**調查日期**: 2025-10-07  
**完整報告**: `LAP_ANALYSIS_LABEL_CONSISTENCY_REPORT.md`

---

## 🚨 關鍵問題總覽

| 問題類型 | 受影響模組數 | 嚴重程度 |
|---------|------------|---------|
| **單車手判斷邏輯錯誤** | 4 個 (Acceleration, Brake, RPM, Gear) | 🔴 **高** |
| **缺少雙圈比較模式** | 7 個 (除 Speed 外全部) | 🔴 **高** |
| **多國語言支援缺失** | 8 個 (全部模組) | 🟡 **中** |
| **字體設置不統一** | 4 個 (RPM, Gear, SpeedDiff, DistanceDiff) | 🟡 **中** |

---

## 📊 模組狀態矩陣

| # | 模組名稱 | 單車手邏輯 | 雙圈標籤 | 多國語言 | 字體 | 總評 |
|---|---------|-----------|---------|---------|------|------|
| 1 | **Speed** | ✅ 正確 | ✅ 完整 | ❌ 缺失 | ✅ 雅黑 | **⭐ 85%** |
| 2 | **Throttle** | ✅ 正確 | ❌ 缺失 | ❌ 缺失 | ✅ 雅黑 | **⚠️ 50%** |
| 3 | **Acceleration** | ❌ 錯誤 | ❌ 缺失 | ❌ 缺失 | ✅ 雅黑 | **🔴 25%** |
| 4 | **Brake** | ❌ 錯誤 | ❌ 缺失 | ❌ 缺失 | ✅ 雅黑 | **🔴 25%** |
| 5 | **RPM** | ❌ 錯誤 | ❌ 缺失 | ❌ 缺失 | ❌ Arial | **🔴 0%** |
| 6 | **Gear** | ❌ 錯誤 | ❌ 缺失 | ❌ 缺失 | ❌ Arial | **🔴 0%** |
| 7 | **SpeedDiff** | ⚠️ 特殊 | ❌ 缺失 | ✅ 部分 | ❌ Arial | **⚠️ 40%** |
| 8 | **DistanceDiff** | ⚠️ 特殊 | ❌ 缺失 | ✅ 部分 | ❌ Arial | **⚠️ 40%** |

**平均完成度**: 33% 🔴

---

## 🎯 具體範例對比

### **情境**: 單車手 VER 比較第 1 圈 vs 第 5 圈

| 模組 | 實際顯示 | 期望顯示 | 狀態 |
|------|---------|---------|------|
| **Speed** | "VER - 第1圈" vs "VER - 第5圈" | "VER - 第1圈" vs "VER - 第5圈" | ✅ |
| **Throttle** | "VER" (只顯示1條線) | "VER - 第1圈" vs "VER - 第5圈" | ❌ |
| **Acceleration** | "VER" (只顯示1條線) | "VER - 第1圈" vs "VER - 第5圈" | ❌ |
| **Brake** | "VER" (只顯示1條線) | "VER - 第1圈" vs "VER - 第5圈" | ❌ |
| **RPM** | "VER" (只顯示1條線) | "VER - 第1圈" vs "VER - 第5圈" | ❌ |
| **Gear** | "VER" (只顯示1條線) | "VER - 第1圈" vs "VER - 第5圈" | ❌ |
| **SpeedDiff** | "VER 領先" vs "VER 領先" | "VER - 第1圈 領先" vs "VER - 第5圈 領先" | ❌ |
| **DistanceDiff** | "VER 領先" vs "VER 領先" | "VER - 第1圈 領先" vs "VER - 第5圈 領先" | ❌ |

---

## 🐛 典型錯誤程式碼

### **錯誤 1: 使用局部變數判斷單車手模式**
```python
# ❌ 錯誤做法 (Acceleration/Brake/RPM/Gear 模組)
def _draw_legend(self, painter):
    is_single_driver = (self.driver1_name == self.driver2_name or 
                       not self.driver2_name or 
                       not self.driver2_xxx)  # 每次重新計算！
    
    if not is_single_driver:  # ⚠️ 會誤判單車手不同圈數為雙車手
        # 顯示第二條圖例線...
```

**問題**: 
- 當 VER 第1圈 vs VER 第5圈時，`driver1_name == driver2_name` 為 `False`（因為已附加 "- 第X圈"）
- 但局部變數重新用原始名稱判斷，導致錯誤隱藏第二條線

### **錯誤 2: 缺少圈數標記**
```python
# ❌ 錯誤做法 (Throttle/Acceleration/Brake/RPM/Gear 模組)
def set_xxx_data(self, ..., driver1_name, driver2_name):
    self.driver1_name = driver1_name  # 直接使用，無圈數標記
    self.driver2_name = driver2_name
```

**問題**:
- 圖例只顯示 "VER" vs "VER"，用戶無法區分是哪一圈

### **錯誤 3: 硬編碼中文文字**
```python
# ❌ 錯誤做法 (Speed 模組)
self.driver1_name = f"{driver1_name} - 第{lap1}圈"  # 中文硬編碼
```

**問題**:
- 英文環境下顯示 "VER - 第1圈"（應該是 "VER - Lap 1"）
- 日文環境下無法顯示 "1周目"

---

## ✅ 正確實現範例

### **標準實現 (參考 Speed Analysis)**

```python
class XxxChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.is_single_driver = False  # ✅ 成員變數
    
    def set_xxx_data(self, ..., driver1_name, driver2_name, lap1=None, lap2=None):
        # ✅ 雙圈比較模式判斷
        if driver1_name == driver2_name and lap1 is not None and lap2 is not None and lap1 != lap2:
            # ✅ 多國語言支援
            self.driver1_name = f"{driver1_name} - {tr('lap_prefix', '第')}{lap1}{tr('lap_suffix', '圈')}"
            self.driver2_name = f"{driver2_name} - {tr('lap_prefix', '第')}{lap2}{tr('lap_suffix', '圈')}"
            self.is_single_driver = False  # 雙圈比較模式
        else:
            self.driver1_name = driver1_name
            self.driver2_name = driver2_name
            # 判斷單車手模式
            if not driver2_name or driver2_name == "" or not driver2_speed:
                self.is_single_driver = True
    
    def _draw_legend(self, painter):
        painter.setFont(QFont("Microsoft YaHei", 9))  # ✅ 中文字體
        
        # ✅ 使用成員變數判斷
        if not self.is_single_driver and self.driver2_name != self.driver1_name:
            # 顯示車手2圖例（包含圈數標記）
            painter.drawText(..., self.driver2_name)
```

---

## 🛠️ 修正任務清單

### **階段 1: 修正單車手判斷邏輯** (P0 緊急)
- [ ] `acceleration_analysis_chart_widget.py` - 行 588-590
- [ ] `brake_analysis_chart_widget.py` - 行 536-538
- [ ] `rpm_analysis_chart_widget.py` - 行 531-533
- [ ] `gear_analysis_chart_widget.py` - 行 534-536

**修正方式**: 將 `is_single_driver` 局部變數改為使用 `self.is_single_driver`

### **階段 2: 實現雙圈比較模式** (P0 緊急)
- [ ] `throttle_analysis_chart_widget.py`
- [ ] `acceleration_analysis_chart_widget.py`
- [ ] `brake_analysis_chart_widget.py`
- [ ] `rpm_analysis_chart_widget.py`
- [ ] `gear_analysis_chart_widget.py`
- [ ] `speeddiff_analysis_chart_widget.py`
- [ ] `distancediff_analysis_chart_widget.py`

**修正方式**: 在 `set_xxx_data()` 方法中加入圈數判斷邏輯（參考 Speed Analysis）

### **階段 3: 修正字體設置** (P1 高優先級)
- [ ] `rpm_analysis_chart_widget.py` - 行 528
- [ ] `gear_analysis_chart_widget.py` - 行 531
- [ ] `speeddiff_analysis_chart_widget.py` - 行 646
- [ ] `distancediff_analysis_chart_widget.py` - 行 605

**修正方式**: `QFont("Arial", 9)` → `QFont("Microsoft YaHei", 9)`

### **階段 4: 多國語言支援** (P1 高優先級)
- [ ] 建立 `core/lap_label_formatter.py` 工具類
- [ ] 建立 `locales/lap_labels_*.json` 多國語言檔案
- [ ] 更新所有模組使用 `tr()` 函數

---

## 📈 修正後預期效果

### **單車手不同圈數比較 (VER 第1圈 vs 第5圈)**
| 模組 | 修正前 | 修正後 |
|------|--------|--------|
| 圖例標籤 | "VER" (只顯示1條) | "VER - 第1圈" vs "VER - 第5圈" |
| 英文環境 | "VER - 第1圈" | "VER - Lap 1" vs "VER - Lap 5" |
| 日文環境 | "VER - 第1圈" | "VER - 1周目" vs "VER - 5周目" |

### **雙車手比較 (VER vs LEC)**
| 模組 | 修正前 | 修正後 |
|------|--------|--------|
| 圖例標籤 | "VER" vs "LEC" | "VER" vs "LEC" (不變) |
| 單車手判斷 | 可能錯誤 | 正確識別為雙車手模式 |

---

## 🔗 相關文件
- **完整報告**: `LAP_ANALYSIS_LABEL_CONSISTENCY_REPORT.md`
- **實現指南**: `IMPLEMENTATION_COMPLETE_Dual_Lap_All_Modules.md`
- **快速參考**: `QUICKREF_Dual_Lap_All_Modules.md`

---

**最後更新**: 2025-10-07  
**狀態**: 🔴 待修正 (平均完成度 33%)
