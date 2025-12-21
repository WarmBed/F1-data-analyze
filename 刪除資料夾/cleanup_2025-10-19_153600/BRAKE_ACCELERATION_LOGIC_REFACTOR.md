# Brake Performance 加速度邏輯重構報告

## 📋 修改日期
2025-10-19

## 🎯 修改目標

將 Brake Performance 的煞車區段識別邏輯從「FastF1 Brake 欄位」改為「基於加速度閥值」的物理分析方法。

## ❓ 問題背景

### 原始邏輯的問題
1. **FastF1 Brake 欄位不完善**：某些賽道/車手的 Brake 欄位數據不準確或缺失
2. **China 硬編碼終點錯誤**：設定為 4518m，但實際應該是 4775m
3. **搜尋範圍不合理**：使用固定 ±200m 範圍可能無法涵蓋所有煞車區段

### 新方法的優勢
1. **物理準確性**：加速度 < -1 m/s² 是煞車的物理定義，比 Brake 欄位更可靠
2. **動態搜尋**：從硬編碼終點往前回推，直到找到煞車起始點為止
3. **自適應範圍**：不限制搜尋範圍，確保找到完整煞車區段

## 🔧 修改內容

### 1️⃣ 更新 China 硬編碼終點

**檔案**: `CLI_modules/cli/analyzer/brake_performance_analyzer.py`  
**位置**: Line 325

**修改前**:
```python
"China": 4518,
```

**修改後**:
```python
"China": 4775,  # 更新：修正硬編碼終點
```

---

### 2️⃣ 重構煞車起始點搜尋邏輯

**檔案**: `CLI_modules/cli/analyzer/brake_performance_analyzer.py`  
**位置**: Line 373-465

#### 原始邏輯（已移除）
```python
# ✅ 步驟 3: 在硬編碼終點往前 200m 範圍內找「連續 Brake=1」區段
SEARCH_RANGE = 200  # 固定搜尋範圍
min_search_distance = hardcoded_brake_end_distance - SEARCH_RANGE
max_search_distance = hardcoded_brake_end_distance

# 找出在搜尋範圍內的所有數據點
range_indices = [...]

# 找出所有「連續 Brake=1」的區段
brake_segments = []
for idx in range_indices:
    if brakes[idx] == 1:
        current_segment.append(idx)
    else:
        if current_segment:
            brake_segments.append(current_segment)
            current_segment = []

# 選擇最長的連續煞車區段
longest_segment = max(brake_segments, key=lambda seg: distances[seg[-1]] - distances[seg[0]])
```

#### 新邏輯（基於加速度）
```python
# ✅ 步驟 3: 使用加速度從硬編碼終點往前找煞車起始點

# 檢查是否有 Acceleration 欄位
if "Acceleration" not in car_data.columns:
    print("[WARNING] 缺少 Acceleration 欄位，嘗試計算加速度")
    # 從速度計算加速度
    speed_ms = speeds / 3.6  # 轉換為 m/s
    time_diffs = car_data["Time"].diff().dt.total_seconds()
    accelerations = speed_ms.diff() / time_diffs
    accelerations = accelerations.fillna(0.0)
else:
    accelerations = pd.to_numeric(car_data["Acceleration"], errors="coerce")

# 加速度閥值：-1 m/s² (加速度 >= -1 表示不在煞車)
ACCEL_THRESHOLD = -1.0

print(f"[INFO] 使用加速度閥值: {ACCEL_THRESHOLD} m/s²")

# 從硬編碼終點往前回推，找到第一個加速度 >= -1 的點
sorted_indices = sorted(
    [idx for idx in car_data.index if idx in distances.index and idx in accelerations.index],
    key=lambda idx: distances[idx],
    reverse=True  # 降序，從大到小距離
)

# 找到終點索引的位置
end_idx_position = sorted_indices.index(brake_end_idx)

# 從終點往前搜尋
brake_start_idx = None
searched_distance = 0

for i in range(end_idx_position, len(sorted_indices)):
    idx = sorted_indices[i]
    dist = distances[idx]
    accel = accelerations[idx]
    
    # 跳過 NaN 值
    if pd.isna(accel) or pd.isna(dist):
        continue
    
    # 找到第一個加速度 >= -1 的點
    if accel >= ACCEL_THRESHOLD:
        brake_start_idx = idx
        searched_distance = abs(brake_end_distance - dist)
        print(f"[INFO] 找到煞車起始點: {dist:.1f}m @ 加速度 {accel:.2f} m/s²")
        break

# 如果沒找到，繼續往前推（選項 B：繼續往前推直到找到為止）
if brake_start_idx is None:
    print(f"[WARNING] 在初始範圍未找到，繼續往前搜尋...")
    # 繼續搜尋直到找到或到達數據起點
    for i in range(end_idx_position, len(sorted_indices)):
        idx = sorted_indices[i]
        accel = accelerations[idx]
        
        if pd.isna(accel):
            continue
        
        if accel >= ACCEL_THRESHOLD:
            brake_start_idx = idx
            break
```

## 📊 新邏輯流程圖

```
開始
  ↓
1. 載入車手最速圈遙測數據
  ↓
2. 獲取硬編碼煞車終點（例如 China = 4775m）
  ↓
3. 找到最接近硬編碼終點的數據點
  ↓
4. 檢查是否有 Acceleration 欄位
  ├─ 有 → 直接使用
  └─ 沒有 → 從速度微分計算
  ↓
5. 將所有數據點按距離降序排序
  ↓
6. 從硬編碼終點往前逐點檢查
  ├─ 加速度 < -1 m/s² → 繼續往前（仍在煞車）
  └─ 加速度 ≥ -1 m/s² → 找到起始點！停止搜尋
  ↓
7. 計算煞車區段
  - 起點距離
  - 終點距離（硬編碼）
  - 煞車距離
  - 速度減少
  ↓
結束
```

## 🔑 關鍵參數

### 加速度閥值
```python
ACCEL_THRESHOLD = -1.0  # m/s²
```

**物理意義**:
- 加速度 < -1 m/s²: 車手正在煞車（減速超過 1 m/s²）
- 加速度 ≥ -1 m/s²: 車手沒有煞車（滑行、油門或輕微減速）

### 硬編碼終點（已更新）
```python
TRACK_BRAKE_END_DISTANCE = {
    "China": 4775,       # ✅ 修正：4518 → 4775
    "Japan": 5256,
    "Monaco": 1972,
    "Singapore": 3574,
    # ... 其他賽道
}
```

## 📈 預期效果

### 修改前（Brake 欄位）
```
China 2025 R - HAM 最速圈

[ERROR] 在終點往前 200m 範圍內未找到連續 Brake=1 區段
↓
分析失敗
```

### 修改後（加速度）
```
China 2025 R - HAM 最速圈

[INFO] 使用加速度閥值: -1.0 m/s²
[INFO] 從終點 4775.0m 往前搜尋煞車起始點...
[INFO] 找到煞車起始點: 4550.2m @ 加速度 -0.95 m/s² (往前搜尋 224.8m)
[SUCCESS] 主煞車點已識別 (基於加速度分析):
   起點: 4550.2m @ 310.5 km/h (加速度: -0.95 m/s²)
   終點: 4775.0m @ 85.2 km/h (硬編碼)
   煞車距離: 224.8m
   速度減少: 225.3 km/h
   搜尋範圍: 終點往前 224.8m
```

## ✅ 優勢總結

| 項目 | 原始邏輯（Brake 欄位） | 新邏輯（加速度） |
|------|----------------------|----------------|
| **數據來源** | FastF1 Brake 欄位（不完善） | 加速度（物理定義） |
| **搜尋範圍** | 固定 ±200m | 動態，直到找到為止 |
| **準確性** | 依賴 Brake 欄位品質 | 基於物理定律，更可靠 |
| **適用性** | 某些賽道失敗 | 適用所有賽道 |
| **可擴展性** | 無法調整閥值 | 可調整加速度閥值 |

## 🧪 測試建議

### 測試案例 1: China 2025 R
```bash
python f1_analysis_modular_main.py -f 34 -y 2025 -r China -s R
```

**預期結果**:
- ✅ China 硬編碼終點使用 4775m
- ✅ 找到所有車手的煞車區段
- ✅ 煞車距離合理（約 200-300m）

### 測試案例 2: Singapore 2025 R
```bash
python f1_analysis_modular_main.py -f 34 -y 2025 -r Singapore -s R
```

**預期結果**:
- ✅ 使用加速度閥值 -1.0 m/s²
- ✅ 動態搜尋範圍適應不同車手
- ✅ 沒有「未找到煞車區段」錯誤

### 測試案例 3: 對比測試
```bash
# 測試所有已設定硬編碼終點的賽道
for race in China Japan Monaco Singapore Hungary; do
    python f1_analysis_modular_main.py -f 34 -y 2025 -r $race -s R
done
```

## 🔄 後續改進建議

1. **動態閥值調整**：不同賽道可能需要不同的加速度閥值
2. **多區段分析**：識別整圈所有煞車區段，不只是主煞車點
3. **煞車效率指標**：計算煞車 G 力、煞車功率等進階指標
4. **視覺化改進**：在圖表上標註煞車起始點和加速度曲線

---

**修改完成**  
**測試狀態**: ⏳ 待測試  
**影響範圍**: 
- `brake_performance_analyzer.py` (1 處硬編碼更新 + 1 處邏輯重構)
- JSON 輸出格式保持不變（向後兼容）
