# 日文環境視窗標題問題修復報告

## 📊 執行時間
**2025-10-19 02:05**

---

## 🚨 問題發現

### 用戶報告
> "日語下有視窗開啟問題"

### 問題分析

從用戶截圖中發現：
- 視窗標題顯示為：`All Drivers Straight Line Speed_2025_Singapore_R`
- 應該顯示為：`全ドライバー速度と加速_2025_Singapore_R`（日文）

**根本原因：** 視窗標題的 `get_window_title()` 方法只處理了中文（zh），沒有處理日文（ja）和其他語言。

---

## 🔍 代碼分析

### **問題代碼（修復前）**

#### All Drivers Straight Line Speed
**檔案：** `all_drivers_straight_line_speed_mdi.py` 第 403-410 行

```python
# ❌ 錯誤：只處理中文，其他語言使用硬編碼英文
def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
    from core.gui_i18n import tr, get_gui_language
    language = get_gui_language()
    
    if language == 'zh':
        return f"{tr('all_drivers_straight_line_speed', '全車手直線速度')}_{year}_{race}_{session}"
    else:
        return f"All Drivers Straight Line Speed_{year}_{race}_{session}"  # ❌ 硬編碼英文
```

**問題：**
- 只有中文（zh）使用 `tr()` 函數
- 英文和日文都使用硬編碼的 "All Drivers Straight Line Speed"
- 導致日文環境下視窗標題無法多國語言化

#### All Drivers Brake Performance
**檔案：** `all_drivers_brake_performance_mdi.py` 第 303-310 行

```python
# ❌ 錯誤：只處理中文，其他語言使用硬編碼英文
def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
    from core.gui_i18n import tr, get_gui_language
    language = get_gui_language()
    
    if language == 'zh':
        return f"{tr('all_drivers_brake_performance', '全車手煞車性能')}_{year}_{race}_{session}"
    else:
        return f"All Drivers Brake Performance_{year}_{race}_{session}"  # ❌ 硬編碼英文
```

**相同問題：**
- 日文環境下無法顯示正確的標題

---

## ✅ 修復方案

### **修正後代碼**

#### All Drivers Straight Line Speed

```python
# ✅ 正確：直接使用 tr() 函數，自動支援所有語言
def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
    year = year or self.current_year or "2025"
    race = race or self.current_race or "Unknown"
    session = session or self.current_session or "R"
    
    # 使用國際化翻譯
    from core.gui_i18n import tr
    
    # 獲取多國語言化的模組名稱
    module_name = tr('all_drivers_straight_speed', 'All Drivers Speed & Acceleration')
    
    return f"{module_name}_{year}_{race}_{session}"
```

**改進：**
- ✅ 移除 `get_gui_language()` 和 `if language == 'zh'` 判斷
- ✅ 直接使用 `tr()` 函數，自動根據當前語言返回對應翻譯
- ✅ 支援所有語言（zh、en、ja）

#### All Drivers Brake Performance

```python
# ✅ 正確：直接使用 tr() 函數，自動支援所有語言
def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
    year = year or self.current_year or "2025"
    race = race or self.current_race or "Unknown"
    session = session or self.current_session or "R"
    
    # 使用國際化翻譯
    from core.gui_i18n import tr
    
    # 獲取多國語言化的模組名稱
    module_name = tr('all_drivers_brake_performance', 'All Drivers Brake Performance')
    
    return f"{module_name}_{year}_{race}_{session}"
```

---

## 🔬 測試驗證

### **測試結果**

```
✅ 所有測試通過 (6/6)

繁體中文：
  ✅ Brake Performance: 全車手煞車性能
  ✅ Straight Speed: 全車手速度與加速
  視窗標題：
    - 全車手煞車性能_2025_Singapore_R
    - 全車手速度與加速_2025_Singapore_R

English：
  ✅ Brake Performance: All Drivers Brake Performance
  ✅ Straight Speed: All Drivers Speed & Acceleration
  視窗標題：
    - All Drivers Brake Performance_2025_Singapore_R
    - All Drivers Speed & Acceleration_2025_Singapore_R

日本語：
  ✅ Brake Performance: 全ドライバーブレーキ性能
  ✅ Straight Speed: 全ドライバー速度と加速
  視窗標題：
    - 全ドライバーブレーキ性能_2025_Singapore_R
    - 全ドライバー速度と加速_2025_Singapore_R
```

---

## 📊 視窗標題對比

### **修復前（日文環境）**

```
❌ All Drivers Straight Line Speed_2025_Singapore_R
❌ All Drivers Brake Performance_2025_Singapore_R
```

**問題：** 硬編碼英文，無法多國語言化

---

### **修復後（日文環境）**

```
✅ 全ドライバー速度と加速_2025_Singapore_R
✅ 全ドライバーブレーキ性能_2025_Singapore_R
```

**改進：** 正確顯示日文標題

---

## 🌍 所有語言視窗標題對比

### **繁體中文（zh）**

| 模組 | 視窗標題 |
|------|----------|
| Straight Line Speed | 全車手速度與加速_2025_Singapore_R |
| Brake Performance | 全車手煞車性能_2025_Singapore_R |

### **English (en)**

| 模組 | 視窗標題 |
|------|----------|
| Straight Line Speed | All Drivers Speed & Acceleration_2025_Singapore_R |
| Brake Performance | All Drivers Brake Performance_2025_Singapore_R |

### **日本語 (ja)**

| 模組 | 視窗標題 |
|------|----------|
| Straight Line Speed | 全ドライバー速度と加速_2025_Singapore_R |
| Brake Performance | 全ドライバーブレーキ性能_2025_Singapore_R |

---

## 📁 修改的檔案

### 1. **all_drivers_straight_line_speed_mdi.py**
- **位置**：第 403-410 行
- **修改內容**：移除語言判斷，直接使用 `tr()` 函數

### 2. **all_drivers_brake_performance_mdi.py**
- **位置**：第 303-310 行
- **修改內容**：移除語言判斷，直接使用 `tr()` 函數

### 3. **測試檔案（新增）**
- `test_window_title_i18n_simple.py` - 簡化版視窗標題測試

---

## 🎯 修復原理

### **錯誤模式**
```python
# ❌ 不良實踐
language = get_gui_language()
if language == 'zh':
    return tr('key', 'fallback')  # 只有中文使用翻譯
else:
    return "Hardcoded English"     # 其他語言硬編碼
```

**問題：**
- 需要手動處理每種語言
- 容易遺漏新增的語言（如日文）
- 代碼冗長且易出錯

---

### **正確模式**
```python
# ✅ 最佳實踐
module_name = tr('key', 'fallback')  # 自動根據當前語言返回翻譯
return f"{module_name}_{year}_{race}_{session}"
```

**優點：**
- `tr()` 函數自動處理語言切換
- 添加新語言時無需修改代碼
- 代碼簡潔易維護

---

## ✅ 最終檢查清單

### **視窗標題多國語言化：完成**

- [x] All Drivers Brake Performance - 支援繁體中文、英文、日文
- [x] All Drivers Straight Line Speed - 支援繁體中文、英文、日文
- [x] 移除硬編碼英文
- [x] 使用 `tr()` 函數統一處理
- [x] 測試驗證 - 所有測試通過 (6/6)

---

## 🚀 手動驗證步驟

### **1. 啟動 GUI**
```powershell
python f1t_gui_main.py
```

### **2. 切換到日文**
- 選單 → 設定 → 語言 → 日本語

### **3. 開啟視窗**
- 展開樹狀圖：車手表現分析 → 直線速度分析
- 點擊：全ドライバー速度と加速
- 點擊：全ドライバーブレーキ性能

### **4. 驗證視窗標題**
- ✅ 視窗標題顯示為：`全ドライバー速度と加速_2025_Singapore_R`
- ✅ 視窗標題顯示為：`全ドライバーブレーキ性能_2025_Singapore_R`
- ✅ 不再顯示硬編碼的英文標題

### **5. 測試其他語言**
- 切換到繁體中文：確認標題為 `全車手速度與加速_...`
- 切換到 English：確認標題為 `All Drivers Speed & Acceleration_...`

---

## 📊 總結

### ✅ **修復完成**

1. **移除語言判斷邏輯**：
   - 移除 `if language == 'zh'` 條件判斷
   - 移除硬編碼的英文標題

2. **統一使用 tr() 函數**：
   - 直接調用 `tr()` 獲取多國語言化的模組名稱
   - 自動支援所有語言（zh、en、ja）

3. **測試結果**：
   - ✅ 所有測試通過 (6/6)
   - ✅ 繁體中文、英文、日文均正確顯示

### 🎉 **問題解決**

- ✅ **日文環境視窗標題問題已修復**
- ✅ 視窗標題現在完全支援多國語言化
- ✅ 所有模組標題一致使用 `tr()` 函數

---

**修復完成時間：** 2025-10-19 02:10  
**修復狀態：** ✅ **完成**  
**測試結果：** ✅ **全部通過** (6/6)

**建議：** 請手動啟動 GUI 並切換到日文驗證視窗標題顯示  
**命令：** `python f1t_gui_main.py`
