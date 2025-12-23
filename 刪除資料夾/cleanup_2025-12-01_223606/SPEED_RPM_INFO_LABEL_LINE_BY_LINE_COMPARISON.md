# 🔍 Speed vs RPM 模組資訊標籤逐行對比分析

## 📋 對比範圍

- **Speed Analysis**: `speed_analysis_mdi.py` Line 576-630
- **RPM Analysis**: `rpm_analysis_mdi.py` Line 600-654

---

## 🎯 _update_info_label() 方法逐行對比

### Line 1: 方法定義
```python
# Speed (Line 576)
def _update_info_label(self):
    """更新參數資訊標籤（只在取消同步時顯示）"""

# RPM (Line 600)
def _update_info_label(self):
    """更新參數資訊標籤（只在取消同步時顯示）"""
```
**狀態**: ✅ **完全一致**

---

### Line 2-3: Try 區塊開始
```python
# Speed (Line 578-579)
    try:
        # 檢查同步狀態

# RPM (Line 602-603)
    try:
        # 檢查同步狀態
```
**狀態**: ✅ **完全一致**

---

### Line 4: 讀取同步狀態
```python
# Speed (Line 580)
        sync_enabled = getattr(self, 'sync_driver_lap_enabled', True)

# RPM (Line 604)
        sync_enabled = getattr(self, 'sync_driver_lap_enabled', True)
```
**狀態**: ✅ **完全一致**
**說明**: 使用 `getattr()` 安全讀取屬性，預設值為 `True`

---

### Line 5-10: 同步模式 - 隱藏標籤
```python
# Speed (Line 582-587)
        if sync_enabled:
            # 同步模式：隱藏資訊標籤
            if hasattr(self, 'info_label'):
                self.info_label.hide()
            print(f"[SPEED_MDI] 同步模式：隱藏資訊標籤")
            return

# RPM (Line 606-611)
        if sync_enabled:
            # 同步模式：隱藏資訊標籤
            if hasattr(self, 'info_label'):
                self.info_label.hide()
            print(f"[RPM_MDI] 同步模式：隱藏資訊標籤")
            return
```
**狀態**: ✅ **完全一致**（僅 print 前綴不同）
**邏輯**: 
1. ✅ 檢查 `sync_enabled`
2. ✅ 使用 `hasattr()` 安全檢查
3. ✅ 調用 `hide()` 隱藏標籤
4. ✅ 打印調試訊息
5. ✅ `return` 提前退出

---

### Line 11-13: 取消同步模式 - 顯示標籤
```python
# Speed (Line 589-591)
        # 取消同步模式：顯示資訊標籤
        if hasattr(self, 'info_label'):
            self.info_label.show()

# RPM (Line 613-615)
        # 取消同步模式：顯示資訊標籤
        if hasattr(self, 'info_label'):
            self.info_label.show()
```
**狀態**: ✅ **完全一致**
**邏輯**: 
1. ✅ 使用 `hasattr()` 安全檢查
2. ✅ 調用 `show()` 顯示標籤

---

### Line 14-18: 獲取車手 1 參數
```python
# Speed (Line 593-597)
        # 獲取當前參數
        year1 = getattr(self, 'driver1_year', self.current_year)
        race1 = getattr(self, 'driver1_race', self.current_race)
        session1 = getattr(self, 'driver1_session', self.current_session)
        driver1 = self.driver1

# RPM (Line 617-621)
        # 獲取當前參數
        year1 = getattr(self, 'driver1_year', self.current_year)
        race1 = getattr(self, 'driver1_race', self.current_race)
        session1 = getattr(self, 'driver1_session', self.current_session)
        driver1 = self.driver1
```
**狀態**: ✅ **完全一致**

---

### Line 19: 獲取圈數 1
```python
# Speed (Line 598)
        lap1 = self.lap1

# RPM (Line 622)
        lap1 = self.lap1
```
**狀態**: ✅ **完全一致**

---

### Line 20-25: 獲取車手 2 參數
```python
# Speed (Line 600-604)
        year2 = getattr(self, 'driver2_year', self.current_year)
        race2 = getattr(self, 'driver2_race', self.current_race)
        session2 = getattr(self, 'driver2_session', self.current_session)
        driver2 = self.driver2
        lap2 = self.lap2

# RPM (Line 624-628)
        year2 = getattr(self, 'driver2_year', self.current_year)
        race2 = getattr(self, 'driver2_race', self.current_race)
        session2 = getattr(self, 'driver2_session', self.current_session)
        driver2 = self.driver2
        lap2 = self.lap2
```
**狀態**: ✅ **完全一致**

---

### Line 26-27: 檢測跨賽事比較
```python
# Speed (Line 606-607)
        # 檢測是否為跨賽事比較
        is_cross_event = (year1 != year2) or (session1 != session2)

# RPM (Line 630-631)
        # 檢測是否為跨賽事比較
        is_cross_event = (year1 != year2) or (session1 != session2)
```
**狀態**: ✅ **完全一致**
**邏輯**: 
1. ✅ 比較 `year1 != year2`（跨年度）
2. ✅ 比較 `session1 != session2`（跨賽段）
3. ✅ 使用 `or` 邏輯（任一條件滿足即為跨賽事）

---

### Line 28-35: 跨賽事比較格式
```python
# Speed (Line 609-615)
        if is_cross_event:
            # 跨賽事比較格式
            info_text = (
                f"<b>車手 1:</b> {year1} {race1} {session1} - {driver1} Lap {lap1}  "
                f"<b style='color: #999;'>vs</b>  "
                f"<b>車手 2:</b> {year2} {race2} {session2} - {driver2} Lap {lap2}"
            )

# RPM (Line 633-639)
        if is_cross_event:
            # 跨賽事比較格式
            info_text = (
                f"<b>車手 1:</b> {year1} {race1} {session1} - {driver1} Lap {lap1}  "
                f"<b style='color: #999;'>vs</b>  "
                f"<b>車手 2:</b> {year2} {race2} {session2} - {driver2} Lap {lap2}"
            )
```
**狀態**: ✅ **完全一致**
**格式**: 
- ✅ 顯示雙方完整資訊（year/race/session/driver/lap）
- ✅ 使用 HTML `<b>` 標籤加粗
- ✅ "vs" 使用灰色（`color: #999`）
- ✅ 使用空格分隔雙方資訊

---

### Line 36-41: 標準比較格式
```python
# Speed (Line 616-620)
        else:
            # 標準比較格式
            info_text = (
                f"<b>賽事:</b> {year1} {race1} {session1}  |  "
                f"<b>車手:</b> {driver1} (Lap {lap1}) vs {driver2} (Lap {lap2})"
            )

# RPM (Line 640-644)
        else:
            # 標準比較格式
            info_text = (
                f"<b>賽事:</b> {year1} {race1} {session1}  |  "
                f"<b>車手:</b> {driver1} (Lap {lap1}) vs {driver2} (Lap {lap2})"
            )
```
**狀態**: ✅ **完全一致**
**格式**: 
- ✅ 顯示賽事資訊（year/race/session）
- ✅ 顯示雙車手對比（driver1 vs driver2）
- ✅ 使用 ` | ` 分隔賽事和車手
- ✅ 圈數用括號包裹

---

### Line 42-43: 設置標籤文字
```python
# Speed (Line 622-623)
        self.info_label.setText(info_text)
        print(f"[SPEED_MDI] 取消同步模式：顯示資訊標籤")

# RPM (Line 646-647)
        self.info_label.setText(info_text)
        print(f"[RPM_MDI] 取消同步模式：顯示資訊標籤")
```
**狀態**: ✅ **完全一致**（僅 print 前綴不同）

---

### Line 44-46: 異常處理
```python
# Speed (Line 625-626)
    except Exception as e:
        print(f"[ERROR] [SPEED_MDI] 更新資訊標籤失敗: {e}")

# RPM (Line 649-650)
    except Exception as e:
        print(f"[ERROR] [RPM_MDI] 更新資訊標籤失敗: {e}")
```
**狀態**: ✅ **完全一致**（僅 print 前綴不同）

---

## 🎨 UI 組件設置對比

### Speed Analysis: _setup_ui() (Line 548-575)
```python
def _setup_ui(self):
    """設置用戶界面"""
    # 創建主容器 widget
    self.main_widget = QWidget()
    layout = QVBoxLayout()
    
    # ⚠️ [參數資訊標籤] 新增：參數資訊標籤（淺色背景）
    # 用於顯示當前分析參數（賽事、車手、圈數）
    self.info_label = QLabel()
    self.info_label.setObjectName("AnalysisInfoLabel")
    self.info_label.setStyleSheet("""
        QLabel#AnalysisInfoLabel {
            background-color: #F0F0F0;
            color: #333333;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 11pt;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
    """)
    self.info_label.setWordWrap(True)
    self._update_info_label()  # 初始化標籤內容
    layout.addWidget(self.info_label)
    
    # 添加速度圖表
    if self.speed_chart_widget:
        layout.addWidget(self.speed_chart_widget)
    
    # 設置佈局到主 widget
    self.main_widget.setLayout(layout)
```

### RPM Analysis: _setup_ui() (Line 572-599)
```python
def _setup_ui(self):
    """設置用戶界面"""
    # 創建主容器 widget
    self.main_widget = QWidget()
    layout = QVBoxLayout()
    
    # ⚠️ [參數資訊標籤] 新增：參數資訊標籤（淺色背景）
    # 複製自 Speed Analysis 模組
    self.info_label = QLabel()
    self.info_label.setObjectName("AnalysisInfoLabel")
    self.info_label.setStyleSheet("""
        QLabel#AnalysisInfoLabel {
            background-color: #F0F0F0;
            color: #333333;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 11pt;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
    """)
    self.info_label.setWordWrap(True)
    self._update_info_label()  # 初始化標籤內容
    layout.addWidget(self.info_label)
    
    # 添加RPM圖表
    if self.rpm_chart_widget:
        layout.addWidget(self.rpm_chart_widget)
    
    # 設置佈局到主 widget
    self.main_widget.setLayout(layout)
```

**狀態**: ✅ **完全一致**（僅註解和變數名稱不同）

---

## 📊 功能完整性對比

### 1. 標籤創建 ✅
| 檢查項目 | Speed | RPM | 狀態 |
|---------|-------|-----|------|
| 創建 QLabel | ✅ | ✅ | ✅ 一致 |
| 設置 ObjectName | ✅ | ✅ | ✅ 一致 |
| 設置樣式表 | ✅ | ✅ | ✅ 一致 |
| 設置 WordWrap | ✅ | ✅ | ✅ 一致 |
| 初始化調用 | ✅ | ✅ | ✅ 一致 |
| 添加到佈局 | ✅ | ✅ | ✅ 一致 |

### 2. 同步模式處理 ✅
| 檢查項目 | Speed | RPM | 狀態 |
|---------|-------|-----|------|
| 讀取 sync_enabled | ✅ | ✅ | ✅ 一致 |
| 使用 getattr() | ✅ | ✅ | ✅ 一致 |
| 預設值為 True | ✅ | ✅ | ✅ 一致 |
| 調用 hide() | ✅ | ✅ | ✅ 一致 |
| 打印調試訊息 | ✅ | ✅ | ✅ 一致 |
| return 退出 | ✅ | ✅ | ✅ 一致 |

### 3. 取消同步模式處理 ✅
| 檢查項目 | Speed | RPM | 狀態 |
|---------|-------|-----|------|
| 調用 show() | ✅ | ✅ | ✅ 一致 |
| 讀取參數 | ✅ | ✅ | ✅ 一致 |
| 檢測跨賽事 | ✅ | ✅ | ✅ 一致 |
| 跨賽事格式 | ✅ | ✅ | ✅ 一致 |
| 標準格式 | ✅ | ✅ | ✅ 一致 |
| 設置文字 | ✅ | ✅ | ✅ 一致 |
| 打印調試訊息 | ✅ | ✅ | ✅ 一致 |

### 4. 異常處理 ✅
| 檢查項目 | Speed | RPM | 狀態 |
|---------|-------|-----|------|
| try-except 區塊 | ✅ | ✅ | ✅ 一致 |
| 捕獲 Exception | ✅ | ✅ | ✅ 一致 |
| 打印錯誤訊息 | ✅ | ✅ | ✅ 一致 |

---

## 🔍 樣式表對比

### CSS 屬性逐行對比
```css
/* Speed & RPM 完全一致 */
QLabel#AnalysisInfoLabel {
    background-color: #F0F0F0;    /* ✅ 淺灰色背景 */
    color: #333333;                /* ✅ 深灰色文字 */
    padding: 8px 12px;             /* ✅ 內距：上下 8px，左右 12px */
    border-radius: 4px;            /* ✅ 圓角 4px */
    font-size: 11pt;               /* ✅ 字體大小 11pt */
    font-family: 'Segoe UI', Arial, sans-serif;  /* ✅ 字體家族 */
}
```

**狀態**: ✅ **100% 一致**

---

## 🎯 總結

### ✅ 完全一致的項目（23/23）

1. ✅ 方法定義和文檔字串
2. ✅ try-except 異常處理結構
3. ✅ 同步狀態讀取邏輯
4. ✅ 同步模式 - 隱藏標籤邏輯
5. ✅ 取消同步模式 - 顯示標籤邏輯
6. ✅ 車手 1 參數獲取
7. ✅ 車手 2 參數獲取
8. ✅ 跨賽事檢測邏輯
9. ✅ 跨賽事比較格式
10. ✅ 標準比較格式
11. ✅ 標籤文字設置
12. ✅ 調試訊息打印
13. ✅ QLabel 創建
14. ✅ ObjectName 設置
15. ✅ 樣式表設置
16. ✅ WordWrap 設置
17. ✅ 初始化調用
18. ✅ 佈局添加
19. ✅ 背景顏色 (#F0F0F0)
20. ✅ 文字顏色 (#333333)
21. ✅ 內距 (8px 12px)
22. ✅ 圓角 (4px)
23. ✅ 字體設置 (11pt, Segoe UI)

### ⚠️ 唯一的差異

**僅有變數名稱和 print 前綴的差異**：
- Speed: `[SPEED_MDI]`, `speed_chart_widget`
- RPM: `[RPM_MDI]`, `rpm_chart_widget`

**這是合理的命名差異，不影響功能邏輯！**

---

## ✅ 最終結論

**RPM 模組的資訊標籤實現與 Speed 模組 100% 一致！**

### 驗證結果
- ✅ **邏輯結構**: 完全一致
- ✅ **代碼行數**: 完全一致
- ✅ **功能實現**: 完全一致
- ✅ **樣式設置**: 完全一致
- ✅ **異常處理**: 完全一致

### 功能保證
1. ✅ **勾選同步**: 標籤自動隱藏
2. ✅ **取消同步**: 標籤自動顯示
3. ✅ **跨賽事**: 顯示雙方完整資訊
4. ✅ **標準模式**: 顯示賽事+車手對比
5. ✅ **樣式一致**: 淺灰色背景，深灰色文字

---

**驗證時間**: 2025-11-14  
**驗證狀態**: ✅ **通過（100% 一致）**
