# Track Analysis 重構 - 測試任務清單
**Testing Checklist for Track Analysis Refactoring**

**日期**: 2025-10-02  
**狀態**: 待測試

---

## 🎯 快速測試指引

### 階段 1: 基本啟動測試 (5 分鐘)

#### 測試步驟
1. **啟動 GUI**
   ```powershell
   python f1t_gui_main.py
   ```

2. **開啟 Track Analysis**
   - 點擊選單: Analysis → Track Analysis
   - 或使用快捷鍵（如果有設定）

3. **檢查視窗**
   - [ ] MDI 視窗正常開啟
   - [ ] 視窗標題正確: "Track Analysis - 2025 Japan R"
   - [ ] 控制面板顯示在右側
   - [ ] 地圖區域顯示在左側

4. **檢查控制面板**
   - [ ] 顯示模式下拉選單可見
   - [ ] 顯示選項核取方塊可見
   - [ ] 縮放滑桿可見
   - [ ] 賽道資訊區域可見

---

## ✅ 預期行為

### 正常情況 A: 本地 JSON 存在

```
[TRACK_ANALYSIS_MDI] 初始化完成
[TRACK_DATA_MANAGER] 初始化完成，搜索目錄: ['json', 'json_exports', 'cache']
[TRACK_ANALYSIS_MDI] 創建 TrackMapWidget
[TRACK_ANALYSIS_MDI] 創建控制面板
[TRACK_ANALYSIS_MDI] 信號連接完成
[STATUS] ✅ 已開啟賽道分析視窗 (MDI): Track Analysis - 2025 Japan R
[TRACK_ANALYSIS] 搜索 JSON 檔案...
[TRACK_ANALYSIS] 找到 JSON: json/track_positions_2025_Japan_R.json
[TRACK_ANALYSIS_MDI] 數據載入完成
[TRACK_MAP] 賽道數據載入完成: Suzuka Circuit
[TRACK_ANALYSIS_MDI] 賽道數據已載入至地圖組件
```

### 正常情況 B: 本地 JSON 不存在（自動生成）

```
[TRACK_ANALYSIS_MDI] 初始化完成
[TRACK_DATA_MANAGER] 初始化完成，搜索目錄: ['json', 'json_exports', 'cache']
[STATUS] ✅ 已開啟賽道分析視窗 (MDI): Track Analysis - 2025 Japan R
[TRACK_ANALYSIS] 搜索 JSON 檔案...
[TRACK_ANALYSIS] 找不到 JSON，啟動 CLI 生成...
[TRACK_ANALYSIS] 🚀 啟動 CLI 賽道數據生成
[TRACK_ANALYSIS] 🔧 CLI 命令參數: -f 2 -y 2025 -r Japan -s R
[CLI] 正在執行賽道分析...
[CLI] 數據已生成: json/track_positions_2025_Japan_R.json
[TRACK_ANALYSIS] ✅ CLI 分析完成: 成功
[TRACK_ANALYSIS_MDI] 數據載入完成
```

---

## ⚠️ 可能的問題和解決方案

### 問題 1: 導入錯誤

**錯誤信息**:
```
[ERROR] 無法導入 TrackAnalysisUniversal: ...
```

**檢查**:
- [ ] `track_analysis_mdi.py` 是否存在
- [ ] `__init__.py` 是否正確匯出
- [ ] Python 路徑是否正確

**解決**:
```powershell
# 檢查檔案
Get-ChildItem modules\gui\track_analysis\*.py

# 應該看到:
# track_analysis_mdi.py
# __init__.py
# ...
```

### 問題 2: 控制面板不顯示

**症狀**: 只看到地圖區域，沒有控制面板

**檢查**:
- [ ] `create_control_widget()` 是否返回正確的 QWidget
- [ ] UniversalAnalysisMDI 基類是否正確處理控制面板

**解決**: 檢查控制台輸出，應該看到:
```
[TRACK_ANALYSIS_MDI] 創建控制面板
```

### 問題 3: 地圖顯示佔位符

**症狀**: 地圖區域顯示「賽道地圖（準備中...）」

**說明**: 這是**正常的**！

`TrackMapWidget` 目前是佔位符實現：
- ✅ 可以接收數據
- ✅ 可以更新佔位符文字
- ⚠️ 尚未實現真正的賽道繪製

**預期顯示**:
```
賽道地圖
Suzuka Circuit
1234 個位置點
```

### 問題 4: CLI 生成失敗

**錯誤信息**:
```
[ERROR] CLI 生成失敗: ...
```

**檢查**:
- [ ] CLI 功能 2 是否正常運作
- [ ] 命令格式是否正確: `-f 2 -y 2025 -r Japan -s R`

**手動測試 CLI**:
```powershell
python f1_analysis_modular_main.py -f 2 -y 2025 -r Japan -s R
```

---

## 🔍 詳細驗證

### 驗證 1: 控制面板功能

#### 1.1 顯示模式切換
```
操作: 切換顯示模式下拉選單
預期: 控制台輸出「[TRACK_ANALYSIS_MDI] 顯示模式變更: XXX」
```

#### 1.2 縮放控制
```
操作: 拖動縮放滑桿
預期: 
  - 縮放標籤更新: "縮放倍率: X.Xx"
  - 控制台輸出「[TRACK_ANALYSIS_MDI] 縮放變更: X.Xx」
```

#### 1.3 網格/標記切換
```
操作: 切換核取方塊
預期: 控制台輸出對應的切換信息
```

### 驗證 2: 參數同步

#### 2.1 切換年份
```
操作: 在主視窗切換年份（如 2025 → 2024）
預期: Track Analysis 視窗自動重新載入數據
```

#### 2.2 切換賽事
```
操作: 在主視窗切換賽事（如 Japan → Australia）
預期: Track Analysis 視窗自動重新載入數據
```

### 驗證 3: 多視窗

```
操作: 開啟兩個 Track Analysis 視窗
預期:
  - 兩個視窗獨立運作
  - 各自可以設定不同參數
  - 互不干擾
```

---

## 📊 效能檢查

### 啟動時間
```
測量: 從點擊選單到視窗顯示的時間
目標: < 0.5 秒
實際: _____ 秒
```

### 數據載入時間（本地 JSON）
```
測量: 從 update_parameters() 到數據載入完成
目標: < 1 秒
實際: _____ 秒
```

### 數據生成時間（CLI）
```
測量: 從 CLI 啟動到 JSON 生成完成
目標: 5-15 秒
實際: _____ 秒
```

---

## 🎯 最小可行測試（2 分鐘）

**最簡單的驗證方式**:

1. **啟動 GUI**
   ```powershell
   python f1t_gui_main.py
   ```

2. **開啟 Track Analysis**
   - 點擊 Analysis → Track Analysis

3. **檢查三件事**:
   - [ ] 視窗正常開啟（沒有錯誤彈窗）
   - [ ] 右側有控制面板
   - [ ] 左側有地圖區域（即使只是佔位符）

如果這三項都通過 → ✅ **重構成功！**

---

## 📝 測試結果記錄

### 測試環境
- **作業系統**: Windows 11
- **Python 版本**: _____
- **PyQt5 版本**: _____
- **測試日期**: 2025-10-02

### 測試結果

#### ✅ 通過項目
- [ ] 基本啟動
- [ ] 視窗創建
- [ ] 控制面板顯示
- [ ] 數據載入（本地 JSON）
- [ ] 數據生成（CLI）
- [ ] 參數同步
- [ ] 多視窗

#### ❌ 失敗項目
- [ ] _______________
- [ ] _______________

#### ⚠️ 問題記錄
```
問題 1: 
描述: 
解決方案: 

問題 2:
描述:
解決方案:
```

---

## 🎉 完成確認

當所有基本測試通過後：

✅ **Track Analysis 重構完成！**

下一步:
1. 實現 TrackMapWidget 完整繪製功能
2. 進行進階功能測試
3. 效能優化

---

**祝測試順利！** 🚀
