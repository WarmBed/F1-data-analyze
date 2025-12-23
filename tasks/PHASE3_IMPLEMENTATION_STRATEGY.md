# Phase 3 實施策略：GUI 模組全面三語翻譯

## 📋 總覽

Phase 3 目標是翻譯所有 GUI 分析模組，使其完全支援中文/英文/日文三語切換。

### 模組清單與工作量評估

| 模組檔案 | 行數 | 估計字串數 | 優先級 | 狀態 |
|---------|------|-----------|--------|------|
| telemetry_analysis_mdi.py | 1905 | ~150 | P1 | ⏳ 待開始 |
| speed_analysis_mdi.py | ~800 | ~80 | P2 | ⏳ 待開始 |
| track_analysis_module.py | ~600 | ~60 | P3 | ⏳ 待開始 |
| rain_universal_analysis_mdi.py | ~1200 | ~100 | P3 | ⏳ 待開始 |
| accident_universal_analysis_mdi.py | ~900 | ~80 | P3 | ⏳ 待開始 |

**總計**：約 470+ 個需要翻譯的字串

## 🔧 技術實施方案

### 方案 A：手動逐步翻譯（推薦 ✅）
**優點**：
- 精確控制每個翻譯
- 可以優化翻譯鍵命名
- 確保翻譯品質

**缺點**：
- 時間成本高
- 需要多次編輯操作

**實施步驟**：
1. 選定一個模組
2. 掃描所有硬編碼字串
3. 在 `gui_i18n.py` 添加翻譯鍵（一次性批量添加）
4. 使用 `multi_replace_string_in_file` 批量替換
5. 測試語言切換
6. 處理下一個模組

### 方案 B：自動化腳本批量處理
**優點**：
- 快速完成大量字串
- 減少手動操作

**缺點**：
- 需要開發複雜腳本
- 可能誤判某些字串
- 翻譯品質需人工審核

**實施方案**：
創建 `tools/translate_gui_modules.py` 自動化腳本：
- 掃描 Python 檔案中所有字串
- 過濾非翻譯項（如技術關鍵字、變數名）
- 自動生成翻譯鍵
- 替換原始字串為 tr() 調用

## 📦 標準化翻譯模板

### 1. 遙測分析模組 (telemetry_analysis_mdi.py)

#### 狀態訊息類別
```python
# Loading states
'telemetry_preparing_data': {
    'zh': '準備載入遙測分析資料...', 
    'en': 'Preparing to load telemetry analysis data...', 
    'ja': 'テレメトリ分析データの読み込み準備中...'
},
'telemetry_loading_via_api': {
    'zh': '正在透過 API 載入遙測分析資料...', 
    'en': 'Loading telemetry analysis data via API...', 
    'ja': 'API経由でテレメトリ分析データを読み込み中...'
},
'telemetry_api_success': {
    'zh': '已從 API 載入遙測分析資料', 
    'en': 'Telemetry analysis data loaded from API', 
    'ja': 'APIからテレメトリ分析データを読み込みました'
},
'telemetry_loading_complete': {
    'zh': '遙測數據載入完成', 
    'en': 'Telemetry data loading complete', 
    'ja': 'テレメトリデータの読み込みが完了しました'
},

# Error messages
'telemetry_api_init_failed': {
    'zh': 'API 請求初始化失敗，改用本地 JSON/CLI 後備流程', 
    'en': 'API request initialization failed, falling back to local JSON/CLI', 
    'ja': 'APIリクエストの初期化に失敗、ローカルJSON/CLIにフォールバック'
},
'telemetry_load_failed': {
    'zh': '載入遙測數據失敗: {error}', 
    'en': 'Failed to load telemetry data: {error}', 
    'ja': 'テレメトリデータの読み込みに失敗: {error}'
},
'telemetry_timeout': {
    'zh': '遙測數據生成超時，請檢查網路連線或稍後重試', 
    'en': 'Telemetry data generation timeout, please check network or retry later', 
    'ja': 'テレメトリデータ生成タイムアウト、ネットワークを確認するか後で再試行してください'
},

# UI labels
'telemetry_comparison_tab': {
    'zh': '⚔️ 對比分析功能開發中...', 
    'en': '⚔️ Comparison Analysis (In Development)...', 
    'ja': '⚔️ 比較分析（開発中）...'
},
'telemetry_trend_tab': {
    'zh': '📈 圈速趨勢功能開發中...', 
    'en': '📈 Lap Time Trends (In Development)...', 
    'ja': '📈 ラップタイムトレンド（開発中）...'
},
'telemetry_sector_tab': {
    'zh': '🏁 區間分析功能開發中...', 
    'en': '🏁 Sector Analysis (In Development)...', 
    'ja': '🏁 セクター分析（開発中）...'
},
'telemetry_tire_tab': {
    'zh': '🛞 輪胎策略功能開發中...', 
    'en': '🛞 Tire Strategy (In Development)...', 
    'ja': '🛞 タイヤ戦略（開発中）...'
},
```

### 2. 速度分析模組 (speed_analysis_mdi.py)
（待補充）

### 3. 賽道分析模組 (track_analysis_module.py)
（待補充）

### 4. 降雨分析模組 (rain_universal_analysis_mdi.py)
（待補充）

### 5. 事故分析模組 (accident_universal_analysis_mdi.py)
（待補充）

## 🚀 實施計劃

### Week 1: P1 遙測分析模組
**目標**：完成 telemetry_analysis_mdi.py 的完整翻譯

**步驟**：
1. **Day 1-2**：字串掃描與翻譯鍵設計
   - 掃描所有 emit() 調用中的字串
   - 掃描所有 UI 元件字串（QLabel, QPushButton, setWindowTitle）
   - 設計翻譯鍵命名規範（telemetry_xxx）
   
2. **Day 3-4**：批量添加翻譯鍵
   - 在 gui_i18n.py 添加所有遙測相關翻譯鍵（~150 個）
   - 確保每個鍵都有 zh/en/ja 三語
   - 使用自動化腳本輔助日文翻譯
   
3. **Day 5-6**：程式碼替換
   - 使用 multi_replace_string_in_file 批量替換
   - 分批處理：狀態訊息 → UI 元件 → 錯誤訊息
   - 測試每批次的替換結果
   
4. **Day 7**：測試與驗證
   - 啟動遙測分析模組
   - 測試三語切換
   - 修復翻譯錯誤或遺漏

### Week 2: P2 速度分析 + P3 其他模組
**目標**：完成剩餘 4 個模組的翻譯

**分配**：
- Day 1-2: speed_analysis_mdi.py (~80 strings)
- Day 3-4: track_analysis_module.py (~60 strings)
- Day 5-6: rain_universal_analysis_mdi.py (~100 strings)
- Day 7: accident_universal_analysis_mdi.py (~80 strings)

### Week 3: 整合測試與優化
**目標**：全系統三語測試與問題修正

**測試範圍**：
- [ ] 主視窗選單（已完成 Phase 2）
- [ ] 自定義標題欄（已完成 Phase 2）
- [ ] 遙測分析模組
- [ ] 速度分析模組
- [ ] 賽道分析模組
- [ ] 降雨分析模組
- [ ] 事故分析模組

## 🛠️ 開發工具支援

### 自動化腳本規劃

#### 1. `tools/scan_gui_strings.py`
掃描模組中所有需要翻譯的字串：
```python
def scan_python_file(filepath):
    """
    掃描 Python 檔案中的所有硬編碼字串
    返回：List[Dict] 包含 line_number, string_content, context
    """
    pass
```

#### 2. `tools/generate_translation_keys.py`
自動生成翻譯鍵和三語內容：
```python
def generate_key_name(string_content, module_name):
    """
    基於字串內容和模組名稱生成合適的翻譯鍵
    例如："載入遙測數據..." → "telemetry_loading_data"
    """
    pass

def translate_to_japanese(chinese_text):
    """
    使用 JA_TRANSLATIONS 字典自動翻譯常見詞彙
    """
    pass
```

#### 3. `tools/batch_replace_gui_strings.py`
批量替換硬編碼字串為 tr() 調用：
```python
def replace_strings_in_file(filepath, replacements):
    """
    在指定檔案中批量替換字串
    replacements: List[Tuple[old_string, translation_key]]
    """
    pass
```

## 📊 進度追蹤

使用 `tasks/PHASE3_PROGRESS.md` 追蹤每個模組的完成狀態：

```markdown
## 遙測分析模組 (telemetry_analysis_mdi.py)
- [ ] 字串掃描完成
- [ ] 翻譯鍵設計完成
- [ ] 翻譯鍵添加到 gui_i18n.py
- [ ] 程式碼替換完成
- [ ] 語言切換測試通過

## 速度分析模組 (speed_analysis_mdi.py)
- [ ] 字串掃描完成
...
```

## ⚠️ 注意事項

### 1. 不需翻譯的字串類型
- 技術日誌標籤：`[DEBUG]`, `[ERROR]`, `[SUCCESS]`, `[LINK]`, `[REFRESH]`
- 技術關鍵字：`API`, `JSON`, `CLI`, `HTTP`
- 變數名稱和鍵名
- 正則表達式和格式化字串中的佔位符

### 2. 格式化字串處理
保持佔位符原樣，只翻譯外部文字：
```python
# 錯誤範例
'window_title': {'zh': '視窗 {標題}', 'en': 'Window {title}', 'ja': 'ウィンドウ {タイトル}'}

# 正確範例
'window_title': {'zh': '視窗 {title}', 'en': 'Window {title}', 'ja': 'ウィンドウ {title}'}
```

### 3. 多行字串處理
使用 `\n` 保持換行一致：
```python
'multi_line_text': {
    'zh': '第一行\n第二行\n第三行',
    'en': 'Line 1\nLine 2\nLine 3',
    'ja': '行1\n行2\n行3'
}
```

## 🎯 成功指標

Phase 3 完成時應達到：
- ✅ 所有 GUI 模組支援即時三語切換
- ✅ 無硬編碼字串殘留（技術關鍵字除外）
- ✅ 所有翻譯鍵有完整的 zh/en/ja 內容
- ✅ 語言切換測試全部通過
- ✅ 文檔更新完整

---
**文件版本**：v1.0  
**預計完成時間**：3 週  
**負責人**：AI 編程助手  
**狀態**：📝 規劃完成，待執行
