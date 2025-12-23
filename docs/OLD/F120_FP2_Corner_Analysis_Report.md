# F120 FP2 彎道全圈數分析報告

## 功能概述

**功能編號**: F120 (FP2 Corner All Laps Analysis)  
**分析賽事**: 2025 Abu Dhabi FP2  
**生成日期**: 2025-12-13

---

## 一、功能實現原理

### 1.1 分析目標

透過 FP2 練習賽數據，分析各車手在不同類型彎道的過彎速度，從而推斷車輛的空力設定特性：

| 彎道類型 | 速度範圍 | 下壓力關係 |
|----------|----------|------------|
| **低速彎** | < 80 km/h | 高下壓力 = 速度快（機械抓地力 + 下壓力優勢） |
| **中速彎** | 80-150 km/h | 綜合平衡指標 |
| **高速彎** | > 150 km/h | 低阻力 = 速度快（空氣動力效率優勢） |

### 1.2 技術架構

```
CLI 命令: python f1_analysis_modular_main.py -f 120 -y 2025 -r "Abu Dhabi" -s FP2

┌─────────────────────────────────────────────────────────────────┐
│                    F120 分析流程                                 │
├─────────────────────────────────────────────────────────────────┤
│  STEP 1: 載入賽道數據                                            │
│    └─ FastF1 API → 獲取 FP2 session 所有圈數                     │
│                                                                  │
│  STEP 2: 彎道分類                                                │
│    └─ 根據平均速度分為: 低速(2個) / 中速(7個) / 高速(7個)          │
│                                                                  │
│  STEP 3: 選擇代表性彎道                                          │
│    └─ 低速: T6 (avg=67.2 km/h)                                  │
│    └─ 中速: T5 (avg=104.2 km/h)                                 │
│    └─ 高速: T8 (avg=238.7 km/h)                                 │
│                                                                  │
│  STEP 4: Mode A 統一分析                                         │
│    └─ 分析所有 20 位車手在選定彎道的速度統計                       │
│                                                                  │
│  STEP 5: Mode B 分組分析                                         │
│    └─ Long Run / Quali Sim 分組統計                              │
│                                                                  │
│  STEP 6: 輸出 JSON 報告                                          │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 核心技術突破

#### 問題：FastF1 Distance 插值導致低速彎數據異常

原始問題：ANT 車手在 T6 低速彎顯示 **282 km/h**（應為 ~67 km/h）

**根本原因**：FastF1 的 `get_telemetry()` 方法使用 Distance 插值時，會在低速區段遺失數據點，導致跳躍到高速區段的數據。

#### 解決方案 A：使用原始 car_data

```python
def _get_speed_at_distance_v2(self, lap, target_distance: float, tolerance: float = 15.0) -> Optional[float]:
    """
    使用原始 car_data 而非 get_telemetry() 的 Distance 插值
    避免低速區段數據遺失問題
    """
    try:
        # 直接從 session.car_data 獲取該圈的遙測數據
        car_data = self.session.car_data.pick_driver(lap['Driver'])
        
        # 根據時間範圍過濾
        lap_start = lap['LapStartTime']
        lap_end = lap_start + lap['LapTime']
        lap_car_data = car_data[(car_data['Time'] >= lap_start) & 
                                 (car_data['Time'] <= lap_end)]
        
        # 計算累積距離並查找目標位置的速度
        # ...
    except:
        return None
```

#### 解決方案 B：中位數異常值過濾

```python
def _filter_outliers_by_median(self, speeds: List[float], corner_name: str, 
                                threshold: float = 2.0) -> Tuple[List[float], int]:
    """
    過濾偏離中位數超過 threshold 倍的異常值
    
    例如：median = 69 km/h, threshold = 2.0
    → 過濾掉 > 69 + 69*2 = 207 km/h 的值
    → 成功移除 254 km/h 和 221 km/h 異常值
    """
    if not speeds or len(speeds) < 3:
        return speeds, 0
    
    median = np.median(speeds)
    filtered = []
    outliers = []
    
    for speed in speeds:
        deviation = abs(speed - median)
        if deviation <= threshold * median:
            filtered.append(speed)
        else:
            outliers.append(speed)
    
    if outliers:
        print(f"[MEDIAN-FILTER] {corner_name}: 移除 {len(outliers)} 個異常值 "
              f"(median={median}, outliers={outliers})")
    
    return filtered, len(outliers)
```

### 1.4 數據修復結果

| 指標 | 修復前 | 修復後 |
|------|--------|--------|
| ANT T6 max | 282 km/h | **83 km/h** |
| ANT T6 median | ~69 km/h | 67 km/h |
| 異常圈數 | 8 | **0** |
| 過濾的異常值 | - | 254, 221 km/h (2個) |

---

## 二、分析結果

### 2.1 Abu Dhabi 2025 賽道彎道配置

| 彎道編號 | 類型 | 平均速度 | 用途 |
|----------|------|----------|------|
| **T6** | 低速彎 | 67.2 km/h | 下壓力指標 |
| **T5** | 中速彎 | 104.2 km/h | 平衡指標 |
| **T8** | 高速彎 | 238.7 km/h | 阻力指標 |

### 2.2 車手彎道速度排名

#### 低速彎 T6 排名（高下壓力指標）

| 排名 | 車手 | 中位數速度 | 平均速度 |
|------|------|------------|----------|
| 1 | HAM | 67 km/h | 67.31 km/h |
| 2 | ANT | 67 km/h | 68.00 km/h |
| 3 | HUL | 66 km/h | 63.62 km/h |
| 4 | OCO | 66 km/h | 61.64 km/h |
| 5 | BOR | 65 km/h | 64.80 km/h |

#### 高速彎 T8 排名（低阻力指標）

| 排名 | 車手 | 中位數速度 | 平均速度 |
|------|------|------------|----------|
| 1 | HAD | 228 km/h | 217.38 km/h |
| 2 | LEC | 226 km/h | 202.47 km/h |
| 3 | TSU | 225.5 km/h | 216.33 km/h |
| 4 | ALB | 225 km/h | 207.78 km/h |
| 5 | SAI | 225 km/h | 216.27 km/h |

#### 中速彎 T5 排名（平衡指標）

| 排名 | 車手 | 中位數速度 | 平均速度 |
|------|------|------------|----------|
| 1 | STR | 97.5 km/h | 94.75 km/h |
| 2 | BEA | 96 km/h | 94.67 km/h |
| 3 | SAI | 96 km/h | 95.47 km/h |
| 4 | GAS | 95 km/h | 89.85 km/h |
| 5 | ALO | 94.5 km/h | 91.41 km/h |

### 2.3 車隊空力特性分析

#### 高下壓力設定（低速彎優勢）

| 車手 | T6 低速 | T8 高速 | 分析 |
|------|---------|---------|------|
| **HAM** | 67 km/h | 221 km/h | 低速彎最快，Mercedes 高下壓設定 |
| **ANT** | 67 km/h | 205 km/h | 低速強但高速最弱，極端高下壓 |
| **HUL** | 66 km/h | 221 km/h | Haas 偏高下壓力設定 |
| **OCO** | 66 km/h | 224 km/h | Alpine 高下壓但高速不差 |

#### 低阻力設定（高速彎優勢）

| 車手 | T6 低速 | T8 高速 | 分析 |
|------|---------|---------|------|
| **HAD** | 60 km/h | 228 km/h | 最明顯的低阻力設定 |
| **LEC** | 58 km/h | 226 km/h | Ferrari 低阻力，低速彎最慢 |
| **TSU** | 62 km/h | 226 km/h | RB 偏低阻力設定 |
| **ALB** | 60 km/h | 225 km/h | Williams 低阻力設定 |
| **SAI** | 62 km/h | 225 km/h | Ferrari 確認低阻力取向 |

#### 平衡設定

| 車手 | T6 低速 | T8 高速 | 分析 |
|------|---------|---------|------|
| **VER** | 62 km/h | 224 km/h | Red Bull 平衡設定 |
| **NOR** | 63 km/h | 221 km/h | McLaren 平衡偏高下壓 |
| **PIA** | 63 km/h | 220 km/h | McLaren 確認平衡取向 |

### 2.4 車隊空力特性總結

| 車隊 | 空力特性 | 低速彎表現 | 高速彎表現 | 策略推測 |
|------|----------|------------|------------|----------|
| **Mercedes** | 高下壓力 | ⭐⭐⭐ 優秀 | ⭐⭐ 普通 | 針對賽道第二、三區段優化 |
| **Ferrari** | 低阻力 | ⭐ 較弱 | ⭐⭐⭐ 優秀 | 直線速度優先 |
| **Red Bull** | 平衡 | ⭐⭐ 普通 | ⭐⭐ 普通 | 全面性設定 |
| **McLaren** | 平衡偏高下壓 | ⭐⭐ 良好 | ⭐⭐ 普通 | 略偏彎道性能 |
| **Aston Martin** | 平衡 | ⭐⭐ 普通 | ⭐⭐ 普通 | 中規中矩 |
| **Alpine** | 高下壓力 | ⭐⭐⭐ 優秀 | ⭐⭐ 普通 | 彎道速度取向 |
| **Haas** | 高下壓力 | ⭐⭐⭐ 優秀 | ⭐⭐ 普通 | 偏重機械抓地力 |
| **RB** | 低阻力 | ⭐ 較弱 | ⭐⭐⭐ 優秀 | 直線速度優先 |
| **Williams** | 低阻力 | ⭐ 較弱 | ⭐⭐⭐ 優秀 | 直線速度優先 |
| **Kick Sauber** | 極端高下壓 | ⭐⭐⭐ 優秀 | ⭐ 較弱 | ANT 高速彎明顯劣勢 |

---

## 三、生成的圖表

### 3.1 圖表清單

| 圖表 | 檔案路徑 | 說明 |
|------|----------|------|
| Box Plot | `charts/f120/f120_box_plot.png` | 各車手三種彎道的速度分布箱形圖 |
| Violin Plot | `charts/f120/f120_violin_plot.png` | 速度分布密度小提琴圖 |
| Heatmap | `charts/f120/f120_heatmap.png` | 車手 × 彎道中位數速度熱力圖 |
| ANT T6 Analysis | `charts/f120/f120_ant_t6_analysis.png` | ANT T6 彎道專項分析 |

### 3.2 視覺化腳本

```bash
python visualize_f120_fp2.py
```

---

## 四、相關檔案

| 檔案 | 路徑 | 說明 |
|------|------|------|
| 分析模組 | `CLI_modules/cli/analyzer/fp2_corner_all_laps_analysis.py` | F120 核心分析邏輯 |
| JSON 報告 | `json/fp2_corner_all_laps_analysis_2025_Abu Dhabi_FP2.json` | 分析結果數據 |
| 視覺化腳本 | `visualize_f120_fp2.py` | 圖表生成腳本 |

---

## 五、使用方式

### CLI 執行

```powershell
# 執行 F120 分析
python f1_analysis_modular_main.py -f 120 -y 2025 -r "Abu Dhabi" -s FP2

# 生成視覺化圖表
python visualize_f120_fp2.py
```

### 參數說明

| 參數 | 說明 | 範例 |
|------|------|------|
| `-f` | 功能編號 | `120` |
| `-y` | 年份 | `2025` |
| `-r` | 賽事名稱 | `"Abu Dhabi"` |
| `-s` | 場次 | `FP2` |

---

## 六、結論

F120 FP2 彎道全圈數分析成功實現了以下目標：

1. **數據品質修復**：透過 `_get_speed_at_distance_v2()` 和 `_filter_outliers_by_median()` 解決了 FastF1 Distance 插值導致的異常數據問題

2. **空力特性分析**：根據低速彎與高速彎的速度對比，成功識別各車隊的空力設定取向

3. **視覺化呈現**：生成 Box Plot、Violin Plot、Heatmap 等多種圖表，直觀展示分析結果

4. **關鍵發現**：
   - Ferrari、RB、Williams 採用低阻力設定
   - Mercedes、Haas、Alpine 採用高下壓力設定
   - Red Bull、McLaren 採用平衡設定
