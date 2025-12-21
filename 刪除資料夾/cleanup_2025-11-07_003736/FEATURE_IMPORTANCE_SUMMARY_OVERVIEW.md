# F1 2025 特徵重要性分析報告總覽

**生成時間**: 2025-11-06 07:29  
**模型版本**: V3.8 (F73 訓練 / F74 預測)  
**分析賽道**: 24 個 (2025 賽季完整賽曆)

---

## 📋 報告文件

本次分析生成了以下報告文件：

### 1. **完整報告** (詳細版)
📄 `feature_importance_summary_v3.8_readable.md`

包含所有 24 個賽道的前五項特徵重要性，附帶：
- 詳細的特徵說明
- 關鍵洞察分析
- 特殊賽道說明

**適用場景**: 深入了解各賽道特徵分布

---

### 2. **快速參考表** (表格版)
📊 `feature_importance_summary_quick_reference.md`

一張大表格列出所有賽道的前五特徵，包含：
- 完整的特徵與占比對照
- 統計分析（最高占比、最常出現特徵）
- 特殊賽道觀察

**適用場景**: 快速查找某個賽道的特徵重要性

---

### 3. **TOP 1 特徵一覽** (摘要版)
🎯 `feature_importance_top1_overview.md`

只顯示每個賽道最重要的一項特徵，包含：
- 特徵類型分類統計
- 極端值賽道標記
- 關鍵洞察總結

**適用場景**: 快速掌握各賽道的核心預測因子

---

### 4. **原始 JSON 數據**
📦 `feature_importance_summary_v3.8_20251106_072945.json`

完整的機器可讀格式數據，包含：
- 所有賽道的前五特徵
- 元數據（模型版本、生成時間等）

**適用場景**: 進一步數據分析或程式化處理

---

## 🔑 核心發現

### 最重要的特徵類別

1. **分段理想時間** (50% 賽道)
   - `ideal_s1`, `ideal_s2`, `ideal_s3`
   - 平均重要性: 40.69%

2. **理想圈速** (25% 賽道)
   - `ideal_lap`
   - 平均重要性: 31.23%

3. **彎角性能** (17% 賽道)
   - `high_speed_apex`, `mid_speed_apex`, `low_speed_apex`
   - 平均重要性: 62.03%

4. **FP3 練習賽表現** (8% 賽道)
   - `fp3_gap_to_fastest`, `fp3_relative_position`
   - 平均重要性: 30.64%

---

## 🏆 特殊賽道亮點

### 極高占比賽道 (>50%)
- **Las Vegas**: `mid_speed_apex` (100.00%) ⚠️ 異常值
- **Brazil**: `low_speed_apex` (81.22%)
- **Great Britain**: `ideal_s1` (61.77%)
- **Italy**: `ideal_s2` (58.83%)
- **Belgium**: `ideal_s2` (56.28%)

### FP3 依賴型賽道
- **Monaco**: `fp3_gap_to_fastest` (24.88%)
- **Abu Dhabi**: `fp3_gap_to_fastest` (36.40%)

### 分散型賽道 (無單一主導)
- **Saudi Arabia**: 最高特徵僅 18.67%
- **Mexico**: 最高特徵僅 14.26%
- **Austria**: 最高特徵僅 19.74%

---

## ⚠️ 注意事項

1. **Las Vegas 數據異常**
   - `mid_speed_apex` 占 100.00%，其他特徵全為 0%
   - 建議重新檢查訓練數據或重新訓練此賽道模型

2. **特徵工程意義**
   - 分段理想時間 (`ideal_s*`) 是最普遍的預測因子
   - 建議在未來版本中優化這些特徵的計算方式

3. **賽道特性反映**
   - 特徵重要性反映了各賽道的實際特性
   - 例如：Brazil 的低速彎角重要性證實了 Interlagos 的賽道設計

---

## 📈 使用建議

### 查看順序
1. 先查看 `feature_importance_top1_overview.md` 了解整體概況
2. 使用 `feature_importance_summary_quick_reference.md` 快速查詢特定賽道
3. 深入閱讀 `feature_importance_summary_v3.8_readable.md` 了解詳細特徵說明

### 應用場景
- **模型優化**: 識別需要加強的特徵類型
- **賽道分析**: 理解各賽道的核心預測因子
- **特徵工程**: 發現新的特徵工程方向
- **預測調整**: 根據賽道類型調整預測策略

---

## 🔗 相關文件

- **模型訓練結果**: `v3.8_training_results.json`
- **訓練腳本**: `batch_train_all_tracks_v3.8.py`
- **預測腳本**: `f1_analysis_modular_main.py` (F74功能)
- **模型檔案**: `models/track_specific_v3.8/*.pkl`

---

**生成腳本**: `generate_feature_importance_summary.py`  
**最後更新**: 2025-11-06 07:29:45
