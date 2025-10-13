# Ideal Lap 模組國際化 - 快速驗證清單
**Quick Verification Checklist for Ideal Lap Module Internationalization**

---

## ✅ 完成項目

### 1. 翻譯系統整合
- [x] `core/gui_i18n.py` - 新增 67 個翻譯鍵
- [x] `ideal_lap_ranking_table_widget.py` - 完整多國語言化
- [x] `ideal_lap_options_dialog.py` - 驗證正確使用 `tr()`

### 2. 翻譯完成度
- [x] 中文 (zh): 27/27 (100%)
- [x] 英文 (en): 27/27 (100%)
- [x] 日文 (ja): 27/27 (100%)

### 3. 自動化測試
- [x] 測試腳本：`test_ideal_lap_i18n.py`
- [x] 翻譯鍵存在性測試：✅ 通過
- [x] 格式化字串測試：✅ 通過
- [x] 語言切換測試：✅ 通過

---

## 🧪 手動驗證步驟（待執行）

### Step 1: 啟動 GUI 主程式
```powershell
python f1t_gui_main.py
```

### Step 2: 切換語言到中文
1. 主選單 → 說明 (Help) → 語言設定
2. 選擇「中文」
3. 確認主視窗所有文字變為中文

### Step 3: 開啟 Ideal Lap 分析
1. 點擊「分析模組」樹狀圖
2. 找到「理想圈分析」（或 Ideal Lap Analysis）
3. 雙擊開啟選項對話框

### Step 4: 驗證選項對話框翻譯
**預期中文內容：**
- 標題：「理想圈分析選項」
- 描述：「請選擇要開啟的理想圈分析類型。」
- 選項：
  - ✓ 排名表格
  - ✓ 分段熱力圖
  - ✓ 分段比較
- 按鈕：
  - 全選
  - 全不選
  - 確定
  - 取消

### Step 5: 開啟排名表格
1. 勾選「排名表格」
2. 點擊「確定」
3. 等待數據載入

### Step 6: 驗證排名表格翻譯
**預期中文內容：**

**統計摘要面板：**
- 📊 賽事統計摘要
- 總車手數: XX
- 全場最速實際圈: X:XX.XXX
- 最快理想圈: X:XX.XXX
- 理想圈範圍: X.XXXs
- 平均差異: X.XXXs
- 完美單圈達成率: X/XX

**表格欄位標題：**
- 排名
- 車手
- 車手最速圈
- 理想圈
- 差異
- 與全場最速差距
- 分段
- 操作

**按鈕與狀態：**
- 📊 匯出 CSV
- 詳情（每行）
- 已載入 XX 位車手（底部狀態列）

**Tooltip（懸停提示）：**
- 最速圈: X:XX.XXX (Lap XX)
- 理想圈: X:XX.XXX
  - S1: X.XXXs (Lap XX)
  - S2: X.XXXs (Lap XX)
  - S3: X.XXXs (Lap XX)
- 差異: +X.XXXs (+X.XX%)
  - 評估: 接近完美單圈 / 有中等提升空間 / 有明顯改善空間

### Step 7: 切換到英文
1. 主選單 → Help → Language Settings
2. 選擇「English」
3. 確認所有文字變為英文

**預期英文內容：**
- Window Title: "Ideal Lap Ranking - 2025 Japan R"
- Summary: "📊 Race Statistics Summary"
- Table Headers: "Pos", "Driver", "Fastest Lap", "Ideal Lap", "Gap", etc.
- Button: "📊 Export CSV", "Details"
- Status: "Loaded XX drivers"

### Step 8: 切換到日文
1. 主選單 → Help → Language Settings
2. 選擇「日本語」
3. 確認所有文字變為日文

**預期日文內容：**
- Window Title: "理想ラップランキング - 2025 Japan R"
- Summary: "📊 レース統計サマリー"
- Table Headers: "順位", "ドライバー", "最速ラップ", "理想ラップ", "ギャップ", etc.
- Button: "📊 CSV出力", "詳細"
- Status: "XX人のドライバーを読み込みました"

---

## ⚠️ 已知限制

1. **Heatmap 和 Comparison 模組**
   - 目前尚未實作
   - 翻譯鍵已預留，但模組本身需要開發

2. **語言切換不即時**
   - 需要關閉並重新開啟視窗才能看到新語言
   - 未來可改進為即時切換

---

## 📋 驗證結果記錄

| 測試項目 | 中文 (zh) | 英文 (en) | 日文 (ja) | 備註 |
|----------|-----------|-----------|-----------|------|
| Options Dialog | ⬜ 待測 | ⬜ 待測 | ⬜ 待測 | |
| 統計摘要面板 | ⬜ 待測 | ⬜ 待測 | ⬜ 待測 | |
| 表格欄位標題 | ⬜ 待測 | ⬜ 待測 | ⬜ 待測 | |
| 按鈕與工具列 | ⬜ 待測 | ⬜ 待測 | ⬜ 待測 | |
| Tooltip 內容 | ⬜ 待測 | ⬜ 待測 | ⬜ 待測 | |
| 格式化字串 | ⬜ 待測 | ⬜ 待測 | ⬜ 待測 | |
| 語言切換流暢度 | ⬜ 待測 | ⬜ 待測 | ⬜ 待測 | |

**圖例：**
- ✅ 通過
- ❌ 失敗
- ⚠️  部分通過
- ⬜ 待測試

---

## 🐛 問題回報

如發現翻譯問題，請記錄：

1. **問題描述**：
2. **預期翻譯**：
3. **實際顯示**：
4. **語言**：
5. **截圖**（如有）：

---

**最後更新**: 2025-10-09  
**負責人**: F1T Team
