# 車手-車隊手動覆寫系統使用指南

## 📋 概述

當 FastF1/Ergast API 的車手資料延遲更新時（例如季中替補、轉隊等情況），F1T 系統提供手動覆寫機制，允許用戶自訂車手-車隊映射關係。

**覆寫優先級：** `config/driver_team_overrides.json` > FastF1 API > Ergast API

---

## 🎯 適用場景

| 場景 | 說明 | 範例 |
|------|------|------|
| **季中替補** | 車手因傷病/表現被替換 | 2024 美國站：LAW 替補 RIC |
| **緊急轉隊** | 賽季中途車手轉換車隊 | 2025 假設：TSU → Red Bull |
| **測試車手** | 週五練習賽測試車手參賽 | FP1 測試車手替換正賽車手 |
| **資料延遲** | FastF1 未及時更新車手資料 | 官宣轉隊後 FastF1 尚未更新 |

---

## 📝 配置檔案結構

**檔案路徑：** `config/driver_team_overrides.json`

### 基本結構

```json
{
  "metadata": {
    "description": "手動車手-車隊覆寫配置（優先於 FastF1）",
    "last_updated": "2025-10-19T10:00:00Z"
  },
  "overrides": {
    "2025": {
      "TSU": {
        "enabled": true,
        "team_slug": "red bull",
        "team_name": "Red Bull",
        "full_name": "Yuki Tsunoda",
        "reason": "2025 季中升級到主隊",
        "effective_from": "2025-06-01",
        "comment": "巴林站起生效"
      }
    }
  }
}
```

### 欄位說明

| 欄位 | 必填 | 說明 | 範例 |
|------|------|------|------|
| `enabled` | ✅ | 是否啟用此覆寫 | `true` / `false` |
| `team_slug` | ✅ | 車隊 slug（小寫，見支援清單） | `"red bull"` |
| `team_name` | ✅ | 車隊顯示名稱 | `"Red Bull"` |
| `full_name` | ❌ | 車手全名 | `"Yuki Tsunoda"` |
| `reason` | ❌ | 覆寫原因（文件用途） | `"季中升級"` |
| `effective_from` | ❌ | 生效日期（文件用途） | `"2025-06-01"` |
| `comment` | ❌ | 額外說明 | `"巴林站起生效"` |

### 支援的 team_slug 清單

```json
{
  "teams": [
    "red bull",       // Red Bull Racing
    "ferrari",        // Scuderia Ferrari
    "mercedes",       // Mercedes-AMG Petronas
    "mclaren",        // McLaren Racing
    "aston martin",   // Aston Martin Aramco
    "alpine",         // Alpine F1 Team
    "williams",       // Williams Racing
    "racing bulls",   // RB F1 Team (前身 AlphaTauri)
    "haas",           // MoneyGram Haas F1
    "sauber"          // Stake F1 / Kick Sauber
  ]
}
```

---

## 🚀 使用步驟

### 步驟 1：編輯配置檔案

使用任何文字編輯器開啟 `config/driver_team_overrides.json`：

```json
{
  "overrides": {
    "2025": {
      "TSU": {
        "enabled": true,
        "team_slug": "red bull",
        "team_name": "Red Bull",
        "full_name": "Yuki Tsunoda",
        "reason": "2025 季中升級到主隊",
        "effective_from": "2025-06-01"
      },
      "LAW": {
        "enabled": true,
        "team_slug": "racing bulls",
        "team_name": "RB",
        "full_name": "Liam Lawson",
        "reason": "2025 季中降級到姊妹隊",
        "effective_from": "2025-06-01"
      }
    }
  }
}
```

### 步驟 2：重新生成顏色配置（CLI）

執行 Function 98 強制刷新：

```powershell
python f1_analysis_modular_main.py -f 98 -y 2025 --force
```

**預期輸出：**
```
==================================================
🔧 套用車手-車隊手動覆寫
==================================================
[OVERRIDE] ✅ 載入覆寫: TSU → Red Bull (2025 季中升級到主隊)
[OVERRIDE] ✅ 載入覆寫: LAW → RB (2025 季中降級到姊妹隊)
   TSU: racing bulls → red bull (覆寫)
   LAW: red bull → racing bulls (覆寫)
==================================================

[FINISH] ✅ 2025 顏色配置生成完成
```

### 步驟 3：驗證 GUI 顯示

啟動 GUI：

```powershell
python f1t_gui_main.py
```

**驗證項目：**
- ✅ 車手列表顯示正確的車隊顏色
- ✅ 分析圖表使用正確的車隊配色
- ✅ 控制台輸出覆寫套用日誌

---

## 🔍 驗證和測試

### CLI 測試

測試顏色配置生成：

```powershell
# 生成 2025 顏色配置
python f1_analysis_modular_main.py -f 98 -y 2025 --force

# 檢查生成的 JSON
Get-Content json/team_colors_2025_fastf1_*.json | ConvertFrom-Json | Select-Object -ExpandProperty data | Select-Object -ExpandProperty drivers | Where-Object { $_.PSObject.Properties.Name -contains "TSU" } | ConvertTo-Json
```

### GUI 測試

1. **啟動 GUI 並觀察控制台輸出：**
   ```
   [GUI_OVERRIDE] 🔄 更新車手: TSU: RB → Red Bull (2025 季中升級到主隊)
   [GUI_OVERRIDE] ✅ 共套用 2 個車手覆寫（2025 賽季）
   ```

2. **檢查車手顏色：**
   - 打開任何包含車手列表的分析模組（例如直線速度分析）
   - 驗證 TSU 顯示 Red Bull 顏色（#0600EF 藍色）
   - 驗證 LAW 顯示 RB 顏色（#364AA9 深藍色）

3. **測試分析功能：**
   ```powershell
   # 測試需要車隊分組的分析
   python f1_analysis_modular_main.py -f 34 -y 2025 -r Japan -s R  # 煞車分析
   python f1_analysis_modular_main.py -f 48 -y 2025 -r Japan -s R  # 速度分析
   ```

---

## 📊 覆寫影響範圍

| 模組 | 影響項目 | 說明 |
|------|----------|------|
| **CLI 顏色配置** | Function 98 | 生成的 `team_colors_*.json` 包含覆寫後的資料 |
| **GUI 車手列表** | 所有分析模組 | 車手名稱旁顯示正確的車隊顏色 |
| **分析圖表** | Matplotlib 圖表 | 車手資料點使用正確的車隊配色 |
| **車隊分組** | 煞車/速度分析 | 覆寫後的車手歸屬於正確的車隊組別 |
| **積分榜** | 車手/車隊積分榜 | 車手積分計入正確的車隊 |

---

## ⚠️ 注意事項

### 1. **JSON 格式嚴格**
   - 必須使用雙引號 `"`（不可用單引號 `'`）
   - 布林值小寫 `true` / `false`（不可用 `True` / `False`）
   - 陣列/物件最後一項不可有逗號

### 2. **team_slug 必須匹配**
   - 使用支援清單中的標準 slug
   - 全部小寫（`"red bull"` 不可寫成 `"Red Bull"`）

### 3. **覆寫持久性**
   - 覆寫會**永久套用**，直到你手動停用（`enabled: false`）
   - FastF1 更新後不會自動移除覆寫

### 4. **測試建議**
   - 先在測試賽季（例如 2024）驗證配置
   - 確認無錯誤後再套用到正式賽季

---

## 🛠️ 常見問題

### Q1: 覆寫沒有生效？

**檢查清單：**
```powershell
# 1. 驗證 JSON 格式
Get-Content config/driver_team_overrides.json | ConvertFrom-Json

# 2. 確認 enabled = true
Get-Content config/driver_team_overrides.json | ConvertFrom-Json | Select-Object -ExpandProperty overrides | Select-Object -ExpandProperty 2025 | Select-Object -ExpandProperty TSU

# 3. 強制重新生成顏色配置
python f1_analysis_modular_main.py -f 98 -y 2025 --force

# 4. 檢查控制台輸出是否有 [OVERRIDE] 日誌
```

### Q2: GUI 顯示錯誤顏色？

**解決步驟：**
1. 重啟 GUI（覆寫在啟動時載入）
2. 確認 CLI 已生成最新的 `team_colors_*.json`
3. 檢查 GUI 控制台是否有 `[GUI_OVERRIDE]` 日誌

### Q3: 如何暫時停用覆寫？

將 `enabled` 設為 `false`：

```json
{
  "TSU": {
    "enabled": false,  // ← 改這裡
    "team_slug": "red bull",
    ...
  }
}
```

---

## 📚 進階用法

### 批次覆寫多個車手

```json
{
  "overrides": {
    "2025": {
      "TSU": { "enabled": true, "team_slug": "red bull", "team_name": "Red Bull", ... },
      "LAW": { "enabled": true, "team_slug": "racing bulls", "team_name": "RB", ... },
      "ALO": { "enabled": true, "team_slug": "aston martin", "team_name": "Aston Martin", ... }
    }
  }
}
```

### 多賽季覆寫管理

```json
{
  "overrides": {
    "2024": {
      "LAW": { "enabled": true, "team_slug": "racing bulls", ... }
    },
    "2025": {
      "TSU": { "enabled": true, "team_slug": "red bull", ... },
      "LAW": { "enabled": false, "team_slug": "red bull", ... }
    }
  }
}
```

---

## 🔗 相關文件

- [Function 98 文件](https://github.com/WarmBed/F1-data-analyze/blob/main/docs/functions/F98_team_colors.md)
- [GUI 多國語言化](https://github.com/WarmBed/F1-data-analyze/blob/main/docs/gui_i18n.md)
- [API-ONLY 模式政策](https://github.com/WarmBed/F1-data-analyze/blob/main/.github/copilot-instructions.md#4-api-only-模式政策)

---

## 📝 版本歷史

| 版本 | 日期 | 變更內容 |
|------|------|----------|
| 1.0.0 | 2025-10-19 | 初始版本：車手-車隊手動覆寫系統 |

---

**如有問題，請查看系統日誌或聯繫技術支援。**
