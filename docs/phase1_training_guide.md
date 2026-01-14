# Phase 1：聯合訓練說明指南

## 📌 目標

為每個**車隊**、**賽道**和**輪胎配方**組合訓練精確的策略係數，取代現有的固定預設值，以提高策略預測的準確度。

---

## 📐 訓練公式模型

本模型使用多元線性回歸來擬合圈速，考慮以下四個主要變數：

$$
\text{LapTime}(t) = \text{Base} + (\alpha \times \text{Age} + 0.5 \times \beta \times \text{Age}^2) + (\gamma \times \text{Fuel}) + (\delta \times \text{LapNum})
$$

| 係數 | 符號 | 說明 | 單位 | 預期符號 |
|:---:|:---:|:---|:---:|:---:|
| **$\alpha$** | `base_rate` | 輪胎基礎衰退率 | s/lap | + (變慢) |
| **$\beta$** | `acceleration` | 輪胎衰退加速度 | s/lap² | + (變慢) |
| **$\gamma$** | `fuel_effect` | 燃油效應 | s/kg | - (變快) |
| **$\delta$** | `track_evo` | 賽道進化基準 | s/lap | - (變快) |

---

## 📊 訓練維度

訓練將針對以下組合分別產生係數：

*   **車隊 (Teams)**: 10 支車隊
*   **賽道 (Circuits)**: 23 條賽道
*   **輪胎 (Compounds)**: 3 種配方 (SOFT, MEDIUM, HARD)

總計約 **690** 組參數配置。

---

## 🔧 訓練腳本使用說明

訓練腳本位於：`CLI_modules/cli/prediction/train_strategy_coefficients.py`

### 環境準備

確保已安裝必要的 Python 套件：

```bash
pip install fastf1 scikit-learn pandas numpy
```

### 執行訓練

#### 1. 完整訓練模式
訓練 2023-2025 年的數據，並保留 Abu Dhabi 作為測試集。

```bash
python -m CLI_modules.cli.prediction.train_strategy_coefficients \
    --years 2023 2024 2025 \
    --test-year 2025 \
    --test-races "Abu Dhabi" "Qatar"
```

#### 2. 快速測試模式
僅使用 2025 年數據進行快速測試。

```bash
python -m CLI_modules.cli.prediction.train_strategy_coefficients \
    --years 2025 \
    --test-year 2025 \
    --test-races "Abu Dhabi"
```

### 參數說明

| 參數 | 預設值 | 說明 |
|:---|:---|:---|
| `--years` | 2023 2024 2025 | 訓練使用的年份列表 |
| `--test-year` | 2025 | 用於驗證準確度的年份 |
| `--test-races` | Abu Dhabi, Qatar | 從訓練集中排除並用於測試的比賽名稱 |
| `--output` | `config/team_strategy_coefficients.json` | 訓練結果輸出路徑 |
| `--cache-dir` | `fastf1_cache` | FastF1 緩存目錄 |

---

## 📁 輸出結果格式

訓練完成後將產生 JSON 檔案，結構如下：

```json
{
  "version": "1.0",
  "description": "車隊+賽道+輪胎維度的策略係數",
  "teams": {
    "Red Bull Racing": {
      "circuits": {
        "Abu_Dhabi": {
          "compounds": {
            "SOFT": {
              "base_rate": 0.095, 
              "acceleration": 0.003,
              "r2_score": 0.85,
              "sample_count": 120
            },
            "MEDIUM": { ... },
            "HARD": { ... }
          },
          "fuel_effect_per_kg": -0.031,
          "track_evolution_baseline": -0.022
        }
      }
    }
  }
}
```

---

## 🔄 系統整合更新需求

為了應用訓練結果，系統需進行以下更新：

### 1. API 層 (`api/routers/config.py`)
*   新增 `/team-strategy-coefficients` API 端點，發布訓練好的 JSON 數據。

### 2. GUI 層 (`driver_strategy.py`)
*   修改初始化邏輯，載入 `team_strategy` 配置。
*   預測時優先查詢特定車隊與賽道的係數，若無則回退至通用設定。

---

## ✅ 執行檢核表

- [x] 建立訓練腳本 `train_strategy_coefficients.py`
- [ ] 執行數據收集與模型訓練
- [ ] 驗證模型準確率 (MAE improvement)
- [ ] 部署 JSON 配置檔
- [ ] 更新 API 與 GUI 程式碼
