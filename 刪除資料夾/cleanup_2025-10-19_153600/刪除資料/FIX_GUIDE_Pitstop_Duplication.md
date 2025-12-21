# 🎯 完整修復指南：Pitstop 重複視窗問題

## 📌 問題核心

**根本原因**：Brake/RPM 模組違反 API-ONLY 模式政策，在更新圈速參數時自動調用 `main_window.create_telemetry_analysis()`，導致創建不必要的遙測分析視窗，連帶啟動 Pitstop 分析視窗。

---

## ✅ 已完成的修復

### 1. Brake 模組 - `_check_and_load_telemetry_if_needed()` 方法

**檔案**：`modules/gui/lap_analysis/brake_analysis/brake_analysis_mdi.py`  
**位置**：第 789-834 行  
**狀態**：✅ 已修復

**修復內容**：
- 移除自動觸發 `create_telemetry_analysis()` 的邏輯
- 改為僅檢查本地 JSON 緩存
- 添加 API-ONLY 模式提示訊息

---

## ⏳ 待完成的修復

### 2. Brake 模組 - `_trigger_telemetry_analysis()` 方法

**檔案**：`modules/gui/lap_analysis/brake_analysis/brake_analysis_mdi.py`  
**位置**：第 895-928 行  
**狀態**：⏳ 待修復

**需要修改的代碼段**：

```python
# 第 917-921 行 - 需要刪除
# 如果沒有遙測分析視窗，嘗試創建一個
print(f"[brake_MDI] 📡 嘗試創建遙測分析視窗...")
if hasattr(main_window, 'create_telemetry_analysis'):
    main_window.create_telemetry_analysis()  # ← 刪除這行！
    return True

# 替換為：
# ❌ [API-ONLY 修復] 不自動創建遙測分析視窗
print(f"[brake_MDI] 💡 [API-ONLY] 未找到現有遙測分析視窗")
```

### 3. RPM 模組 - 相同問題

**檔案**：`modules/gui/lap_analysis/rpm_analysis/rpm_analysis_mdi.py`  
**狀態**：⏳ 待修復

需要應用與 Brake 模組相同的修復模式。

---

## 🛠️ 手動修復步驟

### 方法 1：使用 VS Code 搜尋替換

1. 開啟 `brake_analysis_mdi.py`
2. 搜尋：`if hasattr(main_window, 'create_telemetry_analysis')`
3. 找到第 920 行附近的匹配項
4. 刪除以下代碼塊：

```python
# 如果沒有遙測分析視窗，嘗試創建一個
print(f"[brake_MDI] 📡 嘗試創建遙測分析視窗...")
if hasattr(main_window, 'create_telemetry_analysis'):
    main_window.create_telemetry_analysis()
    return True
```

5. 替換為：

```python
# ❌ [API-ONLY 修復] 不自動創建遙測分析視窗
print(f"[brake_MDI] 💡 [API-ONLY] 未找到現有遙測分析視窗")
```

6. 儲存檔案

### 方法 2：使用 Git Diff

1. 查看已修復的部分：
```powershell
git diff modules/gui/lap_analysis/brake_analysis/brake_analysis_mdi.py
```

2. 參考已修復的模式應用到待修復部分

---

## 🧪 驗證修復

### 測試步驟

1. **測試 Brake 模組**：
   ```
   a. 啟動 F1T GUI
   b. 開啟 Brake 分析視窗
   c. 勾選 "最速圈" 選項
   d. 更新 driver1 或 driver2
   e. 觀察終端輸出
   ```

2. **預期行為**：
   - ✅ 終端顯示：`[brake_MDI] 💡 [API-ONLY] 未找到現有遙測分析視窗`
   - ✅ 終端顯示：`[brake_MDI] 🔍 [API-ONLY] 檢查本地遙測分析緩存...`
   - ✅ **不會**創建 Pitstop 分析視窗
   - ✅ **不會**創建遙測分析視窗

3. **錯誤行為**（修復前）：
   - ❌ 自動創建遙測分析視窗
   - ❌ 自動創建 Pitstop 分析視窗
   - ❌ 每次更新參數都重複創建

---

## 📋 修復檢查清單

- [x] Brake 模組 - `_check_and_load_telemetry_if_needed()` ✅ 已完成
- [ ] Brake 模組 - `_trigger_telemetry_analysis()` ⏳ 待完成
- [ ] RPM 模組 - `_check_and_load_telemetry_if_needed()` ⏳ 待完成
- [ ] RPM 模組 - `_trigger_telemetry_analysis()` ⏳ 待完成
- [ ] Gear 模組 - 檢查是否存在相同問題 ⏳ 待檢查
- [ ] Throttle 模組 - 檢查是否存在相同問題 ⏳ 待檢查
- [ ] 全面測試所有圈速分析模組 ⏳ 待測試

---

## 🎓 學到的教訓

### API-ONLY 模式的核心原則

1. **禁止自動創建視窗**：
   - ❌ 不可調用 `create_*` 方法
   - ❌ 不可調用 `open_*` 方法
   - ✅ 只可檢查現有視窗

2. **禁止自動啟動 CLI**：
   - ❌ 不可執行 `subprocess.run()`
   - ❌ 不可執行 `os.system()`
   - ✅ 只可提示用戶手動執行

3. **允許的操作**：
   - ✅ 讀取本地 JSON 緩存
   - ✅ 通過 REST API 獲取數據
   - ✅ 檢查現有資源（視窗、檔案）
   - ✅ 提示用戶手動操作

---

## 🔗 相關資源

- **API-ONLY 政策文檔**：`.github/copilot-instructions.md`
- **修復報告**：`CRITICAL_FIX_REPORT_Pitstop_Duplication.md`
- **日誌檔案**：`dist/logs/f1_gui_2025-10-06.log`

---

## 📞 支援

如有問題，請參考：
1. API-ONLY 模式政策文檔
2. 本修復指南
3. 終端調試輸出

---

**修復日期**：2025-10-06  
**修復作者**：GitHub Copilot + mike2
