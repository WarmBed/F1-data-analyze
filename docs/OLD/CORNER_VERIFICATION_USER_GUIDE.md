# 彎道一致性驗證工具 - 使用指南
## Corner Consistency Verification Tool - User Guide

---

## 📖 工具概述

此工具用於驗證 F1 彎道識別算法的穩定性和準確性，通過分析同一賽道多年的數據，檢查識別出的彎道位置是否一致。

### 核心功能

✅ **彎道自動識別**: 使用速度局部極小值檢測算法  
✅ **跨年度比較**: 比對 2022-2025 年的彎道位置  
✅ **一致性評分**: 計算彎道位置偏差和一致性分數  
✅ **視覺化報告**: 生成圖表和 JSON 報告  

---

## 🚀 快速開始

### 1. 單一賽道驗證

驗證美國站（已完成，結果優秀）:

```powershell
python scripts\corner_consistency_verification.py
```

**輸出**:
- JSON 報告: `json/corner_consistency/corner_consistency_United States_2022-2023-2024-2025.json`
- 視覺化圖表: `json/corner_consistency/corner_consistency_United States_2022-2023-2024-2025.png`

### 2. 測試其他賽道

修改 `corner_consistency_verification.py` 的 `main()` 函數：

```python
# 測試日本站（鈴鹿）
years = [2022, 2023, 2024, 2025]
race_name = "Japan"  # 改這裡！

report = verifier.compare_multi_year(years, race_name)
```

然後執行：

```powershell
python scripts\corner_consistency_verification.py
```

### 3. 批次測試多個賽道

使用多賽道驗證腳本：

```powershell
# 測試所有預設賽道（美國、日本、義大利、摩納哥、新加坡）
python scripts\multi_circuit_verification.py
```

或指定單一賽道：

```powershell
# 只測試日本站
python scripts\multi_circuit_verification.py Japan
```

---

## 📊 輸出報告解讀

### JSON 報告結構

```json
{
  "verification_type": "corner_consistency_multi_year",
  "race": "United States",
  "years_analyzed": [2022, 2023, 2024, 2025],
  "yearly_results": {
    "2022": {
      "corners_detected": 6,
      "corners": {
        "1": {
          "apex_distance": 659.88,  // 彎心位置 (m)
          "min_speed": 80.0,         // 最低速度 (km/h)
          "type": "低速彎"
        }
      }
    }
  },
  "consistency_analysis": {
    "consistency_score": 100.0,      // 一致性評分 (%)
    "matching_rate": 100.0,          // 匹配率 (%)
    "matched_corners": [...]         // 匹配的彎道詳情
  }
}
```

### 關鍵指標說明

#### 1. 一致性評分 (Consistency Score)
- **定義**: 位置偏差在容差內的彎道比例
- **容差**: 50 米
- **計算**: `一致彎道數 / 總彎道數 × 100%`
- **評級**:
  - 90-100%: ⭐⭐⭐⭐⭐ 優秀
  - 80-90%: ⭐⭐⭐⭐ 良好
  - 70-80%: ⭐⭐⭐ 中等
  - < 70%: ⚠️ 需要改進

#### 2. 匹配率 (Matching Rate)
- **定義**: 成功跨年匹配的彎道比例
- **計算**: `匹配彎道數 / 識別彎道總數 × 100%`
- **意義**: 評估算法在不同年份識別相同彎道的能力

#### 3. 位置偏差 (Position Deviation)
- **標準差 (Std Deviation)**: 彎道位置的離散程度
  - < 5 m: 非常穩定
  - 5-10 m: 穩定
  - > 10 m: 需要關注
- **最大偏差 (Max Deviation)**: 年度間最大的位置差異

---

## 🔧 進階配置

### 調整算法參數

在 `corner_consistency_verification.py` 的 `_identify_corners_from_speed()` 方法中：

```python
peaks, properties = find_peaks(
    -speeds,
    distance=30,     # 最小彎道間距（數據點）
                     # 增大 = 減少識別的彎道數
                     # 減小 = 增加識別的彎道數
    
    prominence=15    # 最小速度下降（km/h）
                     # 增大 = 只識別明顯的彎道
                     # 減小 = 識別更多輕微的彎道
)
```

### 修改容差範圍

在 `_compare_corner_positions()` 方法中：

```python
matching_tolerance = 50.0  # 改為 30.0 (更嚴格) 或 100.0 (更寬鬆)
```

### 添加新賽道測試

編輯 `multi_circuit_verification.py` 的 `TEST_CIRCUITS` 列表：

```python
TEST_CIRCUITS = [
    # ... 現有賽道 ...
    {
        'name': 'Spain',           # 賽道名稱（FastF1 格式）
        'years': [2022, 2023, 2024, 2025],
        'expected_corners': 16,    # 預期彎道數
        'circuit_type': 'Mixed'    # 賽道類型
    }
]
```

---

## 📈 美國站驗證結果（已完成）

### 驗證摘要

- **一致性評分**: 100.0% ⭐⭐⭐⭐⭐
- **匹配率**: 100.0%
- **識別彎道數**: 6 個（所有年份一致）
- **平均位置偏差**: 11.8 m

### 彎道位置穩定性

| 彎道 | 平均位置 | 標準差 | 評級 |
|------|---------|--------|------|
| 1    | 657 m   | 5.8 m  | ⭐⭐⭐ |
| 2    | 1,876 m | 5.1 m  | ⭐⭐⭐⭐ |
| 3    | 2,551 m | 2.0 m  | ⭐⭐⭐⭐⭐ 最穩定 |
| 4    | 3,750 m | 6.4 m  | ⭐⭐⭐ |
| 5    | 4,246 m | 6.4 m  | ⭐⭐⭐ |
| 6    | 5,294 m | 2.4 m  | ⭐⭐⭐⭐⭐ |

### 建議

✅ **算法已驗證可用於生產環境**  
可直接整合至 F55 彎道分析功能。

---

## 🛠️ 故障排除

### 問題 1: 無法載入數據

**症狀**: `Failed to load session data`

**解決方案**:
1. 檢查 FastF1 緩存: `f1_analysis_cache/`
2. 清除緩存重試: `rm -r f1_analysis_cache/*`
3. 確認網路連線（首次下載需要連網）

### 問題 2: 識別的彎道數量異常

**症狀**: 識別到 20+ 個彎道或 < 5 個彎道

**原因**: 算法參數不適合該賽道

**解決方案**:
```python
# 對於高速賽道（如 Monza），降低 prominence
prominence=10  # 原本 15

# 對於街道賽（如 Monaco），增加 distance
distance=40  # 原本 30
```

### 問題 3: 匹配率低

**症狀**: Matching Rate < 80%

**原因**: 彎道位置年度差異大或識別數量不一致

**解決方案**:
```python
# 放寬容差
matching_tolerance = 100.0  # 原本 50.0
```

---

## 📝 輸出檔案說明

### 檔案位置

所有輸出都在 `json/corner_consistency/` 目錄:

```
json/corner_consistency/
├── corner_consistency_United States_2022-2023-2024-2025.json
├── corner_consistency_United States_2022-2023-2024-2025.png
├── corner_consistency_Japan_2022-2023-2024-2025.json
├── corner_consistency_Japan_2022-2023-2024-2025.png
└── multi_circuit_summary_YYYYMMDD_HHMMSS.json
```

### 視覺化圖表內容

**圖表 1**: 彎道數量比較（柱狀圖）  
**圖表 2**: 彎道位置偏差（柱狀圖，綠色=一致，紅色=偏差過大）  
**圖表 3**: 彎道位置變化趨勢（折線圖）  
**圖表 4**: 一致性與匹配率評估（雙層餅圖）  

---

## 🎯 應用場景

### 1. 算法開發驗證

在開發或修改彎道識別算法後，使用此工具驗證:
- 識別結果是否穩定
- 不同年份數據是否一致
- 參數調整的影響

### 2. 賽道資料庫建立

為每個賽道建立標準彎道位置參考:
```json
{
  "United States": {
    "corners": [657, 1876, 2551, 3750, 4246, 5294],
    "verified_years": [2022, 2023, 2024, 2025],
    "consistency": 100.0
  }
}
```

### 3. 數據質量檢查

識別 FastF1 數據的異常:
- 某年數據缺失
- 遙測數據不完整
- 位置偏差過大（可能是賽道修改）

---

## 🔗 相關文檔

- **F55 彎道分析開發文件**: `docs/develop task/CLI develop task/F55_彎道分析_開發文件.md`
- **驗證報告**: `docs/CORNER_CONSISTENCY_VERIFICATION_REPORT.md`
- **源代碼**: `scripts/corner_consistency_verification.py`

---

## 📞 支援

如有問題或建議，請參考:
- **開發核心原則**: `.github/copilot-instructions.md`
- **專案 README**: `README.md`

---

**最後更新**: 2025-10-26  
**工具版本**: v1.0  
**驗證狀態**: ✅ 美國站驗證通過（100% 一致性）
