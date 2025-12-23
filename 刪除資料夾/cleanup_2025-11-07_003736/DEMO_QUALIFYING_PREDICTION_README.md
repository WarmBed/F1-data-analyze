# 排位賽預測 GUI Demo 系列
# Qualifying Prediction GUI Demo Suite

## 📋 概述

本系列包含 **5 個獨立的 GUI Demo**，展示排位賽預測功能的不同介面設計。所有 Demo 使用相同的模擬數據（Austria 2025），但採用不同的欄位組合和視覺化風格。

---

## 🎯 Demo 版本對比

| 版本 | 檔名 | 欄位數 | 特點 | 適合場景 |
|------|------|--------|------|----------|
| **V1 基礎版** | `demo_qualifying_prediction.py` | 6 欄 | 完整功能，平衡顯示 | 一般使用 ✅ |
| **V2 極簡版** | `demo_qualifying_prediction_v2_minimal.py` | 4 欄 | 快速查看，僅前 10 名 | 快速預覽 |
| **V3 詳細版** | `demo_qualifying_prediction_v3_detailed.py` | 10 欄 | 深度分析，包含 R²/MAE/樣本數 | 專業分析 |
| **V4 對比版** | `demo_qualifying_prediction_v4_comparison.py` | 8 欄 | v3.7 vs v3.8 模型對比 | 模型評估 |
| **V5 棒狀圖版** | `demo_qualifying_prediction_v5_barchart.py` | 7 欄 | 自定義 Delegate 繪製視覺化 | 視覺化展示 |

---

## 📊 V1 基礎版（推薦）

### 欄位設計
```
┌────┬─────┬────────────────┬────────────┬─────────────┬─────────┐
│排名│車手 │     車隊       │ 預測時間   │   信賴度    │ △ FP3  │
├────┼─────┼────────────────┼────────────┼─────────────┼─────────┤
│ 🥇1│ VER │ Red Bull Racing│ 1:04.523   │ ████ 98%    │ -0.120s │
│ 🥈2│ LEC │ Ferrari        │ 1:04.689   │ ███░ 95%    │ -0.180s │
│ 🥉3│ NOR │ McLaren        │ 1:04.712   │ ███░ 92%    │ -0.150s │
└────┴─────┴────────────────┴────────────┴─────────────┴─────────┘
```

### 特點
- ✅ **車隊顏色編碼**：背景色對應實際車隊配色
- ✅ **信賴度進度條**：基於 R² 值，漸變顏色（綠→黃→紅）
- ✅ **時間改善梯度**：△ FP3 使用顏色梯度（深綠→淺綠→黃→橙→紅）
- ✅ **獎牌圖示**：前三名顯示 🥇🥈🥉
- ✅ **統計面板**：底部顯示模型 R²、MAE、樣本數、平均改善

### 啟動方式
```powershell
python demo_qualifying_prediction.py
```

---

## 🚀 V2 極簡版

### 欄位設計
```
┌────┬─────┬────────────┬─────────────┐
│排名│車手 │ 預測時間   │   信賴度    │
├────┼─────┼────────────┼─────────────┤
│  1 │ VER │ 1:04.523   │  98%        │
│  2 │ LEC │ 1:04.689   │  95%        │
└────┴─────┴────────────┴─────────────┘
```

### 特點
- 🎯 **僅 4 欄**：排名、車手、預測時間、信賴度
- 🎯 **僅顯示前 10 名**：快速查看頂級車手
- 🎯 **極簡設計**：無車隊色、無改善色，純文字
- 🎯 **小視窗**：800x600，適合快速預覽

### 啟動方式
```powershell
python demo_qualifying_prediction_v2_minimal.py
```

---

## 🔬 V3 詳細版

### 欄位設計
```
┌────┬─────┬────────┬──────┬──────┬──────┬────┬────────────┬──────┬────┐
│排名│車手 │  車隊  │ FP3  │ 預測 │ △FP3 │信賴│    R²      │ MAE  │樣本│
├────┼─────┼────────┼──────┼──────┼──────┼────┼────────────┼──────┼────┤
│ 1  │ VER │Red Bull│64.643│64.523│-0.120│98% │R²=0.9234██ │1.823s│152 │
└────┴─────┴────────┴──────┴──────┴──────┴────┴────────────┴──────┴────┘
```

### 特點
- 📈 **10 欄完整數據**：包含所有技術指標
- 📈 **R² 進度條**：自定義 Delegate 繪製 R² 值 + 進度條
- 📈 **模型指標**：顯示 MAE、樣本數
- 📈 **FP3 對比**：顯示 FP3 原始時間
- 📈 **詳細統計**：平均 R²、平均 MAE

### 啟動方式
```powershell
python demo_qualifying_prediction_v3_detailed.py
```

---

## ⚖️ V4 對比版

### 欄位設計
```
┌────┬─────┬──────────┬──────────┬────────┬──────┬────────┬──────────┐
│排名│車手 │ v3.7 預測│ v3.8 預測│模型差異│ FP3  │實際 Q  │v3.8準確度│
├────┼─────┼──────────┼──────────┼────────┼──────┼────────┼──────────┤
│ 1  │ VER │ 64.643   │ 64.523   │-0.120s │64.643│ 64.512 │ ±0.011s  │
└────┴─────┴──────────┴──────────┴────────┴──────┴────────┴──────────┘
```

### 特點
- ⚖️ **模型對比**：v3.7 vs v3.8 預測結果
- ⚖️ **差異分析**：顯示兩模型預測差異
- ⚖️ **實際結果**：顯示實際排位賽時間（已完賽）
- ⚖️ **準確度評估**：v3.8 預測誤差
- ⚖️ **統計對比**：底部顯示兩模型的 MAE、R² 對比
- ⚖️ **改進百分比**：計算 v3.8 相對 v3.7 的改進

### 啟動方式
```powershell
python demo_qualifying_prediction_v4_comparison.py
```

---

## 🎨 V5 棒狀圖版

### 欄位設計
```
┌────┬─────┬────────┬────────────────────────┬──────────────┬────┬──────┐
│排名│車手 │  車隊  │     預測時間棒         │  FP3 對比棒  │信賴│ △FP3 │
├────┼─────┼────────┼────────────────────────┼──────────────┼────┼──────┤
│ 1  │ VER │Red Bull│████████████ 1:04.523   │ FP3  ███████ │98% │-0.120│
│    │     │        │                        │ 預測 ██████  │    │      │
└────┴─────┴────────┴────────────────────────┴──────────────┴────┴──────┘
```

### 特點
- 🎨 **自定義 Delegate**：TimeBarDelegate、ComparisonBarDelegate
- 🎨 **預測時間棒**：長度代表時間，顏色漸變（綠→黃→紅）
- 🎨 **FP3 對比雙棒**：上方紫色 FP3，下方綠色預測
- 🎨 **視覺化強**：直觀看出時間差異
- 🎨 **35px 行高**：給棒狀圖足夠空間

### 啟動方式
```powershell
python demo_qualifying_prediction_v5_barchart.py
```

---

## 🚀 快速啟動

### 方法 1：啟動器腳本（推薦）
```powershell
.\launch_prediction_demos.ps1
```
- 互動式選單
- 可選擇單一版本或啟動所有 Demo
- 彩色輸出，易於選擇

### 方法 2：直接執行
```powershell
# 啟動單一版本
python demo_qualifying_prediction.py

# 啟動所有版本
python demo_qualifying_prediction.py
python demo_qualifying_prediction_v2_minimal.py
python demo_qualifying_prediction_v3_detailed.py
python demo_qualifying_prediction_v4_comparison.py
python demo_qualifying_prediction_v5_barchart.py
```

---

## 📐 架構設計參考

所有 Demo 均遵循以下設計原則：

### 1. **反幻覺編碼五原則**
- ✅ 禁止幻覺編碼：所有代碼基於實際檢查的模組實現
- ✅ 模組資料夾優先：參考 `ideal_lap_ranking_table`、`all_drivers_straight_line_speed_analysis`
- ✅ 通用模組優先：遵循 `UniversalDataLoader` 架構模式
- ✅ 多國語言化：支援 `tr()` 翻譯（Demo 中未實現，正式版將實現）
- ✅ Logger 整合：print 輸出導向 log

### 2. **參考模組**
| 模組 | 參考內容 |
|------|----------|
| `ideal_lap_ranking_table_widget.py` | 表格基礎架構、欄位設計 |
| `all_drivers_straight_line_speed_table_widget.py` | 自定義 Delegate 棒狀圖 |
| `all_drivers_brake_performance_table_widget.py` | 進度條委託實現 |
| `pitstop_analysis_mdi.py` | 車隊顏色編碼、統計面板 |

### 3. **視覺化元素**
- **車隊顏色**：從 `color_palette_provider` 獲取
- **進度條**：QProgressBar 樣式化
- **自定義 Delegate**：QPainter 繪製棒狀圖
- **梯度顏色**：改善幅度、準確度、時間快慢

---

## 🎯 推薦使用場景

| 場景 | 推薦版本 | 原因 |
|------|----------|------|
| 一般使用者 | V1 基礎版 | 功能完整，資訊平衡 |
| 快速查看 | V2 極簡版 | 僅顯示關鍵資訊，快速載入 |
| 數據分析師 | V3 詳細版 | 包含所有技術指標，深度分析 |
| 模型開發者 | V4 對比版 | 評估模型改進效果 |
| 簡報展示 | V5 棒狀圖版 | 視覺化強，易於理解 |

---

## 📝 模擬數據說明

所有 Demo 使用相同的模擬數據：

- **賽道**：Austria（Red Bull Ring）
- **年份**：2025
- **會話**：Q（排位賽）
- **模型版本**：v3.8
- **車手數量**：15 位（V2 僅顯示前 10）
- **模型指標**：
  - R² = 0.8923
  - MAE = 2.534s
  - 樣本數 = 145
  - 平均改善 = -0.165s

### 模擬車手排名
1. VER (Red Bull) - 64.523s
2. LEC (Ferrari) - 64.689s
3. NOR (McLaren) - 64.712s
4. SAI (Ferrari) - 64.801s
5. PIA (McLaren) - 64.834s
... (共 15 位)

---

## 🔧 技術實現細節

### 信賴度計算（基於 R²）
```python
def calculate_confidence(model_r2: float) -> tuple:
    if model_r2 >= 0.90:
        return model_r2, "very_high", "████"  # 98%
    elif model_r2 >= 0.85:
        return model_r2, "high", "███░"       # 95%
    elif model_r2 >= 0.75:
        return model_r2, "medium", "██░░"     # 85%
    else:
        return model_r2, "low", "█░░░"        # 75%
```

### 時間改善顏色梯度
```python
def get_improvement_color(improvement: float) -> QColor:
    if improvement <= -0.18:       # 深綠色（最大改善）
        return QColor(0, 150, 0)
    elif improvement <= -0.15:     # 綠色
        return QColor(50, 200, 50)
    elif improvement <= -0.12:     # 淺綠
        return QColor(100, 255, 100)
    elif improvement <= -0.08:     # 黃綠
        return QColor(200, 255, 100)
    elif improvement <= -0.05:     # 黃色
        return QColor(255, 255, 100)
    elif improvement <= 0:         # 橙色
        return QColor(255, 200, 100)
    else:                          # 紅色（退步）
        return QColor(255, 100, 100)
```

---

## 🎨 深色主題

所有 Demo 統一使用 **Fusion 深色主題**：
- 主視窗背景：`#353535`
- 表格背景：`#232323`
- 交替行背景：`#2d2d2d`
- 文字顏色：白色 (`#FFFFFF`)
- 選中高亮：`#2a82da`

---

## 📌 下一步計畫

完成 Demo 確認後，將進行：

1. **擴展 CLI F73**：添加 `--predict` 參數支援
2. **實施 API 端點**：`POST /api/predict`
3. **創建正式 GUI 模組**：`modules/gui/qualifying_prediction/`
4. **整合翻譯系統**：使用 `tr()` 函數
5. **連接真實數據**：替換模擬數據為 API 調用

---

## ❓ FAQ

**Q: 為什麼有 5 個版本？**
A: 展示不同的介面設計，讓用戶選擇最適合的風格。

**Q: 哪個版本會成為正式版？**
A: 預計以 V1 基礎版為主，但會提供選項切換到其他風格。

**Q: 數據是真實的嗎？**
A: 目前是模擬數據，正式版將連接 v3.8 模型和 API。

**Q: 可以自訂欄位嗎？**
A: 正式版將支援欄位顯示/隱藏設定。

---

**作者**: F1T Team  
**日期**: 2025-11-05  
**版本**: 1.0.0  
**授權**: F1T 專案內部使用
