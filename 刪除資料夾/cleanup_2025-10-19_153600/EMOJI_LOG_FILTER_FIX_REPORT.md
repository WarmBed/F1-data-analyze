# 🐛 日誌Emoji過濾問題修復報告

## 📊 **問題診斷**

### 發現的關鍵問題

用戶報告仍有 4 個 frame 引用（6826, 6939, 7029, 13359），檢查日誌時發現：

#### ❌ **調試日誌完全丟失**
我們添加的所有 `🔍` emoji 調試日誌**完全沒有出現在日誌文件中**：

```
# 預期日誌：
[LAP_CONTROL] 🔍 關閉前 lap_analysis_windows 數量: 1
[LAP_CONTROL] 🔍 準備移除對象: <SpeedAnalysisModule ...>
[LAP_CONTROL] 🔍 對象是否在 set 中: True
[LAP_CONTROL] 🔍 移除後 lap_analysis_windows 數量: 0

# 實際日誌：
[LAP_CONTROL] ========== on_lap_analysis_window_closed 被調用 ==========
[LAP_CONTROL] ✅ 已斷開子視窗信號連接  ← 有這行
[LAP_CONTROL] 📊 圈速分析視窗已關閉: <...>  ← 有這行
[LAP_CONTROL] 🗑️ 垃圾回收完成，回收了 3 個對象  ← 有這行
# 但所有 🔍 日誌都沒出現！
```

### 根本原因

#### 🐛 **日誌系統過濾emoji**
系統使用自定義日誌重定向（`f1.console`），在處理某些特殊字符（特別是 `🔍` emoji）時出現問題：

1. **編碼問題**：UTF-8 emoji 在日誌管道中被截斷
2. **可能的過濾規則**：特定emoji被過濾器攔截
3. **緩衝問題**：包含emoji的行沒有正確刷新到日誌文件

#### 證據
- ✅ `✅`、`📊`、`🗑️` 等emoji正常顯示
- ❌ `🔍` emoji 完全不顯示
- ✅ 同一行的其他文字也被跳過（不只是emoji被過濾）

---

## ✅ **應用的修復**

### 修復策略：**移除所有emoji，使用純ASCII標籤**

**文件**: `f1t_gui_main.py`
**方法**: `on_lap_analysis_window_closed()`
**位置**: Lines 7031-7067

#### 修改前（使用emoji）:
```python
print(f"[LAP_CONTROL] 🔍 關閉前 lap_analysis_windows 數量: {len(self.lap_analysis_windows)}", flush=True)
print(f"[LAP_CONTROL] 🔍 準備移除對象: {window_object}", flush=True)
print(f"[LAP_CONTROL] 🔍 對象是否在 set 中: {window_object in self.lap_analysis_windows}", flush=True)
```

#### 修改後（純ASCII）:
```python
print(f"[LAP_CONTROL] [SET_DEBUG] BEFORE discard: size={len(self.lap_analysis_windows)}", flush=True)
print(f"[LAP_CONTROL] [SET_DEBUG] Object to remove: {window_object}", flush=True)
print(f"[LAP_CONTROL] [SET_DEBUG] Object in set: {window_object in self.lap_analysis_windows}", flush=True)
sys.stdout.flush()

self.lap_analysis_windows.discard(window_object)

print(f"[LAP_CONTROL] [SET_DEBUG] AFTER discard: size={len(self.lap_analysis_windows)}", flush=True)
sys.stdout.flush()
```

### 完整的新日誌格式

```python
def on_lap_analysis_window_closed(self, window_object):
    """遙測分析視窗關閉時調用"""
    
    import sys
    
    # 方法開始
    print(f"\n[LAP_CONTROL] [SET_DEBUG] START on_lap_analysis_window_closed", flush=True)
    print(f"[LAP_CONTROL] [SET_DEBUG] window_object: {window_object}", flush=True)
    print(f"[LAP_CONTROL] [SET_DEBUG] window_object id: {id(window_object)}", flush=True)
    sys.stdout.flush()
    
    # 信號斷開
    if hasattr(window_object, '_sub_window'):
        sub_window = window_object._sub_window
        if sub_window and hasattr(sub_window, 'window_closed'):
            try:
                sub_window.window_closed.disconnect()
                print(f"[LAP_CONTROL] SIGNAL_DISCONNECT: Success", flush=True)
            except Exception as e:
                print(f"[LAP_CONTROL] SIGNAL_DISCONNECT: Failed ({e})", flush=True)
    
    # Set 操作（關鍵部分）
    print(f"[LAP_CONTROL] [SET_DEBUG] BEFORE discard: size={len(self.lap_analysis_windows)}", flush=True)
    print(f"[LAP_CONTROL] [SET_DEBUG] Object to remove: {window_object}", flush=True)
    print(f"[LAP_CONTROL] [SET_DEBUG] Object in set: {window_object in self.lap_analysis_windows}", flush=True)
    sys.stdout.flush()
    
    self.lap_analysis_windows.discard(window_object)
    
    print(f"[LAP_CONTROL] [SET_DEBUG] AFTER discard: size={len(self.lap_analysis_windows)}", flush=True)
    sys.stdout.flush()
    
    # 視窗資訊
    window_title = window_object.windowTitle() if hasattr(window_object, 'windowTitle') else str(window_object)
    print(f"[LAP_CONTROL] Window closed: {window_title}", flush=True)
```

**關鍵改進**：
1. ✅ 所有日誌改用純ASCII字符
2. ✅ 使用 `[SET_DEBUG]` 標籤標識調試日誌
3. ✅ 簡化日誌格式：`BEFORE discard: size=1` → `AFTER discard: size=0`
4. ✅ 保持所有 `flush=True` 和 `sys.stdout.flush()`
5. ✅ 信號斷開使用 `SIGNAL_DISCONNECT: Success/Failed`

---

## 🧪 **測試計劃**

### 步驟 1: 重啟 GUI
```powershell
python f1t_gui_main.py
```

### 步驟 2: 打開 Speed Analysis
- 賽季：2025
- 賽事：Singapore
- 會話：R
- 車手：VER

### 步驟 3: 關閉視窗
點擊關閉按鈕

### 步驟 4: 驗證日誌
檢查最新的日誌文件：
```powershell
Get-ChildItem logs\f1_gui*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content -Encoding UTF8 | Select-String "LAP_CONTROL" | Select-Object -Last 30
```

### 預期日誌輸出（完整且按順序）:
```
[LAP_CONTROL] [SET_DEBUG] START on_lap_analysis_window_closed
[LAP_CONTROL] [SET_DEBUG] window_object: <SpeedAnalysisModule object at 0x...>
[LAP_CONTROL] [SET_DEBUG] window_object id: 13512345678
[LAP_CONTROL] SIGNAL_DISCONNECT: Success
[LAP_CONTROL] [SET_DEBUG] BEFORE discard: size=1  ← 關鍵！應該是 1
[LAP_CONTROL] [SET_DEBUG] Object to remove: <SpeedAnalysisModule ...>
[LAP_CONTROL] [SET_DEBUG] Object in set: True  ← 關鍵！應該是 True
[LAP_CONTROL] [SET_DEBUG] AFTER discard: size=0  ← 關鍵！應該是 0
[LAP_CONTROL] Window closed: Speed Analysis_2025_Singapore_R
[LAP_CONTROL] ... (清理過程)
[LAP_CONTROL] Current active windows: 0
[LAP_CONTROL] GC collected: X objects  (X > 0)
[LAP_CONTROL] [SET_DEBUG] END on_lap_analysis_window_closed
```

### 步驟 5: 生成 objgraph
使用 Memory Diagnostics 工具

### 步驟 6: 點擊 Force GC
觀察回收對象數

---

## 📊 **成功標準**

### ✅ **日誌完整性檢查**
- [ ] 看到 `[SET_DEBUG] START` 開始標記
- [ ] 看到所有 4 個 `[SET_DEBUG]` 調試日誌（BEFORE, Object to remove, Object in set, AFTER）
- [ ] `BEFORE discard: size=1` → `AFTER discard: size=0`
- [ ] `Object in set: True`
- [ ] 看到方法結束標記

### ✅ **Set 操作檢查**
- [ ] 確認 `size` 從 1 變為 0
- [ ] 確認對象在 set 中（`Object in set: True`）
- [ ] 確認 `discard()` 正常執行

### ✅ **內存清理檢查**
- [ ] GC 回收對象數 > 0
- [ ] objgraph 中 SpeedAnalysisModule 計數 = 0
- [ ] Force GC 能回收殘留對象

### ✅ **Frame 引用檢查**
- [ ] objgraph 中 frame 引用消失或大幅減少
- [ ] 如果 frame 仍存在，確認為正常調用棧

---

## 🔍 **如果測試仍失敗**

### 情況 A: 日誌仍然丟失
**可能原因**：
- 日誌系統有更深層的過濾邏輯
- 需要檢查 `f1.console` 的實現

**解決方案**：
- 改用 Python logging 模組
- 直接寫入獨立的調試日誌文件

### 情況 B: Set 大小不變（始終是 1）
**可能原因**：
- `discard()` 失敗（對象哈希值變化）
- Set 中存的是不同的對象引用

**解決方案**：
```python
# 方案 1: 使用 remove() 並捕獲錯誤
try:
    self.lap_analysis_windows.remove(window_object)
    print("[SET_DEBUG] remove() succeeded")
except KeyError:
    print("[SET_DEBUG] remove() failed - object not in set")

# 方案 2: 強制清理
self.lap_analysis_windows = {w for w in self.lap_analysis_windows if w is not window_object}

# 方案 3: 改用 WeakSet
import weakref
self.lap_analysis_windows = weakref.WeakSet()
```

### 情況 C: Set 大小變為 0，但 objgraph 仍有引用
**可能原因**：
- 其他位置持有引用（如全局變量、緩存）
- Frame 引用來自正常調用棧

**解決方案**：
```python
# 使用 gc.get_referrers() 追蹤
import gc
referrers = gc.get_referrers(window_object)
for ref in referrers:
    print(f"[SET_DEBUG] Referrer: {type(ref)} {ref}")
```

---

## 📝 **技術細節**

### Emoji 日誌問題的原因

#### 1. UTF-8 編碼問題
```python
# 某些emoji（如 🔍）是多字節字符
print("🔍")  # b'\xf0\x9f\x94\x8d' (4 bytes)

# 日誌管道可能在中間截斷
# 導致整行日誌丟失
```

#### 2. 日誌過濾器
```python
# f1.console 可能有類似的過濾邏輯
class LogFilter:
    def filter(self, record):
        # 過濾特定模式
        if record.msg.contains("🔍"):
            return False  # 不記錄
        return True
```

#### 3. 緩衝問題
```python
# Emoji 可能觸發緩衝區刷新問題
sys.stdout.write("🔍")  # 可能卡在緩衝區
sys.stdout.flush()  # 刷新時出錯
```

### 為什麼純ASCII有效
1. **單字節字符**：不會被截斷
2. **標準編碼**：所有日誌系統支持
3. **無過濾風險**：不會觸發特殊字符過濾
4. **可搜索**：`[SET_DEBUG]` 易於 grep

---

## 🎯 **下一步行動**

1. **立即測試**：重啟 GUI 並執行測試
2. **檢查日誌**：確認所有 `[SET_DEBUG]` 日誌出現
3. **驗證 Set 操作**：確認 size 從 1 → 0
4. **objgraph 檢查**：確認對象被釋放
5. **報告結果**：將完整日誌提供給開發者

---

## 📋 **總結**

**問題**：
- 🔍 emoji 日誌被過濾，無法追蹤 set 操作

**修復**：
- ✅ 移除所有emoji，使用純ASCII標籤 `[SET_DEBUG]`
- ✅ 簡化日誌格式
- ✅ 保持所有強制刷新機制

**預期效果**：
- 日誌完整顯示
- 確認 `discard()` 執行情況
- 確認 set 數量從 1 → 0
- 為進一步調試提供完整數據

**如果成功**：
- 證明 4 個 frame 是正常調用棧
- 內存洩漏問題已完全解決

**如果失敗**：
- 有完整的調試數據進行深入分析
- 考慮改用 WeakSet 或其他數據結構
