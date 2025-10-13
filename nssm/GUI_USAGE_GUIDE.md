# NSSM GUI 使用指南 - 圖形介面管理服務

## 🎨 使用 NSSM 圖形介面管理服務

NSSM 提供強大的 GUI 介面，讓您可以輕鬆編輯服務配置。

---

## 📋 NSSM GUI 命令速查

### **1. 編輯現有服務**

```powershell
# 編輯 API 服務
.\nssm\nssm.exe edit F1T-API

# 編輯定時更新服務
.\nssm\nssm.exe edit F1T-PeriodicUpdate

# 編輯 Cloudflare Tunnel 服務
.\nssm\nssm.exe edit F1T-CloudflareTunnel
```

**GUI 視窗包含的分頁：**
- **Application** - 應用程式路徑、參數、工作目錄
- **Details** - 服務名稱、顯示名稱、描述
- **Log on** - 登入帳戶設定
- **Dependencies** - 服務依賴關係
- **Process** - 進程優先級、親和性
- **Shutdown** - 關機方式、超時設定
- **Exit actions** - 退出時的動作（重啟策略）
- **I/O** - 標準輸入/輸出重定向
- **File rotation** - 日誌檔案輪轉
- **Environment** - 環境變數

---

### **2. 安裝新服務（GUI 模式）**

```powershell
# 開啟安裝 GUI（會提示輸入服務名稱）
.\nssm\nssm.exe install

# 直接指定服務名稱開啟安裝 GUI
.\nssm\nssm.exe install MyNewService
```

---

### **3. 移除服務（GUI 模式）**

```powershell
# 開啟移除 GUI（會提示選擇服務）
.\nssm\nssm.exe remove

# 直接指定服務開啟移除 GUI
.\nssm\nssm.exe remove F1T-API
```

---

## 🖥️ GUI 編輯常用設定

### **Application 分頁（最重要）**

| 欄位 | 說明 | F1T-API 範例 |
|------|------|-------------|
| **Path** | 程式路徑 | `C:\...\python.exe` |
| **Startup directory** | 工作目錄 | `C:\...\F1-data-analyze` |
| **Arguments** | 命令參數 | `refactored_api.py` |

---

### **Details 分頁**

| 欄位 | 說明 | F1T-API 範例 |
|------|------|-------------|
| **Display name** | 顯示名稱 | `F1T Telemetry API Server` |
| **Description** | 服務描述 | `F1 Telemetry REST API service...` |
| **Startup type** | 啟動類型 | `Automatic` |

**啟動類型選項：**
- **Automatic** - 開機自動啟動
- **Automatic (Delayed)** - 延遲自動啟動
- **Manual** - 手動啟動
- **Disabled** - 停用

---

### **I/O 分頁（日誌設定）**

| 欄位 | 說明 | F1T-API 範例 |
|------|------|-------------|
| **Output (stdout)** | 標準輸出日誌 | `C:\...\logs\f1t-api.log` |
| **Error (stderr)** | 錯誤日誌 | `C:\...\logs\f1t-api.error.log` |

---

### **File rotation 分頁（日誌輪轉）**

| 欄位 | 說明 | 建議值 |
|------|------|--------|
| **Replace existing output files** | 覆蓋現有檔案 | 不勾選 |
| **Rotate files** | 啟用輪轉 | 勾選 |
| **Restrict rotation to files bigger than** | 檔案大小限制 | `10485760` (10MB) |
| **Keep** | 保留備份數 | `5` 個 |

---

### **Exit actions 分頁（重啟策略）**

| 欄位 | 說明 | 建議值 |
|------|------|--------|
| **Exit action** | 退出動作 | `Restart application` |
| **Delay restart by** | 重啟延遲 | `5000` 毫秒 (5秒) |
| **Throttle** | 節流時間 | `1500` 毫秒 |

---

### **Dependencies 分頁（服務依賴）**

設定此服務依賴哪些服務（依賴的服務會先啟動）

**範例：** F1T-PeriodicUpdate 依賴 F1T-API
```
F1T-API
```

---

### **Environment 分頁（環境變數）**

逐行輸入環境變數：

```
PYTHONPATH=C:\Users\mike2\OneDrive\Code\F1-data-analyze
PYTHONIOENCODING=utf-8
DEBUG=false
LOG_LEVEL=INFO
```

---

## 🚀 快速操作腳本

我已為您創建了便捷腳本：

### **編輯 API 服務**
```powershell
.\nssm\edit-api.ps1
```

### **編輯定時更新服務**
```powershell
.\nssm\edit-update.ps1
```

### **編輯 Cloudflare Tunnel 服務**
```powershell
.\nssm\edit-tunnel.ps1
```

---

## 💡 GUI 操作技巧

### **1. 查看當前配置**
在 GUI 中打開服務，所有當前設定都會顯示，方便檢查。

### **2. 批量修改設定**
修改多個分頁後，最後點擊 **Edit service** 按鈕一次性套用所有變更。

### **3. 測試配置**
修改後建議：
1. 點擊 **Edit service** 儲存
2. 在 PowerShell 中啟動服務測試：
   ```powershell
   Start-Service F1T-API
   ```
3. 查看日誌確認：
   ```powershell
   Get-Content logs\f1t-api.log -Tail 20
   ```

### **4. 恢復預設值**
如果修改錯誤，可以：
1. 記錄原始值（在修改前）
2. 或使用卸載後重新安裝：
   ```powershell
   .\nssm\uninstall-services.ps1
   .\nssm\install-services.ps1
   ```

---

## ⚠️ 注意事項

### **1. 需要管理員權限**
編輯服務需要管理員權限，請：
- 右鍵 PowerShell → **以系統管理員身分執行**
- 或使用提供的腳本（會自動提升權限）

### **2. 停止服務後再編輯**
建議先停止服務再編輯，避免設定衝突：
```powershell
Stop-Service F1T-API -Force
.\nssm\nssm.exe edit F1T-API
# 編輯完成後再啟動
Start-Service F1T-API
```

### **3. 路徑使用絕對路徑**
所有路徑欄位請使用完整絕對路徑，避免相對路徑問題。

### **4. 驗證設定**
修改後驗證：
```powershell
# 查看服務狀態
Get-Service F1T-API

# 檢查進程
Get-Process python

# 查看日誌
Get-Content logs\f1t-api.log -Tail 20
```

---

## 📚 命令列替代方案

如果不想使用 GUI，也可以用命令列修改：

```powershell
# 查看當前設定
.\nssm\nssm.exe get F1T-API Application

# 修改設定
.\nssm\nssm.exe set F1T-API Application "C:\path\to\python.exe"
.\nssm\nssm.exe set F1T-API AppParameters "refactored_api.py --port 8080"
.\nssm\nssm.exe set F1T-API AppDirectory "C:\path\to\project"

# 查看所有設定
.\nssm\nssm.exe dump F1T-API
```

---

## 🎯 總結

**GUI 優勢：**
- ✅ 視覺化操作，直觀易用
- ✅ 所有選項一目了然
- ✅ 即時驗證輸入
- ✅ 不需要記憶命令

**命令列優勢：**
- ✅ 可腳本化、自動化
- ✅ 批量操作
- ✅ 遠端管理
- ✅ 版本控制友好

**推薦：** 日常管理用 GUI，自動化部署用命令列！
