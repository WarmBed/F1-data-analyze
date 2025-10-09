# ✅ 修復報告：對話框與主視窗參數同步

**修復日期**: 2025-10-07  
**問題**: 用戶在對話框選擇參數後，主視窗參數欄未同步更新  
**解決方案**: 對話框確認後自動同步參數到主視窗  
**狀態**: ✅ 已完成

---

## 🔍 問題描述

### 正確的流程理解

```
用戶點擊「圈速分析」按鈕
  ↓
彈出 LapAnalysisOptionsDialog 對話框
  ↓
用戶在對話框中選擇:
  - Driver 1: VER, Lap 1: 13
  - Driver 2: LEC, Lap 2: 25
  - 圖表類型: Speed, Brake, Throttle
  ↓
點擊 OK 確認
  ↓
創建多個 MDI 視窗 (Speed Analysis, Brake Analysis...)
  ↓
問題: 主視窗上方的參數欄仍顯示舊值 ❌
  - Driver 1: (舊值)
  - Lap 1: (舊值)
  - Driver 2: (舊值)
  - Lap 2: (舊值)
```

### 用戶期望

**創建 MDI 視窗後，主視窗參數欄應該自動同步為對話框的選擇**：
```
對話框選擇: VER/13/LEC/25
  ↓
主視窗參數欄: VER/13/LEC/25 ✅
```

---

## 🔧 修復內容

### 檔案: `f1t_gui_main.py`

#### 修改位置: 第 10276-10285 行

#### 修改前（無同步機制）
```python
print(f"[圈速分析] 使用者選擇的圖表: {selected_charts}")
print(f"[圈速分析] 選擇的車手: 車手1={driver1}, 車手2={driver2 if driver2 else none_display}")
if is_fastest_lap:
    print(f"[圈速分析] 圈數設定: {fastest_label}")
else:
    if driver2:
        print(f"[圈速分析] 圈數設定: 車手1第{lap1_number}{lap_word}, 車手2第{lap2_number}{lap_word}")
    else:
        print(f"[圈速分析] 圈數設定: 車手1第{lap1_number}{lap_word}")

# 為每個選擇的圖表類型創建視窗
for chart_type in selected_charts:
    # ...
```

#### 修改後（添加同步機制）
```python
print(f"[圈速分析] 使用者選擇的圖表: {selected_charts}")
print(f"[圈速分析] 選擇的車手: 車手1={driver1}, 車手2={driver2 if driver2 else none_display}")
if is_fastest_lap:
    print(f"[圈速分析] 圈數設定: {fastest_label}")
else:
    if driver2:
        print(f"[圈速分析] 圈數設定: 車手1第{lap1_number}{lap_word}, 車手2第{lap2_number}{lap_word}")
    else:
        print(f"[圈速分析] 圈數設定: 車手1第{lap1_number}{lap_word}")

# 🆕 將對話框的選擇同步到主視窗參數欄
try:
    # 同步 Driver 1
    if driver1 and hasattr(self, 'driver1_combo'):
        index = self.driver1_combo.findText(driver1)
        if index >= 0:
            self.driver1_combo.setCurrentIndex(index)
            print(f"[同步] Driver 1 → {driver1}")
    
    # 同步 Driver 2
    if hasattr(self, 'driver2_combo'):
        if driver2:
            index = self.driver2_combo.findText(driver2)
            if index >= 0:
                self.driver2_combo.setCurrentIndex(index)
                print(f"[同步] Driver 2 → {driver2}")
        else:
            # Driver 2 為 None，設定為第一個選項（通常是空或 None）
            self.driver2_combo.setCurrentIndex(0)
            print(f"[同步] Driver 2 → None")
    
    # 同步 Lap 1
    if lap1_number and hasattr(self, 'lap1_spinbox'):
        self.lap1_spinbox.setValue(lap1_number)
        print(f"[同步] Lap 1 → {lap1_number}")
    
    # 同步 Lap 2
    if lap2_number and hasattr(self, 'lap2_spinbox'):
        self.lap2_spinbox.setValue(lap2_number)
        print(f"[同步] Lap 2 → {lap2_number}")
    
    # 同步 Fastest Lap 選項
    if hasattr(self, 'fastest_lap_checkbox'):
        self.fastest_lap_checkbox.setChecked(is_fastest_lap)
        print(f"[同步] Fastest Lap → {is_fastest_lap}")
    
    print(f"[同步] ✅ 主視窗參數已同步")
except Exception as sync_error:
    print(f"[同步] ⚠️ 參數同步失敗: {sync_error}")

# 為每個選擇的圖表類型創建視窗
for chart_type in selected_charts:
    # ...
```

---

## 📊 同步機制說明

### 同步的參數

1. **Driver 1** (`self.driver1_combo`)
   - 從對話框的 `driver1` 值查找對應的下拉選項
   - 設定為對應的索引

2. **Driver 2** (`self.driver2_combo`)
   - 如果有 `driver2`，查找對應選項並設定
   - 如果 `driver2` 為 None，設定為第一個選項（None）

3. **Lap 1** (`self.lap1_spinbox`)
   - 直接設定為 `lap1_number` 的數值

4. **Lap 2** (`self.lap2_spinbox`)
   - 直接設定為 `lap2_number` 的數值

5. **Fastest Lap** (`self.fastest_lap_checkbox`)
   - 設定勾選狀態為 `is_fastest_lap`

### 錯誤處理

- 使用 `hasattr()` 檢查控制項是否存在
- 使用 `try-except` 捕捉同步過程中的任何錯誤
- 錯誤不會中斷 MDI 視窗的創建流程

---

## 🎯 修復效果

### 修復前

```
1. 用戶打開對話框
2. 選擇: VER/13/LEC/25
3. 點擊 OK
4. 創建 MDI 視窗 ✅
5. 主視窗參數欄: (保持舊值) ❌

結果: 參數不一致，造成困惑
```

### 修復後

```
1. 用戶打開對話框
2. 選擇: VER/13/LEC/25
3. 點擊 OK
4. 創建 MDI 視窗 ✅
5. 主視窗參數欄: VER/13/LEC/25 ✅ (自動同步)

結果: 參數一致，清晰明確
```

---

## 🧪 測試建議

### 測試案例 1: 雙車手模式
```
1. 點擊「圈速分析」
2. 對話框選擇:
   - Driver 1: VER, Lap 1: 13
   - Driver 2: LEC, Lap 2: 25
   - 圖表: Speed, Brake
3. 點擊 OK

預期結果:
✅ 創建 Speed Analysis MDI 視窗
✅ 創建 Brake Analysis MDI 視窗
✅ 主視窗參數欄顯示: VER/13/LEC/25
✅ 終端顯示同步日誌:
   [同步] Driver 1 → VER
   [同步] Driver 2 → LEC
   [同步] Lap 1 → 13
   [同步] Lap 2 → 25
   [同步] Fastest Lap → False
   [同步] ✅ 主視窗參數已同步
```

### 測試案例 2: 單車手模式
```
1. 點擊「圈速分析」
2. 對話框選擇:
   - Driver 1: HAM, Lap 1: 7
   - Driver 2: (None)
   - 圖表: Throttle
3. 點擊 OK

預期結果:
✅ 創建 Throttle Analysis MDI 視窗
✅ 主視窗參數欄顯示: HAM/7/(None)/1
✅ Driver 2 下拉選單顯示 "None"
```

### 測試案例 3: 最速圈模式
```
1. 點擊「圈速分析」
2. 對話框選擇:
   - Driver 1: NOR
   - Fastest Lap: ✅ (勾選)
   - 圖表: Speed, RPM
3. 點擊 OK

預期結果:
✅ 創建 Speed Analysis MDI 視窗 (使用最速圈)
✅ 創建 RPM Analysis MDI 視窗 (使用最速圈)
✅ 主視窗 Fastest Lap 選項被勾選 ✅
✅ 終端顯示:
   [同步] Fastest Lap → True
```

---

## 📝 調試日誌範例

### 正常同步
```
[圈速分析] 使用者選擇的圖表: ['speed_analysis', 'brake']
[圈速分析] 選擇的車手: 車手1=VER, 車手2=LEC
[圈速分析] 圈數設定: 車手1第13圈, 車手2第25圈
[同步] Driver 1 → VER
[同步] Driver 2 → LEC
[同步] Lap 1 → 13
[同步] Lap 2 → 25
[同步] Fastest Lap → False
[同步] ✅ 主視窗參數已同步
[OK] 圈速分析完成，已開啟 2 個遙測圖表視窗 (車手: VER vs LEC, 車手1第13圈, 車手2第25圈)
```

### 同步失敗（控制項不存在）
```
[圈速分析] 使用者選擇的圖表: ['speed_analysis']
[圈速分析] 選擇的車手: 車手1=HAM, 車手2=None
[同步] ⚠️ 參數同步失敗: 'MainWindow' object has no attribute 'driver1_combo'
[OK] 圈速分析完成，已開啟 1 個遙測圖表視窗 (車手: HAM, 第7圈)
```

---

## ✅ 優點

1. **一致性**: 對話框與主視窗參數保持同步
2. **直觀性**: 用戶可以清楚看到當前分析的參數
3. **便利性**: 下次操作可以直接使用已同步的參數
4. **可追蹤性**: 調試日誌清楚記錄同步過程
5. **穩定性**: 錯誤處理確保同步失敗不影響主要功能

---

## ⚠️ 注意事項

### 1. Driver 2 同步邏輯
```python
if driver2:
    # 有選擇 Driver 2，查找並設定
    index = self.driver2_combo.findText(driver2)
    if index >= 0:
        self.driver2_combo.setCurrentIndex(index)
else:
    # 沒有選擇 Driver 2，設定為第一個選項（None）
    self.driver2_combo.setCurrentIndex(0)
```

**重要**: 假設 `driver2_combo` 的第一個選項是 "None"

### 2. Lap 2 數值
```python
if lap2_number and hasattr(self, 'lap2_spinbox'):
    self.lap2_spinbox.setValue(lap2_number)
```

**注意**: 如果 `lap2_number` 為 None，不會同步（保持原值）

### 3. 控制項存在性檢查
所有同步操作都使用 `hasattr()` 檢查控制項是否存在，確保不會因為控制項不存在而崩潰。

---

## 🎉 總結

### 修復內容
✅ 添加對話框到主視窗的參數同步機制  
✅ 同步 5 個參數（Driver 1/2, Lap 1/2, Fastest Lap）  
✅ 完善的錯誤處理和調試日誌  
✅ 不影響原有功能

### 修復效果
✅ 對話框選擇後，主視窗參數欄自動更新  
✅ 參數一致性，減少用戶困惑  
✅ 提升用戶體驗

### 下一步
- [ ] 測試各種場景（雙車手、單車手、最速圈）
- [ ] 驗證同步日誌是否正確顯示
- [ ] 確認不影響其他功能

---

**修復者**: GitHub Copilot  
**日期**: 2025-10-07  
**狀態**: ✅ 完成，等待測試驗證

