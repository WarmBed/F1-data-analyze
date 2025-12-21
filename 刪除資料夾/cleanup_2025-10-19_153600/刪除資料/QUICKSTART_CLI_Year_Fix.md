# CLI 年份修復快速指南

## ✅ 修復完成

CLI 現在支援 **2020-2025** 年份範圍（原本僅支援 2024-2025）

---

## 🚀 立即測試

### 測試原始問題（2023 年日本站）
```powershell
python f1_analysis_modular_main.py -f 5 -y 2023 -r Japan -s R
```

**修復前**: ❌ `error: invalid choice: '2023' (choose from 2024, 2025)`  
**修復後**: ✅ 正常執行分析

---

## 📋 可用命令範例

### 歷史賽季分析（2020-2023）

```powershell
# 2020 年奧地利站正賽
python f1_analysis_modular_main.py -f 1 -y 2020 -r Austria -s R

# 2021 年摩納哥站排位賽
python f1_analysis_modular_main.py -f 2 -y 2021 -r Monaco -s Q

# 2022 年日本站速度分析
python f1_analysis_modular_main.py -f 13 -y 2022 -r Japan -s R -d VER

# 2023 年巴林站車手比較
python f1_analysis_modular_main.py -f 13 -y 2023 -r Bahrain -s R -d VER -d2 LEC
```

### 批量日曆查詢

```powershell
# 查詢所有年份（2020-2025）
python f1_analysis_modular_main.py -f 99

# 查詢特定歷史年份
python f1_analysis_modular_main.py -f 99 -y 2022
```

---

## 🔍 邊界值測試

```powershell
# ❌ 2019 應拒絕（超出範圍）
python f1_analysis_modular_main.py -f 99 -y 2019
# 預期錯誤: invalid choice: '2019' (choose from 2020, ..., 2025)

# ✅ 2020 應接受（最小值）
python f1_analysis_modular_main.py -f 99 -y 2020

# ✅ 2025 應接受（最大值）
python f1_analysis_modular_main.py -f 99 -y 2025

# ❌ 2026 應拒絕（超出範圍）
python f1_analysis_modular_main.py -f 99 -y 2026
# 預期錯誤: invalid choice: '2026' (choose from 2020, ..., 2025)
```

---

## 📊 系統狀態

| 組件 | 支援年份 | 狀態 |
|------|---------|------|
| **CLI 參數解析** | 2020-2025 | ✅ **已修復** |
| **API 服務器** | 2020-2025 | ✅ 已修復 |
| **GUI 日曆** | 2020-2025 | ✅ 已修復 |
| **功能 -f99** | 2020-2025 | ✅ 正常 |

**完全一致**: CLI、API、GUI 現在統一支援相同的年份範圍！

---

## ⚠️ 注意事項

- 某些歷史賽事可能缺少完整遙測數據
- 2020 年因疫情僅有 17 場賽事
- 首次查詢歷史數據可能需要下載時間

---

## 📚 相關文檔

- 詳細修復報告: `FIX_REPORT_CLI_Year_Limit_Removed.md`
- API 修復報告: `FIX_REPORT_API_Year_Limit_Removed.md`
- GUI 修復報告: `FIX_REPORT_GUI_Calendar_Multi_Year_Support.md`

---

**修復狀態**: ✅ 完成並可立即使用  
**無需重啟任何服務** 🎉
