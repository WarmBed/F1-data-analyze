# F120彎道分析圖表 - 過濾數據視覺化報告

## 📊 圖表位置
- **Charts 1-3**: `charts/f120_5charts/f120_charts_1_3_corner_analysis.png`
- **Chart 4**: `charts/f120_5charts/f120_chart_4_corner_comparison.png`
- **Chart 5**: `charts/f120_5charts/f120_chart_5_aero_analysis.png`

## 🎨 視覺化方案

### 正常數據點
- **顏色**: Apex速度熱力圖 (紅→黃→綠)
- **邊框**: 黑色
- **標籤**: 黑色普通字體
- **圖例**: "Normal Data"

### 過濾數據點 (異常值替換為估算)
- **顏色**: 淺紫色 (#D8BFD8 - Thistle)
- **邊框**: 紫色
- **透明度**: 80%
- **層級**: zorder=3 (顯示在正常點上方)
- **標籤**: 紫色粗體字
- **圖例**: "Filtered (Estimated)"

## 🔍 過濾數據詳情

### 數據來源
- **賽事**: 2025 Abu Dhabi GP
- **會話**: FP2
- **總數據點**: 120 (20車手 × 3彎道 × 2數據/彎道)
- **過濾點數**: 2
- **過濾率**: 1.7%

### 被過濾的數據點

#### 1. ANT - T6 低速彎 Entry
- **原始數據**: 196.0 km/h
- **Apex速度**: 67.0 km/h
- **Entry/Apex比值**: 2.93
- **過濾閾值**: 2.0 (低速彎)
- **替換估算**: 90.5 km/h (67 × 1.35)
- **原因**: Entry速度異常高,可能是-50m採樣點落在直線上

#### 2. LAW - T8 高速彎 Exit
- **原始數據**: 238 km/h
- **Apex速度**: ~216 km/h
- **Exit/Apex比值**: 1.10
- **過濾閾值**: 1.1 (高速彎)
- **替換估算**: 238 km/h (剛好等於原值,邊界情況)
- **原因**: 高速彎出彎加速特別快,剛好觸發閾值

## 🎯 過濾邏輯

### 彎道類型閾值
```python
低速彎 (T6):
  - Entry/Apex < 2.0
  - Exit/Apex < 2.0
  - 估算係數: Entry=1.35x, Exit=1.40x

中速彎 (T5):
  - Entry/Apex < 1.5
  - Exit/Apex < 1.5
  - 估算係數: Entry=1.25x, Exit=1.20x

高速彎 (T8):
  - Entry/Apex < 1.2
  - Exit/Apex < 1.1
  - 估算係數: Entry=1.15x, Exit=1.10x
```

### 雙層過濾架構
1. **F120模組** (`fp2_corner_all_laps_analysis.py`):
   - 中位數濾波: 2.0倍中位數偏差
   - 行數: 335, 338, 341 (Mode A) 和 480, 483, 486 (Mode B)

2. **視覺化腳本** (`visualize_f120_5charts.py`):
   - 比值過濾: 基於Entry/Apex和Exit/Apex比值
   - 函數: `_filter_outlier_by_apex()` (行33-51)
   - 標記: 布林旗標 `{corner}_entry_filtered`, `{corner}_exit_filtered`

## 📈 數據品質指標

### 正常範圍參考 (Abu Dhabi FP2)
```
T6 低速彎 Entry/Apex比值:
  VER: 1.34 ✅
  NOR: 1.32 ✅
  BOR: 1.46 ✅
  HAD: 1.36 ✅
  GAS: 1.32 ✅
  ANT: 2.93 🔴 (過濾)
```

### 異常原因分析
**ANT的196 km/h Entry問題**:
- F120分析使用-50m位置作為Entry採樣點
- 某些單圈的-50m點可能落在T6前的直線段
- 導致Entry速度反映直線速度而非入彎速度
- 解決: 過濾後使用物理合理估算 (Apex×1.35)

## ✅ 實施清單

### 已完成修改
- [x] 添加過濾旗標到數據結構 (`low_entry_filtered` 等6個布林值)
- [x] 修改 `extract_corner_data()` 進行異常值檢測和標記
- [x] 重寫 `create_corner_scatter()` 支援雙色渲染
- [x] 更新 `create_chart_1_3()` 傳遞過濾旗標
- [x] 驗證ANT異常數據被正確過濾
- [x] 生成帶淺紫色標記的圖表

### 圖表覆蓋範圍
- [x] Chart 1: T6低速彎 (ANT Entry點顯示為紫色)
- [x] Chart 2: T5中速彎 (無異常點)
- [x] Chart 3: T8高速彎 (LAW Exit點顯示為紫色)
- [ ] Chart 4: 僅使用Apex數據,不需過濾標記
- [ ] Chart 5: 僅使用Apex數據,不需過濾標記

## 🔧 代碼位置

### 關鍵函數
1. **`_filter_outlier_by_apex()`** (行33-51)
   - 根據Entry/Apex或Exit/Apex比值過濾異常值
   - 返回None表示需要替換

2. **`extract_corner_data()`** (行53-180)
   - 從JSON提取數據並應用過濾
   - 設置6個布林旗標標記過濾點
   - 用估算值替換None

3. **`create_corner_scatter()`** (行182-240)
   - 接收 `entry_filtered` 和 `exit_filtered` 布林列表
   - 分離數據為 `normal_mask` 和 `filtered_mask`
   - 渲染兩個scatter系列 (正常+過濾)
   - 添加雙圖例

4. **`create_chart_1_3()`** (行242-291)
   - 提取6個過濾旗標列表
   - 為3個彎道分別調用散點圖函數

## 📝 使用說明

### 重新生成圖表
```powershell
python visualize_f120_5charts.py
```

### 驗證過濾數據
```powershell
python verify_filtered_data.py
```

### 檢查特定車手
```powershell
python check_ant_data.py
```

## 🎓 技術說明

### 為什麼需要過濾?
F1遙測數據的採樣位置可能因為:
1. 賽道幾何形狀變化
2. 車手走線差異
3. GPS定位誤差

導致-50m或+50m採樣點落在非預期位置,產生不合理的Entry/Exit速度。

### 為什麼用淺紫色?
- 紫色傳統上表示"警告但非錯誤"
- 淺色 (#D8BFD8) 提供良好可見性但不過於突兀
- 與紅黃綠熱力圖形成明顯對比
- 紫色邊框和粗體標籤進一步強化視覺區分

### 估算係數來源
基於F1低速/中速/高速彎的物理特性:
- **低速彎**: 大幅減速入彎,快速加速出彎 (Entry 1.35x, Exit 1.40x)
- **中速彎**: 中等減速,平穩加速 (Entry 1.25x, Exit 1.20x)
- **高速彎**: 輕微減速,緩慢加速 (Entry 1.15x, Exit 1.10x)

這些係數是經驗性的,基於正常車手的平均表現。
