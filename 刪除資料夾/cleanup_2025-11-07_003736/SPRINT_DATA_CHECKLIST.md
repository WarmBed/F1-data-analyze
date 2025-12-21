# 🏁 Sprint Weekend 數據收集清單

## 📊 當前狀態

### ✅ 已完成
- **Function 70 (FP-Q Data)**: 全部完成 ✓
  - 2018-2024 所有 Austria/Brazil/Qatar 數據都已生成

### 🔴 缺少的數據

#### Function 47: Corner Analysis (Sprint Session)
需要手動執行以下 **5 個命令**：

```powershell
# 2022 年
python f1_analysis_modular_main.py -f 47 -y 2022 -r Austria -s Sprint
python f1_analysis_modular_main.py -f 47 -y 2022 -r Brazil -s Sprint

# 2023 年
python f1_analysis_modular_main.py -f 47 -y 2023 -r Austria -s Sprint
python f1_analysis_modular_main.py -f 47 -y 2023 -r Brazil -s Sprint
python f1_analysis_modular_main.py -f 47 -y 2023 -r Qatar -s Sprint
```

### 📝 說明
- **為什麼只需要 Function 47?**
  - Function 70 (FP-Q Data) 使用 `-s R` (正賽) 參數，會自動收集 FP1、FP2、FP3 (或 Sprint) 的數據
  - 已在 11/1 和 11/4 完成所有年份的收集

- **為什麼是 Sprint Session?**
  - Austria/Brazil/Qatar 在這些年份採用 Sprint 週末格式
  - 沒有 FP3，系統會自動使用 Sprint 數據（Fallback 機制已啟用）

- **預期輸出檔案**：
  ```
  all_drivers_cornering_analysis_2022_Austria_Sprint.json
  all_drivers_cornering_analysis_2022_Brazil_Sprint.json
  all_drivers_cornering_analysis_2023_Austria_Sprint.json
  all_drivers_cornering_analysis_2023_Brazil_Sprint.json
  all_drivers_cornering_analysis_2023_Qatar_Sprint.json
  ```

## 🎯 完成後的下一步

執行訓練腳本訓練剩餘 3 個賽道：
```powershell
python batch_train_all_tracks_v3.8.py --trials 500 --workers 4
```

預期結果：
- 訓練 Austria、Brazil、Qatar 模型
- 最終達成 **23/24 賽道** (95.8% 完成率)
- China 因 COVID 取消無法訓練

## 📈 進度追蹤

- [x] Function 70 數據收集 (2018-2024)
- [x] 2024 Sprint 數據 (Function 47)
- [ ] 2022 Sprint 數據 (Function 47) - 2 個檔案
- [ ] 2023 Sprint 數據 (Function 47) - 3 個檔案
- [ ] 訓練 Austria/Brazil/Qatar 模型
- [ ] 生成 v3.8 最終報告
