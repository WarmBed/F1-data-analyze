# F1T GUI 重構快速入門指南
## Quick Start Guide for GUI Refactoring

**開始日期**: 2025-12-15
**預計完成**: 2-3 週
**當前進度**: 0/10 階段完成

---

## 🚀 立即開始

### 第一天：準備工作（現在就可以執行！）

#### Step 1: 建立安全分支（5 分鐘）

```bash
# 確保當前工作目錄乾淨
git status

# 如果有未提交的變更，先提交
git add .
git commit -m "chore: 重構前的最後提交"

# 建立重構專用分支
git checkout -b refactor/gui-modules-restructure

# 建立備份標籤（緊急回滾用）
git tag backup-before-refactor

# 確認分支已建立
git branch
```

#### Step 2: 執行清理腳本（10 分鐘）

```bash
# 1. 預覽將要刪除的檔案
python scripts/cleanup_gui_modules.py --dry-run

# 2. 確認無誤後執行清理
python scripts/cleanup_gui_modules.py

# 3. 查看清理報告
cat cleanup_report.txt

# 4. 提交變更
git add .
git commit -m "refactor(gui): 清理 81 個備份和舊版本檔案

- 刪除 14 個備份檔案 (.backup, .backup_indent 等)
- 刪除 9 個舊版本檔案 (_old, _OLD 等)
- 清理 58 個 __pycache__ 目錄

參考: cleanup_report.txt"
```

**✅ 第一天檢查點**:
- [ ] Git 分支 `refactor/gui-modules-restructure` 已建立
- [ ] 備份標籤 `backup-before-refactor` 已建立
- [ ] 81 個無用檔案已刪除
- [ ] 變更已提交到 Git

---

## 📅 後續步驟規劃

### 第二天：建立新資料夾結構

```bash
# 執行資料夾建立腳本（待建立）
python scripts/create_new_structure.py

# 提交變更
git add modules/gui/telemetry modules/gui/all_drivers modules/gui/lap_analysis
git commit -m "refactor(gui): 建立新的資料夾結構"
```

### 第 3-5 天：遷移遙測分析模組

**優先順序清單**:
1. Speed 分析（最簡單，作為範例）
2. Brake 分析
3. Gear 分析
4. RPM 分析
5. Acceleration 分析
6. Throttle 分析（需整合 3 個模組）
7-9. Diff 分析（speed_diff, distance_diff, time_diff）

**每個模組的標準流程**:
```bash
# 1. 複製模組到新位置
cp -r modules/gui/lap_analysis/speed_analysis modules/gui/telemetry/speed

# 2. 更新內部導入（手動或使用工具）
# 編輯 modules/gui/telemetry/speed/*.py

# 3. 測試模組
python -m pytest tests/gui/telemetry/test_speed_analysis.py

# 4. 提交變更
git add modules/gui/telemetry/speed
git commit -m "refactor(gui): 遷移 Speed 分析到 telemetry/speed"

# 5. 刪除舊模組（確認測試通過後）
git rm -r modules/gui/lap_analysis/speed_analysis
git commit -m "refactor(gui): 移除舊的 speed_analysis 目錄"
```

### 第 6-8 天：整合全車手分析模組

重點：整合煞車分析（3→1）

### 第 9-10 天：重組圈速分析模組

### 第 11-12 天：整合賽事分析模組

### 第 13-14 天：更新所有導入路徑

```bash
# 預覽變更
python scripts/update_imports.py --dry-run

# 執行更新
python scripts/update_imports.py

# 提交變更
git add .
git commit -m "refactor(gui): 更新所有導入路徑到新架構"
```

### 第 15-17 天：執行完整測試

### 第 18-19 天：更新文檔和最終清理

---

## 🛠️ 可用工具

### 清理工具
```bash
# 清理備份和舊版本檔案
python scripts/cleanup_gui_modules.py --dry-run   # 預覽
python scripts/cleanup_gui_modules.py             # 執行
```

### 導入路徑更新工具
```bash
# 自動更新導入路徑
python scripts/update_imports.py --dry-run        # 預覽
python scripts/update_imports.py                  # 執行
```

### 測試工具
```bash
# 執行單元測試
python -m pytest tests/gui/ -v

# 執行特定模組測試
python -m pytest tests/gui/telemetry/test_speed_analysis.py -v

# 執行所有測試並生成覆蓋率報告
python -m pytest tests/gui/ --cov=modules.gui --cov-report=html
```

---

## 📊 進度追蹤

### Todo List 狀態

使用以下命令查看當前進度：
```bash
# 查看完整計畫
cat docs/GUI_REFACTORING_MASTER_PLAN.md

# 查看當前 todo 狀態
# （在 Claude Code 中會自動顯示）
```

### 每日檢查清單

**每天工作結束前必做**:
```bash
# 1. 執行測試
python -m pytest tests/gui/ -v

# 2. 提交變更
git add .
git commit -m "refactor(gui): [簡短描述今天的工作]"

# 3. 推送到遠端（如果有）
git push origin refactor/gui-modules-restructure

# 4. 更新進度
# 在 Claude Code 中更新 todo list
```

---

## ⚠️ 緊急情況處理

### 如果遇到嚴重問題

#### 情境 1: 單一模組遷移失敗

```bash
# 回滾該模組的變更
git log --oneline modules/gui/telemetry/speed/
git revert <commit-hash>

# 恢復舊模組
git checkout HEAD~1 modules/gui/lap_analysis/speed_analysis/
```

#### 情境 2: 需要暫停並修復問題

```bash
# 暫存當前工作
git stash save "WIP: 暫停重構，修復問題"

# 修復問題...

# 恢復工作
git stash pop
```

#### 情境 3: 完全回滾

```bash
# 切換到備份標籤
git checkout backup-before-refactor

# 檢視舊版本...

# 回到重構分支
git checkout refactor/gui-modules-restructure

# 如果需要重新開始
git checkout backup-before-refactor
git checkout -b refactor/gui-modules-restructure-v2
```

---

## 📞 獲取幫助

### 文檔資源

1. **完整計畫書**: `docs/GUI_REFACTORING_MASTER_PLAN.md`
   - 詳細的階段劃分
   - 風險管理
   - 測試策略

2. **模組分析報告**: `docs/GUI_MODULE_ANALYSIS_REPORT.md`
   - 當前架構分析
   - 重複功能檢測
   - 整理建議

3. **架構設計**: `docs/UNIVERSAL_ARCHITECTURE_DESIGN.md`
   - 通用基類說明
   - 最佳實踐

### 常見問題

**Q: 如何確認某個模組是否已遷移？**
```bash
# 檢查新位置是否存在
ls modules/gui/telemetry/speed/

# 檢查舊位置是否已刪除
ls modules/gui/lap_analysis/speed_analysis/  # 應該報錯
```

**Q: 如何測試單一模組？**
```bash
# 方法 1: 使用 pytest
python -m pytest tests/gui/telemetry/test_speed_analysis.py

# 方法 2: 直接啟動 GUI 並手動測試
python f1t_gui_main.py
# 然後在 GUI 中開啟該模組
```

**Q: 如果導入路徑更新後出現錯誤怎麼辦？**
```bash
# 1. 檢查錯誤訊息中的檔案
# 2. 手動檢查該檔案的導入語句
# 3. 對照映射表確認是否正確
cat scripts/update_imports.py | grep "import_mappings"
```

---

## ✅ 下一步行動

**立即執行**（現在！）:

1. **建立分支和備份**
   ```bash
   git checkout -b refactor/gui-modules-restructure
   git tag backup-before-refactor
   ```

2. **執行清理腳本**
   ```bash
   python scripts/cleanup_gui_modules.py --dry-run
   python scripts/cleanup_gui_modules.py
   ```

3. **提交變更**
   ```bash
   git add .
   git commit -m "refactor(gui): 清理 81 個無用檔案"
   ```

**明天執行**:

1. 建立新的資料夾結構
2. 開始遷移第一個模組（Speed 分析）

**本週目標**:

- ✅ 完成階段 0-2（準備 + 清理 + 結構）
- ✅ 遷移 3-5 個遙測模組

---

**最後更新**: 2025-12-15
**狀態**: 🟢 準備就緒，可以開始
