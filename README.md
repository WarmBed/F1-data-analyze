# F1T Racing Data Analysis - GUI Edition

## 🏎️ 專案概覽

F1T-LOCAL-V13 是一個專業的F1賽車數據分析系統，提供完整的GUI界面和模組化分析功能。

## 🚀 快速啟動

### GUI模式 (推薦)
```bash
# 方式1: 使用批次檔案
Start_F1T_GUI.bat

# 方式2: 直接運行Python
python main.py
```

### CLI模式
```bash
# 使用主CLI程式
python f1_analysis_modular_main.py

# 使用簡化CLI程式  
python f1_analysis_simple.py
```

### API服務模式
```bash
# 啟動API服務器
python APIserver.py
# 或使用批次檔案
Start_API_Server.bat
```

## 📋 主要功能

### 🌧️ 天氣分析模組
- 降雨強度分析
- 天氣變化趨勢

### 🏁 賽道分析模組
- 賽道特性分析
- 賽道位置數據

### 🔧 進站策略模組
- 進站時間分析
- 策略效果評估

### 🏎️ 車手分析模組
- 單車手詳細分析
- 車手遙測數據
- 圈速表現分析

### ⚖️ 比較分析模組
- 車手間比較
- 距離差距分析

### 📊 統計分析模組
- 綜合統計報告
- 性能趨勢分析

## 📁 專案結構

```
F1T-LOCAL-V13/
├── main.py                    # 主GUI啟動器
├── simplified_f1t_gui.py      # 主GUI實現
├── f1_analysis_modular_main.py # CLI主程式
├── APIserver.py               # REST API服務
├── modules/                   # 分析模組目錄
│   ├── analysis_module_manager.py
│   ├── gui_modules/          # GUI相關模組
│   └── *.py                  # 各種分析模組
├── cache/                    # 數據快取
├── json/                     # JSON輸出
├── logs/                     # 日誌檔案
├── testcode/                 # 測試程式碼
├── testGUI/                  # GUI測試
└── archive/                  # 存檔檔案
    ├── debug_files/         # 調試檔案
    ├── reports/             # 開發報告
    ├── old_gui/             # 舊GUI檔案
    └── old_cache/           # 舊快取檔案
```

## 🔧 系統需求

- Python 3.8+
- PyQt5
- fastf1
- pandas
- numpy
- matplotlib
- requests

## 💡 使用提示

1. **首次使用**: 建議先運行GUI模式熟悉界面
2. **數據載入**: 選擇年份、賽事、會話後點擊"載入數據"
3. **分析執行**: 從左側樹狀結構選擇分析模組，點擊"執行分析"
4. **結果查看**: 分析結果會顯示在右側區域
5. **JSON輸出**: 所有分析結果自動保存為JSON格式

## 🐛 故障排除

### GUI無法啟動
- 檢查Python和PyQt5安裝
- 確認當前目錄為專案根目錄
- 查看終端輸出的錯誤訊息

### 數據載入失敗
- 檢查網路連接
- 確認選擇的賽事數據可用
- 查看cache目錄權限

### 分析執行錯誤
- 確保已正確載入數據
- 檢查logs目錄中的錯誤日誌
- 嘗試重新啟動程式

## 📝 開發說明

本專案採用模組化架構，所有分析功能都封裝在獨立模組中。GUI和CLI共享相同的分析引擎，確保結果一致性。

更多技術細節請參考 `archive/reports/` 目錄中的開發文檔。

---

**版本**: V13  
**更新日期**: 2025-08-24  
**開發狀態**: 穩定版本 ✅
