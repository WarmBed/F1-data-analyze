# F48 賽道加速段起點硬編碼配置指南

**更新日期**: 2025-10-15  
**目的**: 修正加速度計算錯誤（如 STR 加速度顯示 2.93 m/s²，實際應為 7.80 m/s²）

---

## 📋 問題背景

### 原問題
- **公式計算起點**：`calculated_start = max_speed_distance - (track_straight_length - 100)`
- **問題**：某些車手的最高速度位置較晚，導致計算出的起點錯過了低速加速段
- **範例**：STR 在 754m 有 110 km/h，但公式計算起點為 3420m（此時已 235 km/h）

### 解決方案
使用**硬編碼**的賽道加速段起點，替代不準確的公式計算。

---

## 🚀 使用流程

### 步驟 1: 生成賽道數據

```powershell
# 執行 CLI 生成 JSON 數據
python f1_analysis_modular_main.py -f 48 -y 2025 -r China -s R
```

### 步驟 2: 測量加速段起點

**方法 A: 使用測量工具（推薦）** ⭐

```powershell
# 執行測量工具
python tools/measure_track_acceleration_start.py -y 2025 -r China -s R
```

**輸出範例**：
```
【統計摘要】
  最早起點: 754.0m (STR)
  最晚起點: 1200.0m (OCO)
  平均起點: 980.5m

【建議的加速段起點】
  建議起點: 704m
  計算方式: 最早起點 (754.0m) - 50m 緩衝

【複製到 TRACK_ACCELERATION_START_DISTANCE】
    "China": 704,  # 建議值：最早起點 - 50m 緩衝
```

**方法 B: 手動從 GUI 測量**

1. 在 GUI 中打開速度圖
2. 找到主直線段的起點（綠色虛線標註）
3. 記錄該位置的距離值（例如：3096m）

### 步驟 3: 填入硬編碼字典

編輯 `CLI_modules/cli/analyzer/all_drivers_straight_line_speed.py`

找到 `TRACK_ACCELERATION_START_DISTANCE` 字典（約 Line 1106）：

```python
TRACK_ACCELERATION_START_DISTANCE = {
    # 已測試賽道（填入實際值）：
    "China": 704,           # 從測量工具獲得的建議值
    
    # 未測試賽道（暫時留空）：
    # "Azerbaijan": None,
    # "Japan": None,
    # ...
}
```

**注意**：
- 移除 `None` 並填入實際數值
- 數值單位為米（m）
- 可以是整數或浮點數

### 步驟 4: 重新生成數據並驗證

```powershell
# 強制重新生成（覆蓋舊數據）
python f1_analysis_modular_main.py -f 48 -y 2025 -r China -s R --force

# 執行測試腳本檢查 STR 加速度
python tools/test_china_acceleration_start.py
```

**預期結果**：
```
✅ 使用硬編碼起點: 704.0m
📍 加速段搜索範圍: 704.0m → 4720.0m (來源: 硬編碼)

【STR 車手加速度檢查】
  加速度: 7.80 m/s²
  ✅ 加速度正常（預期: 7.80 m/s²）
```

### 步驟 5: 重複其他賽道

對每個賽道重複步驟 1-4：

```powershell
# Azerbaijan
python f1_analysis_modular_main.py -f 48 -y 2025 -r Azerbaijan -s R
python tools/measure_track_acceleration_start.py -r Azerbaijan
# 填入字典 → 驗證

# Japan
python f1_analysis_modular_main.py -f 48 -y 2025 -r Japan -s Q
python tools/measure_track_acceleration_start.py -r Japan -s Q
# 填入字典 → 驗證
```

---

## 📊 硬編碼字典格式

### 完整範例

```python
TRACK_ACCELERATION_START_DISTANCE = {
    # 格式：賽道名稱: 起點距離（米）
    
    # 已測試賽道（2025 賽季數據）
    "China": 704,           # 測量值：754m - 50m 緩衝
    "Azerbaijan": 3385,     # Baku 超長直線
    "Japan": 3800,          # 日本站
    "Monaco": 5000,         # 短直線，起點較晚
    "Monza": 3500,          # 義大利站
    
    # 未測試賽道（暫時留空或使用公式計算）
    # "Singapore": None,
    # "Hungary": None,
    # "Zandvoort": None,
    # ...
}
```

### 字典規則

1. **賽道名稱格式**：
   - 使用官方英文名稱
   - 首字母大寫（例如：`"China"` 不是 `"china"`）
   - 與 CLI 參數 `-r` 的值一致

2. **起點距離值**：
   - 單位：米（m）
   - 類型：整數或浮點數
   - 範圍：通常 500-5000m（視賽道而定）

3. **註釋說明**：
   - 建議添加註釋說明測量方式或來源
   - 範例：`"China": 704,  # 測量工具建議值（2025-10-15）`

---

## 🔍 調試與驗證

### 查看調試輸出

執行 CLI 時會顯示：

```
✅ 使用硬編碼起點: 704.0m
📍 加速段搜索範圍: 704.0m → 4720.0m (來源: 硬編碼)
🏁 最高速度位置: 4520.0m
```

或

```
⚠️  使用公式計算起點: 3420.0m
💡 建議: 在 TRACK_ACCELERATION_START_DISTANCE 中添加 'China' 的硬編碼值
```

### 驗證加速度是否修正

**修正前**（公式計算）：
```json
{
  "driver": "STR",
  "avg_acceleration_100_300_ms2": 2.93,  ❌ 錯誤
  "acceleration_100_300_start_distance": 3420.0
}
```

**修正後**（硬編碼起點）：
```json
{
  "driver": "STR",
  "avg_acceleration_100_300_ms2": 7.80,  ✅ 正確
  "acceleration_100_300_start_distance": 754.0
}
```

### 驗證公式

```python
# 手動驗證加速度計算
Δv = (310 - 110) / 3.6 = 55.56 m/s
Δt = 7.119 秒（從 JSON 讀取）
a = 55.56 / 7.119 = 7.80 m/s² ✅
```

---

## 🛠️ 工具腳本說明

### measure_track_acceleration_start.py

**用途**：分析賽道數據，提供建議的起點距離

**使用方法**：
```powershell
python tools/measure_track_acceleration_start.py -y 2025 -r China -s R
```

**參數**：
- `-y, --year`：年份（預設: 2025）
- `-r, --race`：賽道名稱（必填）
- `-s, --session`：會話類型（預設: R）

**輸出**：
- 所有車手的加速起點位置
- 統計摘要（最早/最晚/平均）
- 建議的硬編碼值
- 可直接複製的字典條目

---

### test_china_acceleration_start.py

**用途**：快速測試 China 站的配置

**使用方法**：
```powershell
python tools/test_china_acceleration_start.py
```

**輸出**：
- China 站的起點分析
- STR 車手的加速度檢查
- 是否需要設定硬編碼起點

---

## 📝 賽道清單（待填入）

| 賽道名稱 | 硬編碼起點 | 測試狀態 | 備註 |
|---------|----------|---------|------|
| China | 704 | ✅ 已測試 | 測量工具建議值 |
| Azerbaijan | ? | ⏳ 待測試 | Baku 超長直線 |
| Japan | ? | ⏳ 待測試 | |
| Monaco | ? | ⏳ 待測試 | 短直線 |
| Singapore | ? | ⏳ 待測試 | |
| Hungary | ? | ⏳ 待測試 | |
| Zandvoort | ? | ⏳ 待測試 | |
| Saudi Arabia | ? | ⏳ 待測試 | |
| Monza | ? | ⏳ 待測試 | 長直線 |
| Spa | ? | ⏳ 待測試 | |
| Silverstone | ? | ⏳ 待測試 | |
| Austria | ? | ⏳ 待測試 | |
| Canada | ? | ⏳ 待測試 | |
| Miami | ? | ⏳ 待測試 | |
| Las Vegas | ? | ⏳ 待測試 | 長直線 |
| Qatar | ? | ⏳ 待測試 | |
| Abu Dhabi | ? | ⏳ 待測試 | |
| Bahrain | ? | ⏳ 待測試 | |
| Australia | ? | ⏳ 待測試 | |
| United States | ? | ⏳ 待測試 | |
| Mexico | ? | ⏳ 待測試 | |
| Brazil | ? | ⏳ 待測試 | |
| Spain | ? | ⏳ 待測試 | |
| Emilia Romagna | ? | ⏳ 待測試 | Imola |

---

## ⚠️ 注意事項

### 1. 賽道名稱一致性
確保硬編碼字典中的賽道名稱與 CLI 參數 `-r` 的值完全一致。

### 2. 不同賽季可能需要不同起點
如果賽道配置改變（例如：賽道改建），可能需要為不同年份設定不同的起點。

### 3. 優先級
- 硬編碼值 > 公式計算
- 如果字典中有該賽道，系統會優先使用硬編碼值
- 如果沒有，系統會回退到公式計算並顯示警告

### 4. 驗證建議
每次填入新的硬編碼值後：
1. 重新生成該賽道的數據（使用 `--force`）
2. 檢查至少 3-5 位車手的加速度是否合理
3. 驗證加速時間是否在預期範圍內

---

## 🎯 FAQ

**Q: 為什麼不使用自動計算？**  
A: 因為不同車手的最高速度位置不同，公式計算可能錯過低速段。手動測量更準確。

**Q: 每個賽道都必須填入硬編碼值嗎？**  
A: 不是必須的。如果不填，系統會使用公式計算。但強烈建議填入，以確保數據準確性。

**Q: 起點距離的精確度要求？**  
A: 建議精確到整數米（m）。±50m 的誤差通常不會影響結果。

**Q: 如何知道硬編碼值是否正確？**  
A: 檢查所有車手的加速度是否在合理範圍內（2-8 m/s²），且加速時間合理（5-20 秒）。

**Q: 測量工具建議的起點是否一定正確？**  
A: 測量工具提供的是參考值（最早起點 - 50m）。您可以根據實際情況調整。

---

## 📞 問題回報

如果遇到問題，請提供：
1. 賽道名稱、年份、會話
2. 調試輸出（顯示使用硬編碼還是公式計算）
3. 異常車手的加速度數據
4. 測量工具的輸出

---

**文件版本**: 1.0  
**最後更新**: 2025-10-15  
**作者**: GitHub Copilot
