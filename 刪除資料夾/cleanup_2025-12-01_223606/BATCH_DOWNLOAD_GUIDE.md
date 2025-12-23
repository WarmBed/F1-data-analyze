# Function 100 批量下載工具使用指南

## 🎯 功能說明

`batch_download_function100.py` 是一個批量下載所有 F1 賽道歷年旗幟統計數據的工具。

### 主要特點
- ✅ 自動下載 24 個賽道的完整數據
- ✅ 支援自定義年份範圍（預設 2022-2025）
- ✅ 智能跳過已存在的檔案
- ✅ 錯誤處理與超時保護
- ✅ 詳細的進度顯示與統計報告

---

## 📋 基本使用

### 1. 下載所有賽道（預設）
```powershell
python batch_download_function100.py
```
- 年份範圍：2022-2025
- 賽道數量：24 場
- 預估時間：15-30 分鐘（取決於緩存）

### 2. 列出所有可用賽道
```powershell
python batch_download_function100.py --list
```

輸出範例：
```
可用賽道列表:
  1. Bahrain
  2. Saudi Arabia
  3. Australia
  ...
  24. Abu Dhabi

總計: 24 場賽事
```

---

## 🔧 進階選項

### 自定義年份範圍
```powershell
# 下載 2020-2025 年數據
python batch_download_function100.py --start-year 2020 --end-year 2025
```

### 只下載特定賽道
```powershell
# 只下載日本、中國、巴西
python batch_download_function100.py --races Japan China Brazil

# 只下載歐洲賽道
python batch_download_function100.py --races Monaco Spain Italy Belgium Netherlands
```

### 強制重新生成
```powershell
# 即使檔案已存在，也重新下載
python batch_download_function100.py --force

# 組合使用：重新下載特定賽道
python batch_download_function100.py --races Japan Brazil --force
```

### 組合選項
```powershell
# 下載 2023-2025 年的亞洲賽道（強制重新生成）
python batch_download_function100.py --start-year 2023 --races Japan China Singapore Qatar --force
```

---

## 📊 執行範例

### 輸出畫面
```
======================================================================
🏁 F1 歷年旗幟統計批量下載工具
======================================================================
年份範圍: 2022-2025
賽道數量: 24
強制重新生成: 否
開始時間: 2025-11-12 00:30:00
======================================================================

[進度 1/24] 處理: Bahrain
執行命令: python f1_analysis_modular_main.py -f 100 -y 2025 -r Bahrain
✅ 成功生成 JSON (耗時: 25.3秒)

[進度 2/24] 處理: Saudi Arabia
執行命令: python f1_analysis_modular_main.py -f 100 -y 2025 -r Saudi Arabia
⏭️  檔案已存在，跳過

[進度 3/24] 處理: Australia
...
```

### 完成報告
```
======================================================================
📊 批量下載完成報告
======================================================================
總耗時: 1234.5 秒 (20.6 分鐘)
總賽道數: 24
✅ 成功: 20 場
⏭️  跳過: 3 場
❌ 失敗: 1 場

✅ 成功生成的賽道 (20):
   - Bahrain              (25.3秒)
   - Australia            (32.1秒)
   - Japan                (28.7秒)
   ...

⏭️  已跳過的賽道 (3):
   - Saudi Arabia         (檔案已存在)
   - China                (檔案已存在)
   - Brazil               (檔案已存在)

❌ 失敗的賽道 (1):
   - Monaco               ❌ 執行超時（> 10 分鐘）

⏱️  平均處理時間: 31.2 秒/場
======================================================================
完成時間: 2025-11-12 00:50:45
======================================================================
```

---

## 📁 生成檔案

所有生成的 JSON 檔案會儲存在 `json/` 目錄：

```
json/
├── historical_flags_Bahrain_2022-2025.json
├── historical_flags_Saudi Arabia_2022-2025.json
├── historical_flags_Australia_2022-2025.json
├── historical_flags_Japan_2022-2025.json
├── historical_flags_China_2022-2025.json
...
└── historical_flags_Abu Dhabi_2022-2025.json
```

---

## ⚠️ 注意事項

### 執行時間
- **單個賽道**：20-60 秒（取決於是否有緩存）
- **所有賽道（24 場）**：15-30 分鐘
- **首次執行**：需要下載 FastF1 數據，會較慢

### 超時處理
- 每個賽道最長執行時間：10 分鐘
- 超時會自動跳過並記錄失敗

### 緩存機制
- 已下載的 FastF1 數據會緩存在 `cache/` 目錄
- 已生成的 JSON 檔案預設會跳過（除非使用 `--force`）

### 錯誤重試
- 失敗的賽道不會自動重試
- 可以記錄失敗清單，稍後手動重試：
  ```powershell
  python batch_download_function100.py --races Monaco Belgium --force
  ```

---

## 🔍 故障排除

### 問題 1: 執行超時
**症狀**: 某些賽道顯示 "執行超時（> 10 分鐘）"

**解決方案**:
1. 單獨執行該賽道確認問題：
   ```powershell
   python f1_analysis_modular_main.py -f 100 -y 2025 -r Monaco
   ```
2. 檢查是否為數據問題或網路問題
3. 清理緩存後重試：
   ```powershell
   Remove-Item cache/* -Recurse -Force
   ```

### 問題 2: 部分賽道失敗
**症狀**: 顯示 "執行失敗" 或其他錯誤

**解決方案**:
1. 查看 log 檔案了解詳細錯誤：
   ```powershell
   Get-Content logs/f1_cli_*.log -Tail 50
   ```
2. 針對失敗賽道使用 `--force` 重新執行

### 問題 3: 記憶體不足
**症狀**: 系統變慢或程式崩潰

**解決方案**:
1. 分批執行（每次 5-10 個賽道）：
   ```powershell
   # 第一批
   python batch_download_function100.py --races Bahrain "Saudi Arabia" Australia Japan China
   
   # 第二批
   python batch_download_function100.py --races Miami Monaco Canada Spain Austria
   ```
2. 關閉其他程式釋放記憶體

---

## 💡 使用技巧

### 技巧 1: 快速更新新賽季數據
```powershell
# 只下載 2025 年數據（最快）
python batch_download_function100.py --start-year 2025 --end-year 2025
```

### 技巧 2: 檢查缺少的賽道
```powershell
# 列出 json 目錄中的檔案，找出缺少的賽道
Get-ChildItem json/historical_flags_*_2022-2025.json | ForEach-Object { $_.Name }
```

### 技巧 3: 平行處理（進階）
如果要更快完成，可以開多個終端分別執行：

**終端 1**:
```powershell
python batch_download_function100.py --races Bahrain "Saudi Arabia" Australia Japan China
```

**終端 2**:
```powershell
python batch_download_function100.py --races Miami Monaco Canada Spain Austria
```

**終端 3**:
```powershell
python batch_download_function100.py --races "Great Britain" Hungary Belgium Netherlands Italy
```

---

## 📚 賽道列表完整清單

| 編號 | 賽道名稱 | 英文名稱 | 賽事站次 |
|------|----------|----------|----------|
| 1 | 巴林 | Bahrain | 第 1 站 |
| 2 | 沙烏地阿拉伯 | Saudi Arabia | 第 2 站 |
| 3 | 澳洲 | Australia | 第 3 站 |
| 4 | 日本 | Japan | 第 4 站 |
| 5 | 中國 | China | 第 5 站 |
| 6 | 邁阿密 | Miami | 第 6 站 |
| 7 | 艾米利亞-羅馬涅 | Emilia Romagna | 第 7 站 |
| 8 | 摩納哥 | Monaco | 第 8 站 |
| 9 | 加拿大 | Canada | 第 9 站 |
| 10 | 西班牙 | Spain | 第 10 站 |
| 11 | 奧地利 | Austria | 第 11 站 |
| 12 | 英國 | Great Britain | 第 12 站 |
| 13 | 匈牙利 | Hungary | 第 13 站 |
| 14 | 比利時 | Belgium | 第 14 站 |
| 15 | 荷蘭 | Netherlands | 第 15 站 |
| 16 | 義大利 | Italy | 第 16 站 |
| 17 | 亞塞拜然 | Azerbaijan | 第 17 站 |
| 18 | 新加坡 | Singapore | 第 18 站 |
| 19 | 美國 | United States | 第 19 站 |
| 20 | 墨西哥 | Mexico | 第 20 站 |
| 21 | 巴西 | Brazil | 第 21 站 |
| 22 | 拉斯維加斯 | Las Vegas | 第 22 站 |
| 23 | 卡達 | Qatar | 第 23 站 |
| 24 | 阿布達比 | Abu Dhabi | 第 24 站 |

---

## 🚀 快速開始

```powershell
# 1. 列出所有賽道
python batch_download_function100.py --list

# 2. 下載全部（第一次執行）
python batch_download_function100.py

# 3. 更新特定賽道
python batch_download_function100.py --races Japan Brazil --force

# 4. 下載新賽季
python batch_download_function100.py --start-year 2025 --end-year 2025 --force
```

---

**腳本版本**: v1.0  
**最後更新**: 2025-11-12  
**相容性**: Python 3.8+, Windows PowerShell
