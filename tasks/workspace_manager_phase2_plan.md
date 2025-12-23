# Workspace Manager - Phase 2 實施計劃

**開始日期**: 2025-10-21  
**預計完成**: 2-3 個工作日  
**目標**: 實現完整的 Workspace 載入功能

---

## 🎯 Phase 2 目標

實現 `deserialize_workspace()` 方法，使 Workspace Manager 成為**完全可用**的功能：
- 從資料庫載入配置
- 清除當前工作區
- 重建所有分頁和 MDI 視窗
- 恢復視窗位置、大小、彈出狀態
- 載入對應的資料檔案

---

## 📋 任務分解

### Task 5: WindowFactory 重建邏輯

#### 子任務 5.1: 模組工廠映射表 ⏱️ 1-2 小時

**目標**: 建立完整的模組實例化映射

**步驟**:

1️⃣ **分析所有模組的實例化模式**
```python
# 搜尋 f1t_gui_main.py 中的實例化代碼
grep -n "RainAnalysis\|TireAnalysis\|TrackAnalysis" f1t_gui_main.py

# 記錄每個模組的：
# - 類別名稱
# - 導入路徑
# - 必需參數
# - 可選參數
```

2️⃣ **建立映射表**
```python
# 在 workspace_serializer.py 中添加
MODULE_FACTORY_MAPPING = {
    "rain_analysis": {
        "class_name": "RainAnalysisModuleAdapter",
        "import_path": "modules.gui.rain_analysis.rain_analysis_module",
        "required_params": ["year", "race", "session"],
        "optional_params": [],
        "init_signature": "RainAnalysisModuleAdapter(main_window, year, race, session)"
    },
    "tire_strategy": {
        "class_name": "TireAnalysisModuleAdapter",
        "import_path": "modules.gui.tire_analysis.tire_analysis_module",
        "required_params": ["year", "race", "session"],
        "optional_params": [],
        "init_signature": "TireAnalysisModuleAdapter(main_window, year, race, session)"
    },
    # ... 其他 15 種模組
}
```

3️⃣ **驗證映射表**
```python
# 創建測試腳本
python -c "
from core.workspace_serializer import MODULE_FACTORY_MAPPING
print(f'共 {len(MODULE_FACTORY_MAPPING)} 種模組類型')
for key, value in MODULE_FACTORY_MAPPING.items():
    print(f'  {key}: {value[\"class_name\"]}')
"
```

**交付物**:
- [ ] `MODULE_FACTORY_MAPPING` 字典（17 種模組）
- [ ] 每種模組的實例化簽名文檔

---

#### 子任務 5.2: 實現模組實例化方法 ⏱️ 2-3 小時

**目標**: 創建能夠動態實例化任何模組的方法

**實現**:

1️⃣ **添加動態導入方法**
```python
def _import_module_class(self, window_type: str):
    """
    動態導入模組類別
    
    Args:
        window_type: 視窗類型（例如 "rain_analysis"）
        
    Returns:
        (module, class) 元組
    """
    factory_info = MODULE_FACTORY_MAPPING.get(window_type)
    if not factory_info:
        raise ValueError(f"未知視窗類型: {window_type}")
    
    # 動態導入模組
    module_path = factory_info['import_path']
    class_name = factory_info['class_name']
    
    try:
        module = __import__(module_path, fromlist=[class_name])
        cls = getattr(module, class_name)
        return module, cls
    except ImportError as e:
        raise ImportError(f"無法導入 {module_path}.{class_name}: {e}")
```

2️⃣ **實現參數驗證**
```python
def _validate_parameters(self, window_type: str, parameters: Dict) -> bool:
    """驗證參數是否完整"""
    factory_info = MODULE_FACTORY_MAPPING.get(window_type)
    required = factory_info['required_params']
    
    missing = [p for p in required if p not in parameters]
    if missing:
        print(f"⚠️ 缺少必需參數: {missing}")
        return False
    
    return True
```

3️⃣ **實現模組實例化**
```python
def _create_module_instance(self, window_info: Dict) -> Optional[QWidget]:
    """
    創建模組實例
    
    Args:
        window_info: 視窗配置字典
        
    Returns:
        模組 widget 或 None
    """
    window_type = window_info['window_type']
    parameters = window_info.get('parameters', {})
    
    # 驗證參數
    if not self._validate_parameters(window_type, parameters):
        return None
    
    # 導入類別
    try:
        module, cls = self._import_module_class(window_type)
    except (ValueError, ImportError) as e:
        print(f"❌ 導入失敗: {e}")
        return None
    
    # 創建實例
    try:
        # 大部分模組的簽名
        instance = cls(
            main_window=self.main_window,
            **parameters
        )
        
        print(f"✅ 創建模組: {window_type}")
        return instance
        
    except Exception as e:
        print(f"❌ 實例化失敗 ({window_type}): {e}")
        import traceback
        traceback.print_exc()
        return None
```

**測試**:
```python
# 測試單個模組實例化
window_info = {
    "window_type": "rain_analysis",
    "parameters": {"year": 2025, "race": "Japan", "session": "R"}
}
instance = serializer._create_module_instance(window_info)
assert instance is not None
```

**交付物**:
- [ ] `_import_module_class()` 方法
- [ ] `_validate_parameters()` 方法
- [ ] `_create_module_instance()` 方法
- [ ] 單元測試（至少 3 種模組類型）

---

#### 子任務 5.3: 實現分頁清除方法 ⏱️ 1 小時

**目標**: 安全清除當前所有分頁（除 HOME）

**實現**:

```python
def _clear_existing_tabs(self):
    """清除所有現有分頁（除 HOME）"""
    tab_widget = self.main_window.tab_widget
    
    # 從後往前刪除（避免索引問題）
    for i in range(tab_widget.count() - 1, 0, -1):  # 從最後一個到第 1 個
        tab_name = tab_widget.tabText(i)
        
        if tab_name == "HOME" or i == 0:
            continue
        
        print(f"🗑️ 移除分頁: {tab_name} (索引 {i})")
        
        # 關閉彈出視窗（如果有）
        if i in self.main_window.popped_out_tabs:
            popout_info = self.main_window.popped_out_tabs[i]
            standalone_window = popout_info.get('standalone_window')
            if standalone_window:
                standalone_window.close()
            del self.main_window.popped_out_tabs[i]
        
        # 移除分頁
        widget = tab_widget.widget(i)
        tab_widget.removeTab(i)
        
        # 清理 widget
        if widget:
            widget.deleteLater()
    
    print("✅ 所有分頁已清除（保留 HOME）")
```

**測試**:
```python
# 手動測試步驟
1. 開啟 GUI
2. 創建多個分頁
3. 彈出一個分頁
4. 執行 _clear_existing_tabs()
5. 驗證：
   - 只剩下 HOME 分頁
   - 彈出視窗已關閉
   - 無記憶體洩漏
```

**交付物**:
- [ ] `_clear_existing_tabs()` 方法
- [ ] 彈出視窗清理邏輯
- [ ] 手動測試確認

---

#### 子任務 5.4: 實現分頁重建方法 ⏱️ 3-4 小時

**目標**: 根據配置重建單個分頁及其所有 MDI 視窗

**實現**:

1️⃣ **創建分頁結構**
```python
def _rebuild_tab(self, tab_config: Dict) -> bool:
    """
    重建單個分頁
    
    Args:
        tab_config: 分頁配置字典
        
    Returns:
        是否成功
    """
    try:
        tab_name = tab_config['tab_name']
        tab_index = tab_config['tab_index']
        is_popped_out = tab_config.get('is_popped_out', False)
        
        print(f"🔨 重建分頁: {tab_name} (索引 {tab_index})")
        
        # 創建 MDI 區域
        from modules.gui.base.custom_mdi_area import CustomMdiArea
        mdi_area = CustomMdiArea()
        
        # 添加到 TabWidget
        tab_widget = self.main_window.tab_widget
        actual_index = tab_widget.addTab(mdi_area, tab_name)
        
        # 重建所有 MDI 視窗
        for window_info in tab_config.get('mdi_windows', []):
            self._rebuild_mdi_window(mdi_area, window_info)
        
        # 處理彈出狀態
        if is_popped_out:
            popped_geometry = tab_config.get('popped_window_geometry')
            if popped_geometry:
                self._restore_popout_state(actual_index, mdi_area, popped_geometry)
        
        return True
        
    except Exception as e:
        print(f"❌ 重建分頁失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
```

2️⃣ **重建 MDI 視窗**
```python
def _rebuild_mdi_window(self, mdi_area, window_info: Dict) -> bool:
    """
    重建單個 MDI 視窗
    
    Args:
        mdi_area: 目標 MDI 區域
        window_info: 視窗配置字典
        
    Returns:
        是否成功
    """
    try:
        # 創建模組實例
        module_widget = self._create_module_instance(window_info)
        if not module_widget:
            return False
        
        # 創建 MDI 子視窗
        from PyQt5.QtWidgets import QMdiSubWindow
        sub_window = QMdiSubWindow()
        sub_window.setWidget(module_widget)
        sub_window.setWindowTitle(window_info['window_title'])
        
        # 添加到 MDI 區域
        mdi_area.addSubWindow(sub_window)
        
        # 恢復位置和大小
        position = window_info.get('position', {})
        size = window_info.get('size', {})
        
        if position and size:
            sub_window.setGeometry(
                position.get('x', 0),
                position.get('y', 0),
                size.get('width', 800),
                size.get('height', 600)
            )
        
        # 顯示視窗
        sub_window.show()
        
        # 檢查是否為固定視窗
        if window_info.get('is_fixed', False):
            sub_window.setProperty("is_welcome_fixed", True)
        
        print(f"  ✅ 重建視窗: {window_info['window_title']}")
        return True
        
    except Exception as e:
        print(f"  ❌ 重建視窗失敗: {e}")
        return False
```

3️⃣ **恢復彈出狀態**
```python
def _restore_popout_state(self, tab_index: int, mdi_area, geometry: Dict):
    """
    恢復彈出視窗狀態
    
    Args:
        tab_index: 分頁索引
        mdi_area: 原始 MDI 區域
        geometry: 視窗幾何資訊
    """
    try:
        # 調用主視窗的彈出方法
        # 注意：需要確認主視窗有 _pop_out_tab 方法
        if hasattr(self.main_window, '_pop_out_tab'):
            self.main_window._pop_out_tab(tab_index)
            
            # 恢復視窗幾何
            if tab_index in self.main_window.popped_out_tabs:
                standalone_window = self.main_window.popped_out_tabs[tab_index]['standalone_window']
                standalone_window.setGeometry(
                    geometry.get('x', 100),
                    geometry.get('y', 100),
                    geometry.get('width', 1200),
                    geometry.get('height', 800)
                )
                print(f"  ✅ 恢復彈出狀態")
        else:
            print(f"  ⚠️ 主視窗不支援彈出功能，跳過")
            
    except Exception as e:
        print(f"  ❌ 恢復彈出狀態失敗: {e}")
```

**交付物**:
- [ ] `_rebuild_tab()` 方法
- [ ] `_rebuild_mdi_window()` 方法
- [ ] `_restore_popout_state()` 方法
- [ ] 完整測試（至少 3 個分頁）

---

#### 子任務 5.5: 實現主 deserialize_workspace 方法 ⏱️ 2 小時

**目標**: 整合所有子方法，實現完整的反序列化

**實現**:

```python
def deserialize_workspace(self, config: Dict) -> bool:
    """
    從配置重建完整 Workspace
    
    Args:
        config: Workspace 配置字典（來自資料庫）
        
    Returns:
        是否成功重建
    """
    try:
        print("=" * 60)
        print(f"🔄 開始載入 Workspace")
        print("=" * 60)
        
        # 驗證配置版本
        version = config.get('version', '1.0')
        if version != '1.0':
            print(f"⚠️ 配置版本不匹配: {version}")
            return False
        
        # 步驟 1: 清除現有分頁
        print("\n[1/4] 清除現有分頁...")
        self._clear_existing_tabs()
        
        # 步驟 2: 重建所有分頁
        print("\n[2/4] 重建分頁和視窗...")
        tabs = config.get('tabs', [])
        success_count = 0
        failed_count = 0
        
        for i, tab_config in enumerate(tabs, 1):
            print(f"\n  處理分頁 {i}/{len(tabs)}: {tab_config['tab_name']}")
            if self._rebuild_tab(tab_config):
                success_count += 1
            else:
                failed_count += 1
        
        print(f"\n  分頁重建完成: {success_count} 成功, {failed_count} 失敗")
        
        # 步驟 3: 恢復活動分頁
        print("\n[3/4] 恢復活動分頁...")
        active_tab_index = config.get('active_tab_index', 0)
        tab_widget = self.main_window.tab_widget
        
        # 調整索引（因為可能有分頁失敗）
        if 0 <= active_tab_index < tab_widget.count():
            tab_widget.setCurrentIndex(active_tab_index)
            print(f"  ✅ 切換到分頁 {active_tab_index}")
        else:
            print(f"  ⚠️ 活動分頁索引無效: {active_tab_index}")
        
        # 步驟 4: 最終確認
        print("\n[4/4] 最終確認...")
        total_tabs = len(tabs)
        total_windows = sum(len(tab.get('mdi_windows', [])) for tab in tabs)
        
        print(f"  目標: {total_tabs} 個分頁, {total_windows} 個視窗")
        print(f"  實際: {success_count} 個分頁")
        
        print("\n" + "=" * 60)
        if failed_count == 0:
            print("✅ Workspace 載入完成！")
        else:
            print(f"⚠️ Workspace 載入完成（{failed_count} 個分頁失敗）")
        print("=" * 60)
        
        return success_count > 0
        
    except Exception as e:
        print(f"\n❌ Workspace 載入失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
```

**交付物**:
- [ ] `deserialize_workspace()` 主方法
- [ ] 完整的錯誤處理
- [ ] 詳細的日誌輸出
- [ ] 進度追蹤

---

#### 子任務 5.6: 錯誤處理和資料驗證 ⏱️ 1-2 小時

**目標**: 完善錯誤處理機制

**實現**:

1️⃣ **資料檔案驗證**
```python
def _validate_data_file(self, window_info: Dict) -> bool:
    """驗證資料檔案是否存在"""
    data_file = window_info.get('data_file')
    
    if not data_file:
        # 沒有資料檔案路徑，可能需要重新載入
        return True
    
    if not Path(data_file).exists():
        print(f"⚠️ 資料檔案不存在: {data_file}")
        
        # 提示使用者
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self.main_window,
            "資料檔案遺失",
            f"視窗 '{window_info['window_title']}' 的資料檔案不存在:\n"
            f"{data_file}\n\n"
            f"是否跳過此視窗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        return reply == QMessageBox.No
    
    return True
```

2️⃣ **配置驗證**
```python
def _validate_config(self, config: Dict) -> Tuple[bool, Optional[str]]:
    """
    驗證配置完整性
    
    Returns:
        (is_valid, error_message)
    """
    # 檢查必需欄位
    if 'version' not in config:
        return False, "配置缺少 version 欄位"
    
    if 'tabs' not in config:
        return False, "配置缺少 tabs 欄位"
    
    # 檢查分頁結構
    for i, tab in enumerate(config.get('tabs', [])):
        if 'tab_name' not in tab:
            return False, f"分頁 {i} 缺少 tab_name 欄位"
        
        if 'mdi_windows' not in tab:
            return False, f"分頁 {i} 缺少 mdi_windows 欄位"
    
    return True, None
```

3️⃣ **回滾機制**（可選）
```python
def _create_backup_state(self):
    """創建當前狀態快照（用於回滾）"""
    # 序列化當前狀態
    return self.serialize_workspace()

def _restore_backup_state(self, backup_config):
    """恢復備份狀態"""
    self.deserialize_workspace(backup_config)
```

**交付物**:
- [ ] `_validate_data_file()` 方法
- [ ] `_validate_config()` 方法
- [ ] 使用者友好的錯誤訊息
- [ ] （可選）回滾機制

---

#### 子任務 5.7: 更新主視窗載入處理 ⏱️ 30 分鐘

**目標**: 替換臨時提示為實際調用

**實現**:

修改 `f1t_gui_main.py` 中的 `_on_workspace_loaded()`:

```python
def _on_workspace_loaded(self, workspace_id: int, config: Dict):
    """Workspace 載入的回調 - 重建所有分頁和視窗"""
    print(f"[WORKSPACE] 🔄 開始載入 Workspace: ID={workspace_id}")
    
    try:
        # 調用反序列化
        success = self.workspace_serializer.deserialize_workspace(config)
        
        if success:
            QMessageBox.information(
                self,
                "載入成功",
                f"Workspace 已成功載入！\n\n"
                f"• 分頁數: {len(config.get('tabs', []))}\n"
                f"• 視窗數: {sum(len(tab.get('mdi_windows', [])) for tab in config.get('tabs', []))}"
            )
        else:
            QMessageBox.warning(
                self,
                "載入失敗",
                "Workspace 載入失敗，請檢查日誌。"
            )
        
    except Exception as e:
        logger.exception("Failed to load workspace", exc_info=e)
        QMessageBox.critical(
            self,
            "載入失敗",
            f"無法載入 Workspace：{str(e)}"
        )
```

**交付物**:
- [ ] 更新 `_on_workspace_loaded()` 方法
- [ ] 移除臨時提示訊息
- [ ] 測試完整流程

---

### Task 7: 端對端測試 ⏱️ 2-3 小時

#### 測試場景

##### 場景 1: 基本儲存和載入
**步驟**:
1. 開啟 GUI
2. 創建 2 個分頁
3. 在每個分頁中開啟 2-3 個分析模組
4. 調整視窗位置和大小
5. 執行 Save Workspace（命名："Test_Basic"）
6. 關閉所有分頁
7. 執行 Load Workspace 選擇 "Test_Basic"
8. 驗證：
   - [ ] 分頁數量正確
   - [ ] 視窗數量正確
   - [ ] 視窗位置正確
   - [ ] 視窗大小正確
   - [ ] 參數正確（年份、賽事、會話）

##### 場景 2: 彈出視窗
**步驟**:
1. 創建 1 個分頁
2. 開啟 2 個分析模組
3. 彈出該分頁
4. 調整彈出視窗位置和大小
5. Save Workspace（命名："Test_Popout"）
6. 關閉
7. Load Workspace
8. 驗證：
   - [ ] 分頁正確彈出
   - [ ] 彈出視窗位置正確
   - [ ] 彈出視窗大小正確
   - [ ] MDI 視窗完整

##### 場景 3: 多分頁混合
**步驟**:
1. 創建 3 個分頁
   - 分頁 1: 正常（2 個視窗）
   - 分頁 2: 彈出（3 個視窗）
   - 分頁 3: 正常（1 個視窗）
2. 設定活動分頁為分頁 2
3. Save Workspace（命名："Test_Mixed"）
4. 關閉
5. Load Workspace
6. 驗證：
   - [ ] 3 個分頁正確創建
   - [ ] 分頁 2 正確彈出
   - [ ] 活動分頁為分頁 2
   - [ ] 所有視窗完整

##### 場景 4: 資料檔案遺失
**步驟**:
1. 創建並儲存 Workspace
2. 手動刪除其中一個資料檔案
3. Load Workspace
4. 驗證：
   - [ ] 顯示資料檔案遺失警告
   - [ ] 詢問是否跳過
   - [ ] 其他視窗正常載入

##### 場景 5: 錯誤處理
**步驟**:
1. 手動修改資料庫，破壞 JSON 格式
2. Load Workspace
3. 驗證：
   - [ ] 顯示友好的錯誤訊息
   - [ ] GUI 不崩潰
   - [ ] 可以繼續操作

##### 場景 6: 搜尋和刪除
**步驟**:
1. 創建 5 個不同的 Workspace
2. 使用搜尋功能過濾
3. 刪除其中 2 個
4. 重新整理列表
5. 驗證：
   - [ ] 搜尋結果正確
   - [ ] 刪除成功
   - [ ] 列表更新正確

---

## 📊 預計時間表

```
子任務                        時間估計     累計時間
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5.1 模組工廠映射表             1-2 小時     2 小時
5.2 模組實例化方法             2-3 小時     5 小時
5.3 分頁清除方法               1 小時       6 小時
5.4 分頁重建方法               3-4 小時     10 小時
5.5 主 deserialize 方法        2 小時       12 小時
5.6 錯誤處理和驗證             1-2 小時     14 小時
5.7 更新主視窗處理             0.5 小時     14.5 小時
Task 7 端對端測試              2-3 小時     17 小時
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
總計                          11-17 小時
```

**建議工作安排**:
- **第 1 天**: 子任務 5.1 - 5.3（約 4-6 小時）
- **第 2 天**: 子任務 5.4 - 5.6（約 6-9 小時）
- **第 3 天**: 子任務 5.7 + Task 7 測試（約 3-4 小時）

---

## ✅ 驗收標準

### 功能標準
- [ ] 能夠完整載入所有 17 種模組類型
- [ ] 視窗位置誤差 < 10px
- [ ] 視窗大小誤差 < 20px
- [ ] 彈出視窗正確恢復
- [ ] 活動分頁正確恢復
- [ ] 參數完整保留

### 效能標準
- [ ] 載入 10 個視窗 < 5 秒
- [ ] 載入 50 個視窗 < 15 秒
- [ ] 無記憶體洩漏

### 穩定性標準
- [ ] 所有測試場景通過
- [ ] 錯誤處理完善
- [ ] 無崩潰或凍結

---

## 🎯 成功指標

**Phase 2 完成後，使用者應該能夠**:
1. ✅ 儲存當前完整工作區狀態
2. ✅ 瀏覽和搜尋已儲存的 Workspace
3. ✅ 載入 Workspace，完全恢復之前的狀態
4. ✅ 管理多個 Workspace（刪除、重命名）
5. ✅ 在不同分析任務間快速切換

**使用場景**:
- 🏎️ "2025 USA GP 分析" - 包含輪胎策略、降雨分析、單圈對比
- 🏁 "Japan Suzuka Race" - 賽道分析、事故分析、進站策略
- 📊 "賽季總結" - 排名表、賽季進度、日曆視圖

---

## 📝 下一步行動

### 立即開始
1. 閱讀本計劃文檔
2. 確認理解所有子任務
3. 開始執行子任務 5.1

### 每日檢查點
- 完成的子任務數量
- 遇到的技術問題
- 需要調整的計劃

### 完成後
1. 更新 WORKSPACE_MANAGER_PHASE1_COMPLETION_REPORT.md
2. 創建 Phase 2 完成報告
3. 規劃 Phase 3（進階功能）

---

## 🆘 風險和緩解

### 風險 1: 模組實例化簽名不一致
**緩解**: 建立詳細的映射表，針對特殊模組單獨處理

### 風險 2: 資料檔案路徑變更
**緩解**: 實現檔案查找邏輯，支援相對路徑和絕對路徑

### 風險 3: 彈出視窗機制不支援
**緩解**: 檢查主視窗方法，必要時提供替代方案

### 風險 4: 效能問題（大量視窗）
**緩解**: 實現批次載入，顯示進度條

---

**準備開始了嗎？讓我們完成 Workspace Manager！** 🚀
