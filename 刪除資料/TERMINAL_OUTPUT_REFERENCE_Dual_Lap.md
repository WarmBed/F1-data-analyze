# 🔍 雙圈比較模式終端輸出參考

**用途**: 驗證雙圈比較模式是否正確運作  
**查看方式**: 在 F1T GUI 載入數據時，觀察終端/控制台輸出

---

## ✅ 成功案例：雙圈比較模式

### Speed Analysis

```
[SPEED_CHART_WIDGET] 🔢 提取圈數: lap1=10, lap2=50
[SPEED_CHART_WIDGET] 👤 driver1_name: VER
[SPEED_CHART_WIDGET] 👤 driver2_name: VER
[SPEED_CHART] 🔄 檢測到雙圈比較模式: VER 第10圈 vs 第50圈
[SPEED_CHART] 🔄 使用雙圈比較模式顯示: VER 第10圈 vs 第50圈
[SPEED_CHART_WIDGET] 🎨 調用 chart_widget.set_speed_data...
[SPEED_CHART] 🔄 雙圈比較模式: VER - 第10圈 vs VER - 第50圈
[SPEED_CHART_WIDGET] ✅ chart_widget.set_speed_data 完成
```

**關鍵標誌**:
- ✅ `🔢 提取圈數: lap1=10, lap2=50`
- ✅ `🔄 檢測到雙圈比較模式`
- ✅ `🔄 雙圈比較模式: VER - 第10圈 vs VER - 第50圈`

---

### Brake Analysis

```
[brake_CHART] 🔢 提取圈數: lap1=10, lap2=50
[brake_CHART] 車手名稱更新: VER vs VER
[brake_CHART] 🔄 檢測到雙圈比較模式: VER 第10圈 vs 第50圈
[brake_CHART] 🔄 使用雙圈比較模式顯示: VER 第10圈 vs 第50圈
[brake_CHART] 📊 更新圖表...
[BRAKE_CHART] 🔄 雙圈比較模式: VER - 第10圈 vs VER - 第50圈
[brake_CHART] ✅ 圖表更新完成
```

**關鍵標誌**:
- ✅ `🔢 提取圈數`
- ✅ `🔄 檢測到雙圈比較模式`
- ✅ `VER - 第10圈 vs VER - 第50圈`

---

### Throttle Analysis

```
[THROTTLE_CHART] 🔢 提取圈數: lap1=10, lap2=50
[THROTTLE_CHART] 🔄 檢測到雙圈比較模式: VER 第10圈 vs 第50圈
[THROTTLE_CHART] 🔄 使用雙圈比較模式顯示: VER 第10圈 vs 第50圈
[THROTTLE_CHART] 🔄 雙圈比較模式: VER - 第10圈 vs VER - 第50圈
```

---

### Gear Analysis

```
[gear_CHART] 🔢 提取圈數: lap1=10, lap2=50
[gear_CHART] 🔄 檢測到雙圈比較模式: VER 第10圈 vs 第50圈
[gear_CHART] 🔄 使用雙圈比較模式顯示: VER 第10圈 vs 第50圈
[GEAR_CHART] 🔄 雙圈比較模式: VER - 第10圈 vs VER - 第50圈
```

---

### RPM Analysis

```
[RPM_CHART] 🔢 提取圈數: lap1=10, lap2=50
[RPM_CHART] 🔄 檢測到雙圈比較模式: VER 第10圈 vs 第50圈
[RPM_CHART] 🔄 使用雙圈比較模式顯示: VER 第10圈 vs 第50圈
[RPM_CHART] 🔄 雙圈比較模式: VER - 第10圈 vs VER - 第50圈
```

---

### Acceleration Analysis

```
[acceleration_CHART] 🔢 提取圈數: lap1=10, lap2=50
[acceleration_CHART] 🔄 檢測到雙圈比較模式: VER 第10圈 vs 第50圈
[acceleration_CHART] 🔄 使用雙圈比較模式顯示: VER 第10圈 vs 第50圈
[ACC_CHART] 🔄 雙圈比較模式: VER - 第10圈 vs VER - 第50圈
```

---

### Speed Diff Analysis ⚠️ 特殊標籤格式

```
[speeddiff_CHART] 🔢 提取圈數: lap1=10, lap2=50
[speeddiff_CHART] 速度差標籤: VER vs VER
[SPEEDDIFF_CHART] 🔄 雙圈比較模式: VER 第10圈 vs 第50圈
```

**注意**: SpeedDiff 標籤格式為 `VER 第10圈 vs 第50圈`（無 " - " 符號）

---

### Distance Diff Analysis ⚠️ 特殊標籤格式

```
[distancediff_CHART] 🔢 提取圈數: lap1=10, lap2=50
[distancediff_CHART] 距離差標籤: VER vs VER
[DISTANCEDIFF_CHART] 🔄 雙圈比較模式: VER 第10圈 vs 第50圈
```

**注意**: DistanceDiff 標籤格式為 `VER 第10圈 vs 第50圈`（無 " - " 符號）

---

## ❌ 失敗案例：未檢測到雙圈模式

### 原因 1: 相同圈數（應該顯示單車手模式）

```
[brake_CHART] 🔢 提取圈數: lap1=10, lap2=10
[brake_CHART] 🔍 檢測到相同車手比較（單車手模式）: VER
[brake_CHART] 🎯 使用單車手模式顯示
```

**這是正常行為！** 當 lap1 == lap2 時，系統會正確切換到單車手模式。

---

### 原因 2: 圈數提取失敗

```
[brake_CHART] 車手名稱更新: VER vs VER
[brake_CHART] 🔍 檢測到相同車手比較: VER vs VER
[brake_CHART] 🎯 使用單車手模式顯示
```

**問題**:
- ❌ 未顯示 `🔢 提取圈數`
- ❌ JSON 檔案可能缺少 `metadata.drivers[].lap_number`

**解決方案**:
1. 檢查 JSON 檔案內容，確認包含 lap_number
2. 重新生成 JSON 檔案（使用最新的 CLI）

---

### 原因 3: 不同車手（應該顯示雙車手模式）

```
[brake_CHART] 🔢 提取圈數: lap1=10, lap2=50
[brake_CHART] 車手名稱更新: VER vs LEC
[brake_CHART] 🎯 使用雙車手模式顯示: VER vs LEC
```

**這是正常行為！** 當 driver1 != driver2 時，系統會顯示雙車手模式。

---

## 🔧 調試技巧

### 1. 啟用詳細調試輸出

確保在載入數據時終端保持開啟，觀察以下關鍵輸出：

```python
# 數據載入階段
[brake_CHART] ========== 更新brake數據 ==========
[brake_CHART] 收到數據鍵: ['metadata', 'brake_data', 'statistics']
[brake_CHART] 車手數量: 2
```

```python
# 圈數提取階段
[brake_CHART] 🔢 提取圈數: lap1=10, lap2=50  # ✅ 成功
# 或
[brake_CHART] 車手名稱更新: VER vs VER      # ❌ 未提取到圈數
```

```python
# 模式判斷階段
[brake_CHART] 🔄 檢測到雙圈比較模式: VER 第10圈 vs 第50圈  # ✅ 雙圈模式
# 或
[brake_CHART] 🔍 檢測到相同車手比較（單車手模式）: VER   # ✅ 單車手模式
# 或
[brake_CHART] 🎯 使用雙車手模式顯示: VER vs LEC         # ✅ 雙車手模式
```

---

### 2. 檢查 JSON 檔案結構

雙圈比較模式需要 JSON 檔案包含正確的 lap_number：

```json
{
  "metadata": {
    "drivers": [
      {
        "code": "VER",
        "lap_number": 10  // ✅ 必須存在
      },
      {
        "code": "VER",
        "lap_number": 50  // ✅ 必須存在且與 lap1 不同
      }
    ]
  }
}
```

---

### 3. 快速驗證腳本

使用以下 PowerShell 命令快速驗證 JSON 檔案：

```powershell
# 檢查 JSON 檔案中的 lap_number
Get-Content "json/comparison_telemetry_VER_VER_2024_Japan_R_Lap10_Lap50.json" | Select-String "lap_number"
```

預期輸出：
```
    "lap_number": 10,
    "lap_number": 50
```

---

## 📊 標籤格式對照表

| 模組 | 雙圈標籤格式 | 雙車手標籤格式 | 單車手標籤格式 |
|------|-------------|---------------|---------------|
| Speed | `VER - 第10圈` vs `VER - 第50圈` | `VER` vs `LEC` | `VER` |
| Brake | `VER - 第10圈` vs `VER - 第50圈` | `VER` vs `LEC` | `VER` |
| Throttle | `VER - 第10圈` vs `VER - 第50圈` | `VER` vs `LEC` | `VER` |
| Gear | `VER - 第10圈` vs `VER - 第50圈` | `VER` vs `LEC` | `VER` |
| RPM | `VER - 第10圈` vs `VER - 第50圈` | `VER` vs `LEC` | `VER` |
| Acceleration | `VER - 第10圈` vs `VER - 第50圈` | `VER` vs `LEC` | `VER` |
| **SpeedDiff** | `VER 第10圈 vs 第50圈` ⚠️ | `VER vs LEC` | `VER` |
| **DistanceDiff** | `VER 第10圈 vs 第50圈` ⚠️ | `VER vs LEC` | `VER` |

**注意**: SpeedDiff 和 DistanceDiff 使用不同的標籤格式（無 " - " 符號）

---

## ✅ 驗證完成清單

使用以下清單快速驗證每個模組：

- [ ] **Speed Analysis**: 終端顯示 `🔄 雙圈比較模式`，圖表標籤 `VER - 第10圈` vs `VER - 第50圈`
- [ ] **Brake Analysis**: 終端顯示 `🔄 雙圈比較模式`，圖表標籤 `VER - 第10圈` vs `VER - 第50圈`
- [ ] **Throttle Analysis**: 終端顯示 `🔄 雙圈比較模式`，圖表標籤 `VER - 第10圈` vs `VER - 第50圈`
- [ ] **Gear Analysis**: 終端顯示 `🔄 雙圈比較模式`，圖表標籤 `VER - 第10圈` vs `VER - 第50圈`
- [ ] **RPM Analysis**: 終端顯示 `🔄 雙圈比較模式`，圖表標籤 `VER - 第10圈` vs `VER - 第50圈`
- [ ] **Acceleration Analysis**: 終端顯示 `🔄 雙圈比較模式`，圖表標籤 `VER - 第10圈` vs `VER - 第50圈`
- [ ] **SpeedDiff Analysis**: 終端顯示 `🔄 雙圈比較模式`，圖表標籤 `VER 第10圈 vs 第50圈`
- [ ] **DistanceDiff Analysis**: 終端顯示 `🔄 雙圈比較模式`，圖表標籤 `VER 第10圈 vs 第50圈`

---

**文檔版本**: 1.0  
**最後更新**: 2025-01-03  
**相關文檔**: `IMPLEMENTATION_COMPLETE_Dual_Lap_All_Modules.md`, `TEST_CHECKLIST_Dual_Lap_All_Modules.md`
