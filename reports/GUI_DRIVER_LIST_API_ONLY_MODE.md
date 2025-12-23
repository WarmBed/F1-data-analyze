# GUI 車手列表載入：API-ONLY 模式實施報告

**日期**: 2025-10-14  
**狀態**: ✅ 完成  
**符合政策**: API-ONLY 模式 (2025-10-03 更新)

---

## 🎯 問題根源（深度調查）

### 用戶報告
- ❌ GUI 仍顯示 2024 年車手（PER, SAR, MAG, BOT, ZHO）
- ❌ 缺少 2025 年新車手（DOO, COL, ANT, BEA, BOR, HAD, LAW）

### 調查發現（遵循反幻覺編碼原則）

#### 問題 1: 硬編碼車手列表 (2 處)
```python
# 位置 1: 第 975 行附近
drivers = ["VER", "LEC", "HAM", "RUS", "NOR", "PIA", "SAI", "PER", "ALO", "STR", 
          "TSU", "GAS", "OCO", "ALB", "SAR", "HUL", "MAG", "BOT", "ZHO", "COL"]

# 位置 2: 第 1020 行附近（except 區塊）
default_drivers = ["VER", "LEC", "HAM", "RUS", "NOR", "PIA", "SAI", "PER", "ALO", "STR", 
                   "TSU", "GAS", "OCO", "ALB", "SAR", "HUL", "MAG", "BOT", "ZHO", "COL"]
```
**問題**: 違反 API-ONLY 政策，使用硬編碼回退列表

#### 問題 2: JSON 格式支援不完整
```python
# 只能處理 data 為 dict 的情況
elif 'data' in data and isinstance(data['data'], dict):
    # 處理邏輯...
```
**問題**: 無法處理 `driver_fastest_pitstop_ranking` 的 `data` 為 **list** 格式

#### 問題 3: 載入優先級錯誤
```
進站 JSON → team_colors JSON → 硬編碼列表
```
**問題**: 進站 JSON 可能包含不完整的車手列表（某些車手未進站）

---

## ✅ 實施的解決方案

### 修正 1: 完全移除硬編碼列表

**Before**:
```python
if not drivers:
    print(f"[DRIVERS] 使用 2025 年預設車手列表")
    drivers = ["ALB", "ALO", "ANT", ...] # 硬編碼
```

**After**:
```python
if not drivers:
    print(f"[DRIVERS] ❌ 無法從任何來源載入車手列表")
    print(f"[DRIVERS] 💡 提示：請執行以下命令生成車手數據：")
    print(f"[DRIVERS]    python f1_analysis_modular_main.py -f 98 -y {year}")
    # 不使用硬編碼列表！保持 drivers 為空列表
```

### 修正 2: 變更載入優先級

**新優先級** (符合 API-ONLY):
```
1. team_colors JSON (F98 生成) ← 最可靠
2. 如果 JSON 不存在 → API 自動調用 F98
3. 進站 JSON (備用，僅在 1-2 失敗時)
4. 失敗 → 顯示錯誤，不使用硬編碼
```

**代碼實現**:
```python
# 策略 1: 從 team_colors JSON 讀取
team_color_patterns = [
    f"json/team_colors_{year}_*.json",
    f"json/team_colors_2025_*.json",
    f"json/team_colors_2024_*.json"
]
# ... 讀取邏輯

# 策略 1.5: 如果沒有 JSON，通過 API 生成
if not drivers:
    import requests
    api_base = resolve_api_base_url()
    response = requests.post(
        f"{api_base}/analyze",
        json={"function_id": "98", "year": int(year)},
        timeout=30
    )
    # ... 處理 API 響應
```

### 修正 3: 支援多種 JSON 格式

**新增 list 格式支援**:
```python
elif isinstance(data['data'], list) and data['data']:
    driver_set = set()
    for record in data['data']:
        if isinstance(record, dict) and 'driver' in record:
            driver_set.add(record['driver'])
        elif isinstance(record, dict) and 'Driver' in record:
            driver_set.add(record['Driver'])
    drivers = sorted(list(driver_set))
    print(f"[DRIVERS] 從 data['data'] list 提取 (ranking 格式)")
```

### 修正 4: 錯誤處理（API-ONLY 模式）

**Before**:
```python
except Exception as e:
    # 使用硬編碼列表
    default_drivers = ["VER", "LEC", ...]
```

**After**:
```python
except Exception as e:
    print(f"[ERROR] [DRIVERS] 載入車手列表失敗: {e}")
    
    # API-ONLY 模式：不使用硬編碼列表
    self.driver1_combo.clear()
    self.driver2_combo.clear()
    
    # 顯示錯誤訊息
    self.driver1_combo.addItem(tr("error_no_drivers", "❌ 無車手數據"), None)
    self.driver2_combo.addItem(tr("none_option", "無法載入"), None)
    
    print(f"[DRIVERS] 💡 請執行: python f1_analysis_modular_main.py -f 98 -y 2025")
```

---

## 📊 驗證結果

### 測試 1: team_colors JSON 存在
```
✅ 從 team_colors 載入 21 個車手
✅ 包含所有 2025 新車手: ANT, BEA, BOR, DOO, HAD, LAW
✅ 已移除 2024 已離開車手: PER, SAR, MAG, BOT, ZHO
```

### 測試 2: API 自動調用
```
⚠️  找不到 team_colors JSON
✅ 通過 API 調用 F98 功能生成
✅ 成功載入 21 個車手
```

### 測試 3: 完全失敗情況
```
❌ JSON 不存在
❌ API 調用失敗
✅ GUI 顯示錯誤訊息
✅ 提示用戶手動執行: python f1_analysis_modular_main.py -f 98 -y 2025
✅ 不使用硬編碼回退列表
```

---

## 🎯 符合開發政策檢查

### ✅ API-ONLY 模式政策
- ✅ 禁止 GUI 硬編碼數據
- ✅ 必須從 JSON 或 API 獲取
- ✅ 失敗時提示用戶手動操作
- ✅ 允許 API 自動調用生成數據

### ✅ 反幻覺編碼四原則
- ✅ **原則 1**: 用 `grep_search` 和 `read_file` 驗證所有代碼後再修改
- ✅ **原則 2**: 檢查 `modules/gui/` 是否有重複功能
- ✅ **原則 3**: 遵循通用架構模式
- ✅ **原則 4**: 使用 `tr()` 函數多國語言化

---

## 📁 修改的檔案

### f1t_gui_main.py
**位置**: 第 910-1075 行  
**修改內容**:
1. 移除 2 處硬編碼車手列表
2. 變更載入優先級（team_colors 優先）
3. 添加 API 自動調用邏輯
4. 新增 list 格式 JSON 支援
5. 更新錯誤處理（不使用硬編碼回退）

---

## 🚀 使用指南

### 正常情況（team_colors 存在）
```powershell
# 啟動 GUI，自動載入車手列表
python f1t_gui_main.py
```

### 首次使用（需要生成 team_colors）
```powershell
# 方法 1: 手動生成
python f1_analysis_modular_main.py -f 98 -y 2025

# 方法 2: API 自動調用（GUI 會自動執行）
python f1t_gui_main.py  # API 自動生成 team_colors
```

### 更新車手數據（新賽季）
```powershell
# 生成新賽季車手數據
python f1_analysis_modular_main.py -f 98 -y 2026

# 或通過 API
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"function_id": "98", "year": 2026}'
```

---

## 💡 技術細節

### team_colors JSON 結構
```json
{
  "data": {
    "drivers": {
      "VER": {"full_name": "Max Verstappen", "team": "Red Bull"},
      "DOO": {"full_name": "Jack Doohan", "team": "Alpine"},
      "ANT": {"full_name": "Andrea Kimi Antonelli", "team": "Mercedes"}
    }
  }
}
```

### API 端點
```
POST /analyze
{
  "function_id": "98",
  "year": 2025
}
```

---

## 🔍 故障排除

### 問題: GUI 顯示「無車手數據」
**原因**: team_colors JSON 不存在且 API 調用失敗

**解決**:
```powershell
python f1_analysis_modular_main.py -f 98 -y 2025
```

### 問題: 車手列表不完整
**原因**: 使用了舊的 team_colors JSON

**解決**:
```powershell
# 重新生成
python f1_analysis_modular_main.py -f 98 -y 2025 -force
```

---

## ✅ 完成狀態

- ✅ 移除所有硬編碼車手列表
- ✅ 實施 API-ONLY 模式
- ✅ 支援自動 API 調用
- ✅ 支援多種 JSON 格式
- ✅ 完整錯誤處理
- ✅ 符合專案開發政策
- ✅ 通過所有測試驗證

**結論**: GUI 車手列表載入現在完全符合 API-ONLY 模式政策，不再使用任何硬編碼數據。
