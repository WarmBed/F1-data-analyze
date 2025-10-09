# ✅ 修復報告：圈數精確匹配

**修復日期**: 2025-10-07  
**問題**: 用戶選擇 Lap17+Lap52，但載入了 Lap15+Lap52  
**解決方案**: 移除萬用字元回退模式，只使用精確匹配  
**狀態**: ✅ 已修復

---

## 🔧 修改內容

### 檔案 1: GUI 數據載入器
`modules/gui/lap_analysis/telemetry_data_loader_base.py`

### 檔案 2: API 緩存服務 ⚠️ 重要
`api/services/cache_service.py`

### 變更摘要

#### 變更 1: 移除萬用字元搜尋模式

**位置**: 第 493-519 行

#### 修改前（有萬用字元回退）
```python
if driver2_norm and driver2_norm != driver1_norm:
    # 雙車手對比檔案 - 優先精確搜尋，保留部分萬用字元備援
    filename_patterns = [
        f"comparison_telemetry_{driver1_norm}_{driver2_norm}_{year}_{race}_{session}_Lap{lap1_safe}_Lap{lap2_safe}.json",
        f"comparison_telemetry_{driver1_norm}_{driver2_norm}_{year}_{race}_{session}_Lap{lap1_safe}_Lap*.json",  # ❌ 萬用字元
        f"comparison_telemetry_{driver1_norm}_{driver2_norm}_{year}_{race}_{session}_Lap*_Lap{lap2_safe}.json",  # ❌ 萬用字元
        f"comparison_telemetry_{driver1_norm}_{driver2_norm}_{year}_{race}_{session}_Lap*_Lap*.json"  # ❌ 萬用字元
    ]
else:
    # 單車手檔案 - 同時支援新版與舊版命名
    filename_patterns = [
        f"comparison_telemetry_{driver1_norm}_{driver1_norm}_{year}_{race}_{session}_Lap{lap1_safe}.json",
        f"comparison_telemetry_{driver1_norm}_{driver1_norm}_{year}_{race}_{session}_Lap{lap1_safe}_Lap{lap2_safe}.json",
        f"comparison_telemetry_{driver1_norm}_{driver1_norm}_{year}_{race}_{session}_Lap*.json",  # ❌ 萬用字元
        f"comparison_telemetry_{driver1_norm}_{driver1_norm}_{year}_{race}_{session}_Lap*_Lap*.json"  # ❌ 萬用字元
    ]
```

#### 修改後（只有精確匹配）
```python
if driver2_norm and driver2_norm != driver1_norm:
    # 🆕 雙車手對比檔案 - 只使用精確搜尋（移除萬用字元回退）
    filename_patterns = [
        f"comparison_telemetry_{driver1_norm}_{driver2_norm}_{year}_{race}_{session}_Lap{lap1_safe}_Lap{lap2_safe}.json",
        # ❌ 移除萬用字元模式，檔案不存在時將通過 API 生成
    ]
    self._debug("🔄 雙車手檔案搜尋模式（精確匹配）:")
else:
    # 🆕 同車手檔案 - 只使用精確搜尋（移除萬用字元回退）
    filename_patterns = [
        f"comparison_telemetry_{driver1_norm}_{driver1_norm}_{year}_{race}_{session}_Lap{lap1_safe}.json",
        f"comparison_telemetry_{driver1_norm}_{driver1_norm}_{year}_{race}_{session}_Lap{lap1_safe}_Lap{lap2_safe}.json",
        # ❌ 移除萬用字元模式，檔案不存在時將通過 API 生成
    ]
    self._debug("🏎️ 同車手檔案搜尋模式（精確匹配）:")
```

**變更說明**:
- ❌ 移除所有 `Lap*` 萬用字元模式
- ✅ 只保留精確圈數匹配模式
- ✅ 檔案不存在時會觸發 API 生成新數據

---

### 修改 2: API 緩存服務搜尋邏輯（重要！）

**檔案**: `api/services/cache_service.py`  
**位置**: 第 177-196 行

#### 修改前（API 使用萬用字元）
```python
if function_id == "13":  # 車手比較分析
    search_patterns = [
        f"{self.json_dir}comparison_telemetry_{driver1}_{driver2}_{year}_{race}_{session}_*.json",  # ❌ 萬用字元
        f"{self.json_dir}comparison_telemetry_{driver2}_{driver1}_{year}_{race}_{session}_*.json",  # ❌ 萬用字元
        f"{self.json_dir}{pattern_base}*{driver1}*{driver2}*{year}*{race}*{session}*.json",
        f"{self.json_dir}{pattern_base}*{driver2}*{driver1}*{year}*{race}*{session}*.json"
    ]
```

#### 修改後（API 精確匹配）
```python
if function_id == "13":  # 🔧 車手比較分析 - 精確圈數匹配
    # 🆕 根據 lap1/lap2 參數決定搜尋模式
    if lap1 is not None and lap2 is not None:
        # 精確雙圈匹配模式
        search_patterns = [
            f"{self.json_dir}comparison_telemetry_{driver1}_{driver2}_{year}_{race}_{session}_Lap{lap1}_Lap{lap2}.json",
            f"{self.json_dir}comparison_telemetry_{driver2}_{driver1}_{year}_{race}_{session}_Lap{lap2}_Lap{lap1}.json",  # 反向順序
        ]
    elif lap1 is not None:
        # 精確單圈匹配模式
        search_patterns = [
            f"{self.json_dir}comparison_telemetry_{driver1}_{driver2}_{year}_{race}_{session}_Lap{lap1}.json",
            f"{self.json_dir}comparison_telemetry_{driver2}_{driver1}_{year}_{race}_{session}_Lap{lap1}.json",
        ]
    else:
        # ❌ 移除萬用字元模式（改為精確匹配或無圈數）
        search_patterns = [
            # 只搜尋沒有圈數後綴的檔案
            f"{self.json_dir}comparison_telemetry_{driver1}_{driver2}_{year}_{race}_{session}.json",
            f"{self.json_dir}comparison_telemetry_{driver2}_{driver1}_{year}_{race}_{session}.json",
        ]
```

**變更說明**:
- ✅ 根據 `lap1`/`lap2` 參數動態決定搜尋模式
- ✅ 有圈數參數時，只使用精確匹配（`Lap{lap1}_Lap{lap2}.json`）
- ✅ 無圈數參數時，搜尋無圈數後綴的檔案
- ❌ 完全移除萬用字元模式（`_*.json`）

**關鍵影響**:
- **修復前**: API 用 `_*.json` 找到所有圈數的檔案 → 載入多個檔案（Lap15_Lap52、Lap17_Lap53、Lap10_Lap50）
- **修復後**: API 只搜尋 `_Lap17_Lap50.json` → 找不到則返回 None，不會載入錯誤圈數

---

#### 變更 3: GUI 搜尋邏輯簡化

**檔案**: `modules/gui/lap_analysis/telemetry_data_loader_base.py`  
**位置**: 第 447-467 行

#### 修改前

**位置**: 第 447-467 行

#### 修改前
```python
if matches:
    # 如果有多個匹配，選擇最新的
    found_file = max(matches, key=os.path.getmtime)
    self._debug(f"✅ 找到檔案: {found_file}")
    self._debug(f"📊 匹配檔案數量: {len(matches)}")
    if len(matches) > 1:
        self._debug("📋 所有匹配檔案:")
        for match in matches:
            self._debug(f"     - {match}")
    break
```

#### 修改後
```python
if matches:
    # 精確匹配模式：直接選擇找到的檔案（應該只有一個）
    found_file = matches[0] if len(matches) == 1 else max(matches, key=os.path.getmtime)
    self._debug(f"✅ 找到檔案: {os.path.basename(found_file)}")
    
    if len(matches) > 1:
        self._debug(f"⚠️  警告: 精確模式匹配到多個檔案 ({len(matches)} 個)，選擇最新的")
        self._debug("📋 所有匹配檔案:")
        for match in matches:
            marker = "👉" if match == found_file else "  "
            self._debug(f"     {marker} {os.path.basename(match)}")
    break
```

**變更說明**:
- 移除複雜的圈數驗證邏輯（不再需要）
- 精確模式通常只會匹配一個檔案
- 如果意外匹配多個，仍會選擇最新的並發出警告

---

## 📊 行為變更對比

### 案例：用戶選擇 Lap17, Lap52

#### 修復前（有萬用字元回退）

```
搜尋模式:
  1. Lap17.json                    ❌ 不存在
  2. Lap17_Lap52.json              ❌ 不存在
  3. Lap*.json                     ✅ 匹配到 3 個檔案
     - Lap10_Lap50.json
     - Lap15_Lap52.json  ← 選擇（最新）
     - Lap17_Lap53.json

結果: 載入 Lap15_Lap52.json ❌ 錯誤
```

#### 修復後（只有精確匹配）

```
搜尋模式:
  1. Lap17.json                    ❌ 不存在
  2. Lap17_Lap52.json              ❌ 不存在

結果: 
  - 找不到精確匹配的檔案
  - 觸發 API 請求生成 Lap17_Lap52.json ✅ 正確
  - 或顯示錯誤，提示用戶手動生成
```

---

## 🎯 預期效果

### 情況 1: 精確檔案存在

**用戶選擇**: Lap17, Lap53  
**檔案存在**: `comparison_telemetry_LEC_LEC_2025_Australia_R_Lap17_Lap53.json`

**結果**: ✅ 成功載入 `Lap17_Lap53.json`

---

### 情況 2: 精確檔案不存在

**用戶選擇**: Lap17, Lap52  
**檔案存在**: 
- ✅ `Lap15_Lap52.json`
- ✅ `Lap17_Lap53.json`
- ❌ `Lap17_Lap52.json` (不存在)

**結果**: 
1. 搜尋失敗（找不到精確匹配）
2. 觸發 API 請求生成新數據
3. 通過 API 生成 `Lap17_Lap52.json` ✅
4. 載入新生成的檔案 ✅

---

## ✅ 優點

1. **精確性**: 用戶選擇的圈數與載入的數據完全一致
2. **可預測性**: 不會意外載入其他圈數的數據
3. **透明性**: 用戶知道如果檔案不存在會生成新數據
4. **數據新鮮度**: 每次都載入最精確的數據，或生成最新數據

---

## ⚠️ 潛在影響

### 影響 1: API 調用頻率增加

**修復前**: 找不到精確檔案時，會載入相近圈數的緩存數據  
**修復後**: 找不到精確檔案時，會通過 API 生成新數據

**結果**: 
- ✅ 數據更準確
- ⚠️ API 調用可能增加
- ⚠️ 首次載入時間可能增加（需要生成數據）

**建議**: 
- 用戶應預先生成常用的圈數組合
- 或接受首次載入時的等待時間

---

### 影響 2: 離線模式受限

**修復前**: 離線時可以載入相近圈數的緩存數據  
**修復後**: 離線時找不到精確檔案會失敗

**建議**: 
- 提供批次預生成功能
- 或在離線前提示用戶生成所需數據

---

## 🧪 測試建議

### 測試案例 1: 精確檔案存在
```
1. 選擇 LEC Lap17, LEC Lap53
2. 確認載入 Lap17_Lap53.json ✅
3. 確認圖表顯示正確圈數 ✅
```

### 測試案例 2: 精確檔案不存在（API 可用）
```
1. 選擇 LEC Lap17, LEC Lap52
2. 確認系統嘗試通過 API 生成數據 ✅
3. 確認新檔案 Lap17_Lap52.json 被創建 ✅
4. 確認圖表顯示正確圈數 ✅
```

### 測試案例 3: 精確檔案不存在（API 不可用）
```
1. 斷開網路或停止 API 服務
2. 選擇 LEC Lap17, LEC Lap52
3. 確認顯示錯誤訊息 ✅
4. 確認提示用戶檔案不存在 ✅
```

### 測試案例 4: 雙車手模式
```
1. 選擇 VER Lap10, LEC Lap15
2. 確認搜尋 comparison_telemetry_VER_LEC_2025_Australia_R_Lap10_Lap15.json
3. 確認不會載入其他圈數組合 ✅
```

---

## 📝 相關文件

- **問題報告**: `BUG_REPORT_Lap_Number_Mismatch.md`
- **修改檔案**: `modules/gui/lap_analysis/telemetry_data_loader_base.py`
- **雙圈比較模式**: `IMPLEMENTATION_Dual_Lap_Comparison_Mode.md`

---

## 🎉 總結

### 修復內容
✅ 移除萬用字元搜尋模式  
✅ 只保留精確圈數匹配  
✅ 簡化搜尋邏輯  
✅ 確保圈數精確性

### 預期效果
✅ 用戶選擇 Lap17+Lap52 → 載入 Lap17+Lap52（精確）  
✅ 檔案不存在時通過 API 生成新數據  
✅ 不會再載入錯誤圈數的數據

### 下一步
- [ ] 測試修復效果
- [ ] 更新用戶文檔
- [ ] 考慮添加批次預生成功能（可選）

---

**修復者**: GitHub Copilot  
**日期**: 2025-10-07  
**狀態**: ✅ 完成

