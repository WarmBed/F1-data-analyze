# F1 2025 排位賽預測 - 特徵重要性總表 (V3.8)

> **生成時間**: 2025-11-06  
> **模型版本**: V3.8 (使用 F73 訓練、F74 預測)  
> **賽道數量**: 24  
> **數據來源**: XGBoost 模型特徵重要性分析

---

## 📊 總覽

本報告展示 2025 賽季所有 24 個賽道的 **前五項特徵重要性占比**，用於預測排位賽 (Q) 成績。

---

## 🏁 各賽道前五特徵

### 1. Australia (澳大利亞)
| 排名 | 特徵 | 重要性 |
|------|------|--------|
| 1 | `ideal_lap` | **36.14%** |
| 2 | `ideal_s2` | 15.47% |
| 3 | `max_speed_lap_ratio` | 14.25% |
| 4 | `fp3_relative_position` | 6.83% |
| 5 | `is_top_driver` | 6.03% |

### 2. China (中國)
| 排名 | 特徵 | 重要性 |
|------|------|--------|
| 1 | `speed_consistency` | **37.20%** |
| 2 | `ideal_s1` | 33.17% |
| 3 | `ideal_s2` | 15.16% |
| 4 | `max_speed` | 7.55% |
| 5 | `is_top_driver` | 6.92% |

### 3. Japan (日本)
| 排名 | 特徵 | 重要性 |
|------|------|--------|
| 1 | `ideal_lap` | **35.73%** |
| 2 | `fp3_relative_position` | 23.11% |
| 3 | `ideal_s3` | 9.58% |
| 4 | `is_top_driver` | 5.06% |
| 5 | `ideal_s2` | 4.23% |

### 4. Bahrain (巴林)
| 排名 | 特徵 | 重要性 |
|------|------|--------|
| 1 | `ideal_lap` | **26.20%** |
| 2 | `ideal_s1` | 22.48% |
| 3 | `max_speed_lap_ratio` | 14.58% |
| 4 | `ideal_s2` | 5.14% |
| 5 | `ideal_s3` | 4.80% |

### 5. Saudi Arabia (沙烏地阿拉伯)
| 排名 | 特徵 | 重要性 |
|------|------|--------|
| 1 | `high_speed_apex` | **18.67%** |
| 2 | `speed_consistency` | 12.46% |
| 3 | `sector_cv` | 11.24% |
| 4 | `s1_s2_ratio` | 9.06% |
| 5 | `mid_speed_apex` | 8.70% |

### 6. Miami (邁阿密)
| 排名 | 特徵 | 重要性 |
|------|------|--------|
| 1 | `ideal_s1` | **25.42%** |
| 2 | `ideal_s2` | 22.95% |
| 3 | `ideal_s3` | 6.69% |
| 4 | `max_speed_s2_ratio` | 6.55% |
| 5 | `ideal_lap` | 5.42% |

### 7. Emilia Romagna (艾米利亞-羅馬涅)
| 排名 | 特徵 | 重要性 |
|------|------|--------|
| 1 | `ideal_s2` | **38.40%** |
| 2 | `ideal_s1` | 20.84% |
| 3 | `speed_consistency` | 12.92% |
| 4 | `max_speed` | 5.38% |
| 5 | `max_speed_s2_ratio` | 5.22% |

### 8. Monaco (摩納哥)
| 排名 | 特徵 | 重要性 |
|------|------|--------|
| 1 | `fp3_gap_to_fastest` | **24.88%** |
| 2 | `ideal_s1` | 14.15% |
| 3 | `ideal_lap` | 13.91% |
| 4 | `fp3_relative_position` | 11.78% |
| 5 | `ideal_s2` | 7.21% |

### 9. Spain (西班牙)
| 排名 | 特徵 | 重要性 |
|------|------|--------|
| 1 | `ideal_s3` | **36.61%** |
| 2 | `low_speed_apex` | 28.09% |
| 3 | `ideal_lap` | 24.95% |
| 4 | `high_speed_apex` | 7.67% |
| 5 | `sector_cv` | 0.41% |

### 10. Canada (加拿大)
| 排名 | 特徵 | 重要性 |
|------|------|--------|
| 1 | `ideal_s1` | **30.20%** |
| 2 | `max_speed_lap_ratio` | 23.99% |
| 3 | `ideal_s2` | 11.10% |
| 4 | `mid_speed_apex` | 11.08% |
| 5 | `max_speed` | 5.57% |

### 11. Austria (奧地利)
| 排名 | 特徵 | 重要性 |
|------|------|--------|
| 1 | `s1_s2_ratio` | **19.74%** |
| 2 | `high_speed_apex` | 13.37% |
| 3 | `speed_consistency` | 12.32% |
| 4 | `low_speed_apex` | 11.56% |
| 5 | `ideal_s1` | 11.28% |

### 12. Great Britain (英國)
| 排名 | 特徵 | 重要性 |
|------|------|--------|
| 1 | `ideal_s1` | **61.77%** |
| 2 | `ideal_s2` | 31.74% |
| 3 | `ideal_s3` | 5.70% |
| 4 | `max_speed` | 0.25% |
| 5 | `max_speed_s2_ratio` | 0.15% |

### 13. Belgium (比利時)
| 排名 | 特徵 | 重要性 |
|------|------|--------|
| 1 | `ideal_s2` | **56.28%** |
| 2 | `ideal_s1` | 33.37% |
| 3 | `s1_s2_ratio` | 2.56% |
| 4 | `ideal_s3` | 2.23% |
| 5 | `max_speed` | 1.61% |

### 14. Hungary (匈牙利)
| 排名 | 特徵 | 重要性 |
|------|------|--------|
| 1 | `ideal_s2` | **23.66%** |
| 2 | `ideal_s3` | 16.99% |
| 3 | `max_speed_s2_ratio` | 14.07% |
| 4 | `fp3_relative_position` | 10.70% |
| 5 | `s2_lap_ratio` | 7.36% |

### 15. Netherlands (荷蘭)
| 排名 | 特徵 | 重要性 |
|------|------|--------|
| 1 | `mid_speed_apex` | **34.04%** |
| 2 | `ideal_s3` | 20.89% |
| 3 | `high_speed_apex` | 11.37% |
| 4 | `max_speed_s2_ratio` | 7.89% |
| 5 | `is_top_driver` | 6.72% |

### 16. Italy (義大利)
| 排名 | 特徵 | 重要性 |
|------|------|--------|
| 1 | `ideal_s2` | **58.83%** |
| 2 | `ideal_lap` | 13.36% |
| 3 | `ideal_s3` | 8.91% |
| 4 | `is_top_driver` | 7.41% |
| 5 | `fp3_relative_position` | 2.45% |

### 17. Azerbaijan (亞塞拜然)
| 排名 | 特徵 | 重要性 |
|------|------|--------|
| 1 | `ideal_lap` | **25.42%** |
| 2 | `ideal_s2` | 22.94% |
| 3 | `ideal_s1` | 19.76% |
| 4 | `fp3_gap_to_fastest` | 9.47% |
| 5 | `s2_lap_ratio` | 8.43% |

### 18. Singapore (新加坡)
| 排名 | 特徵 | 重要性 |
|------|------|--------|
| 1 | `ideal_s2` | **43.01%** |
| 2 | `ideal_s1` | 37.62% |
| 3 | `ideal_s3` | 11.66% |
| 4 | `s1_s2_ratio` | 2.37% |
| 5 | `max_speed_s2_ratio` | 1.79% |

### 19. United States (美國)
| 排名 | 特徵 | 重要性 |
|------|------|--------|
| 1 | `ideal_lap` | **32.65%** |
| 2 | `is_top_driver` | 23.84% |
| 3 | `ideal_s3` | 20.88% |
| 4 | `ideal_s2` | 7.94% |
| 5 | `max_speed_lap_ratio` | 3.67% |

### 20. Mexico (墨西哥)
| 排名 | 特徵 | 重要性 |
|------|------|--------|
| 1 | `max_speed_lap_ratio` | **14.26%** |
| 2 | `max_speed_s2_ratio` | 11.43% |
| 3 | `ideal_s2` | 9.86% |
| 4 | `ideal_lap` | 9.02% |
| 5 | `fp3_relative_position` | 8.14% |

### 21. Brazil (巴西)
| 排名 | 特徵 | 重要性 |
|------|------|--------|
| 1 | `low_speed_apex` | **81.22%** |
| 2 | `ideal_s1` | 6.32% |
| 3 | `high_speed_apex` | 2.46% |
| 4 | `speed_consistency` | 1.86% |
| 5 | `sector_cv` | 1.20% |

### 22. Las Vegas (拉斯維加斯) 🔴 數據警告

| 排名 | 特徵 | 重要性 | 備註 |
|------|------|--------|------|
| 1 | `mid_speed_apex` | **100.00%** | ⚠️  異常：單一特徵主導 |
| 2-17 | *(其他 16 個特徵)* | **0.00%** | ⚠️  無有效貢獻 |

**🚨 數據質量警告**：
- **訓練樣本不足**：僅 40 筆樣本（其他賽道通常 60-80 筆）
- **模型 R² = 0.0182**：接近 0，表示模型**無法學習有效模式**
- **已重新訓練 (500 trials)**：問題仍然存在，非訓練 bug
- **結論**：此賽道的特徵重要性數據**不具參考價值**

> **建議**：等待 2024-2025 賽季數據累積後重新訓練。Las Vegas 為新賽道（2023 首辦），歷史數據不足導致模型無法產生可靠預測。詳見 [Las Vegas 訓練異常報告](LAS_VEGAS_TRAINING_ANOMALY_REPORT.md)

### 23. Qatar (卡達)
| 排名 | 特徵 | 重要性 |
|------|------|--------|
| 1 | `ideal_s2` | **39.68%** |
| 2 | `ideal_s1` | 30.12% |
| 3 | `ideal_lap` | 8.52% |
| 4 | `ideal_s3` | 4.80% |
| 5 | `max_speed_s2_ratio` | 4.50% |

### 24. Abu Dhabi (阿布達比)
| 排名 | 特徵 | 重要性 |
|------|------|--------|
| 1 | `fp3_gap_to_fastest` | **36.40%** |
| 2 | `ideal_lap` | 19.82% |
| 3 | `fp3_relative_position` | 18.74% |
| 4 | `ideal_s3` | 11.17% |
| 5 | `max_speed_lap_ratio` | 2.55% |

---

## 🔍 特徵名稱說明

### 理想圈速相關
- `ideal_lap` - 理想單圈時間
- `ideal_s1` / `ideal_s2` / `ideal_s3` - 各分段理想時間

### 速度相關
- `max_speed` - 最高速度
- `max_speed_lap_ratio` - 最高速度與單圈時間比率
- `max_speed_s2_ratio` - 最高速度與 S2 時間比率
- `speed_consistency` - 速度一致性

### 彎角性能
- `high_speed_apex` - 高速彎角頂點速度
- `mid_speed_apex` - 中速彎角頂點速度
- `low_speed_apex` - 低速彎角頂點速度

### FP3 練習賽相關
- `fp3_gap_to_fastest` - FP3 與最快圈速的差距
- `fp3_relative_position` - FP3 相對位置

### 分段比例
- `s1_s2_ratio` - S1 與 S2 時間比
- `s2_lap_ratio` - S2 佔單圈時間比例
- `sector_cv` - 分段時間變異係數

### 車手屬性
- `is_top_driver` - 是否為頂尖車手標記

---

## 📈 關鍵洞察

### 最重要的特徵類型
1. **理想圈速系列** (`ideal_*`) - 在多數賽道佔主導地位
2. **分段時間** - 特別是 S1 和 S2
3. **速度一致性** - 在部分賽道（如中國）非常關鍵
4. **FP3 表現** - 在摩納哥和阿布達比特別重要

### 特殊賽道特徵
- **Great Britain**: `ideal_s1` (61.77%) 和 `ideal_s2` (31.74%) 幾乎決定一切
- **Belgium & Italy**: `ideal_s2` 重要性極高 (>56%)
- **Brazil**: `low_speed_apex` (81.22%) 佔絕對主導
- **Las Vegas**: 數據異常，需要重新檢查

---

**報告生成**: 2025-11-06  
**數據來源**: `models/track_specific_v3.8/*.pkl`  
**模型版本**: V3.8
