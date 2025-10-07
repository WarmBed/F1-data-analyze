# Lap Analysis 模組 - 多國語言支援修正計畫

**調查日期**: 2025-10-07  
**狀態**: 🟡 功能正常，僅需 i18n 支援

---

## ✅ **實際情況確認（根據截圖驗證）**

### **所有模組功能正常運作**

根據實際截圖驗證，**8 個模組的圖例標籤顯示全部正確**：

| 模組 | 實際顯示 | 功能狀態 |
|------|---------|---------|
| **Speed Analysis** | "HAM - 第58圈" vs "HAM - 第59圈" | ✅ **正常** |
| **Brake Analysis** | "HAM - 第53圈" vs "HAM - 第59圈" | ✅ **正常** |
| **Throttle Analysis** | "HAM - 第58圈" vs "HAM - 第59圈" | ✅ **正常** |
| **Gear Analysis** | "HAM - 第58圈" vs "HAM - 第59圈" | ✅ **正常** |
| **RPM Analysis** | "HAM - 第58圈" vs "HAM - 第59圈" | ✅ **正常** |
| **Acceleration Analysis** | "HAM - 第58圈" vs "HAM - 第59圈" | ✅ **正常** |
| **Speed Diff Analysis** | "HAM 第58圈 vs 第59圈 Leading" | ✅ **正常** |
| **Distance Diff Analysis** | "HAM 第58圈 vs 第59圈 Leading" | ✅ **正常** |

**結論**: 
- ✅ 單車手不同圈數比較功能：**完整實現**
- ✅ 雙車手比較功能：**完整實現**
- ✅ 圖例標籤顯示邏輯：**完全正確**
- ❌ 多國語言支援：**缺失**（唯一問題）

---

## 🌍 **唯一問題：多國語言支援缺失**

### **當前問題**

所有模組的圈數標籤都**硬編碼中文**：

```python
# ❌ 當前實現（所有模組共通問題）
self.driver1_name = f"{driver1_name} - 第{lap1}圈"
self.driver2_name = f"{driver2_name} - 第{lap2}圈"
```

### **影響範圍**

| 語言環境 | 當前顯示 | 期望顯示 | 狀態 |
|---------|---------|---------|------|
| **中文 (zh-TW/zh-CN)** | "HAM - 第58圈" | "HAM - 第58圈" | ✅ **正確** |
| **英文 (en)** | "HAM - 第58圈" | "HAM - Lap 58" | ❌ **錯誤** |
| **日文 (ja)** | "HAM - 第58圈" | "HAM - 58周目" | ❌ **錯誤** |
| **西班牙文 (es)** | "HAM - 第58圈" | "HAM - Vuelta 58" | ❌ **錯誤** |
| **德文 (de)** | "HAM - 第58圈" | "HAM - Runde 58" | ❌ **錯誤** |

---

## 🛠️ **修正方案**

### **方案 1: 使用現有 i18n 系統** (建議)

利用現有的 `core/gui_i18n.py` 的 `tr()` 函數：

```python
# ✅ 修正實現
from core.gui_i18n import tr

# 在 set_xxx_data() 方法中
if driver1_name == driver2_name and lap1 is not None and lap2 is not None and lap1 != lap2:
    # 使用 tr() 函數進行國際化
    lap_format = tr('lap_number_format', '第{lap}圈')
    self.driver1_name = f"{driver1_name} - {lap_format.format(lap=lap1)}"
    self.driver2_name = f"{driver2_name} - {lap_format.format(lap=lap2)}"
```

**優點**:
- 利用現有系統，無需額外開發
- 與其他 GUI 元素的 i18n 保持一致
- 修改量小，風險低

**需要新增的翻譯鍵**:
```python
# 在 core/gui_i18n.py 中新增
'lap_number_format': {
    'zh-TW': '第{lap}圈',
    'zh-CN': '第{lap}圈',
    'en': 'Lap {lap}',
    'ja': '{lap}周目',
    'es': 'Vuelta {lap}',
    'de': 'Runde {lap}',
}
```

---

### **方案 2: 專用圈數標籤格式化工具** (進階)

建立專用的 `LapLabelFormatter` 類：

```python
# 新檔案: core/lap_label_formatter.py
from core.gui_i18n import get_current_locale

class LapLabelFormatter:
    """圈數標籤格式化工具"""
    
    FORMATS = {
        'zh-TW': lambda name, lap: f"{name} - 第{lap}圈",
        'zh-CN': lambda name, lap: f"{name} - 第{lap}圈",
        'en': lambda name, lap: f"{name} - Lap {lap}",
        'ja': lambda name, lap: f"{name} - {lap}周目",
        'es': lambda name, lap: f"{name} - Vuelta {lap}",
        'de': lambda name, lap: f"{name} - Runde {lap}",
    }
    
    @classmethod
    def format_lap_label(cls, driver_name: str, lap_number: int) -> str:
        """格式化圈數標籤"""
        locale = get_current_locale()
        formatter = cls.FORMATS.get(locale, cls.FORMATS['en'])
        return formatter(driver_name, lap_number)
    
    @classmethod
    def format_dual_lap_labels(cls, driver_name: str, lap1: int, lap2: int) -> tuple:
        """格式化雙圈比較標籤"""
        return (
            cls.format_lap_label(driver_name, lap1),
            cls.format_lap_label(driver_name, lap2)
        )

# 使用範例
from core.lap_label_formatter import LapLabelFormatter

if driver1_name == driver2_name and lap1 != lap2:
    self.driver1_name, self.driver2_name = LapLabelFormatter.format_dual_lap_labels(
        driver1_name, lap1, lap2
    )
```

**優點**:
- 集中管理圈數標籤邏輯
- 易於測試和維護
- 未來可擴展更多格式（如 "L58" 簡寫）

**缺點**:
- 需要新增檔案和類別
- 稍微增加代碼複雜度

---

## 📋 **修正任務清單**

### **階段 1: 選擇實現方案**
- [ ] 評估方案 1 vs 方案 2
- [ ] 確認現有 `core/gui_i18n.py` 的功能
- [ ] 決定採用的方案

### **階段 2: 實現 i18n 支援**（假設採用方案 1）

#### **2.1 更新 core/gui_i18n.py**
- [ ] 新增 `lap_number_format` 翻譯鍵
- [ ] 新增至少 3 種語言支援（中文、英文、日文）

#### **2.2 更新所有 Chart Widget 模組**
需修改的檔案（8 個）：
- [ ] `speed_analysis/speed_analysis_chart_widget.py`
- [ ] `throttle_analysis/throttle_analysis_chart_widget.py`
- [ ] `acceleration_analysis/acceleration_analysis_chart_widget.py`
- [ ] `brake_analysis/brake_analysis_chart_widget.py`
- [ ] `rpm_analysis/rpm_analysis_chart_widget.py`
- [ ] `gear_analysis/gear_analysis_chart_widget.py`
- [ ] `speeddiff_analysis/speeddiff_analysis_chart_widget.py`
- [ ] `distancediff_analysis/distancediff_analysis_chart_widget.py`

**修改位置**: 每個模組的 `set_xxx_data()` 方法中的圈數標籤生成邏輯

### **階段 3: 測試驗證**
- [ ] 中文環境測試：顯示 "HAM - 第58圈"
- [ ] 英文環境測試：顯示 "HAM - Lap 58"
- [ ] 日文環境測試：顯示 "HAM - 58周目"
- [ ] 語言切換測試：動態切換語言時圖例更新

---

## 🔍 **具體修改範例**

### **Speed Analysis 模組修改**

**檔案**: `modules/gui/lap_analysis/speed_analysis/speed_analysis_chart_widget.py`

**修改位置**: 行 158-167

#### **修改前**:
```python
# 🆕 雙圈比較模式：判斷是否為同車手不同圈數比較
is_dual_lap_mode = False
if driver1_name == driver2_name and lap1 is not None and lap2 is not None and lap1 != lap2:
    # 同車手不同圈數 → 雙圈比較模式
    is_dual_lap_mode = True
    self.driver1_name = f"{driver1_name} - 第{lap1}圈"  # ❌ 硬編碼中文
    self.driver2_name = f"{driver2_name} - 第{lap2}圈"  # ❌ 硬編碼中文
    print(f"[SPEED_CHART] 🔄 雙圈比較模式: {self.driver1_name} vs {self.driver2_name}")
else:
    # 正常模式：直接使用車手名稱
    self.driver1_name = driver1_name
    self.driver2_name = driver2_name
```

#### **修改後**（方案 1）:
```python
from core.gui_i18n import tr

# 🆕 雙圈比較模式：判斷是否為同車手不同圈數比較
is_dual_lap_mode = False
if driver1_name == driver2_name and lap1 is not None and lap2 is not None and lap1 != lap2:
    # 同車手不同圈數 → 雙圈比較模式
    is_dual_lap_mode = True
    # ✅ 使用 tr() 進行國際化
    lap_format = tr('lap_number_format', '第{lap}圈')
    self.driver1_name = f"{driver1_name} - {lap_format.format(lap=lap1)}"
    self.driver2_name = f"{driver2_name} - {lap_format.format(lap=lap2)}"
    print(f"[SPEED_CHART] 🔄 雙圈比較模式: {self.driver1_name} vs {self.driver2_name}")
else:
    # 正常模式：直接使用車手名稱
    self.driver1_name = driver1_name
    self.driver2_name = driver2_name
```

#### **修改後**（方案 2）:
```python
from core.lap_label_formatter import LapLabelFormatter

# 🆕 雙圈比較模式：判斷是否為同車手不同圈數比較
is_dual_lap_mode = False
if driver1_name == driver2_name and lap1 is not None and lap2 is not None and lap1 != lap2:
    # 同車手不同圈數 → 雙圈比較模式
    is_dual_lap_mode = True
    # ✅ 使用專用格式化工具
    self.driver1_name, self.driver2_name = LapLabelFormatter.format_dual_lap_labels(
        driver1_name, lap1, lap2
    )
    print(f"[SPEED_CHART] 🔄 雙圈比較模式: {self.driver1_name} vs {self.driver2_name}")
else:
    # 正常模式：直接使用車手名稱
    self.driver1_name = driver1_name
    self.driver2_name = driver2_name
```

---

### **其他模組修改位置**

| 模組 | 檔案 | 修改行數 (大約) | 修改位置 |
|------|------|----------------|---------|
| **Throttle** | `throttle_analysis_chart_widget.py` | ~160-170 | `set_throttle_data()` |
| **Acceleration** | `acceleration_analysis_chart_widget.py` | ~160-170 | `set_acceleration_data()` |
| **Brake** | `brake_analysis_chart_widget.py` | ~160-170 | `set_brake_data()` |
| **RPM** | `rpm_analysis_chart_widget.py` | ~160-170 | `set_rpm_data()` |
| **Gear** | `gear_analysis_chart_widget.py` | ~160-170 | `set_gear_data()` |
| **SpeedDiff** | `speeddiff_analysis_chart_widget.py` | ~160-170 | `set_speeddiff_data()` |
| **DistanceDiff** | `distancediff_analysis_chart_widget.py` | ~160-170 | `set_distancediff_data()` |

**每個模組的修改邏輯完全相同**，只需將硬編碼的 `f"{driver_name} - 第{lap}圈"` 替換為 i18n 版本。

---

## 📊 **工作量估算**

### **方案 1: 使用現有 tr() 系統**
| 任務 | 工作量 | 說明 |
|------|--------|------|
| 更新 `core/gui_i18n.py` | **15 分鐘** | 新增翻譯鍵 |
| 修改 8 個 Chart Widget | **40 分鐘** | 每個模組 5 分鐘 |
| 測試驗證 | **20 分鐘** | 3 種語言測試 |
| **總計** | **~75 分鐘** | 約 1.5 小時 |

### **方案 2: 建立專用工具類**
| 任務 | 工作量 | 說明 |
|------|--------|------|
| 建立 `lap_label_formatter.py` | **30 分鐘** | 新增工具類 |
| 修改 8 個 Chart Widget | **40 分鐘** | 每個模組 5 分鐘 |
| 單元測試 | **20 分鐘** | 工具類測試 |
| 整合測試 | **20 分鐘** | 3 種語言測試 |
| **總計** | **~110 分鐘** | 約 2 小時 |

**建議**: 採用**方案 1**（使用現有 tr() 系統），工作量更小且風險更低。

---

## 🎯 **預期修正效果**

### **中文環境 (zh-TW/zh-CN)**
```
修正前: HAM - 第58圈 vs HAM - 第59圈  ✅
修正後: HAM - 第58圈 vs HAM - 第59圈  ✅ (無變化)
```

### **英文環境 (en)**
```
修正前: HAM - 第58圈 vs HAM - 第59圈  ❌
修正後: HAM - Lap 58 vs HAM - Lap 59  ✅
```

### **日文環境 (ja)**
```
修正前: HAM - 第58圈 vs HAM - 第59圈  ❌
修正後: HAM - 58周目 vs HAM - 59周目  ✅
```

### **SpeedDiff/DistanceDiff 模組**
```
修正前: HAM 第58圈 vs 第59圈 Leading  ❌
修正後: HAM Lap 58 vs Lap 59 Leading  ✅ (英文環境)
```

---

## ✅ **驗收標準**

修正完成後，需確認以下測試通過：

1. **中文環境測試** ✅
   - 圖例顯示: "HAM - 第58圈" vs "HAM - 第59圈"
   - SpeedDiff 顯示: "HAM 第58圈 vs 第59圈 領先"

2. **英文環境測試** ✅
   - 圖例顯示: "HAM - Lap 58" vs "HAM - Lap 59"
   - SpeedDiff 顯示: "HAM Lap 58 vs Lap 59 Leading"

3. **日文環境測試** ✅
   - 圖例顯示: "HAM - 58周目" vs "HAM - 59周目"
   - SpeedDiff 顯示: "HAM 58周目 vs 59周目 リード"

4. **語言切換測試** ✅
   - 運行時切換語言，圖例即時更新（如果支援）

---

## 📝 **相關文件**

- **現有 i18n 系統**: `core/gui_i18n.py`
- **開發指南**: `.github/copilot-instructions.md` (第 7 節 - 國際化框架)
- **原始調查報告**: `LAP_ANALYSIS_LABEL_CONSISTENCY_REPORT.md` (已過時，待更新)

---

## 🚀 **下一步行動**

建議執行順序：

1. **確認 i18n 系統** (5 分鐘)
   - 檢查 `core/gui_i18n.py` 的 `tr()` 函數實現
   - 確認支援的語言列表

2. **實現修正** (方案 1，約 1 小時)
   - 更新 `core/gui_i18n.py` 新增翻譯鍵
   - 批次修改 8 個 Chart Widget 模組

3. **測試驗證** (20 分鐘)
   - 切換至英文環境測試
   - 切換至日文環境測試
   - 確認中文環境無破壞

4. **文檔更新** (10 分鐘)
   - 更新錯誤的調查報告
   - 記錄修正過程

---

**報告生成**: 2025-10-07  
**狀態**: 🟡 待修正（僅 i18n 問題）  
**優先級**: P1 (高優先級 - 用戶體驗改善)
