# F47 批次下載腳本使用說明

## 📋 腳本資訊

**檔案位置：** `scripts/batch_f47_2025_to_mexico.py`

**功能：** 批次執行 Function 47（全車手彎道分析），下載 2025 年全季賽事數據

**下載順序：** 墨西哥站 (R20) → 澳洲站 (R1) ⚠️ 反向下載

**包含會話：** R（正賽）、Q（排位賽）、FP1/FP2/FP3（練習賽）

**新功能：** ✨ 包含插值法修復（自動修復缺失的 Entry/Exit 50m 數據）

---

## 🚀 快速啟動

### 基本執行
```powershell
python scripts/batch_f47_2025_to_mexico.py
```

### 執行時選項
執行後會詢問兩個問題：

1. **是否跳過已存在的 JSON 檔案？(Y/n):**
   - 按 `Enter` 或輸入 `Y`：跳過已下載的檔案（推薦）
   - 輸入 `n`：重新下載所有檔案（覆蓋）

2. **是否顯示詳細輸出？(y/N):**
   - 按 `Enter` 或輸入 `N`：靜默模式（推薦，速度更快）
   - 輸入 `y`：顯示每個分析的詳細輸出

---

## 📊 下載範圍

### 賽事列表（20 場 × 5 會話 = 100 個檔案）

| 順序 | Round | 賽事 | 會話 |
|------|-------|------|------|
| 1 | R20 | 墨西哥 (Mexico) | R, Q, FP1, FP2, FP3 |
| 2 | R19 | 美國 (United States) | R, Q, FP1, FP2, FP3 |
| 3 | R18 | 新加坡 (Singapore) | R, Q, FP1, FP2, FP3 |
| 4 | R17 | 亞塞拜然 (Azerbaijan) | R, Q, FP1, FP2, FP3 |
| 5 | R16 | 義大利 (Italy) | R, Q, FP1, FP2, FP3 |
| 6 | R15 | 荷蘭 (Netherlands) | R, Q, FP1, FP2, FP3 |
| 7 | R14 | 匈牙利 (Hungary) | R, Q, FP1, FP2, FP3 |
| 8 | R13 | 比利時 (Belgium) | R, Q, FP1, FP2, FP3 |
| 9 | R12 | 英國 (Great Britain) | R, Q, FP1, FP2, FP3 |
| 10 | R11 | 奧地利 (Austria) | R, Q, FP1, FP2, FP3 |
| 11 | R10 | 加拿大 (Canada) | R, Q, FP1, FP2, FP3 |
| 12 | R9 | 西班牙 (Spain) | R, Q, FP1, FP2, FP3 |
| 13 | R8 | 摩納哥 (Monaco) | R, Q, FP1, FP2, FP3 |
| 14 | R7 | 艾米利亞-羅馬涅 (Emilia Romagna) | R, Q, FP1, FP2, FP3 |
| 15 | R6 | 邁阿密 (Miami) | R, Q, FP1, FP2, FP3 |
| 16 | R5 | 沙烏地阿拉伯 (Saudi Arabia) | R, Q, FP1, FP2, FP3 |
| 17 | R4 | 巴林 (Bahrain) | R, Q, FP1, FP2, FP3 |
| 18 | R3 | 日本 (Japan) | R, Q, FP1, FP2, FP3 |
| 19 | R2 | 中國 (China) | R, Q, FP1, FP2, FP3 |
| 20 | R1 | 澳洲 (Australia) | R, Q, FP1, FP2, FP3 |

---

## 📂 輸出位置

所有 JSON 檔案將保存在：
```
json/all_drivers_cornering_analysis_2025_{賽事}_{會話}.json
```

範例：
- `json/all_drivers_cornering_analysis_2025_Mexico_R.json`
- `json/all_drivers_cornering_analysis_2025_Mexico_Q.json`
- `json/all_drivers_cornering_analysis_2025_United_States_R.json`

---

## ⚡ 性能預估

**單場賽事時間：**
- 正賽 (R)：約 3-5 分鐘
- 排位賽 (Q)：約 2-3 分鐘  
- 練習賽 (FP1/2/3)：約 2-3 分鐘

**全季下載時間：**
- **100 個會話 × 3 分鐘 = 約 5 小時**
- 實際時間因網路速度和系統效能而異

**建議：**
- 🌙 睡前啟動，隔天早上完成
- ☕ 分批下載（先下載最近的賽事）

---

## ✨ 新功能：插值法修復

**問題：** 部分車手在 T13 等彎道缺失 Entry/Exit 50m 數據

**解決方案：** 三層數據獲取策略
1. 標準容差範圍（±10m）
2. 擴大容差範圍（±15m, ±20m）
3. 線性插值估算

**預期改善：**
- 修改前：18/20 車手數據完整（90%）
- 修改後：19-20/20 車手數據完整（95-100%）

---

## 🔍 進度監控

### 即時進度條
腳本會顯示：
```
總進度 |████████████████████░░░░░░░| 80/100 [80.0%] ETA: 3600s
[20] Mexico               - R
```

### 最終統計
```
統計資訊：
  - ✅ 成功：95 個會話
  - ❌ 失敗：2 個會話
  - ⏭️  跳過：3 個會話（已存在）
  - 📊 總計：100 個會話

⏱️  執行時間：18000.0 秒 (300.0 分鐘)
```

---

## ⚠️ 常見問題

### Q1: 為什麼從墨西哥往回下載？
**A:** 最新的賽事數據最有價值，優先下載確保不會因中斷而錯過最新數據。

### Q2: 下載途中可以中斷嗎？
**A:** 可以！按 `Ctrl+C` 中斷，下次執行時選擇「跳過已存在檔案」即可繼續。

### Q3: 如何只下載特定賽事？
**A:** 修改 `get_2025_races()` 函數，只保留需要的賽事。

### Q4: JSON 檔案太大怎麼辦？
**A:** 單個 JSON 約 0.5-1 MB，100 個檔案約 50-100 MB，空間充足。

### Q5: 插值法會影響數據準確性嗎？
**A:** 插值僅在原始數據缺失時使用，且限制在 30m 範圍內，確保合理性。

---

## 📝 使用範例

### 範例 1：首次完整下載
```powershell
PS> python scripts/batch_f47_2025_to_mexico.py
是否跳過已存在的 JSON 檔案？(Y/n): Y
是否顯示詳細輸出？(y/N): N

開始執行...
總進度 |████████████████████████████| 100/100 [100%]
執行完成！
```

### 範例 2：續傳下載
```powershell
PS> python scripts/batch_f47_2025_to_mexico.py
是否跳過已存在的 JSON 檔案？(Y/n): Y  ← 跳過已下載
是否顯示詳細輸出？(y/N): N

統計資訊：
  - ✅ 成功：15 個會話
  - ⏭️  跳過：85 個會話（已存在）
```

### 範例 3：除錯模式
```powershell
PS> python scripts/batch_f47_2025_to_mexico.py
是否跳過已存在的 JSON 檔案？(Y/n): n  ← 重新下載
是否顯示詳細輸出？(y/N): y  ← 顯示詳細輸出

[20] Mexico - R
  [START] 開始執行動態彎道檢測分析...
  [SELECT] low_speed: T13 (平均速度 68.5 km/h)
  ✅ 成功
```

---

## 🎯 執行建議

### 最佳實踐
1. **首次執行：** 
   - 跳過已存在：`Y`
   - 詳細輸出：`N`
   - 讓它自動運行

2. **續傳執行：**
   - 跳過已存在：`Y`
   - 詳細輸出：`N`

3. **除錯執行：**
   - 跳過已存在：`n`
   - 詳細輸出：`y`
   - 僅用於測試或除錯

### 優化建議
- 使用 SSD 硬碟加快 JSON 寫入
- 確保穩定的網路連線
- 關閉不必要的背景程式

---

## 📊 驗證下載結果

### 快速驗證
```powershell
# 檢查 JSON 檔案數量
Get-ChildItem json/all_drivers_cornering_analysis_2025_*.json | Measure-Object

# 應該看到接近 100 個檔案
```

### 詳細驗證
```powershell
# 使用我們的驗證腳本
python verify_interpolation_fix.py
```

---

## 🔧 進階用法

### 只下載正賽 (R)
修改 `get_2025_races()` 的 `sessions` 欄位：
```python
{"round": 20, "name": "Mexico", "sessions": ["R"]},  # 只下載正賽
```

### 只下載最近 5 場
修改 `get_2025_races()` 的返回值：
```python
return list(reversed(races_forward))[:5]  # 只返回前 5 場
```

---

## 📞 技術支援

如遇問題，請檢查：
1. FastF1 緩存是否正常
2. 網路連線是否穩定
3. 硬碟空間是否充足
4. Python 版本是否為 3.9+

祝下載順利！ 🏁
