# Pitstop Analysis 賽段類型檢查修復報告

**修復日期**: 2025-10-25  
**問題編號**: Pitstop-Session-Check  
**影響模組**: `modules/gui/pitstop_analysis/pitstop_analysis_mdi.py`  
**修復類型**: 功能增強 + 邏輯優化

---

## 📋 問題描述

### 原始行為
Pitstop Analysis 模組在用戶選擇非正賽 (R) 的賽事類型（如 FP1, FP2, Q 等）時，會嘗試呼叫 API 獲取數據，導致：
1. ❌ 無意義的 API 請求（練習賽和排位賽沒有進站數據）
2. ❌ 浪費網路資源和 API 配額
3. ❌ 用戶等待時間增加
4. ❌ 錯誤訊息不明確

### 用戶需求
> "當使用者選擇用 R 以外的賽事，則顯示無資料，不需要呼叫 API"

### 技術原因
進站 (Pitstop) 數據**僅在正賽 (Race) 中存在**：
- ✅ **R (Race)**: 有完整進站數據
- ❌ **Q (Qualifying)**: 排位賽無進站
- ❌ **FP1/FP2/FP3**: 練習賽無進站
- ❌ **Sprint**: 衝刺賽（短賽制，通常無進站或極少）

---

## 🔧 修復方案

### 架構分析
Pitstop Analysis 模組使用 **3 個獨立數據載入方法**：
1. `load_data()` - 車手進站排行榜 (Function 3)
2. `load_team_data()` - 車隊進站策略 (Function 4)
3. `load_driver_detailed_data()` - 車手詳細進站記錄 (Function 5)

### 修復位置
**檔案**: `modules/gui/pitstop_analysis/pitstop_analysis_mdi.py`

#### 1️⃣ 修復 `load_data()` (Line 780)
**修改前**:
```python
def load_data(self, year: str, race: str, session: str, force_refresh: bool = False):
    """載入車手進站數據 - API 優先"""
    try:
        print(f"[PITSTOP_MANAGER] 開始載入車手進站數據: {year} {race} {session}")

        if self._is_loading:
            self.error_occurred.emit("載入器正忙，請稍後再試")
            return False

        self._is_loading = True
        self.loading_progress.emit(5)
```

**修改後**:
```python
def load_data(self, year: str, race: str, session: str, force_refresh: bool = False):
    """載入車手進站數據 - API 優先"""
    try:
        print(f"[PITSTOP_MANAGER] 開始載入車手進站數據: {year} {race} {session}")

        # ⚠️ 進站數據僅支援正賽 (R)，其他賽段無進站數據
        if session != 'R':
            print(f"[PITSTOP_MANAGER] ⚠️  進站分析僅支援正賽 (R)，當前賽段: {session}")
            self.error_occurred.emit(tr("進站分析僅適用於正賽 (Race)，練習賽和排位賽無進站數據"))
            self._is_loading = False
            return False

        if self._is_loading:
            self.error_occurred.emit("載入器正忙，請稍後再試")
            return False

        self._is_loading = True
        self.loading_progress.emit(5)
```

#### 2️⃣ 修復 `load_team_data()` (Line 905)
**修改前**:
```python
def load_team_data(self, year: str, race: str, session: str, force_refresh: bool = False):
    """載入車隊進站數據 - API 優先"""
    try:
        print(f"[PITSTOP_MANAGER] 開始載入車隊進站數據: {year} {race} {session}")

        if self._team_is_loading:
            self.error_occurred.emit("車隊數據載入中，請稍後再試")
            return False

        self._team_is_loading = True
```

**修改後**:
```python
def load_team_data(self, year: str, race: str, session: str, force_refresh: bool = False):
    """載入車隊進站數據 - API 優先"""
    try:
        print(f"[PITSTOP_MANAGER] 開始載入車隊進站數據: {year} {race} {session}")

        # ⚠️ 進站數據僅支援正賽 (R)，其他賽段無進站數據
        if session != 'R':
            print(f"[PITSTOP_MANAGER] ⚠️  進站分析僅支援正賽 (R)，當前賽段: {session}")
            self.error_occurred.emit(tr("進站分析僅適用於正賽 (Race)，練習賽和排位賽無進站數據"))
            self._team_is_loading = False
            return False

        if self._team_is_loading:
            self.error_occurred.emit("車隊數據載入中，請稍後再試")
            return False

        self._team_is_loading = True
```

#### 3️⃣ 修復 `load_driver_detailed_data()` (Line 1091)
**修改前**:
```python
def load_driver_detailed_data(self, year: str, race: str, session: str, force_refresh: bool = False):
    """載入車手進站詳細數據 - API 優先"""
    try:
        print(f"[PITSTOP_MANAGER] 開始載入車手詳細進站數據: {year} {race} {session}")

        if self._detail_is_loading:
            self.error_occurred.emit("車手詳細數據載入中，請稍後再試")
            return False

        self._detail_is_loading = True
```

**修改後**:
```python
def load_driver_detailed_data(self, year: str, race: str, session: str, force_refresh: bool = False):
    """載入車手進站詳細數據 - API 優先"""
    try:
        print(f"[PITSTOP_MANAGER] 開始載入車手詳細進站數據: {year} {race} {session}")

        # ⚠️ 進站數據僅支援正賽 (R)，其他賽段無進站數據
        if session != 'R':
            print(f"[PITSTOP_MANAGER] ⚠️  進站分析僅支援正賽 (R)，當前賽段: {session}")
            self.error_occurred.emit(tr("進站分析僅適用於正賽 (Race)，練習賽和排位賽無進站數據"))
            self._detail_is_loading = False
            return False

        if self._detail_is_loading:
            self.error_occurred.emit("車手詳細數據載入中，請稍後再試")
            return False

        self._detail_is_loading = True
```

---

## ✅ 修復效果

### 行為變化表

| 賽段類型 | 修改前 | 修改後 |
|---------|--------|--------|
| **R (正賽)** | ✅ 呼叫 API 載入數據 | ✅ 呼叫 API 載入數據 |
| **Q (排位賽)** | ❌ 呼叫 API (失敗) | ✅ 直接顯示錯誤訊息 |
| **FP1/FP2/FP3** | ❌ 呼叫 API (失敗) | ✅ 直接顯示錯誤訊息 |
| **Sprint** | ❌ 呼叫 API (失敗) | ✅ 直接顯示錯誤訊息 |

### 優點
1. ✅ **避免無意義的 API 請求**
   - 不再對練習賽/排位賽發送 API 請求
   - 節省網路資源和 API 配額

2. ✅ **用戶體驗改善**
   - 立即顯示明確的錯誤訊息
   - 不需要等待 API 超時
   - 訊息清晰：「進站分析僅適用於正賽 (Race)，練習賽和排位賽無進站數據」

3. ✅ **符合設計原則**
   - 遵循「原則 0: 反幻覺編碼」- 基於真實數據存在性
   - 不假設非正賽有進站數據
   - 提前驗證，快速失敗 (Fail-Fast)

4. ✅ **支援多語言**
   - 使用 `tr()` 函數包裹錯誤訊息
   - 自動適應系統語言設定

---

## 🧪 測試驗證

### 測試腳本
**檔案**: `test_pitstop_session_check.py`

### 測試案例
```python
test_cases = [
    ("2025", "Japan", "R", True, "正賽 (R) 應該允許載入"),
    ("2025", "Japan", "Q", False, "排位賽 (Q) 應該拒絕載入"),
    ("2025", "Japan", "FP1", False, "練習賽 (FP1) 應該拒絕載入"),
    ("2025", "Japan", "FP2", False, "練習賽 (FP2) 應該拒絕載入"),
    ("2025", "Japan", "FP3", False, "練習賽 (FP3) 應該拒絕載入"),
    ("2025", "Japan", "Sprint", False, "衝刺賽 (Sprint) 應該拒絕載入"),
]
```

### 測試結果
```
================================================================================
測試摘要
================================================================================
總測試數: 6
✅ 通過: 6
❌ 失敗: 0

🎉 所有測試通過！
```

### 測試輸出範例
```
--- 測試案例: 排位賽 (Q) 應該拒絕載入 ---
參數: year=2025, race=Japan, session=Q
[PITSTOP_MANAGER] 開始載入車手進站數據: 2025 Japan Q
[PITSTOP_MANAGER] ⚠️  進站分析僅支援正賽 (R)，當前賽段: Q
✅ 收到錯誤訊息: 進站分析僅適用於正賽 (Race)，練習賽和排位賽無進站數據
✅ 通過: 正確拒絕非正賽載入
```

---

## 📊 影響範圍

### 修改檔案
- ✅ `modules/gui/pitstop_analysis/pitstop_analysis_mdi.py` (3 處修改)

### 測試檔案
- ✅ `test_pitstop_session_check.py` (新增)

### 受影響功能
1. **車手進站排行榜** (Function 3)
2. **車隊進站策略** (Function 4)
3. **車手詳細進站記錄** (Function 5)

### 不受影響功能
- ✅ 其他分析模組（Lap Analysis, Rain Analysis 等）
- ✅ API 服務器
- ✅ CLI 功能

---

## 🔄 向後兼容性

### API 端點
- ✅ **無變更**：API 端點仍然接受所有 session 類型
- ✅ **GUI 端檢查**：僅在 GUI 端提前驗證，API 仍可被 CLI 或其他客戶端調用

### CLI 功能
- ✅ **無影響**：CLI 仍可執行非正賽的進站分析（如有需要）
- ✅ **範例**: `python f1_analysis_modular_main.py -f 3 -y 2025 -r Japan -s Q`

### 本地 JSON
- ✅ **無影響**：如果本地有非正賽的 JSON 檔案，API-ONLY 模式會阻止讀取

---

## 🎯 用戶指南

### 使用建議
1. **正常使用**
   - 選擇任何站點的 **R (正賽)** 查看進站分析
   - 系統會自動呼叫 API 獲取數據

2. **選擇非正賽時**
   - 系統會立即顯示錯誤訊息
   - 不會發送 API 請求
   - 建議切換到正賽 (R) 重新載入

3. **錯誤訊息處理**
   - 英文: "Pitstop analysis is only applicable for Race, practice sessions and qualifying have no pitstop data"
   - 中文: "進站分析僅適用於正賽 (Race)，練習賽和排位賽無進站數據"

---

## 📚 相關文檔

### 設計原則
- ✅ 遵循 **反幻覺編碼原則 0**: 不假設數據存在性
- ✅ 遵循 **API-ONLY 模式**: GUI 不自動生成數據
- ✅ 遵循 **國際化原則**: 所有用戶訊息使用 `tr()` 函數

### 相關文檔
- [Pitstop Analysis CLI Function Mapping](./PITSTOP_ANALYSIS_CLI_FUNCTION_MAPPING.md)
- [API-ONLY 模式政策](./.github/copilot-instructions.md#4-api-only-模式政策)

---

## ✨ 總結

### 修復摘要
- 🎯 **目標**: 避免對非正賽發送無意義的 API 請求
- ✅ **實現**: 在 3 個載入方法開頭添加 Session 類型檢查
- 🧪 **驗證**: 所有測試通過 (6/6)
- 📊 **影響**: 僅影響 Pitstop Analysis 模組，不影響其他功能

### 下一步建議
1. ✅ **已完成**: Session 類型驗證
2. 🔄 **建議**: 考慮在其他進站相關模組套用相同檢查
3. 📖 **建議**: 更新用戶文檔說明進站分析的賽段限制

---

**修復完成日期**: 2025-10-25  
**測試狀態**: ✅ 全部通過  
**建議合併**: ✅ 是
