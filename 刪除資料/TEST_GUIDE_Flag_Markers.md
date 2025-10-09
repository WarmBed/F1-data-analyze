# 🧪 Throttle Line Chart Flag Markers - 快速測試指南

## 🎯 測試目標
驗證 P 標記現在是否正確顯示，以及過濾功能是否正常運作。

## 📋 測試步驟

### 步驟 1️⃣：重新啟動 GUI

**PowerShell 命令**：
```powershell
# 方法 1: 使用 VS Code 任務
# Ctrl+Shift+P → Tasks: Run Task → 🔄 重啟 F1T GUI

# 方法 2: 手動執行
python f1t_gui_main.py
```

### 步驟 2️⃣：打開 Throttle Line Chart 模組

1. 在左側選單選擇 **Lap Analysis → Throttle Line Chart (Single Driver)**
2. 設定參數：
   - Year: **2025**
   - Race: **Singapore** 
   - Session: **R** (正賽)
   - Driver: **VER**

### 步驟 3️⃣：觀察控制台調試輸出

**在 PowerShell/Terminal 中查看**：

```
✅ 預期看到以下訊息：

🔧 [Filter Status] filter_pit_laps=True, filter_yellow_flags=True
🏁 [Flag Markers] pit_laps=[20], flag_labels={20: 'P'}
🔍 [Filter Stats] {'removed_pit_laps': 1, 'remaining_laps': 59, ...}
```

**關鍵檢查點**：
- `pit_laps` 應該包含進站圈號碼
- `flag_labels` 應該包含 `{圈數: 'P'}` 條目
- 即使 `filter_pit_laps=True`，標記仍然應該生成 ✅

### 步驟 4️⃣：視覺檢查圖表

**檢查 X 軸底部**：
- ✅ 應該看到橘色的 **'P'** 標記（在進站圈位置）
- ✅ 標記下方有短垂直線（tick）
- ✅ 顏色應該是橘色 (RGB: 255, 152, 0)

**檢查數據點**：
- 如果 `filter_pit_laps=True`：進站圈**沒有數據點**（但有 P 標記）✅
- 如果 `filter_pit_laps=False`：進站圈**有數據點**且有 P 標記 ✅

### 步驟 5️⃣：測試 System Settings 同步

1. 打開 **Tools → System Settings**
2. 觀察當前狀態：
   - Filter pit laps: ☐ (未勾選)
   - Filter yellow flag laps: ☐ (未勾選)

3. **勾選** "Filter pit laps"
4. 點擊 **OK**

**預期控制台輸出**：
```
🌐 [Global Settings Changed] Received: {'filter_pit_laps': True, ...}
🌐 [Global Settings Updated] New state: pit=True, yellow=False
⚙️ [Settings] filter_pit_laps changed: False → True
🔄 [Reprocess] Rebuilding data with new filter settings...
🔧 [Filter Status] filter_pit_laps=True, filter_yellow_flags=False
🔍 [Filter Stats] {'removed_pit_laps': 1, ...}
```

**預期圖表變化**：
- ✅ P 標記**仍然顯示**（這是修復的重點！）
- ✅ 進站圈的數據點**消失**
- ✅ 圖表重新繪製

5. **取消勾選** "Filter pit laps"
6. 點擊 **OK**

**預期控制台輸出**：
```
🌐 [Global Settings Changed] Received: {'filter_pit_laps': False, ...}
⚙️ [Settings] filter_pit_laps changed: True → False
🔄 [Reprocess] Rebuilding data with new filter settings...
🔍 [Filter Stats] {'removed_pit_laps': 0, ...}
```

**預期圖表變化**：
- ✅ P 標記**仍然顯示**
- ✅ 進站圈的數據點**出現**
- ✅ 圖表包含所有圈速

---

## ✅ 成功標準

### 必須通過的測試：

1. **P 標記顯示** ✓
   - [ ] 在有進站資料的賽事中，X 軸底部顯示橘色 'P' 標記
   - [ ] 標記位置對應實際進站圈號碼

2. **Filter 功能正常** ✓
   - [ ] `filter_pit_laps=True`：進站圈數據點消失，但 P 標記仍顯示
   - [ ] `filter_pit_laps=False`：進站圈數據點出現，P 標記仍顯示

3. **System Settings 同步** ✓
   - [ ] 修改設定後，控制台顯示 "Global Settings Changed" 訊息
   - [ ] 圖表即時更新（自動重新繪製）
   - [ ] 調試訊息顯示正確的過濾狀態

4. **其他標記正常** ✓
   - [ ] Y 標記（黃旗）正常顯示（如果有）
   - [ ] S 標記（安全車）正常顯示（如果有）
   - [ ] R 標記（紅旗）正常顯示（如果有）

---

## 🐛 如果仍然沒有顯示 P 標記

### 診斷步驟：

1. **檢查控制台輸出**：
   ```
   查找：🏁 [Flag Markers] pit_laps=...
   
   如果是空的 pit_laps=[]：
     → 資料中沒有進站資訊（檢查 JSON 檔案）
   
   如果有 pit_laps=[20] 但 flag_labels={}：
     → _extract_flag_sets() 邏輯有問題
   ```

2. **檢查資料檔案**：
   ```powershell
   # 找到對應的 JSON 檔案
   dir json\ -Filter "*throttle*2025*Singapore*VER*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
   
   # 用文字編輯器打開，檢查是否有 pit_status 欄位
   ```

3. **查看完整調試輸出**：
   將控制台的所有 `🔧`, `🏁`, `🔍` 開頭的訊息複製給我分析

---

## 📸 預期視覺效果

### Before（修復前）❌
```
X 軸: |-------|-------|-------|-------|
圈數:   10      20      30      40
標記:          (沒有 P)
```

### After（修復後）✅
```
X 軸: |-------|-------|-------|-------|
圈數:   10      20      30      40
標記:           🟠P             
               (橘色標記在 Lap 20)
```

---

## 🎬 下一步

測試完成後，請回報：
1. ✅ 成功 - P 標記正常顯示
2. ⚠️ 部分成功 - 有標記但行為異常（請描述）
3. ❌ 失敗 - 仍然沒有標記（請提供控制台輸出）

**完整的調試輸出將幫助我們快速定位問題！** 🔍
