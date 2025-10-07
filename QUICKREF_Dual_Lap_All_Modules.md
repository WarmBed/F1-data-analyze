# 🎯 雙圈比較模式快速參考卡

## 📋 一分鐘速覽

### 什麼是雙圈比較模式？
比較**同一車手**在**不同圈次**的遙測表現。

### 如何啟用？
1. 選擇**相同車手**（driver1 = driver2）
2. 選擇**不同圈數**（lap1 ≠ lap2）
3. 點擊「載入數據」

### 視覺效果
- **圖表標籤**: `VER - 第10圈` vs `VER - 第50圈`
- **圖例**: 兩條不同顏色的曲線
- **終端輸出**: `🔄 檢測到雙圈比較模式`

---

## 🎨 標籤格式對照

| 模式 | 圖表標籤範例 | 使用場景 |
|------|------------|---------|
| **雙圈比較** | `VER - 第10圈` vs `VER - 第50圈` | 同車手不同圈次 |
| **雙車手** | `VER` vs `LEC` | 不同車手相同圈次 |
| **單車手** | `VER` | 單一車手單圈 |

**特殊格式**（SpeedDiff/DistanceDiff）:
- 雙圈: `VER 第10圈 vs 第50圈`（無 " - "）

---

## ✅ 支援的 8 個模組

| # | 模組名稱 | 雙圈支援 | 備註 |
|---|---------|---------|------|
| 1 | Speed Analysis | ✅ | 標準格式 |
| 2 | Brake Analysis | ✅ | 標準格式 |
| 3 | Throttle Analysis | ✅ | 標準格式 |
| 4 | Gear Analysis | ✅ | 標準格式 |
| 5 | RPM Analysis | ✅ | 標準格式 |
| 6 | Acceleration Analysis | ✅ | 標準格式 |
| 7 | Speed Diff Analysis | ✅ | 特殊標籤 |
| 8 | Distance Diff Analysis | ✅ | 特殊標籤 |

---

## 🔍 快速驗證

### 步驟 1: 設定參數
```
Year: 2024
Race: Japan
Session: R
Driver 1: VER, Lap 1: 10
Driver 2: VER, Lap 2: 50
```

### 步驟 2: 檢查終端輸出
```
✅ 看到: [*_CHART] 🔢 提取圈數: lap1=10, lap2=50
✅ 看到: [*_CHART] 🔄 檢測到雙圈比較模式: VER 第10圈 vs 第50圈
```

### 步驟 3: 檢查圖表
```
✅ 圖例顯示: VER - 第10圈
✅ 圖例顯示: VER - 第50圈
✅ 兩條曲線均可見
```

---

## 🛠️ 故障排查

| 問題 | 可能原因 | 解決方案 |
|------|---------|---------|
| 未顯示雙圈標籤 | JSON 缺少 lap_number | 重新生成 JSON 檔案 |
| 顯示為單車手模式 | lap1 == lap2 | 檢查圈數設定 |
| 顯示為雙車手模式 | driver1 ≠ driver2 | 確認車手代碼一致 |

---

## 📚 完整文檔

- **實施報告**: `IMPLEMENTATION_COMPLETE_Dual_Lap_All_Modules.md`
- **測試清單**: `TEST_CHECKLIST_Dual_Lap_All_Modules.md`
- **終端輸出參考**: `TERMINAL_OUTPUT_REFERENCE_Dual_Lap.md`
- **進度追蹤**: `tasks/dual_lap_mode_expansion.md`

---

**版本**: 1.0 | **更新**: 2025-01-03 | **狀態**: ✅ 已完成
