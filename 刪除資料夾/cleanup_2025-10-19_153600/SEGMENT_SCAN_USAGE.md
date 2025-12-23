# Segment 數據掃描腳本使用指南

## 📋 腳本功能

`scan_all_tracks_segment_data.py` 是一個全自動的賽道數據掃描工具，用於：
- 掃描指定賽季的所有賽道
- 檢查每個賽道的 Segment 加速數據覆蓋率
- 生成詳細的統計報告
- 可選：自動生成缺失的數據

## 🚀 快速開始

### 基本用法

```powershell
# 掃描 2024 賽季所有賽道（預設）
python scan_all_tracks_segment_data.py

# 掃描 2025 賽季
python scan_all_tracks_segment_data.py -y 2025

# 掃描排位賽數據
python scan_all_tracks_segment_data.py -s Q
```

### 進階用法

```powershell
# 自動生成缺失的數據（⚠️ 會耗時很長！）
python scan_all_tracks_segment_data.py --generate

# 導出詳細報告到 JSON 檔案
python scan_all_tracks_segment_data.py --export report_2024.json

# 組合使用
python scan_all_tracks_segment_data.py -y 2025 --generate --export report_2025.json
```

## 📊 輸出說明

### 終端輸出

掃描過程會顯示：

```
🏁 Round 03: Japan
--------------------------------------------------------------------------------
   📂 找到檔案: all_drivers_straight_line_speed_2025_Japan_R.json
   ✅ 覆蓋率: 100.0% (20/20)
```

**狀態圖標**：
- ✅ **100% 覆蓋率** - 所有車手都有完整的 Segment 數據
- ⚠️  **80-99% 覆蓋率** - 大部分車手有數據，少數缺失
- ❌ **< 80% 覆蓋率** - 多數車手缺失數據
- 🚫 **未找到 JSON** - 該賽道尚未生成數據

### 統計摘要

掃描結束後會顯示：

```
================================================================================
📊 統計摘要
================================================================================

📋 總賽事數: 24

✅ 完美覆蓋率 (100%): 1 場
   • Japan

⚠️  良好覆蓋率 (80-99%): 0 場

❌ 較低覆蓋率 (< 80%): 1 場
   • Australia: 0.0%

🚫 缺失數據: 22 場
   • China
   • Bahrain
   ...

🎯 整體成功率: 4.2% (1/24)
```

### JSON 報告

使用 `--export` 選項會生成詳細的 JSON 報告：

```json
{
  "scan_info": {
    "year": 2025,
    "session": "R",
    "total_races": 24
  },
  "results": [
    {
      "round": 3,
      "race": "Japan",
      "json_path": "json/all_drivers_straight_line_speed_2025_Japan_R.json",
      "status": "success",
      "total": 20,
      "has_data": 20,
      "no_data": 0,
      "coverage": 100.0,
      "drivers_with_data": [...],
      "drivers_without_data": []
    }
  ]
}
```

## 🔧 命令列參數

| 參數 | 說明 | 預設值 | 範例 |
|------|------|--------|------|
| `-y`, `--year` | 賽季年份 | 2024 | `-y 2025` |
| `-s`, `--session` | 會話類型 | R | `-s Q` |
| `--generate` | 自動生成缺失數據 | False | `--generate` |
| `--export` | 導出報告到檔案 | - | `--export report.json` |

### 會話類型選項

- `R` - 正賽（Race）
- `Q` - 排位賽（Qualifying）
- `FP1` - 第一次練習賽
- `FP2` - 第二次練習賽
- `FP3` - 第三次練習賽
- `Sprint` - 衝刺賽

## ⚠️ 注意事項

### 關於 `--generate` 選項

**警告**：使用 `--generate` 會自動執行 CLI 生成所有缺失的數據：
- ⏰ **耗時極長**：24 場賽事可能需要 1-2 小時
- 💾 **需要大量存儲**：每場賽事約 20-30 KB
- 🌐 **需要網路連接**：需要從 FastF1 API 下載數據
- 📊 **可能失敗**：部分賽事可能因數據不可用而失敗

**建議**：
- 首次使用時不要加 `--generate`，先查看哪些賽道缺失數據
- 手動生成特定賽道：
  ```powershell
  python f1_analysis_modular_main.py -f 48 -y 2025 -r Japan -s R
  ```
- 再次掃描查看結果：
  ```powershell
  python scan_all_tracks_segment_data.py -y 2025
  ```

### JSON 格式相容性

腳本支援三種 JSON 格式：
1. **雙層嵌套**：`{"data": {"data": {"driver_speeds": [...]}}}`（Australia 格式）
2. **單層嵌套**：`{"data": {"driver_speeds": [...]}}`（Japan 格式）
3. **舊格式**：`{"drivers": [...]}`（早期格式）

### 賽道名稱

腳本使用 FastF1 的國家名稱作為賽道名稱：
- ✅ 正確：`Japan`, `Australia`, `United Kingdom`
- ❌ 錯誤：`Suzuka`, `Albert Park`, `Silverstone`

## 📈 使用場景

### 場景 1：驗證時間反轉修正效果

```powershell
# 重新生成數據
python f1_analysis_modular_main.py -f 48 -y 2025 -r Japan -s R

# 掃描驗證覆蓋率
python scan_all_tracks_segment_data.py -y 2025

# 預期結果：Japan 應該顯示 100% 覆蓋率
```

### 場景 2：批次測試多個賽道

```powershell
# 手動生成 3 個賽道
python f1_analysis_modular_main.py -f 48 -y 2024 -r Bahrain -s R
python f1_analysis_modular_main.py -f 48 -y 2024 -r Saudi Arabia -s R
python f1_analysis_modular_main.py -f 48 -y 2024 -r Australia -s R

# 掃描驗證
python scan_all_tracks_segment_data.py -y 2024

# 導出報告
python scan_all_tracks_segment_data.py -y 2024 --export report_2024_test.json
```

### 場景 3：完整賽季數據生成（謹慎使用）

```powershell
# ⚠️ 警告：這將花費 1-2 小時！
python scan_all_tracks_segment_data.py -y 2024 --generate --export report_2024_full.json
```

## 🐛 故障排除

### 問題 1：找不到 JSON 檔案

**症狀**：
```
🏁 Round XX: XXX
--------------------------------------------------------------------------------
   ⚠️  未找到 JSON 檔案
```

**解決方案**：
1. 手動生成該賽道的數據
2. 檢查 `json/` 目錄中的檔名格式
3. 確認年份、賽道名稱和會話類型正確

### 問題 2：覆蓋率 0%

**症狀**：
```
   ❌ 覆蓋率: 0.0% (0/20)
   🚫 缺失數據車手: VER, HAM, LEC, ...
```

**原因**：
- 數據在時間反轉修正之前生成
- 所有車手的 `segment_accel_time_seconds` 為 `null`

**解決方案**：
```powershell
# 重新生成該賽道的數據
python f1_analysis_modular_main.py -f 48 -y 2025 -r Australia -s R

# 再次掃描
python scan_all_tracks_segment_data.py -y 2025
```

### 問題 3：JSON 格式錯誤

**症狀**：
```
   ❌ 分析失敗: 無效的 JSON 格式（缺少 drivers 或 driver_speeds 欄位）
```

**原因**：
- JSON 檔案損壞或不完整
- 使用了不支援的 JSON 格式

**解決方案**：
1. 刪除該 JSON 檔案
2. 重新生成數據
3. 如果問題持續，檢查 CLI 輸出是否有錯誤

## 📝 範例工作流程

### 完整測試工作流程

```powershell
# 1. 掃描當前狀態
python scan_all_tracks_segment_data.py -y 2025

# 2. 生成 3 個測試賽道
python f1_analysis_modular_main.py -f 48 -y 2025 -r Japan -s R
python f1_analysis_modular_main.py -f 48 -y 2025 -r Australia -s R
python f1_analysis_modular_main.py -f 48 -y 2025 -r China -s R

# 3. 再次掃描並導出報告
python scan_all_tracks_segment_data.py -y 2025 --export report_test.json

# 4. 檢查報告
Get-Content report_test.json | ConvertFrom-Json | 
    Select-Object -ExpandProperty results | 
    Where-Object { $_.status -eq 'success' } | 
    Select-Object race, coverage, has_data, no_data
```

## 🎯 預期結果

### 時間反轉修正後

對於使用修正後邏輯生成的數據，預期結果：
- ✅ **覆蓋率 100%**：所有車手都有 Segment 數據
- ✅ **加速度範圍合理**：1.5 - 5.0 m/s²
- ✅ **時間範圍合理**：1.0 - 10.0 秒
- ✅ **無 null 值**：所有 Segment 欄位都有數值

### 舊數據（修正前）

對於修正前生成的數據：
- ❌ **覆蓋率 0-10%**：只有極少數車手有數據
- ❌ **大量 null 值**：大部分車手的 Segment 欄位為 null
- ⚠️  **需要重新生成**：刪除舊 JSON 並重新執行 CLI

## 🔗 相關文檔

- [F1T 專案概述](README.md)
- [CLI 模組文檔](CLI_modules/README.md)
- [Function 48 說明](F48_FIELD_EXPLANATION.md)
- [時間反轉修正報告](F48_SEGMENT_ACCELERATION_COMPLETE.md)
