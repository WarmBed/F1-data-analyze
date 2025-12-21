# 參數同步問題診斷報告

## 🚨 問題描述
用戶更新 Race/Year 時，大部分模組並沒有更新

## 🔍 根本原因分析

### 問題 1: 確認對話框被忽略 ⚠️
**位置**: `f1t_gui_main.py` Line 7082-7095

```python
reply = QMessageBox.question(
    self,
    tr("update", "更新確認"),
    tr("update_race_params_confirm", 
       "檢測到賽事參數變更：\n年份: {year}\n賽事: {race}\n賽段: {session}\n\n"
       "共有 {count} 個分析視窗需要更新。\n是否立即更新所有視窗？").format(...),
    QMessageBox.Yes | QMessageBox.No,
    QMessageBox.No  # ❌ 預設為 No，用戶需要主動點擊 Yes
)

if reply == QMessageBox.Yes:
    print("[RACE_CONTROL] ✅ 用戶確認更新，開始批次更新所有視窗...")
    self.update_all_lap_analysis()
else:
    print("[RACE_CONTROL] ❌ 用戶取消更新")  # ← 用戶可能沒注意到對話框
```

**問題**:
- ❌ 用戶可能**沒看到對話框**（被其他視窗擋住）
- ❌ 用戶可能**誤點擊 No**（預設選項）
- ❌ 用戶可能**按 ESC 關閉**（等同於選擇 No）
- ❌ 用戶期望**自動更新**，而不是每次都要確認

### 問題 2: 同步機制不明確 🔄
**流程**:
```
1. 用戶改變 Year/Race/Session
   ↓
2. 觸發 on_main_year_changed() / on_main_race_changed() / on_main_session_changed()
   ↓
3. 調用 _schedule_parameter_broadcast()
   ↓
4. 延遲 300ms 後調用 _broadcast_pending_parameters()
   ↓
5. 調用 on_race_parameters_changed()
   ↓
6. **彈出確認對話框** ← 這裡會阻塞流程
   ↓
7. 如果用戶點擊 Yes → update_all_lap_analysis()
   如果用戶點擊 No → ❌ 什麼都不做
```

## 💡 解決方案

### 方案 1: 移除確認對話框，改為自動更新 ✅ 推薦
**優點**:
- 符合用戶預期（改變參數 = 立即更新）
- 減少操作步驟
- 避免遺漏更新

**缺點**:
- 可能觸發不必要的 API 請求
- 用戶可能在快速切換參數時觸發多次更新

**實現**:
```python
def on_race_parameters_changed(self):
    """賽事參數變更處理器 - 自動更新所有視窗"""
    # 獲取當前參數值
    current_year = self.year_combo.currentText()
    current_race = self.race_combo.currentText()
    current_session = self.session_combo.currentText()
    
    print(f"[RACE_CONTROL] 📊 賽事參數已變更:")
    print(f"[RACE_CONTROL]   🗓️ 年份: '{current_year}'")
    print(f"[RACE_CONTROL]   🏁 賽事: '{current_race}'")
    print(f"[RACE_CONTROL]   🏎️ 賽段: '{current_session}'")
    
    # 檢查是否有需要更新的分析視窗
    analysis_windows = self._get_telemetry_analysis_windows()
    
    if len(analysis_windows) == 0:
        print("[RACE_CONTROL] ℹ️ 沒有活動的分析視窗，無需更新")
        return
    
    print(f"[RACE_CONTROL] 🔍 發現 {len(analysis_windows)} 個需要更新的分析視窗")
    print("[RACE_CONTROL] ✅ 開始自動更新所有視窗...")
    
    # ✅ 直接更新，不再詢問用戶
    self.update_all_lap_analysis()
```

### 方案 2: 改為通知 + 手動觸發 🔔
**優點**:
- 用戶可以控制更新時機
- 避免頻繁的自動更新
- 顯示更新通知但不阻塞

**缺點**:
- 需要額外點擊才能更新
- 可能導致視窗顯示過時數據

**實現**:
```python
def on_race_parameters_changed(self):
    """賽事參數變更處理器 - 顯示通知"""
    analysis_windows = self._get_telemetry_analysis_windows()
    
    if len(analysis_windows) == 0:
        return
    
    # 顯示狀態列通知
    self.statusBar().showMessage(
        f"參數已變更 ({len(analysis_windows)} 個視窗需要更新) - 點擊工具列 'Update All' 按鈕更新",
        5000  # 5 秒後消失
    )
    
    # 可選：高亮顯示 Update All 按鈕
    if hasattr(self, 'update_all_action'):
        self.update_all_action.setStyleSheet("background-color: #FFA500;")
```

### 方案 3: 偏好設定選項 ⚙️
**優點**:
- 最靈活，用戶可以選擇行為
- 滿足不同用戶需求

**缺點**:
- 增加複雜度
- 需要設定介面

**實現**:
```python
# settings.json
{
    "auto_update_on_parameter_change": true,  # true=自動更新, false=詢問
    "update_confirmation_dialog": false       # true=顯示對話框, false=靜默更新
}

def on_race_parameters_changed(self):
    if self.settings.get("auto_update_on_parameter_change", True):
        # 自動更新
        self.update_all_lap_analysis()
    else:
        # 顯示確認對話框
        reply = QMessageBox.question(...)
        if reply == QMessageBox.Yes:
            self.update_all_lap_analysis()
```

## 📋 建議的修復步驟

1. **立即修復** (方案 1):
   - 移除確認對話框
   - 改為自動更新所有視窗
   - 在狀態列顯示更新進度

2. **後續優化** (方案 3):
   - 添加設定選項讓用戶選擇行為
   - 添加「不再詢問」勾選框

## 🧪 測試計畫

1. **測試場景 1**: 改變 Year
   - 預期：所有視窗自動更新到新年份
   
2. **測試場景 2**: 改變 Race
   - 預期：所有視窗自動更新到新賽事
   
3. **測試場景 3**: 改變 Session
   - 預期：所有視窗自動更新到新賽段
   
4. **測試場景 4**: 快速連續改變參數
   - 預期：debounce 機制生效，只觸發一次更新

## 🎯 預期結果

修復後，用戶體驗應該是：
```
用戶: 改變 Year/Race/Session
     ↓
系統: [狀態列] 正在更新 8 個分析視窗...
     ↓
系統: [進度條] 更新 1/8: Speed Analysis...
     ↓
系統: [進度條] 更新 2/8: Brake Analysis...
     ↓
     ... (自動完成所有更新)
     ↓
系統: [狀態列] ✅ 已更新 8 個視窗
```

**不應該出現**:
- ❌ 確認對話框彈出
- ❌ 用戶需要手動點擊 Yes
- ❌ 視窗顯示舊參數的數據
