# 🏎️ FIA 文件下載與升級套件識別指南

## 📋 目錄
1. [系統概述](#系統概述)
2. [快速開始](#快速開始)
3. [使用場景](#使用場景)
4. [進階功能](#進階功能)
5. [升級套件識別邏輯](#升級套件識別邏輯)

---

## 系統概述

本系統提供兩個主要工具：

### 1. **FIA 文件下載器** (`fia_document_scraper.py`)
- 自動從 FIA 官網下載 F1 技術文件
- 智能分類文件類型（技術報告、處罰決定、賽事須知等）
- 識別與升級套件相關的文件

### 2. **升級套件追蹤器** (`upgrade_tracker.py`)
- 分析 PDF 技術文件，提取升級套件資訊
- 建立車隊升級資料庫
- 生成升級時間線和統計報告

---

## 快速開始

### 安裝依賴
```powershell
pip install requests beautifulsoup4 PyPDF2
```

### 基本使用流程

#### 步驟 1: 搜尋並下載文件
```powershell
# 列出 2025 年 Japan GP 的所有文件
python fia_document_scraper.py -y 2025 -r Japan --list-only

# 下載 Japan GP 的技術文件
python fia_document_scraper.py -y 2025 -r Japan -c technical -d

# 僅搜尋升級相關文件
python fia_document_scraper.py -y 2025 --upgrade-only --list-only

# 下載所有升級文件
python fia_document_scraper.py -y 2025 --upgrade-only -d
```

#### 步驟 2: 分析文件並追蹤升級
```powershell
# 分析單一 PDF 文件
python upgrade_tracker.py -a "fia_documents/technical/2025_japan_technical_report.pdf"

# 查看摘要
python upgrade_tracker.py -s

# 查詢特定車隊的升級
python upgrade_tracker.py -t "Red Bull Racing"

# 查詢特定分站的升級
python upgrade_tracker.py -r Japan

# 匯出 JSON 資料
python upgrade_tracker.py -e
```

---

## 使用場景

### 場景 1: 追蹤 2025 賽季所有升級

```powershell
# 1. 下載所有升級相關文件
python fia_document_scraper.py -y 2025 --upgrade-only -d

# 2. 批次分析所有下載的 PDF
Get-ChildItem fia_documents/upgrade/*.pdf | ForEach-Object {
    python upgrade_tracker.py -a $_.FullName
}

# 3. 生成升級報告
python upgrade_tracker.py -s
python upgrade_tracker.py -e
```

### 場景 2: 研究特定分站的技術升級

```powershell
# 1. 下載 Monaco GP 的技術文件
python fia_document_scraper.py -y 2025 -r Monaco -c technical -d

# 2. 分析文件
python upgrade_tracker.py -a "fia_documents/technical/2025_monaco_technical_report.pdf"

# 3. 查詢該分站的升級
python upgrade_tracker.py -r Monaco
```

### 場景 3: 對比兩支車隊的升級策略

```powershell
# 查詢 Red Bull 的升級
python upgrade_tracker.py -t "Red Bull Racing" > rbr_upgrades.txt

# 查詢 Ferrari 的升級
python upgrade_tracker.py -t "Ferrari" > fer_upgrades.txt

# 匯出完整資料進行分析
python upgrade_tracker.py -e
# → 查看 upgrade_data/upgrades_export.json
```

### 場景 4: 手動建立升級資料庫

```powershell
# 手動新增升級記錄（當 FIA 文件不可用時）
python upgrade_tracker.py --add "Red Bull Racing" "Japan" "front_wing" "aerodynamic" "新設計前翼提升下壓力"

python upgrade_tracker.py --add "Ferrari" "Monaco" "floor" "aerodynamic" "改良底板提升街道賽表現"

python upgrade_tracker.py --add "McLaren" "Singapore" "cooling" "mechanical" "高溫散熱升級"
```

---

## 進階功能

### 文件分類系統

下載的文件會自動分類到以下目錄：

```
fia_documents/
├── technical/          # 技術報告、技術指令
├── sporting/           # 處罰決定、賽事幹事文件
├── event/              # 賽事須知、賽道地圖
├── tire/               # Pirelli 輪胎分析
├── upgrade/            # 升級相關文件
└── other/              # 其他文件
```

### 升級識別關鍵字

系統使用以下關鍵字識別升級：

#### 空氣動力學 (Aerodynamic)
- front wing, rear wing, floor, diffuser, sidepod
- beam wing, bargeboard, nose, endplate

#### 機械 (Mechanical)
- suspension, brake duct, cooling, gearbox
- hydraulic, steering

#### 動力單元 (Power Unit)
- engine, MGU-K, MGU-H, turbo, ERS, battery

#### 其他
- weight reduction, reliability update, stiffness
- carbon fiber, composite

### JSON 資料結構

#### 升級記錄格式
```json
{
  "team": "Red Bull Racing",
  "team_code": "RBR",
  "component": "front wing",
  "category": "aerodynamic",
  "race": "Japan",
  "date": "2025-04-06",
  "source": "2025_japan_technical_report.pdf",
  "context": "red bull racing new front wing upgrade...",
  "detected_at": "2025-11-06T10:30:00"
}
```

#### 匯出資料格式
```json
{
  "export_date": "2025-11-06T10:30:00",
  "total_upgrades": 45,
  "by_team": {
    "Red Bull Racing": 8,
    "Ferrari": 7,
    "Mercedes": 6
  },
  "by_race": {
    "Bahrain": 5,
    "Japan": 8,
    "Monaco": 4
  },
  "by_category": {
    "aerodynamic": 25,
    "mechanical": 12,
    "power_unit": 8
  },
  "timeline": { ... },
  "all_upgrades": [ ... ]
}
```

---

## 升級套件識別邏輯

### 自動識別流程

1. **文件標題分析**
   - 搜尋關鍵字："new parts", "upgrade", "technical update", "development"
   - 匹配文件類型："technical directive", "technical report"

2. **PDF 內容解析**
   - 提取 PDF 文字內容
   - 識別車隊名稱
   - 匹配升級部件關鍵字
   - 提取上下文資訊

3. **模式匹配**
   ```python
   # 搜尋模式範例
   "Red Bull Racing new front wing"
   "Ferrari upgraded floor package"
   "Mercedes modified cooling system"
   ```

4. **資訊提取**
   - 車隊名稱
   - 升級部件
   - 部件類別
   - 分站/日期
   - 來源文件

### 手動驗證建議

由於 FIA 技術文件的格式多樣，建議：

1. **自動識別後手動確認**
   - 檢查 context 欄位
   - 驗證車隊和部件名稱
   - 確認分站資訊

2. **補充媒體報導**
   - Motorsport.com 技術分析
   - The Race 專家評論
   - 車隊官方公告

3. **建立可信來源清單**
   - FIA 官方文件（最高可信度）
   - 車隊技術發布會
   - 認證媒體報導

---

## 整合到 F1T 專案

### 新增 CLI 功能

```python
# 功能 ID 75: 車隊升級時間線
python f1_analysis_modular_main.py -f 75 -y 2025 -t "Red Bull Racing"

# 功能 ID 76: 分站升級對比
python f1_analysis_modular_main.py -f 76 -y 2025 -r Japan
```

### GUI 模組整合

```python
# modules/gui/upgrade_tracker/
# - upgrade_tracker_loader.py  # 繼承 UniversalDataLoader
# - upgrade_tracker_widget.py  # 升級時間線視覺化
# - upgrade_comparison.py      # 車隊升級對比圖表
```

### API 端點

```python
# GET /api/upgrades?year=2025&team=Red Bull Racing
# GET /api/upgrades/timeline?year=2025
# GET /api/upgrades/race?year=2025&race=Japan
```

---

## 常見問題

### Q1: FIA 網站結構變更怎麼辦？
**A**: 檢查並更新 `FIADocumentScraper.DOCUMENTS_URL`，必要時調整爬蟲邏輯。

### Q2: PDF 解析失敗？
**A**: 某些 PDF 使用圖片格式，需要 OCR。可使用 `pytesseract` 或手動輸入。

### Q3: 如何提高識別準確率？
**A**: 
- 增加更多關鍵字到 `UPGRADE_KEYWORDS`
- 改進正則表達式模式
- 結合媒體報導建立訓練資料

### Q4: 資料庫太大怎麼辦？
**A**: 定期匯出並備份，使用 SQLite 取代 JSON。

---

## 未來改進方向

### 短期 (1-2 週)
- [ ] 增加更多車隊和部件關鍵字
- [ ] 支援多語言文件（英文/法文）
- [ ] OCR 支援圖片型 PDF

### 中期 (1-2 月)
- [ ] 機器學習分類器（自動判斷文件類型）
- [ ] 升級效果分析（對比升級前後表現）
- [ ] 整合 FastF1 遙測數據驗證升級效果

### 長期 (3-6 月)
- [ ] 建立公開升級資料庫（眾包）
- [ ] 自動化升級追蹤（每週更新）
- [ ] 升級成本效益分析

---

## 貢獻指南

歡迎貢獻升級資料和改進建議：

1. **新增升級記錄**: 使用 `--add` 命令
2. **回報錯誤識別**: 建立 Issue
3. **改進關鍵字**: 提交 PR 更新 `UPGRADE_KEYWORDS`
4. **分享腳本**: 分享您的自動化腳本

---

## 授權和免責聲明

- FIA 文件版權歸 FIA 所有
- 本工具僅供個人研究和教育用途
- 升級資料僅供參考，不保證完全準確
- 請遵守 FIA 網站使用條款

---

**最後更新**: 2025-11-06  
**維護者**: F1T 開發團隊
