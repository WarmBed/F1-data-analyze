# Function 100 快速上手指南

## 🎯 30 秒快速開始

### 單場分析
```powershell
# 執行單場 Function 100（18-43 秒）
python f1_analysis_modular_main.py -f 100 -y 2025 -r Brazil -s R
```

### 批量下載
```powershell
# 下載全部 24 場賽事（約 48 分鐘）
python batch_download_function100.py

# 僅下載 2025 年（約 12 分鐘）
python batch_download_function100.py --start-year 2025 --end-year 2025

# 下載特定賽道
python batch_download_function100.py --races Japan China Brazil
```

---

## 📊 核心改進

| 項目 | 改善 |
|------|------|
| 執行時間 | 600 秒 → 30 秒 (**20 倍加速**) |
| API 呼叫 | 1,420 次 → 20 次 (**98.6% 減少**) |
| 數據準確性 | **100% 維持**（346 km/h 驗證通過） |

---

## 🚀 常用命令

### 列出賽道
```powershell
python batch_download_function100.py --list
```

### 下載特定年份
```powershell
# 僅 2024 年
python batch_download_function100.py --start-year 2024 --end-year 2024

# 2023-2025 年
python batch_download_function100.py --start-year 2023 --end-year 2025
```

### 強制重新下載
```powershell
# 覆蓋所有現有檔案
python batch_download_function100.py --force

# 強制重新下載特定賽道
python batch_download_function100.py --races Japan --force
```

### 組合使用
```powershell
# 下載 2024-2025 的亞洲賽道
python batch_download_function100.py `
  --start-year 2024 `
  --races Bahrain Japan China Singapore Qatar

# 下載美洲賽事並強制覆蓋
python batch_download_function100.py `
  --races Miami "United States" Mexico Brazil `
  --force
```

---

## 🏎️ 支援賽道（24 場）

### 亞洲賽道（7 場）
```
Bahrain, Saudi Arabia, Japan, China, 
Singapore, Qatar, Abu Dhabi
```

### 歐洲賽道（10 場）
```
Emilia Romagna, Monaco, Spain, Austria, 
Great Britain, Hungary, Belgium, Netherlands, 
Italy, Azerbaijan
```

### 美洲賽道（5 場）
```
Australia, Miami, Canada, United States, 
Mexico, Brazil
```

### 特殊賽道（2 場）
```
Las Vegas, Monaco（街道賽）
```

---

## 🛠️ 疑難排解

### 問題：執行超過 10 分鐘
```powershell
# 解決：檢查是否使用優化版本
grep -r "get_telemetry()" CLI_modules/cli/analyzer/historical_flags_analysis.py
# 應該看到：driver_laps.get_telemetry()（批量載入）
```

### 問題：數據不正確
```powershell
# 驗證 2025 Brazil 應為 346 km/h
python check_2025_speed.py
```

### 問題：批量下載中斷
```powershell
# 重新執行（會自動跳過已完成的）
python batch_download_function100.py
```

---

## 📁 輸出檔案位置

```
json/historical_flags_with_speed_2025_Brazil_R_20250115_123456.json
     └─功能名稱────────┘ └年┘ └賽道┘ └會話┘ └──時間戳記───┘
```

---

## ⏱️ 執行時間參考

| 任務 | 耗時 | 備註 |
|------|------|------|
| 單場分析 | 18-43 秒 | 優化後 |
| 單一年份（24 場） | 12 分鐘 | 需良好網路 |
| 全部 4 年（96 場） | 48 分鐘 | 首次含緩存下載 |
| 特定 3 賽道 | 2-3 分鐘 | - |

---

## 📚 完整文檔

- **完整解決方案：** `FUNCTION_100_COMPLETE_SOLUTION.md`
- **批量下載指南：** `BATCH_DOWNLOAD_GUIDE.md`
- **優化報告：** `FUNCTION_100_OPTIMIZATION_REPORT.md`
- **修復報告：** `FUNCTION_100_FIX_REPORT.md`

---

## 💡 最佳實踐

1. **首次執行：** 從單場開始測試
   ```powershell
   python f1_analysis_modular_main.py -f 100 -y 2025 -r Japan -s R
   ```

2. **批量下載：** 先列出賽道確認
   ```powershell
   python batch_download_function100.py --list
   ```

3. **錯誤處理：** 檢查日誌檔案
   ```powershell
   Get-Content logs\f1_analysis.log -Tail 50
   ```

4. **驗證數據：** 使用驗證腳本
   ```powershell
   python verify_max_speed.py
   ```

---

## 🎓 技術說明

### 優化原理
```python
# 舊方式：1,420 次 API 呼叫
for driver in drivers:  # 20
    for lap in laps:  # 71
        telemetry = lap.get_telemetry()  # 慢！

# 新方式：20 次 API 呼叫
for driver in drivers:  # 20
    driver_laps = session.laps.pick_driver(driver)
    telemetry = driver_laps.get_telemetry()  # 快！
```

### 數據驗證
```python
# 確保使用完整遙測數據
max_speed = driver_telemetry['Speed'].max()
# 而非速度陷阱：laps['SpeedST'].max()
```

---

## ✅ 快速檢查清單

開始前確認：
- [ ] Python 環境已安裝
- [ ] FastF1 套件已更新
- [ ] 網路連線穩定
- [ ] 磁碟空間充足（約 5 GB）

執行後驗證：
- [ ] 執行時間 < 1 分鐘/場
- [ ] JSON 檔案已生成
- [ ] 最高速度數據正確
- [ ] 無錯誤訊息

---

**文檔版本：** v1.0.0  
**快速參考：** 列印此頁面以便隨時查閱  
**更新日期：** 2025-01-XX
