# 定時 API 更新服務使用指南

**版本**: 1.0.0  
**建立日期**: 2025-10-13  
**作者**: F1T Team

---

## 📋 目錄

1. [服務概述](#服務概述)
2. [系統需求](#系統需求)
3. [安裝步驟](#安裝步驟)
4. [配置說明](#配置說明)
5. [運行服務](#運行服務)
6. [智能更新模式](#智能更新模式)
7. [故障排除](#故障排除)
8. [進階配置](#進階配置)

---

## 🎯 服務概述

定時 API 更新服務是一個**獨立背景服務**，自動定時呼叫 CLI 功能以更新 F1 數據：

| Function ID | 功能名稱 | 平時頻率 | 特殊模式 |
|------------|---------|---------|---------|
| **F96** | 賽事天氣預報 | 每 24 小時 | 賽前 72h 內，每 6 小時 |
| **F97** | 賽季積分查詢 | 每 120 小時 (5天) | 賽後 48h 內，每 4 小時 |
| **F98** | 顏色配置輸出 | 每 168 小時 (7天) | 無特殊模式 |
| **F99** | 賽季賽程查詢 | 每 168 小時 (7天) | 無特殊模式 |

### **智能更新策略**

服務會自動檢測當前處於何種模式，並動態調整更新頻率：

1. **平時維護模式** (Normal Maintenance)
   - 無比賽周末時的正常更新頻率

2. **賽後密集模式** (Post-Race Intensive)
   - 賽後 0-48 小時內觸發
   - F97 積分榜每 4 小時更新（捕捉賽後處罰和積分確認）

3. **賽前預熱模式** (Pre-Race Warm-Up)
   - 比賽前 72 小時內觸發
   - F96 天氣預報每 6 小時更新（提供最新天氣預測）

---

## 💻 系統需求

- **作業系統**: Windows 10/11, Linux, macOS
- **Python**: 3.10 或更高版本
- **磁碟空間**: 至少 500MB（用於日誌和數據檔案）
- **網路**: 穩定的網際網路連線（訪問 F1 API）

### **Python 套件依賴**

```powershell
# 核心依賴
pip install schedule requests

# 專案依賴（已在 requirements.txt）
pip install -r requirements.txt
```

---

## 📦 安裝步驟

### **步驟 1: 安裝依賴套件**

```powershell
# 安裝 schedule 庫
pip install schedule
```

### **步驟 2: 驗證安裝**

```powershell
# 測試賽事檢測器
python scripts/race_event_detector.py

# 應該看到類似輸出：
# ✅ 賽程數據載入成功
# 🎯 當前模式: 平時維護模式 (normal)
```

### **步驟 3: 檢查配置檔案**

配置檔案位於 `scripts/config/update_service_config.json`，預設配置即可使用。

---

## ⚙️ 配置說明

### **配置檔案結構**

```json
{
  "api": {
    "base_url": "https://localhost:8000",
    "timeout": 120
  },
  
  "functions": {
    "96": { "name": "賽事天氣預報", "enabled": true },
    "97": { "name": "賽季積分查詢", "enabled": true }
  },
  
  "update_intervals": {
    "normal": {
      "96": 24,   // 每 24 小時
      "97": 120   // 每 120 小時 (5天)
    },
    "post_race": {
      "97": 4     // 賽後模式：每 4 小時
    },
    "pre_race": {
      "96": 6     // 賽前模式：每 6 小時
    }
  }
}
```

### **關鍵配置項**

| 配置項 | 說明 | 預設值 |
|-------|------|--------|
| `api.timeout` | API 請求超時（秒） | 120 |
| `functions.*.enabled` | 是否啟用該功能 | true |
| `update_intervals.*.*` | 更新間隔（小時） | 見上表 |
| `logging.level` | 日誌等級 | INFO |
| `service.check_interval_seconds` | 主循環檢查間隔（秒） | 60 |

---

## 🚀 運行服務

### **方式 1: 前景運行（推薦用於測試）**

```powershell
# 直接運行（可看到即時日誌）
python scripts/periodic_update_service.py

# 輸出示例：
# ============================================================
# 🎯 定時 API 更新服務啟動
# ============================================================
# 📁 配置檔案: scripts/config/update_service_config.json
# 🔄 模式切換: none → normal
#    新模式: 平時維護模式
# 📅 調度任務 - 模式: normal
#    ✅ F96 賽事天氣預報: 每 24 小時
#    ✅ F97 賽季積分查詢: 每 120 小時
#    ✅ F98 顏色配置輸出: 每 168 小時
#    ✅ F99 賽季賽程查詢: 每 168 小時
# ✅ 服務運行中... (按 Ctrl+C 停止)
```

**停止服務**: 按 `Ctrl+C`

---

### **方式 2: 背景運行（用於生產環境）**

#### **Windows (使用 PowerShell)**

```powershell
# 方法 A: 使用 Start-Process (無視窗)
Start-Process powershell -ArgumentList "-NoProfile", "-Command", "python scripts/periodic_update_service.py" -WindowStyle Hidden

# 方法 B: 使用任務排程器（推薦）
# 1. 打開「任務排程器」
# 2. 建立基本任務
# 3. 觸發程序：「電腦啟動時」
# 4. 動作：「啟動程式」
#    程式: python.exe
#    引數: scripts/periodic_update_service.py
#    起始於: C:\Users\mike2\OneDrive\Code\F1-data-analyze
```

#### **Linux / macOS**

```bash
# 使用 nohup 背景運行
nohup python scripts/periodic_update_service.py > /dev/null 2>&1 &

# 使用 systemd (Linux)
# 1. 創建服務檔案: /etc/systemd/system/f1-update.service
# 2. 啟動服務: sudo systemctl start f1-update
# 3. 開機自啟: sudo systemctl enable f1-update
```

---

## 🧠 智能更新模式

### **模式切換邏輯**

服務每小時自動檢查一次當前應處於何種模式：

```
┌─────────────────────────────────────────┐
│ 載入賽程數據 (F99 season_calendar)      │
└───────────────┬─────────────────────────┘
                │
                ├─→ 最近完賽比賽結束 < 48h？
                │   ✅ 是 → 賽後密集模式
                │   ❌ 否 ↓
                │
                ├─→ 下一場比賽開始 < 72h？
                │   ✅ 是 → 賽前預熱模式
                │   ❌ 否 ↓
                │
                └─→ 平時維護模式
```

### **模式切換示例**

```
2025-10-15 08:00 [INFO] 🔄 模式切換: normal → pre_race
                        新模式: 賽前預熱模式
                        下一場: 第 19 站 United States Grand Prix (71.5 小時後)

2025-10-19 20:00 [INFO] 🔄 模式切換: pre_race → post_race
                        新模式: 賽後密集模式
                        最近完賽: 第 19 站 United States Grand Prix

2025-10-21 20:00 [INFO] 🔄 模式切換: post_race → normal
                        新模式: 平時維護模式
```

---

## 🔧 故障排除

### **問題 1: 服務無法啟動**

**症狀**:
```
[ERROR] 載入賽程數據失敗，服務無法啟動
```

**解決方案**:
```powershell
# 1. 檢查是否有賽程檔案
ls json/season_calendar_*.json

# 2. 如果沒有，手動生成
python f1_analysis_modular_main.py -f 99

# 3. 重新啟動服務
python scripts/periodic_update_service.py
```

---

### **問題 2: CLI 執行失敗**

**症狀**:
```
[ERROR] ❌ 執行失敗 (exit code: 1)
```

**解決方案**:
```powershell
# 1. 手動測試 CLI 功能
python f1_analysis_modular_main.py -f 96

# 2. 檢查日誌檔案
Get-Content logs/periodic_update_service.log -Tail 50

# 3. 檢查網路連線
curl https://localhost:8000/health
```

---

### **問題 3: 模式切換不正常**

**症狀**: 服務一直停留在某個模式

**解決方案**:
```powershell
# 1. 測試賽事檢測器
python scripts/race_event_detector.py

# 2. 檢查賽程數據是否最新
python f1_analysis_modular_main.py -f 99 --force

# 3. 重啟服務
```

---

## 📊 日誌系統

### **日誌位置**

```
logs/periodic_update_service.log
```

### **日誌等級**

- **DEBUG**: 詳細除錯資訊（包含 CLI 命令）
- **INFO**: 一般資訊（模式切換、任務執行）
- **WARNING**: 警告訊息（配置問題、輕微錯誤）
- **ERROR**: 錯誤訊息（CLI 執行失敗）

### **日誌輪轉**

- 單檔最大: 10MB
- 保留備份: 5 個
- 總容量: 約 50MB

### **查看日誌**

```powershell
# Windows PowerShell
Get-Content logs/periodic_update_service.log -Tail 50

# 即時監控
Get-Content logs/periodic_update_service.log -Wait
```

---

## 🔐 進階配置

### **修改更新頻率**

編輯 `scripts/config/update_service_config.json`:

```json
{
  "update_intervals": {
    "normal": {
      "96": 12,    // 改為每 12 小時
      "97": 24     // 改為每 24 小時
    }
  }
}
```

### **禁用特定功能**

```json
{
  "functions": {
    "98": {
      "name": "顏色配置輸出",
      "enabled": false   // 禁用 F98
    }
  }
}
```

### **調整錯誤重試**

```json
{
  "error_handling": {
    "strategy": "exponential_backoff",
    "initial_delay": 60,      // 初始延遲 60 秒
    "max_delay": 3600,        // 最大延遲 1 小時
    "max_retries": 3,         // 最多重試 3 次
    "continue_on_error": true // 錯誤後繼續運行
  }
}
```

---

## 📈 效能監控

### **執行統計**

日誌中會記錄每次執行的時長：

```
[INFO] 🚀 執行: F96 賽事天氣預報
[INFO]    ✅ 執行成功 (2.3s)
```

### **資源使用**

- **CPU**: 執行時短暫上升（< 5%），閒置時 < 1%
- **記憶體**: 約 50-100 MB
- **磁碟 I/O**: 執行時產生 JSON 檔案（每個 < 1MB）

---

## ✅ 最佳實踐

1. **定期檢查日誌** - 每週檢查一次日誌檔案，確保服務正常運行

2. **賽季開始前測試** - 每年賽季開始前（2-3月）手動執行一次所有功能

3. **備份數據** - 定期備份 `json/` 目錄

4. **網路穩定性** - 確保伺服器有穩定的網路連線

5. **系統資源** - 監控磁碟空間，確保有足夠空間存放日誌和數據

---

## 📞 支援與回饋

如有問題或建議，請聯絡 F1T Team 或提交 GitHub Issue。

---

**最後更新**: 2025-10-13  
**文檔版本**: 1.0.0
