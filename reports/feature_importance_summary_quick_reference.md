# F1 2025 特徵重要性快速參考總表

**模型**: V3.8 (F73/F74)  
**生成時間**: 2025-11-06

## 各賽道前五特徵占比

| 賽道 | 特徵1 | 占比 | 特徵2 | 占比 | 特徵3 | 占比 | 特徵4 | 占比 | 特徵5 | 占比 |
|------|-------|------|-------|------|-------|------|-------|------|-------|------|
| Australia | ideal_lap | 36.14% | ideal_s2 | 15.47% | max_speed_lap_ratio | 14.25% | fp3_relative_position | 6.83% | is_top_driver | 6.03% |
| China | speed_consistency | 37.20% | ideal_s1 | 33.17% | ideal_s2 | 15.16% | max_speed | 7.55% | is_top_driver | 6.92% |
| Japan | ideal_lap | 35.73% | fp3_relative_position | 23.11% | ideal_s3 | 9.58% | is_top_driver | 5.06% | ideal_s2 | 4.23% |
| Bahrain | ideal_lap | 26.20% | ideal_s1 | 22.48% | max_speed_lap_ratio | 14.58% | ideal_s2 | 5.14% | ideal_s3 | 4.80% |
| Saudi Arabia | high_speed_apex | 18.67% | speed_consistency | 12.46% | sector_cv | 11.24% | s1_s2_ratio | 9.06% | mid_speed_apex | 8.70% |
| Miami | ideal_s1 | 25.42% | ideal_s2 | 22.95% | ideal_s3 | 6.69% | max_speed_s2_ratio | 6.55% | ideal_lap | 5.42% |
| Emilia Romagna | ideal_s2 | 38.40% | ideal_s1 | 20.84% | speed_consistency | 12.92% | max_speed | 5.38% | max_speed_s2_ratio | 5.22% |
| Monaco | fp3_gap_to_fastest | 24.88% | ideal_s1 | 14.15% | ideal_lap | 13.91% | fp3_relative_position | 11.78% | ideal_s2 | 7.21% |
| Spain | ideal_s3 | 36.61% | low_speed_apex | 28.09% | ideal_lap | 24.95% | high_speed_apex | 7.67% | sector_cv | 0.41% |
| Canada | ideal_s1 | 30.20% | max_speed_lap_ratio | 23.99% | ideal_s2 | 11.10% | mid_speed_apex | 11.08% | max_speed | 5.57% |
| Austria | s1_s2_ratio | 19.74% | high_speed_apex | 13.37% | speed_consistency | 12.32% | low_speed_apex | 11.56% | ideal_s1 | 11.28% |
| Great Britain | ideal_s1 | 61.77% | ideal_s2 | 31.74% | ideal_s3 | 5.70% | max_speed | 0.25% | max_speed_s2_ratio | 0.15% |
| Belgium | ideal_s2 | 56.28% | ideal_s1 | 33.37% | s1_s2_ratio | 2.56% | ideal_s3 | 2.23% | max_speed | 1.61% |
| Hungary | ideal_s2 | 23.66% | ideal_s3 | 16.99% | max_speed_s2_ratio | 14.07% | fp3_relative_position | 10.70% | s2_lap_ratio | 7.36% |
| Netherlands | mid_speed_apex | 34.04% | ideal_s3 | 20.89% | high_speed_apex | 11.37% | max_speed_s2_ratio | 7.89% | is_top_driver | 6.72% |
| Italy | ideal_s2 | 58.83% | ideal_lap | 13.36% | ideal_s3 | 8.91% | is_top_driver | 7.41% | fp3_relative_position | 2.45% |
| Azerbaijan | ideal_lap | 25.42% | ideal_s2 | 22.94% | ideal_s1 | 19.76% | fp3_gap_to_fastest | 9.47% | s2_lap_ratio | 8.43% |
| Singapore | ideal_s2 | 43.01% | ideal_s1 | 37.62% | ideal_s3 | 11.66% | s1_s2_ratio | 2.37% | max_speed_s2_ratio | 1.79% |
| United States | ideal_lap | 32.65% | is_top_driver | 23.84% | ideal_s3 | 20.88% | ideal_s2 | 7.94% | max_speed_lap_ratio | 3.67% |
| Mexico | max_speed_lap_ratio | 14.26% | max_speed_s2_ratio | 11.43% | ideal_s2 | 9.86% | ideal_lap | 9.02% | fp3_relative_position | 8.14% |
| Brazil | low_speed_apex | 81.22% | ideal_s1 | 6.32% | high_speed_apex | 2.46% | speed_consistency | 1.86% | sector_cv | 1.20% |
| Las Vegas | mid_speed_apex | 100.00% | ideal_s1 | 0.00% | ideal_s2 | 0.00% | ideal_s3 | 0.00% | ideal_lap | 0.00% |
| Qatar | ideal_s2 | 39.68% | ideal_s1 | 30.12% | ideal_lap | 8.52% | ideal_s3 | 4.80% | max_speed_s2_ratio | 4.50% |
| Abu Dhabi | fp3_gap_to_fastest | 36.40% | ideal_lap | 19.82% | fp3_relative_position | 18.74% | ideal_s3 | 11.17% | max_speed_lap_ratio | 2.55% |

## 關鍵統計

### 最高占比特徵
1. **Las Vegas** - `mid_speed_apex` (100.00%) ⚠️ 數據異常
2. **Brazil** - `low_speed_apex` (81.22%)
3. **Great Britain** - `ideal_s1` (61.77%)
4. **Italy** - `ideal_s2` (58.83%)
5. **Belgium** - `ideal_s2` (56.28%)

### 最常出現的特徵 (前5)
- `ideal_s2` - 出現於 13 個賽道的前五
- `ideal_lap` - 出現於 11 個賽道的前五
- `ideal_s1` - 出現於 11 個賽道的前五
- `ideal_s3` - 出現於 9 個賽道的前五
- `max_speed_lap_ratio` - 出現於 6 個賽道的前五

### 特殊賽道觀察
- **Monaco & Abu Dhabi**: FP3 練習賽表現極為重要
- **Great Britain & Belgium**: 分段理想時間幾乎決定一切
- **Brazil**: 低速彎角性能佔絕對主導
- **Saudi Arabia & Austria**: 特徵分散，無單一主導特徵
- **Las Vegas**: 需要重新檢查訓練數據

---

**完整報告**: `feature_importance_summary_v3.8_readable.md`  
**原始數據**: `feature_importance_summary_v3.8_20251106_072945.json`
