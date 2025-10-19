# F1T NSSM Service Monitor - 獨立監控工具

**版本**: 1.0.0  
**最後更新**: 2025-10-13

---

## 📋 功能概述

F1T NSSM Service Monitor 是一個獨立的 PyQt5 GUI 應用程式，專門用於監控和管理 F1T 專案的三個 NSSM Windows 服務。

### 核心功能

| 功能 | 描述 | 狀態 |
|------|------|------|
| 🔄 **即時狀態監控** | 每 3 秒自動刷新服務狀態 | ✅ |
| 📊 **資源使用監控** | 顯示 CPU/記憶體使用率 | ✅ |
| 🎮 **服務控制** | 啟動/停止/重啟服務按鈕 | ✅ |
| 📝 **日誌查看器** | 即時查看服務日誌 | ✅ |
| 🔍 **日誌搜尋** | 搜尋特定關鍵字的日誌條目 | ✅ |
| 📈 **歷史圖表** | 顯示服務狀態歷史（開發中） | 🚧 |
| 🎨 **深色主題** | 專業的深色 UI 介面 | ✅ |

---

## 🚀 快速開始

### 方法 1：雙擊啟動（推薦）

```batch
雙擊執行: nssm\Launch_Monitor.bat
```

### 方法 2：命令列啟動

```powershell
cd nssm
python nssm_monitor_gui.py
```

### 方法 3：從主目錄啟動

```powershell
python nssm\nssm_monitor_gui.py
```

---

## 📦 安裝依賴

如果遇到缺少套件的錯誤，請安裝依賴：

```powershell
pip install -r nssm\requirements_monitor.txt
```

**必需套件**:
- `PyQt5` - GUI 框架
- `psutil` - 進程監控

**可選套件**:
- `rich` - 終端美化（用於調試）
- `watchdog` - 檔案監控（用於日誌變化通知）
- `PyQtChart` - 圖表顯示（用於歷史圖表）

---

## 🎯 介面說明

### Tab 1: 服務狀態

顯示三個服務的即時狀態：

```
┌──────────────────────────────────────────────────┐
│  F1T-API          F1T-PeriodicUpdate  F1T-Tunnel│
│  ● 運行中          ● 運行中             ● 運行中 │
│  PID: 12345       PID: 12346          PID: 12347│
│  CPU: 2.3%        CPU: 0.1%           CPU: 0.5% │
│  記憶體: 49.7 MB   記憶體: 32.1 MB      記憶體: 36.5 MB│
│  運行時間: 2h 15m  運行時間: 2h 15m     運行時間: 2h 15m│
│  ▓▓▓░░░░░░░        █░░░░░░░░░          ██░░░░░░░░│
│  [啟動][停止][重啟][查看日誌]                      │
└──────────────────────────────────────────────────┘
```

**功能說明**:
- 🟢 **綠色圓點** - 服務正在運行
- 🔴 **紅色圓點** - 服務已停止
- 🟠 **橙色圓點** - 服務狀態異常
- ⚪ **灰色圓點** - 服務未安裝

**控制按鈕**:
- **啟動** - 啟動單一服務
- **停止** - 停止單一服務（需確認）
- **重啟** - 重啟單一服務
- **查看日誌** - 跳轉到日誌頁面

### Tab 2: 日誌查看

即時查看和搜尋服務日誌：

```
┌──────────────────────────────────────────────────┐
│  服務: [F1T-API ▼]  類型: [標準輸出 ▼]  [刷新] [清空]│
│  搜尋: [____________] [搜尋]                      │
├──────────────────────────────────────────────────┤
│  [2025-10-13 15:30:42] [SUCCESS] Request OK     │
│  [2025-10-13 15:30:45] [INFO] Processing data    │
│  [2025-10-13 15:30:48] [SUCCESS] Response sent   │
│  ...                                              │
│                                                   │
├──────────────────────────────────────────────────┤
│  總行數: 523 | 檔案大小: 156.7 KB                 │
└──────────────────────────────────────────────────┘
```

**功能說明**:
- **服務選擇** - 選擇要查看的服務
- **類型選擇** - 標準輸出或錯誤輸出
- **刷新按鈕** - 重新載入日誌
- **清空按鈕** - 清空日誌檔案（需確認）
- **搜尋框** - 輸入關鍵字過濾日誌
- **狀態列** - 顯示總行數和檔案大小

### Tab 3: 歷史圖表（開發中）

將顯示服務狀態的歷史圖表。

---

## 🛠️ 架構說明

### 檔案結構

```
nssm/
├── nssm_monitor_gui.py           # 主 GUI 應用程式
├── service_monitor.py            # 核心監控模組
├── Launch_Monitor.bat            # 啟動腳本
├── requirements_monitor.txt      # 依賴清單
├── MONITOR_README.md             # 本文件
└── logs/                         # NSSM 服務日誌目錄
    ├── f1t-api.log
    ├── f1t-api.error.log
    ├── periodic-update.log
    ├── periodic-update.error.log
    ├── cloudflare-tunnel.log
    └── cloudflare-tunnel.error.log
```

### 核心類別

#### 1. `NSSMServiceMonitor` (service_monitor.py)

核心監控類別，提供服務管理功能：

```python
class NSSMServiceMonitor:
    def get_service_status(service_name) -> Dict
    def start_service(service_name) -> bool
    def stop_service(service_name) -> bool
    def restart_service(service_name) -> bool
    def get_service_logs(service_name, tail, error_log) -> List[str]
    def get_all_services_status() -> Dict
    def check_admin_privileges() -> bool
```

#### 2. `ServiceStatusWidget` (nssm_monitor_gui.py)

單一服務狀態顯示 Widget：

```python
class ServiceStatusWidget(QGroupBox):
    def update_status()          # 更新服務狀態
    def start_service()          # 啟動服務
    def stop_service()           # 停止服務
    def restart_service()        # 重啟服務
    def view_logs()              # 查看日誌
```

#### 3. `LogViewerWidget` (nssm_monitor_gui.py)

日誌查看器 Widget：

```python
class LogViewerWidget(QWidget):
    def load_logs()              # 載入日誌
    def filter_logs()            # 過濾日誌
    def clear_logs()             # 清空日誌
    def show_service_logs(name)  # 顯示指定服務日誌
```

#### 4. `NSSMMonitorGUI` (nssm_monitor_gui.py)

主視窗類別：

```python
class NSSMMonitorGUI(QMainWindow):
    def refresh_all_status()     # 刷新所有狀態
    def start_all_services()     # 啟動所有服務
    def stop_all_services()      # 停止所有服務
    def restart_all_services()   # 重啟所有服務
```

---

## ⚙️ 配置說明

### 自動刷新頻率

預設每 3 秒刷新一次，可在 `nssm_monitor_gui.py` 中修改：

```python
# 行 ~550
self.refresh_timer.start(3000)  # 毫秒，改為 5000 即 5 秒
```

### 日誌顯示行數

預設顯示最後 500 行，可在 `LogViewerWidget.load_logs()` 中修改：

```python
# 行 ~240
logs = self.monitor.get_service_logs(service_name, tail=500, ...)
```

### 深色主題

如需切換為淺色主題，註解掉 `main()` 函數中的 Palette 設定。

---

## 🔧 進階功能

### 命令列測試

測試核心監控模組：

```powershell
cd nssm
python service_monitor.py
```

輸出範例：
```
============================================================
F1T NSSM 服務監控測試
============================================================

服務: F1T-API
------------------------------------------------------------
存在: True
狀態: RUNNING
PID: 12345
啟動類型: AUTO_START
CPU: 2.3%
記憶體: 49.7 MB

最新日誌 (前 5 行):
  [2025-10-13 15:30:42] [SUCCESS] Request OK
  ...
```

### 管理員權限檢測

工具會自動檢測管理員權限：
- ✅ **有權限** - 所有功能正常使用
- ❌ **無權限** - 啟動/停止/重啟操作會失敗

**解決方案**：以管理員身份執行工具
```powershell
# PowerShell 以管理員身份執行
Start-Process python -Verb RunAs -ArgumentList "nssm\nssm_monitor_gui.py"
```

---

## 🐛 故障排除

### 問題 1: 無法啟動 GUI

**錯誤**: `ModuleNotFoundError: No module named 'PyQt5'`

**解決方案**:
```powershell
pip install PyQt5 psutil
```

### 問題 2: 服務控制失敗

**錯誤**: 點擊啟動/停止按鈕沒有反應

**原因**: 沒有管理員權限

**解決方案**:
```powershell
# 以管理員身份執行
右鍵點擊 Launch_Monitor.bat → 以系統管理員身分執行
```

### 問題 3: 日誌無法載入

**錯誤**: 日誌顯示區顯示 "找不到日誌檔案"

**原因**: 日誌目錄不存在或路徑錯誤

**解決方案**:
```powershell
# 確認日誌目錄
Test-Path nssm\logs
# 如不存在，創建目錄
New-Item -ItemType Directory -Path nssm\logs
```

### 問題 4: 編碼問題

**錯誤**: 日誌顯示亂碼

**原因**: Windows 系統編碼問題

**解決方案**: 修改 `service_monitor.py` 中的編碼設定：
```python
# 行 ~200
with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
# 改為
with open(log_file, 'r', encoding='cp950', errors='ignore') as f:
```

---

## 📊 效能考量

### 資源使用

工具本身的資源使用：
- **CPU**: < 1% （閒置時）
- **記憶體**: ~50-80 MB
- **網路**: 0（完全本地運行）

### 刷新頻率建議

| 場景 | 建議頻率 | 說明 |
|------|---------|------|
| 開發調試 | 1-2 秒 | 快速發現問題 |
| 日常監控 | 3-5 秒 | 平衡性能與即時性 |
| 後台監控 | 10 秒 | 降低資源消耗 |

---

## 🚧 未來功能

### V1.1 計劃

- [ ] **歷史圖表實現** - 顯示 CPU/記憶體使用率歷史
- [ ] **警報通知** - 服務停止時桌面通知
- [ ] **系統托盤** - 最小化到系統托盤
- [ ] **日誌即時監控** - 使用 watchdog 監控日誌變化
- [ ] **匯出報告** - 匯出服務狀態報告（PDF/HTML）

### V1.2 計劃

- [ ] **遠端監控** - 監控其他機器上的服務
- [ ] **多語言支援** - 英文/中文切換
- [ ] **自定義主題** - 更多 UI 主題選擇
- [ ] **效能分析** - 詳細的效能分析工具

---

## 🤝 整合到主程式（可選）

如需將監控工具整合到 F1T 主程式：

### 方法 1: 選單項目

在 `f1t_gui_main.py` 中添加：

```python
# 工具選單
tools_menu = menubar.addMenu("工具")

# NSSM 監控器
monitor_action = QAction("NSSM 服務監控", self)
monitor_action.triggered.connect(self.open_nssm_monitor)
tools_menu.addAction(monitor_action)

def open_nssm_monitor(self):
    """開啟 NSSM 監控工具"""
    import subprocess
    subprocess.Popen(["python", "nssm/nssm_monitor_gui.py"])
```

### 方法 2: 狀態列 Widget

在狀態列顯示服務摘要：

```python
from nssm.service_monitor import NSSMServiceMonitor

# 在狀態列添加服務狀態
self.service_status_label = QLabel()
self.statusBar().addPermanentWidget(self.service_status_label)

# 定時更新
def update_service_status():
    monitor = NSSMServiceMonitor()
    status = monitor.get_all_services_status()
    running = sum(1 for s in status.values() if s["state"] == "RUNNING")
    self.service_status_label.setText(f"服務: {running}/3")
```

---

## 📝 開發筆記

### 設計原則

1. **獨立性** - 完全獨立運行，不依賴主程式
2. **輕量化** - 最小化依賴，快速啟動
3. **易用性** - 直覺的 UI，清晰的操作
4. **安全性** - 服務控制需確認，避免誤操作

### 技術選擇

- **PyQt5**: 成熟的跨平台 GUI 框架
- **psutil**: 跨平台的進程監控庫
- **subprocess**: 調用 Windows 系統命令
- **rich**: （可選）美化終端輸出

---

## 📄 授權

本工具是 F1 TelemetryStation Pro 專案的一部分，遵循 MIT 授權條款。

---

## 🔗 相關文件

- **NSSM 指南**: `nssm/NSSM_GUIDE.md`
- **日誌遷移**: `nssm/NSSM_LOG_MIGRATION_GUIDE.md`
- **服務安裝**: `nssm/install-services.ps1`
- **主專案**: `../README.md`

---

**最後更新**: 2025-10-13  
**版本**: 1.0.0  
**作者**: WarmBed + GitHub Copilot
