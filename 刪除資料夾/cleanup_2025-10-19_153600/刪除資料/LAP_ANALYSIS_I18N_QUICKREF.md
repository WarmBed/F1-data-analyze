# Lap Analysis i18n 快速參考指南

## 🎯 一分鐘快速上手

### 什麼完成了？
✅ **8 個 Lap Analysis 模組** 現在支援 **中文/英文/日文** 圈數標籤顯示

### 如何測試？
```powershell
# 1. 啟動 GUI
python f1t_gui_main.py

# 2. 切換語言 (修改 core/gui_i18n.py 第 14 行)
self.current_language = 'en'  # zh/en/ja

# 3. 執行雙圈比較 (例如: HAM 第58圈 vs 第60圈)
# 預期結果:
# 中文: HAM - 第58圈 / HAM - 第60圈
# 英文: HAM - Lap 58 / HAM - Lap 60
# 日文: HAM - 58周目 / HAM - 60周目
```

---

## 📊 支援模組清單

| # | 模組 | 檔案 | 狀態 |
|---|------|------|------|
| 1 | Speed Analysis | `speed_analysis_chart_widget.py` | ✅ 完成 |
| 2 | Acceleration Analysis | `acceleration_analysis_chart_widget.py` | ✅ 完成 |
| 3 | Brake Analysis | `brake_analysis_chart_widget.py` | ✅ 完成 |
| 4 | RPM Analysis | `rpm_analysis_chart_widget.py` | ✅ 完成 |
| 5 | Gear Analysis | `gear_analysis_chart_widget.py` | ✅ 完成 |
| 6 | Throttle Analysis | `throttle_analysis_chart_widget.py` | ✅ 完成 |
| 7 | SpeedDiff Analysis | `speeddiff_analysis_chart_widget.py` | ⚠️ Import 已調整 |
| 8 | DistanceDiff Analysis | `distancediff_analysis_chart_widget.py` | ⚠️ Import 已調整 |

⚠️ **注意**: SpeedDiff/DistanceDiff 可能未實現雙圈比較功能，需進一步確認

---

## 🌍 多語言標籤格式

| 語言 | 標籤格式 | 範例 |
|------|---------|------|
| 中文 (zh) | `{driver} - 第{lap}圈` | HAM - 第58圈 |
| 英文 (en) | `{driver} - Lap {lap}` | HAM - Lap 58 |
| 日文 (ja) | `{driver} - {lap}周目` | HAM - 58周目 |

---

## 🔧 程式碼範例

### 新增翻譯鍵 (core/gui_i18n.py)
```python
'lap_label_format': {
    'zh': '{driver} - 第{lap}圈',
    'en': '{driver} - Lap {lap}',
    'ja': '{driver} - {lap}周目'
},
```

### 模組中使用方式
```python
# Import
from core.gui_i18n import tr

# 雙圈比較邏輯
if lap1 is not None and lap2 is not None and lap1 != lap2 and driver1_name == driver2_name:
    original_driver = driver1_name
    lap_format = tr('lap_label_format', '{driver} - 第{lap}圈')
    driver1_name = lap_format.format(driver=original_driver, lap=lap1)
    driver2_name = lap_format.format(driver=original_driver, lap=lap2)
```

---

## 🐞 常見問題

### Q1: 切換語言後標籤沒變？
**A**: 需關閉舊圖表並重新執行分析 (語言切換不會自動重繪)

### Q2: 出現 KeyError: 'lap_label_format'？
**A**: 確認 `core/gui_i18n.py` 行 196-200 包含翻譯鍵定義

### Q3: SpeedDiff/DistanceDiff 無法測試雙圈比較？
**A**: 這兩個模組可能尚未實現雙圈比較功能，屬於正常情況

---

## 📚 完整文件

- **測試指引**: `LAP_ANALYSIS_I18N_TEST_GUIDE.md`
- **實施報告**: `LAP_ANALYSIS_I18N_IMPLEMENTATION_COMPLETE.md`
- **原始計畫**: `LAP_ANALYSIS_I18N_FIX_PLAN.md`

---

**快速參考版本**: 1.0 | **建立日期**: 2025-01-XX
