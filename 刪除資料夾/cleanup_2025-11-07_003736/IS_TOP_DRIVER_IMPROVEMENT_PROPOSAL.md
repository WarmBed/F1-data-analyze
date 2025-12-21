# `is_top_driver` 特徵改進方案

## 🚨 現有問題

### 當前實現（V3.8）

```python
# 硬編碼的頂尖車手列表
self.top_drivers = ['VER', 'HAM', 'LEC', 'NOR', 'PIA', 'SAI', 'RUS', 'PER']

# 計算特徵
df['is_top_driver'] = df['driver'].isin(self.top_drivers).astype(int)
```

### 問題分析

| 問題 | 影響 | 嚴重性 |
|------|------|--------|
| **硬編碼名單** | 每年都需手動更新 | 🔴 高 |
| **無法反映車手狀態變化** | 無法捕捉賽季中的實力變化 | 🟡 中 |
| **主觀選擇** | 缺乏客觀標準 | 🟡 中 |
| **車隊變動** | 2025 年 HAM → Ferrari，但名單未更新 | 🔴 高 |
| **新秀崛起** | 無法自動納入表現優異的新車手 | 🟡 中 |

## 💡 改進方案：基於積分排名的動態計算

### 核心概念

**使用「每場比賽前的車手積分排名」來動態判定頂尖車手**

- **客觀標準**：基於實際比賽成績積分
- **自動更新**：隨賽季進行自動調整
- **歷史一致**：回溯歷史數據時使用當時的積分榜

### 實現方案

#### 方案 A：前 N 名積分車手（推薦）

```python
def calculate_is_top_driver_dynamic(df: pd.DataFrame, top_n: int = 8) -> pd.DataFrame:
    """
    基於車手積分排名動態計算 is_top_driver
    
    Args:
        df: 包含 driver, year, round, points_before_race 的 DataFrame
        top_n: 前 N 名視為頂尖車手（預設 8）
    
    Returns:
        添加 is_top_driver 欄位的 DataFrame
    """
    df = df.copy()
    
    # 方法 1: 使用 "比賽前積分" (如果有此欄位)
    if 'points_before_race' in df.columns:
        # 每場比賽按積分排名取前 N 名
        df['is_top_driver'] = (
            df.groupby(['year', 'round'])['points_before_race']
            .rank(method='min', ascending=False) <= top_n
        ).astype(int)
    
    # 方法 2: 使用 "賽季總積分" (回溯歷史數據)
    else:
        # 取該賽季積分最高的前 N 名車手
        top_drivers_per_year = (
            df.groupby(['year', 'driver'])['points'].sum()
            .groupby(level=0)
            .nlargest(top_n)
            .index.get_level_values('driver')
        )
        
        df['is_top_driver'] = df.apply(
            lambda row: int(row['driver'] in top_drivers_per_year[row['year']]),
            axis=1
        )
    
    return df
```

#### 方案 B：積分閾值法

```python
def calculate_is_top_driver_threshold(df: pd.DataFrame, percentile: float = 0.7) -> pd.DataFrame:
    """
    基於積分百分位數判定頂尖車手
    
    Args:
        df: 包含 driver, points 的 DataFrame
        percentile: 積分超過此百分位的車手視為頂尖（預設 70%）
    
    Returns:
        添加 is_top_driver 欄位的 DataFrame
    """
    df = df.copy()
    
    # 計算每年的積分閾值
    threshold_per_year = (
        df.groupby('year')['points']
        .quantile(percentile)
    )
    
    df['is_top_driver'] = df.apply(
        lambda row: int(row['points'] >= threshold_per_year[row['year']]),
        axis=1
    )
    
    return df
```

### 數據需求

實現動態計算需要以下數據：

1. **每場比賽前的車手積分** (`points_before_race`)
   - 最理想的方案
   - 需要從 F1 API 或 FastF1 獲取歷史積分榜

2. **賽季總積分** (`season_total_points`)
   - 次佳方案
   - 可從現有數據回溯計算

3. **比賽回合數** (`round`)
   - 用於分組和排序

### 數據來源

系統已有車手積分榜模組：

```python
# 現有模組
from modules.gui.driver_standings import DriverStandingsMDI

# 可能的數據源
# 1. F1 官方 API（通過 OpenF1 或 Ergast）
# 2. FastF1 的 driver_standings
# 3. 本地 JSON 緩存（json/driver_standings_*.json）
```

## 📊 方案對比

| 特性 | 現有硬編碼 | 方案 A (前 N 名) | 方案 B (百分位) |
|------|-----------|-----------------|----------------|
| **客觀性** | ❌ 主觀 | ✅ 完全客觀 | ✅ 完全客觀 |
| **自動化** | ❌ 需手動更新 | ✅ 自動更新 | ✅ 自動更新 |
| **穩定性** | ✅ 固定 8 位 | ✅ 固定 N 位 | ⚠️ 數量可變 |
| **歷史一致** | ⚠️ 需回溯修正 | ✅ 使用當時排名 | ✅ 使用當時排名 |
| **實現難度** | ✅ 簡單 | 🟡 中等 | 🟡 中等 |
| **數據依賴** | ✅ 無 | ⚠️ 需積分數據 | ⚠️ 需積分數據 |

**推薦：方案 A（前 N 名積分車手）**

## 🔧 實施步驟

### Phase 1: 數據準備（1-2 天）

1. **檢查現有積分數據**
   ```bash
   # 檢查 driver_standings 模組的數據格式
   python -c "from modules.gui.driver_standings import *; print('模組已載入')"
   ```

2. **建立積分數據獲取函數**
   ```python
   def get_driver_points_before_race(year: int, round: int) -> dict:
       """獲取某場比賽前的車手積分"""
       # 實現從 F1 API 或本地緩存獲取積分
       pass
   ```

3. **回填歷史數據（2022-2024）**
   - 從 Ergast API 獲取歷史積分榜
   - 生成 `driver_points_history.json`

### Phase 2: 特徵重構（1 天）

1. **修改 `batch_train_all_tracks_v3.8.py`**
   ```python
   # 替換硬編碼部分
   - self.top_drivers = ['VER', 'HAM', ...]
   + self.top_n_drivers = 8  # 可配置參數
   
   # 修改特徵計算
   - df['is_top_driver'] = df['driver'].isin(self.top_drivers).astype(int)
   + df = self._calculate_is_top_driver_dynamic(df, self.top_n_drivers)
   ```

2. **新增動態計算方法**
   ```python
   def _calculate_is_top_driver_dynamic(self, df: pd.DataFrame, top_n: int) -> pd.DataFrame:
       # 實現方案 A 的邏輯
       pass
   ```

### Phase 3: 重新訓練（2-3 天）

1. **重新訓練所有賽道模型（V3.9）**
   ```bash
   python batch_train_all_tracks_v3.9.py
   ```

2. **驗證新特徵效果**
   - 對比 V3.8 vs V3.9 的性能
   - 檢查特徵重要性變化

3. **2025 預測驗證**
   ```bash
   python validate_v39_on_2025.py
   ```

### Phase 4: 文檔更新（1 天）

- 更新特徵說明文檔
- 記錄改進前後的對比
- 更新 API 使用指南

## 📈 預期效果

### 優勢

1. **自動化維護**
   - ✅ 無需每年手動更新車手名單
   - ✅ 自動反映車手狀態變化

2. **客觀性提升**
   - ✅ 基於實際成績，非主觀判斷
   - ✅ 消除人為偏見

3. **歷史數據一致性**
   - ✅ 回溯訓練時使用當時的積分榜
   - ✅ 不會因後見之明影響模型

4. **模型性能**
   - 🎯 預期：部分賽道的預測準確度提升
   - 🎯 特徵重要性可能更穩定

### 風險

1. **賽季初期不穩定**
   - ⚠️ 第 1-3 場比賽積分榜可能不準確
   - 💡 解決：前 3 場使用上一賽季積分榜

2. **數據依賴**
   - ⚠️ 需要可靠的積分數據來源
   - 💡 解決：本地緩存 + API 備援

3. **歷史數據缺失**
   - ⚠️ 2022 年前的積分數據可能不完整
   - 💡 解決：僅回填 2022-2024 年數據

## 🎯 實施計劃

### 短期（V3.9 - 1 週內）

- [ ] 檢查現有積分數據可用性
- [ ] 實現方案 A（前 8 名積分車手）
- [ ] 重新訓練 1-2 個賽道驗證效果
- [ ] 對比 V3.8 vs V3.9 性能

### 中期（V4.0 - 1 個月內）

- [ ] 全面重新訓練所有賽道
- [ ] 回填 2022-2024 歷史積分數據
- [ ] 整合到生產環境
- [ ] 更新所有文檔

### 長期（未來版本）

- [ ] 考慮多維度車手實力評估
  - 積分排名 (60%)
  - 近 3 場表現 (20%)
  - 車隊實力 (20%)
- [ ] 機器學習自動優化閾值

## 📋 待確認事項

1. **積分數據來源**
   - [ ] 確認 FastF1 是否提供歷史積分榜
   - [ ] 確認 Ergast API 的積分數據完整性
   - [ ] 檢查本地是否已有積分緩存

2. **歷史數據處理**
   - [ ] 決定是否回填 2022 年前的數據
   - [ ] 確認賽季初期（前 3 場）的處理策略

3. **性能基準**
   - [ ] 設定 V3.9 vs V3.8 的性能對比目標
   - [ ] 確認哪些賽道預期會有顯著改善

## 🔗 相關資源

- **Ergast API**: http://ergast.com/mrd/methods/standings/
- **FastF1 Standings**: https://docs.fastf1.dev/
- **現有模組**: `modules/gui/driver_standings/`

---

**提案日期：** 2025-11-06  
**提案版本：** V3.9 Feature Improvement  
**預計完成時間：** 1-2 週
