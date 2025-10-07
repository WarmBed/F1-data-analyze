# 🚀 VS Code 啟動配置說明

## 📋 可用的啟動配置

本專案提供了多種啟動配置，方便在不同場景下快速啟動和調試 F1T 系統。

---

## 🎯 單獨啟動配置

### 開發模式

#### 1. **Python: GUI** 🐍
- **用途**：啟動 Python 源碼版本的 GUI（開發調試用）
- **特點**：
  - 完整的 Python 調試功能
  - 支援斷點、變數檢視
  - 即時代碼修改
- **適用場景**：日常開發、Bug 修復、功能開發

#### 2. **Python: API server** 🌐
- **用途**：啟動本地 REST API 服務器
- **端口**：`http://localhost:8000`
- **文檔**：自動開啟 `http://localhost:8000/docs`
- **適用場景**：API 開發、後端測試

#### 3. **Python: CLI entry (interactive)** 💻
- **用途**：啟動 CLI 互動模式
- **特點**：直接執行分析功能
- **適用場景**：快速測試分析邏輯

#### 4. **Python: Pytest** 🧪
- **用途**：執行所有測試
- **覆蓋範圍**：`tests/` 目錄下所有測試
- **適用場景**：單元測試、集成測試

---

### 生產模式

#### 5. **🏎️ F1T GUI (EXE)** 📦
- **用途**：啟動打包後的 EXE 執行檔
- **路徑**：`dist/F1T_GUI.exe`
- **特點**：
  - 模擬最終用戶體驗
  - 無 Python 環境依賴
  - 獨立執行
- **適用場景**：
  - 生產環境測試
  - 發布前驗證
  - 性能測試

#### 6. **🏎️ F1T GUI (EXE - 調試模式)** 🐛
- **用途**：啟動 EXE 並開啟調試控制台
- **參數**：`--debug --console`
- **特點**：
  - 顯示詳細日誌
  - 保留控制台視窗
  - 方便追蹤 EXE 問題
- **適用場景**：
  - EXE 版本調試
  - 打包問題排查
  - 日誌分析

#### 7. **🌐 Cloudflare Tunnel** ☁️
- **用途**：啟動 Cloudflare Tunnel，對外開放 API
- **網址**：`https://api.f1telemetrystationpro.org`
- **適用場景**：
  - 公開 API 服務
  - 遠程訪問
  - 生產環境部署

---

## 🎛️ 組合啟動配置 (Compounds)

### 開發模式組合

#### 1. **🎯 只啟動 GUI**
- **包含**：Python: GUI
- **用途**：純前端開發，使用外部 API
- **適用場景**：
  - GUI 界面開發
  - 使用生產 API (`https://api.f1telemetrystationpro.org`)

#### 2. **🚀 GUI + API (本地開發)**
- **包含**：
  - Python: API server
  - Python: GUI
- **用途**：完整本地開發環境
- **特點**：
  - API 和 GUI 同時運行
  - API 位於 `http://localhost:8000`
  - GUI 使用本地 API
- **適用場景**：
  - 全棧開發
  - API 和 GUI 聯調
  - 離線開發

---

### 生產模式組合

#### 3. **🌐 API + Cloudflare Tunnel (對外開放)**
- **包含**：
  - Python: API server
  - 🌐 Cloudflare Tunnel
- **用途**：對外開放 API 服務
- **訪問**：`https://api.f1telemetrystationpro.org`
- **適用場景**：
  - API 生產部署
  - 遠程團隊協作
  - 公開服務測試

#### 4. **🌍 完整系統 (API + Tunnel + GUI)**
- **包含**：
  - Python: API server
  - 🌐 Cloudflare Tunnel
  - Python: GUI
- **用途**：完整系統模擬生產環境
- **特點**：
  - 本地 API + 公開訪問
  - GUI 可選擇本地或遠程 API
- **適用場景**：
  - 系統集成測試
  - 演示環境
  - 生產環境模擬

#### 5. **🚀 EXE + API (生產測試)** ⭐ 新增
- **包含**：
  - Python: API server
  - 🏎️ F1T GUI (EXE)
- **用途**：測試 EXE 版本與 API 的整合
- **特點**：
  - EXE 使用本地 API
  - 模擬用戶環境
- **適用場景**：
  - 發布前測試
  - EXE 集成驗證
  - 用戶體驗測試

#### 6. **🌍 完整 EXE 系統 (API + Tunnel + EXE)** ⭐ 新增
- **包含**：
  - Python: API server
  - 🌐 Cloudflare Tunnel
  - 🏎️ F1T GUI (EXE)
- **用途**：完整生產環境模擬（EXE 版本）
- **特點**：
  - 最接近實際部署
  - EXE + 公開 API
- **適用場景**：
  - 正式發布前最終測試
  - 生產環境完整驗證

---

## 🎯 使用建議

### 日常開發流程

1. **前端開發**（GUI 界面）：
   ```
   🎯 只啟動 GUI
   ```

2. **後端開發**（API 功能）：
   ```
   Python: API server
   ```

3. **全棧開發**（前後端聯調）：
   ```
   🚀 GUI + API (本地開發)
   ```

4. **測試驗證**：
   ```
   Python: Pytest
   ```

---

### 發布前測試流程

1. **打包 EXE**：
   ```powershell
   python -m PyInstaller F1T_GUI.spec
   ```

2. **測試 EXE 基本功能**：
   ```
   🏎️ F1T GUI (EXE - 調試模式)
   ```

3. **測試 EXE + API 集成**：
   ```
   🚀 EXE + API (生產測試)
   ```

4. **完整系統測試**：
   ```
   🌍 完整 EXE 系統 (API + Tunnel + EXE)
   ```

5. **日誌檢查**：
   - 查看 `dist/logs/f1_gui_*.log`
   - 檢查終端輸出

---

### 生產環境部署

1. **啟動 API 服務**：
   ```
   🌐 API + Cloudflare Tunnel (對外開放)
   ```

2. **分發 EXE**：
   - 將 `dist/F1T_GUI.exe` 和 `dist/_internal/` 打包
   - 提供給用戶下載

3. **用戶執行**：
   - 雙擊 `F1T_GUI.exe`
   - 自動連接 `https://api.f1telemetrystationpro.org`

---

## 🐛 調試技巧

### Python 源碼調試

1. 在 VS Code 中設置斷點
2. 選擇 `Python: GUI` 配置
3. 按 `F5` 啟動調試
4. 程序會在斷點處暫停

### EXE 版本調試

1. 使用 `🏎️ F1T GUI (EXE - 調試模式)`
2. 觀察控制台輸出
3. 檢查 `dist/logs/` 中的日誌檔案
4. 使用 `--debug` 參數獲取更多資訊

### API 調試

1. 啟動 `Python: API server`
2. 訪問 `http://localhost:8000/docs`
3. 使用 Swagger UI 測試 API
4. 查看終端日誌

---

## 📁 相關文件

- **EXE 執行檔**：`dist/F1T_GUI.exe`
- **EXE 依賴**：`dist/_internal/`
- **日誌目錄**：`dist/logs/`
- **打包腳本**：`F1T_GUI.spec`
- **啟動配置**：`.vscode/launch.json`

---

## 🔧 故障排除

### EXE 無法啟動

1. 檢查 `dist/logs/` 中的錯誤日誌
2. 使用調試模式：`🏎️ F1T GUI (EXE - 調試模式)`
3. 確認 `_internal/` 目錄完整

### API 連接失敗

1. 檢查 API 服務器是否運行
2. 確認網址配置正確（本地或遠程）
3. 查看防火牆設置

### Cloudflare Tunnel 無法連接

1. 檢查 `cloudflared.exe` 是否存在
2. 確認 `config.yml` 配置正確
3. 查看 Cloudflare Dashboard

---

## 📝 更新日誌

### 2025-10-06
- ✅ 新增 `🏎️ F1T GUI (EXE)` 配置
- ✅ 新增 `🏎️ F1T GUI (EXE - 調試模式)` 配置
- ✅ 新增 `🚀 EXE + API (生產測試)` 組合配置
- ✅ 新增 `🌍 完整 EXE 系統 (API + Tunnel + EXE)` 組合配置

---

**維護者**：F1T 開發團隊  
**最後更新**：2025-10-06
