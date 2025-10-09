# 🐛 BUG 報告：圈數不精確匹配問題 ✅ 已修復

**發現日期**: 2025-10-07  
**修復日期**: 2025-10-07  
**狀態**: ✅ 已修復  
**症狀**: 用戶選擇 Lap17 + Lap52，但載入了 Lap15 + Lap52 的數據  
**根本原因**: JSON 檔案搜尋使用萬用字元回退邏輯，導致模糊匹配  
**解決方案**: 移除萬用字元模式，只使用精確匹配  
**修復報告**: 參見 `FIX_REPORT_Lap_Number_Exact_Match.md`

---

## 🔍 問題分析

### 用戶操作
1. **Driver1**: LEC, **Lap1**: 17
2. **Driver2**: LEC, **Lap2**: 52
3. **預期載入**: `comparison_telemetry_LEC_LEC_2025_Australia_R_Lap17_Lap52.json`
4. **實際載入**: `comparison_telemetry_LEC_LEC_2025_Australia_R_Lap15_Lap52.json` ❌

### 現有 JSON 檔案
```
comparison_telemetry_LEC_LEC_2025_Australia_R_Lap10_Lap50.json  ✅ 存在
comparison_telemetry_LEC_LEC_2025_Australia_R_Lap15_Lap52.json  ✅ 存在
comparison_telemetry_LEC_LEC_2025_Australia_R_Lap17_Lap53.json  ✅ 存在
comparison_telemetry_LEC_LEC_2025_Australia_R_Lap17_Lap52.json  ❌ 不存在
```

**關鍵發現**: 用戶想要的 `Lap17_Lap52` 檔案**不存在**！

---

## 🔎 搜尋邏輯分析

### 當前搜尋模式（同車手）

**檔案**: `modules/gui/lap_analysis/telemetry_data_loader_base.py`  
**行數**: 505-509

```python
# 單車手檔案 - 同時支援新版與舊版命名
filename_patterns = [
    f"comparison_telemetry_{driver1_norm}_{driver1_norm}_{year}_{race}_{session}_Lap{lap1_safe}.json",
    f"comparison_telemetry_{driver1_norm}_{driver1_norm}_{year}_{race}_{session}_Lap{lap1_safe}_Lap{lap2_safe}.json",
    f"comparison_telemetry_{driver1_norm}_{driver1_norm}_{year}_{race}_{session}_Lap*.json",
    f"comparison_telemetry_{driver1_norm}_{driver1_norm}_{year}_{race}_{session}_Lap*_Lap*.json"
]
```

### 搜尋執行順序

對於 `Lap17, Lap52` 的搜尋：

1. **模式 1** (精確單圈): `comparison_telemetry_LEC_LEC_2025_Australia_R_Lap17.json`
   - ❌ 不匹配（檔案不存在）

2. **模式 2** (精確雙圈): `comparison_telemetry_LEC_LEC_2025_Australia_R_Lap17_Lap52.json`
   - ❌ 不匹配（**目標檔案不存在**）

3. **模式 3** (萬用字元單圈): `comparison_telemetry_LEC_LEC_2025_Australia_R_Lap*.json`
   - ✅ 匹配到：
     - `Lap10_Lap50.json`
     - `Lap15_Lap52.json`
     - `Lap17_Lap53.json`
   - **選擇最新檔案**: `Lap15_Lap52.json` (最後修改時間 2025/10/7 下午 01:23:37)

4. **模式 4** (萬用字元雙圈): `comparison_telemetry_LEC_LEC_2025_Australia_R_Lap*_Lap*.json`
   - （不會執行，因為模式 3 已經找到檔案）

---

## 🐞 根本原因

### 問題 1: 萬用字元回退邏輯過於寬鬆

**代碼位置**: `telemetry_data_loader_base.py:452-465`

```python
for i, filename_pattern in enumerate(filename_patterns, 1):
    search_pattern = os.path.join(search_dir, filename_pattern)
    self._debug(f"   🔍 模式 {i}: {search_pattern}")
    matches = glob.glob(search_pattern)
    
    if matches:
        # ⚠️ 問題：如果有多個匹配，選擇最新的
        found_file = max(matches, key=os.path.getmtime)
        self._debug(f"✅ 找到檔案: {found_file}")
        self._debug(f"📊 匹配檔案數量: {len(matches)}")
        if len(matches) > 1:
            self._debug("📋 所有匹配檔案:")
            for match in matches:
                self._debug(f"     - {match}")
        break  # ⚠️ 找到就跳出，不檢查是否精確匹配
```

**問題**:
- 萬用字元模式 (`Lap*`) 會匹配**所有圈數**
- 選擇最新檔案的邏輯是**基於修改時間**，而非**圈數匹配度**
- 沒有驗證匹配檔案的圈數是否符合用戶選擇

### 問題 2: 同車手模式的搜尋模式設計缺陷

當 `driver1 == driver2` 時，系統認為這是「單車手模式」，搜尋模式包含：

```python
# 模式 3: 萬用字元單圈
f"comparison_telemetry_{driver1_norm}_{driver1_norm}_{year}_{race}_{session}_Lap*.json"
```

這個模式會匹配：
- `Lap10_Lap50.json` ✅
- `Lap15_Lap52.json` ✅
- `Lap17_Lap53.json` ✅
- **任何圈數的組合** ✅

結果是選擇了**最新的檔案**，而非**最匹配的檔案**。

---

## 🎯 案例重現

### 實際發生的搜尋流程

**用戶輸入**: Lap17, Lap52

**搜尋過程**:
```
[DEBUG] 🔍 開始精確搜尋...
[DEBUG] 📂 搜尋目錄: d:\OneDrive\Code\F1-data-analyze\json
[DEBUG] 🏎️ 單車手檔案搜尋模式:
[DEBUG]    1. comparison_telemetry_LEC_LEC_2025_Australia_R_Lap17.json
[DEBUG]    2. comparison_telemetry_LEC_LEC_2025_Australia_R_Lap17_Lap52.json
[DEBUG]    3. comparison_telemetry_LEC_LEC_2025_Australia_R_Lap*.json
[DEBUG]    4. comparison_telemetry_LEC_LEC_2025_Australia_R_Lap*_Lap*.json

[DEBUG]    🔍 模式 1: ...Lap17.json
[DEBUG]    ❌ 模式 1 無匹配

[DEBUG]    🔍 模式 2: ...Lap17_Lap52.json
[DEBUG]    ❌ 模式 2 無匹配（檔案不存在）

[DEBUG]    🔍 模式 3: ...Lap*.json
[DEBUG]    ✅ 找到檔案: comparison_telemetry_LEC_LEC_2025_Australia_R_Lap15_Lap52.json
[DEBUG]    📊 匹配檔案數量: 3
[DEBUG]    📋 所有匹配檔案:
[DEBUG]         - comparison_telemetry_LEC_LEC_2025_Australia_R_Lap10_Lap50.json (2025/10/7 01:07:58)
[DEBUG]         - comparison_telemetry_LEC_LEC_2025_Australia_R_Lap15_Lap52.json (2025/10/7 01:23:37) ← 最新
[DEBUG]         - comparison_telemetry_LEC_LEC_2025_Australia_R_Lap17_Lap53.json (2025/10/7 01:24:19)
```

**選擇結果**: `Lap15_Lap52.json`（最後修改時間較晚，但不是最新的）

**問題**: 
- `Lap17_Lap53.json` 的修改時間是 01:24:19（最新）
- 但為什麼選了 `Lap15_Lap52.json` (01:23:37)？

**可能原因**: 
- `max(matches, key=os.path.getmtime)` 可能有問題
- 或者搜尋時 `Lap17_Lap53.json` 沒被包含在 matches 中

讓我重新檢查搜尋邏輯...

實際上，如果模式 3 是 `Lap*.json`（不含第二個 Lap），那麼：
- ✅ 會匹配 `Lap17.json`（不存在）
- ❌ 不會匹配 `Lap17_Lap52.json`

所以問題應該是在**模式 4**：`Lap*_Lap*.json`

---

## 💡 解決方案

### 方案 A: 改進萬用字元匹配邏輯（推薦）

在萬用字元匹配後，增加**圈數驗證**：

```python
# 在找到萬用字元匹配後，驗證圈數
if matches:
    # 如果是萬用字元模式（i >= 3），進行圈數驗證
    if i >= 3 and lap1_safe is not None and lap2_safe is not None:
        # 從檔名中提取圈數，驗證是否匹配
        validated_matches = []
        for match in matches:
            filename = os.path.basename(match)
            # 提取圈數：comparison_telemetry_LEC_LEC_2025_Australia_R_Lap15_Lap52.json
            lap_match = re.search(r'_Lap(\d+)(?:_Lap(\d+))?\.json$', filename)
            if lap_match:
                file_lap1 = int(lap_match.group(1))
                file_lap2 = int(lap_match.group(2)) if lap_match.group(2) else file_lap1
                
                # 驗證是否匹配用戶輸入
                if file_lap1 == lap1_safe or file_lap2 == lap2_safe:
                    validated_matches.append((match, file_lap1, file_lap2))
        
        if validated_matches:
            # 選擇最匹配的檔案（兩個圈數都匹配 > 一個匹配）
            best_match = max(validated_matches, 
                           key=lambda x: (x[1] == lap1_safe) + (x[2] == lap2_safe))
            found_file = best_match[0]
        else:
            # 沒有驗證通過的檔案，繼續下一個模式
            continue
    else:
        # 精確模式，直接選擇最新檔案
        found_file = max(matches, key=os.path.getmtime)
```

### 方案 B: 移除過於寬鬆的萬用字元模式

刪除模式 3 和模式 4，只保留精確搜尋：

```python
# 同車手模式只使用精確搜尋
filename_patterns = [
    f"comparison_telemetry_{driver1_norm}_{driver1_norm}_{year}_{race}_{session}_Lap{lap1_safe}.json",
    f"comparison_telemetry_{driver1_norm}_{driver1_norm}_{year}_{race}_{session}_Lap{lap1_safe}_Lap{lap2_safe}.json",
    # 移除萬用字元模式
]
```

**缺點**: 如果檔案不存在，無法提供回退選項

### 方案 C: 檔案不存在時直接通過 API 生成（推薦）

如果精確匹配失敗，不使用萬用字元回退，而是：
1. 直接通過 API 請求生成數據
2. 或提示用戶檔案不存在，是否生成新數據

---

## 🔧 建議實施

### 優先方案: **方案 A + 方案 C 組合**

1. **短期修復**: 實施方案 A，增加圈數驗證邏輯
2. **長期優化**: 實施方案 C，檔案不存在時通過 API 生成

### 修改位置

**檔案**: `modules/gui/lap_analysis/telemetry_data_loader_base.py`  
**方法**: `_search_json_files()` (第 449-465 行)

---

## 📊 預期效果

### 修復前
```
用戶選擇: Lap17, Lap52
搜尋結果: Lap15_Lap52.json ❌（錯誤）
原因: 萬用字元匹配 + 最新檔案選擇
```

### 修復後
```
用戶選擇: Lap17, Lap52
搜尋結果: 
  - 精確匹配失敗（檔案不存在）
  - 萬用字元匹配: Lap15_Lap52, Lap17_Lap53, Lap10_Lap50
  - 圈數驗證: Lap15_Lap52 (lap2 匹配), Lap17_Lap53 (lap1 匹配)
  - 選擇: Lap17_Lap53 (lap1 精確匹配) ✅ 更接近
  - 或: 通過 API 生成新檔案 Lap17_Lap52 ✅ 最理想
```

---

**診斷完成時間**: 2025-10-07  
**下一步**: 實施修復方案

