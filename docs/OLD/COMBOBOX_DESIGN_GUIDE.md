# F1T GUI 下拉式選單設計指南
# F1T GUI ComboBox Design Guide

> **版本**: V0.11.0  
> **最後更新**: 2025-12-11  
> **適用範圍**: 所有 F1T GUI 下拉式選單元件

---

## 📋 目錄 (Table of Contents)

1. [基礎樣式系統](#基礎樣式系統)
2. [標準下拉選單類型](#標準下拉選單類型)
3. [Race ComboBox 完整規格](#race-combobox-完整規格)
4. [Driver ComboBox 完整規格](#driver-combobox-完整規格)
5. [Session ComboBox 完整規格](#session-combobox-完整規格)
6. [Year ComboBox 完整規格](#year-combobox-完整規格)
7. [數據綁定模式](#數據綁定模式)
8. [事件處理機制](#事件處理機制)
9. [開發最佳實踐](#開發最佳實踐)
10. [常見問題解答](#常見問題解答)

---

## 🎨 基礎樣式系統

### 1.1 完整 QSS 定義

```css
QComboBox {
    /* 背景與邊框 */
    background-color: #FFFFFF;              /* 白色背景 */
    border: 1px solid #AAAAAA;              /* 灰色邊框 */
    border-radius: 3px;                     /* 圓角 */
    padding: 2px 5px;                       /* 內邊距 */
    
    /* 文字樣式 */
    color: #333333;                         /* 深灰文字 */
    font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
    font-size: 8pt;                         /* 緊湊字型 */
    
    /* 最小高度 */
    min-height: 20px;                       /* 確保可點擊區域 */
}

QComboBox:hover {
    border: 1px solid #999999;              /* 懸停時深灰邊框 */
}

QComboBox:focus {
    border: 1px solid #4CAF50;              /* 焦點時綠色邊框 */
    outline: none;                          /* 移除系統焦點框 */
}

QComboBox:disabled {
    background-color: #F5F5F5;              /* 禁用時淺灰背景 */
    color: #999999;                         /* 禁用時淺色文字 */
    border: 1px solid #CCCCCC;              /* 禁用時淺灰邊框 */
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;                            /* 下拉箭頭寬度 */
    border-left: 1px solid #AAAAAA;         /* 左側分隔線 */
    border-top-right-radius: 3px;           /* 圓角對齊 */
    border-bottom-right-radius: 3px;
}

QComboBox::down-arrow {
    image: none;                            /* 使用系統預設箭頭 */
    width: 10px;
    height: 10px;
}

QComboBox QAbstractItemView {
    /* 下拉選單列表樣式 */
    background-color: #FFFFFF;
    border: 1px solid #AAAAAA;
    selection-background-color: #d1e7dd;    /* 選中項淺綠背景 */
    selection-color: #333333;               /* 選中項文字保持深灰 */
    padding: 2px;
}

QComboBox QAbstractItemView::item {
    min-height: 24px;                       /* 列表項最小高度 */
    padding: 3px 5px;                       /* 列表項內邊距 */
}

QComboBox QAbstractItemView::item:hover {
    background-color: #F0F0F0;              /* 懸停時淺灰背景 */
}

QComboBox QAbstractItemView::item:selected {
    background-color: #d1e7dd;              /* 選中時淺綠背景 */
    border: 1px solid #a3cfbb;              /* 選中時綠色邊框 */
}
```

### 1.2 自訂 ComboBox 類別

F1T GUI 使用自訂的 `AnalysisComboBox` 類別，提供額外功能：

```python
class AnalysisComboBox(QComboBox):
    """
    分析用自訂下拉選單
    
    增強功能：
    - 滑鼠滾輪禁用（防止誤觸）
    - 鍵盤快捷鍵支援
    - 自訂工具提示
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        
    def wheelEvent(self, event):
        """
        禁用滑鼠滾輪（防止使用者誤觸改變選項）
        
        設計理由：
        在工具列中，使用者滾動頁面時可能無意間改變下拉選單的值，
        導致分析參數意外變更。禁用滾輪可避免此問題。
        """
        event.ignore()
        
    def keyPressEvent(self, event):
        """鍵盤快捷鍵支援"""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Enter 鍵觸發選擇
            self.activated.emit(self.currentIndex())
        else:
            super().keyPressEvent(event)
```

---

## 📊 標準下拉選單類型

F1T GUI 包含 **4 種標準下拉選單**，每種都有特定用途和規格：

| 類型 | 寬度 | 資料來源 | 更新頻率 | 複雜度 |
|------|------|----------|----------|--------|
| **Year ComboBox** | 80px | 硬編碼範圍 | 每年一次 | ⭐ 簡單 |
| **Race ComboBox** | 250px | SeasonCalendarProvider | 動態（7天/12小時） | ⭐⭐⭐⭐⭐ 最複雜 |
| **Session ComboBox** | 120px | 賽事相依 | 賽事切換時 | ⭐⭐ 中等 |
| **Driver ComboBox** | 100px | API (Function 97) | 年份切換時 | ⭐⭐⭐ 進階 |

---

## 🏁 Race ComboBox 完整規格

### 2.1 功能概述

Race ComboBox 是系統中**最複雜的下拉選單**，負責賽事選擇並提供智慧化使用者體驗。

**核心特性**：
- ✅ 顯示賽事名稱 + 日期（例如 `"Japan (2025-04-06)"`）
- ✅ 智慧分組（已完賽 / 未來賽事）
- ✅ 視覺分隔線
- ✅ 動態更新（賽事接近時提高頻率）
- ✅ 自動選擇最相關賽事
- ✅ 完整資料綁定（SeasonEvent 物件）

---

### 2.2 資料結構

```python
from dataclasses import dataclass
from typing import Dict

@dataclass
class SeasonEvent:
    """
    賽季賽事資料結構
    
    用於 Race ComboBox 的資料綁定，每個選項儲存完整的賽事資訊。
    """
    round_number: int           # 賽事輪次（1-24）
    race_key: str              # 賽事名稱（FastF1 格式，例如 "Japan"）
    race_date: str             # 賽事日期（ISO 格式 "YYYY-MM-DD"）
    is_completed: bool         # 是否已完賽（基於當前時間判斷）
    sessions: Dict[str, str]   # 可用賽段 {"R": "Race", "Q": "Qualifying", ...}
    display_label: str         # 顯示標籤（自動生成，例如 "Japan (2025-04-06)"）
```

---

### 2.3 初始化代碼

```python
class StyleHMainWindow(QMainWindow):
    def create_professional_toolbar(self):
        """創建專業工具列（包含 Race ComboBox）"""
        toolbar = QToolBar("分析工具列")
        toolbar.setMovable(False)
        
        # 年份選擇
        self.year_combo = AnalysisComboBox()
        self.year_combo.setFixedWidth(80)
        # ... (Year ComboBox 設定)
        
        # 賽事選擇 ⭐ 核心重點
        self.race_combo = AnalysisComboBox()
        self.race_combo.setFixedWidth(250)  # 固定寬度容納日期
        self.race_combo.setToolTip(tr('race_selector_tooltip', 
                                      'Select race event. Shows completed races first, then upcoming races.'))
        
        # 連接事件處理器
        self.year_combo.currentIndexChanged.connect(self._on_year_changed)
        self.race_combo.currentIndexChanged.connect(self._on_race_changed)
        
        # 初始化賽季資料
        current_year = datetime.now().year
        self._load_season_events(current_year)
        
        toolbar.addWidget(QLabel(tr('race_label', 'Race:')))
        toolbar.addWidget(self.race_combo)
```

---

### 2.4 資料載入邏輯

```python
def _load_season_events(self, year: int):
    """
    載入指定年份的賽季賽事
    
    流程：
    1. 從 SeasonCalendarProvider 獲取賽事列表
    2. 分組為已完賽 / 未來賽事
    3. 填充下拉選單（已完賽 → 分隔線 → 未來賽事）
    4. 設定智慧預設選項
    
    Args:
        year: 賽季年份（例如 2025）
    """
    try:
        # 步驟 1: 獲取賽事資料
        events = self._season_provider.get_season_calendar(year)
        
        if not events:
            logger.warning(f"[RACE_COMBO] 無法載入 {year} 年賽季資料")
            self.race_combo.clear()
            self.race_combo.addItem(tr('no_races_available', 'No races available'), None)
            return
        
        # 步驟 2: 分組排序
        completed_events = [e for e in events if e.is_completed]
        upcoming_events = [e for e in events if not e.is_completed]
        
        logger.debug(f"[RACE_COMBO] {year} 年: {len(completed_events)} 場已完賽, "
                    f"{len(upcoming_events)} 場未來賽事")
        
        # 步驟 3: 清空並重新填充
        self.race_combo.blockSignals(True)  # 暫時阻止信號（避免觸發事件）
        self.race_combo.clear()
        
        # 建立查詢字典（用於快速查找）
        self._race_event_lookup.clear()
        self._display_to_race_key.clear()
        
        # 3.1 添加已完賽賽事
        for event in completed_events:
            display = f"{event.race_key} ({event.race_date})"
            self.race_combo.addItem(display, event)  # event 儲存在 UserRole
            
            # 更新查詢字典
            self._race_event_lookup[event.race_key] = event
            self._display_to_race_key[display] = event.race_key
        
        # 3.2 添加分隔線（如果同時有已完賽和未來賽事）
        if completed_events and upcoming_events:
            separator_text = "─" * 30  # 30 個全形破折號
            self.race_combo.addItem(separator_text, None)
            self.race_combo.model().item(self.race_combo.count() - 1).setEnabled(False)
        
        # 3.3 添加未來賽事
        for event in upcoming_events:
            display = f"{event.race_key} ({event.race_date}) [{tr('upcoming_race', '未開賽')}]"
            self.race_combo.addItem(display, event)
            
            # 更新查詢字典
            self._race_event_lookup[event.race_key] = event
            self._display_to_race_key[display] = event.race_key
        
        # 步驟 4: 設定智慧預設選項
        self._set_smart_race_selection(completed_events, upcoming_events)
        
        self.race_combo.blockSignals(False)  # 恢復信號
        
    except Exception as e:
        logger.error(f"[RACE_COMBO] 載入賽季資料失敗: {e}")
        self.race_combo.clear()
        self.race_combo.addItem(tr('load_error', 'Error loading races'), None)
```

---

### 2.5 智慧選擇演算法

```python
def _set_smart_race_selection(self, completed_events: list, upcoming_events: list):
    """
    智慧選擇預設賽事
    
    優先順序：
    1. 使用者上次手動選擇的賽事（年份切換時保留）
    2. 最近完賽的賽事（最相關的歷史數據）
    3. 第一場即將舉行的賽事（如果沒有已完賽）
    
    Args:
        completed_events: 已完賽賽事列表
        upcoming_events: 未來賽事列表
    """
    # 情境 1: 嘗試恢復使用者上次選擇
    if hasattr(self, '_last_selected_race_key') and self._last_selected_race_key:
        for i in range(self.race_combo.count()):
            item_data = self.race_combo.itemData(i)
            if item_data and item_data.race_key == self._last_selected_race_key:
                self.race_combo.setCurrentIndex(i)
                logger.debug(f"[RACE_COMBO] 恢復上次選擇: {self._last_selected_race_key}")
                return
    
    # 情境 2: 選擇最近完賽的賽事
    if completed_events:
        last_completed_index = len(completed_events) - 1
        self.race_combo.setCurrentIndex(last_completed_index)
        logger.debug(f"[RACE_COMBO] 預設選擇最近完賽: {completed_events[-1].race_key}")
        return
    
    # 情境 3: 選擇第一場未來賽事
    if upcoming_events:
        self.race_combo.setCurrentIndex(0)
        logger.debug(f"[RACE_COMBO] 預設選擇未來賽事: {upcoming_events[0].race_key}")
        return
    
    # 情境 4: 無可用賽事（異常情況）
    logger.warning("[RACE_COMBO] 無可用賽事可選擇")
```

---

### 2.6 動態更新機制

```python
class SeasonCalendarProvider:
    """
    賽季日曆提供者
    
    負責從 Ergast API 獲取賽季資料，並實現智慧快取機制。
    """
    
    def __init__(self):
        self._cache: Dict[int, List[SeasonEvent]] = {}
        self._cache_timestamp: Dict[int, datetime] = {}
        
    def get_season_calendar(self, year: int) -> List[SeasonEvent]:
        """
        獲取賽季日曆（帶智慧快取）
        
        快取策略：
        - 正常模式：7 天更新一次（賽季穩定期）
        - 加速模式：12 小時更新一次（下一場賽事 7 天內）
        
        Args:
            year: 賽季年份
            
        Returns:
            SeasonEvent 列表（按 round_number 排序）
        """
        # 檢查快取是否有效
        if year in self._cache and year in self._cache_timestamp:
            cache_age = datetime.now() - self._cache_timestamp[year]
            
            # 判斷快取策略
            cached_events = self._cache[year]
            next_race = self._find_next_race(cached_events)
            
            if next_race:
                days_until_race = (next_race.race_date - datetime.now().date()).days
                
                # 賽事接近時使用短快取（12 小時）
                if days_until_race <= 7:
                    max_cache_age = timedelta(hours=12)
                    logger.debug(f"[CALENDAR] 下一場賽事 {days_until_race} 天內，使用 12 小時快取")
                else:
                    max_cache_age = timedelta(days=7)
            else:
                # 賽季結束，使用長快取
                max_cache_age = timedelta(days=30)
            
            # 快取仍有效
            if cache_age < max_cache_age:
                logger.debug(f"[CALENDAR] 使用快取資料（{cache_age.total_seconds() / 3600:.1f} 小時前）")
                return cached_events
        
        # 快取過期或不存在，重新獲取
        logger.debug(f"[CALENDAR] 從 Ergast API 獲取 {year} 年資料")
        events = self._fetch_from_ergast_api(year)
        
        # 更新快取
        self._cache[year] = events
        self._cache_timestamp[year] = datetime.now()
        
        return events
    
    def _find_next_race(self, events: List[SeasonEvent]) -> Optional[SeasonEvent]:
        """找到下一場即將舉行的賽事"""
        today = datetime.now().date()
        upcoming = [e for e in events if not e.is_completed]
        return upcoming[0] if upcoming else None
    
    def _fetch_from_ergast_api(self, year: int) -> List[SeasonEvent]:
        """從 Ergast API 獲取賽季資料"""
        url = f"http://ergast.com/api/f1/{year}.json"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"[CALENDAR] Ergast API 請求失敗: {response.status_code}")
            return []
        
        data = response.json()
        races = data.get('MRData', {}).get('RaceTable', {}).get('Races', [])
        
        events = []
        today = datetime.now().date()
        
        for race in races:
            race_date_str = race.get('date', '')
            race_date = datetime.strptime(race_date_str, '%Y-%m-%d').date()
            
            # 判斷是否已完賽（賽事日期 + 1 天 < 今天）
            is_completed = (race_date + timedelta(days=1)) < today
            
            # 提取賽事名稱（移除 "Grand Prix" 後綴）
            race_name = race.get('raceName', '').replace(' Grand Prix', '')
            
            event = SeasonEvent(
                round_number=int(race.get('round', 0)),
                race_key=race_name,
                race_date=race_date_str,
                is_completed=is_completed,
                sessions=self._detect_available_sessions(year, race_name),
                display_label=f"{race_name} ({race_date_str})"
            )
            events.append(event)
        
        # 按輪次排序
        events.sort(key=lambda e: e.round_number)
        
        return events
```

---

### 2.7 事件處理

```python
def _on_race_changed(self, index: int):
    """
    Race ComboBox 選擇變更時觸發
    
    連鎖反應：
    1. 記錄使用者選擇（用於智慧恢復）
    2. 更新 Session ComboBox（載入該賽事的可用賽段）
    3. 通知所有訂閱者（MDI 子視窗）
    
    Args:
        index: 新選擇的索引
    """
    # 忽略分隔線
    item_data = self.race_combo.itemData(index)
    if item_data is None:
        logger.debug("[RACE_COMBO] 忽略分隔線點擊")
        return
    
    # 記錄使用者選擇
    self._last_selected_race_key = item_data.race_key
    logger.debug(f"[RACE_COMBO] 使用者選擇: {item_data.race_key} ({item_data.race_date})")
    
    # 更新 Session ComboBox
    self._update_session_combo(item_data.sessions)
    
    # 通知訂閱者（參數變更廣播）
    self._broadcast_parameter_change()
```

---

### 2.8 樣式微調

```python
# Race ComboBox 特殊樣式（在 QSS 中定義）
"""
QComboBox#race_combo {
    min-width: 250px;                       /* 確保寬度足夠 */
    max-width: 250px;                       /* 禁止自動拉伸 */
}

QComboBox#race_combo QAbstractItemView {
    min-width: 280px;                       /* 下拉列表稍寬（顯示完整文字） */
}

QComboBox#race_combo QAbstractItemView::item {
    padding: 4px 8px;                       /* 較寬鬆的內邊距 */
}
"""

# 套用特殊樣式
self.race_combo.setObjectName("race_combo")
```

---

## 👤 Driver ComboBox 完整規格

### 3.1 功能概述

Driver ComboBox 用於選擇 F1 車手，支援年份相依的車手列表。

**核心特性**：
- ✅ 顯示 3 字母車手代碼（例如 `"VER"`, `"HAM"`, `"LEC"`）
- ✅ 年份相依（不同年份車手列表不同）
- ✅ API 優先載入（Function 97: Championship Standings）
- ✅ 全域快取機制（避免重複 API 調用）
- ✅ 支援 "None" 選項（例如車手 2 為選填）

---

### 3.2 資料來源

```python
def get_drivers_for_year(self, year: int) -> list:
    """
    取得指定年份的車手列表（帶全域快取）
    
    載入策略：
    1. 檢查快取 → 如果有則直接返回
    2. 調用 API Function 97 (Championship Standings)
    3. 從積分榜提取車手代碼列表
    4. 快取結果供後續使用
    
    Args:
        year: 賽季年份（例如 2025）
        
    Returns:
        車手代碼列表（已排序），例如 ['ALB', 'ALO', 'VER', ...]
        如果載入失敗返回空列表
    """
    # 檢查快取
    if year in self._cached_drivers_by_year:
        cached_list = self._cached_drivers_by_year[year]
        logger.debug(f"[DRIVER_CACHE] 返回快取車手列表 {year} ({len(cached_list)} 位)")
        return cached_list
    
    logger.debug(f"[DRIVER_CACHE] 快取未命中，從 API 載入 {year} 年車手")
    
    drivers = []
    try:
        import requests
        from core.api_base_url import resolve_api_base_url
        
        api_base = resolve_api_base_url()
        api_url = f"{api_base}/api/v2/analysis/execute"
        
        # 使用 Function 97 (Championship Standings)
        query_params = {"function_id": 97, "year": int(year)}
        
        response = requests.post(api_url, params=query_params, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success') and 'data' in result:
                data = result['data']
                
                # API 返回結構: {"data": {"data": {"drivers": [...]}}}
                if 'data' in data and isinstance(data['data'], dict):
                    inner_data = data['data']
                    
                    if 'drivers' in inner_data:
                        # 從積分榜提取車手代碼
                        for entry in inner_data['drivers']:
                            driver_info = entry.get('driver', {})
                            driver_code = driver_info.get('code', '')
                            if driver_code:
                                drivers.append(driver_code)
                        
                        logger.debug(f"[DRIVER_CACHE] 成功載入 {len(drivers)} 位車手")
    
    except Exception as e:
        logger.error(f"[DRIVER_CACHE] API 調用失敗: {e}")
    
    # 快取結果（即使是空列表，避免重複請求）
    self._cached_drivers_by_year[year] = drivers
    
    return drivers
```

---

### 3.3 初始化代碼

```python
# 方式 1: 工具列中的 Driver ComboBox（單一選擇）
def create_professional_toolbar(self):
    # ... (Year, Race, Session 設定)
    
    # 車手選擇
    self.driver_combo = AnalysisComboBox()
    self.driver_combo.setFixedWidth(100)  # 固定寬度（3 字母代碼）
    self.driver_combo.setToolTip(tr('driver_selector_tooltip', 
                                    'Select driver for analysis'))
    
    # 初始化車手列表
    current_year = int(self.year_combo.currentText())
    self._load_drivers_for_year(current_year)
    
    toolbar.addWidget(QLabel(tr('driver_label', 'Driver:')))
    toolbar.addWidget(self.driver_combo)

def _load_drivers_for_year(self, year: int):
    """載入指定年份的車手列表到 ComboBox"""
    drivers = self.get_drivers_for_year(year)
    
    self.driver_combo.blockSignals(True)
    self.driver_combo.clear()
    
    if drivers:
        self.driver_combo.addItems(drivers)
        logger.debug(f"[DRIVER_COMBO] 已載入 {len(drivers)} 位車手")
    else:
        self.driver_combo.addItem(tr('no_drivers', 'No drivers available'), None)
        logger.warning(f"[DRIVER_COMBO] {year} 年無車手資料")
    
    self.driver_combo.blockSignals(False)
```

```python
# 方式 2: 對話框中的 Driver ComboBox（支援 "None" 選項）
class TelemetryChartDialog(QDialog):
    def init_ui(self):
        # 車手 1（必選）
        self.driver1_combo = QComboBox()
        self.driver1_combo.setFixedWidth(100)
        
        # 車手 2（選填，第一個選項為 "None"）
        self.driver2_combo = QComboBox()
        self.driver2_combo.setFixedWidth(100)
        self.driver2_combo.addItem(tr('none_option', 'None'), None)  # ⭐ 關鍵
        
        # 從主視窗快取載入車手列表
        year = int(parent_window.year_combo.currentText())
        drivers = parent_window.get_drivers_for_year(year)
        
        if drivers:
            self.driver1_combo.addItems(drivers)
            self.driver1_combo.setCurrentText(drivers[0])  # 預設第一位
            
            self.driver2_combo.addItems(drivers)  # ⭐ None 之後添加車手
            self.driver2_combo.setCurrentIndex(0)  # 預設 None
    
    def get_selected_drivers(self):
        """獲取選擇的車手"""
        driver1 = self.driver1_combo.currentText()
        
        # 判斷車手 2 是否選擇了 "None"
        driver2_data = self.driver2_combo.currentData()
        driver2 = None if driver2_data is None else self.driver2_combo.currentText()
        
        return {
            'driver1': driver1,
            'driver2': driver2  # 可能是 None
        }
```

---

### 3.4 事件處理

```python
def _on_year_changed(self, index: int):
    """
    Year ComboBox 變更時觸發
    
    連鎖反應：
    1. 重新載入 Race ComboBox（新年份的賽季資料）
    2. 重新載入 Driver ComboBox（新年份的車手列表）
    3. 清空 Session ComboBox（等待賽事選擇）
    """
    new_year = int(self.year_combo.currentText())
    logger.debug(f"[YEAR_COMBO] 年份變更: {new_year}")
    
    # 重新載入賽事
    self._load_season_events(new_year)
    
    # 重新載入車手
    self._load_drivers_for_year(new_year)
    
    # 通知訂閱者
    self._broadcast_parameter_change()
```

---

### 3.5 快取最佳化

```python
# 主視窗初始化時預載入當前年份車手列表
def __init__(self):
    # ... (其他初始化)
    
    # 車手列表快取機制（啟動時載入，全域共享）
    self._cached_drivers_by_year = {}  # {year: [driver_codes]}
    
    # 預載入當前年份（減少首次顯示延遲）
    current_year = datetime.now().year
    QTimer.singleShot(1000, lambda: self.get_drivers_for_year(current_year))
```

---

## 📅 Session ComboBox 完整規格

### 4.1 功能概述

Session ComboBox 用於選擇賽事的特定賽段（練習賽、排位賽、正賽）。

**核心特性**：
- ✅ 賽事相依（不同賽事可用賽段不同）
- ✅ 顯示完整名稱 + 簡稱（例如 `"Race (R)"`）
- ✅ 智慧預設（正賽優先）
- ✅ 圖示支援（🏁 Race, 🏎️ Qualifying）

---

### 4.2 資料結構

```python
# 標準賽段映射
STANDARD_SESSIONS = {
    'FP1': ('Free Practice 1', '🏎️'),
    'FP2': ('Free Practice 2', '🏎️'),
    'FP3': ('Free Practice 3', '🏎️'),
    'Q': ('Qualifying', '🏁'),
    'SQ': ('Sprint Qualifying', '⚡'),
    'S': ('Sprint', '⚡'),
    'R': ('Race', '🏁')
}
```

---

### 4.3 初始化代碼

```python
def create_professional_toolbar(self):
    # ... (Year, Race 設定)
    
    # 賽段選擇
    self.session_combo = AnalysisComboBox()
    self.session_combo.setFixedWidth(120)  # 固定寬度
    self.session_combo.setToolTip(tr('session_selector_tooltip', 
                                     'Select session type'))
    
    # 預設選項（等待賽事選擇）
    self.session_combo.addItem(tr('select_race_first', 'Select race first'), None)
    self.session_combo.setEnabled(False)
    
    toolbar.addWidget(QLabel(tr('session_label', 'Session:')))
    toolbar.addWidget(self.session_combo)
```

---

### 4.4 動態更新

```python
def _update_session_combo(self, available_sessions: Dict[str, str]):
    """
    更新 Session ComboBox（當賽事變更時）
    
    Args:
        available_sessions: 可用賽段字典
                           例如 {'R': 'Race', 'Q': 'Qualifying', 'FP1': 'Free Practice 1'}
    """
    self.session_combo.blockSignals(True)
    self.session_combo.clear()
    
    if not available_sessions:
        self.session_combo.addItem(tr('no_sessions', 'No sessions available'), None)
        self.session_combo.setEnabled(False)
        self.session_combo.blockSignals(False)
        return
    
    # 按優先順序排序（R > Q > S > SQ > FP3 > FP2 > FP1）
    priority_order = ['R', 'Q', 'S', 'SQ', 'FP3', 'FP2', 'FP1']
    sorted_sessions = sorted(available_sessions.keys(), 
                            key=lambda s: priority_order.index(s) if s in priority_order else 99)
    
    # 填充選項
    for session_key in sorted_sessions:
        full_name = available_sessions[session_key]
        icon = STANDARD_SESSIONS.get(session_key, ('', ''))[1]
        
        display = f"{icon} {full_name} ({session_key})"
        self.session_combo.addItem(display, session_key)
    
    # 智慧預設：優先選擇 Race，否則第一個可用
    race_index = self.session_combo.findData('R')
    if race_index != -1:
        self.session_combo.setCurrentIndex(race_index)
        logger.debug("[SESSION_COMBO] 預設選擇: Race")
    else:
        self.session_combo.setCurrentIndex(0)
        logger.debug(f"[SESSION_COMBO] 預設選擇: {sorted_sessions[0]}")
    
    self.session_combo.setEnabled(True)
    self.session_combo.blockSignals(False)
```

---

## 📆 Year ComboBox 完整規格

### 5.1 功能概述

Year ComboBox 是最簡單的下拉選單，用於選擇賽季年份。

**核心特性**：
- ✅ 硬編碼範圍（通常 2018-2025）
- ✅ 預設當前年份
- ✅ 緊湊寬度 80px

---

### 5.2 初始化代碼

```python
def create_professional_toolbar(self):
    # 年份選擇
    self.year_combo = AnalysisComboBox()
    self.year_combo.setFixedWidth(80)
    self.year_combo.setToolTip(tr('year_selector_tooltip', 'Select season year'))
    
    # 填充年份（2018-2025）
    current_year = datetime.now().year
    for year in range(2018, current_year + 1):
        self.year_combo.addItem(str(year), year)
    
    # 預設當前年份
    self.year_combo.setCurrentText(str(current_year))
    
    # 連接事件
    self.year_combo.currentIndexChanged.connect(self._on_year_changed)
    
    toolbar.addWidget(QLabel(tr('year_label', 'Year:')))
    toolbar.addWidget(self.year_combo)
```

---

## 🔗 數據綁定模式

F1T GUI 使用 **Qt 的 UserRole 機制**進行數據綁定：

### 6.1 基本模式

```python
# 添加項目時綁定數據
combobox.addItem(display_text, user_data)  # user_data 儲存在 Qt.UserRole

# 獲取當前選中項目的數據
current_data = combobox.currentData()

# 獲取指定索引的數據
item_data = combobox.itemData(index)

# 查找數據對應的索引
index = combobox.findData(target_data)
```

---

### 6.2 進階範例：Race ComboBox

```python
# 綁定完整 SeasonEvent 物件
for event in events:
    display = f"{event.race_key} ({event.race_date})"
    self.race_combo.addItem(display, event)  # ⭐ event 是完整物件

# 獲取選中的賽事資料
selected_event = self.race_combo.currentData()
if selected_event:
    print(f"賽事: {selected_event.race_key}")
    print(f"日期: {selected_event.race_date}")
    print(f"已完賽: {selected_event.is_completed}")
    print(f"可用賽段: {selected_event.sessions}")
```

---

### 6.3 進階範例：Session ComboBox

```python
# 綁定簡稱（例如 "R", "Q"）
for session_key, full_name in sessions.items():
    display = f"{full_name} ({session_key})"
    self.session_combo.addItem(display, session_key)  # ⭐ session_key 是字串

# 獲取選中的賽段簡稱
selected_session = self.session_combo.currentData()  # 返回 "R" 或 "Q" 等
```

---

## 🎯 事件處理機制

### 7.1 標準事件

所有 ComboBox 支援以下 Qt 信號：

```python
# currentIndexChanged - 索引變更時觸發（包括程式設定）
combobox.currentIndexChanged.connect(self._on_selection_changed)

# activated - 僅使用者操作時觸發（不包括程式設定）
combobox.activated.connect(self._on_user_activated)

# currentTextChanged - 顯示文字變更時觸發
combobox.currentTextChanged.connect(self._on_text_changed)
```

---

### 7.2 阻止信號（避免連鎖觸發）

```python
# 場景：程式批次更新多個 ComboBox 時，避免每次變更都觸發事件

# ✅ 正確模式
self.race_combo.blockSignals(True)  # 暫時阻止信號
self.race_combo.clear()
for event in events:
    self.race_combo.addItem(event.display_label, event)
self.race_combo.setCurrentIndex(default_index)
self.race_combo.blockSignals(False)  # 恢復信號

# ❌ 錯誤模式（會觸發 N 次事件）
self.race_combo.clear()  # 觸發 1 次
for event in events:
    self.race_combo.addItem(...)  # 每次觸發
self.race_combo.setCurrentIndex(...)  # 再觸發 1 次
```

---

### 7.3 參數變更廣播

F1T GUI 使用**延遲廣播機制**，避免快速連續變更導致的重複處理：

```python
def _on_race_changed(self, index: int):
    """Race 變更時觸發"""
    # 不立即廣播，而是啟動延遲計時器
    self._schedule_parameter_broadcast()

def _schedule_parameter_broadcast(self):
    """安排參數廣播（350ms 延遲）"""
    # 如果已有排程，重新計時
    self._parameter_broadcast_timer.stop()
    self._parameter_broadcast_timer.start(350)  # 350ms 後執行

def _broadcast_pending_parameters(self):
    """實際執行參數廣播"""
    year = int(self.year_combo.currentText())
    race_event = self.race_combo.currentData()
    session = self.session_combo.currentData()
    driver = self.driver_combo.currentText()
    
    payload = {
        'year': year,
        'race': race_event.race_key if race_event else None,
        'session': session,
        'driver': driver
    }
    
    # 通知所有訂閱者（MDI 子視窗）
    for window in self.active_subwindows:
        if hasattr(window, 'on_parameters_changed'):
            window.on_parameters_changed(payload)
```

---

## 💡 開發最佳實踐

### 8.1 寬度設定準則

```python
# ✅ 使用 setFixedWidth() 確保佈局穩定
self.year_combo.setFixedWidth(80)       # 年份：4 位數字
self.driver_combo.setFixedWidth(100)    # 車手：3 字母代碼
self.session_combo.setFixedWidth(120)   # 賽段：全名 + 簡稱
self.race_combo.setFixedWidth(250)      # 賽事：名稱 + 日期

# ❌ 避免使用 setMinimumWidth()（會導致佈局跳動）
self.race_combo.setMinimumWidth(200)  # 不推薦
```

---

### 8.2 資料驗證

```python
# ✅ 獲取資料前先驗證
def _on_race_changed(self, index: int):
    item_data = self.race_combo.itemData(index)
    
    # 檢查是否為分隔線或空資料
    if item_data is None:
        logger.debug("忽略無效選項")
        return
    
    # 檢查資料類型
    if not isinstance(item_data, SeasonEvent):
        logger.error(f"資料類型錯誤: {type(item_data)}")
        return
    
    # 處理有效資料
    self._process_race_selection(item_data)

# ❌ 不驗證直接使用（可能導致 AttributeError）
def _on_race_changed_bad(self, index: int):
    item_data = self.race_combo.itemData(index)
    print(item_data.race_key)  # 如果是 None 會崩潰！
```

---

### 8.3 初始化順序

```python
# ✅ 正確順序：先填充資料，再連接事件
def setup_comboboxes(self):
    # 步驟 1: 創建 ComboBox
    self.race_combo = AnalysisComboBox()
    self.race_combo.setFixedWidth(250)
    
    # 步驟 2: 填充初始資料
    self._load_season_events(2025)
    
    # 步驟 3: 連接事件（避免初始化時觸發）
    self.race_combo.currentIndexChanged.connect(self._on_race_changed)

# ❌ 錯誤順序：先連接事件，再填充資料（會觸發不必要的事件）
def setup_comboboxes_bad(self):
    self.race_combo = AnalysisComboBox()
    self.race_combo.currentIndexChanged.connect(self._on_race_changed)  # 過早
    self._load_season_events(2025)  # 每次 addItem 都觸發事件
```

---

### 8.4 工具提示最佳實踐

```python
# ✅ 提供有意義的工具提示
self.race_combo.setToolTip(
    tr('race_selector_tooltip', 
       'Select race event. Completed races are shown first, '
       'followed by upcoming races.')
)

# ✅ 動態工具提示（顯示額外資訊）
def _update_race_tooltip(self, event: SeasonEvent):
    if event.is_completed:
        status = tr('completed', 'Completed')
    else:
        days_until = (event.race_date - datetime.now().date()).days
        status = tr('in_days', f'In {days_until} days')
    
    tooltip = f"{event.race_key}\n{event.race_date}\nStatus: {status}"
    self.race_combo.setToolTip(tooltip)
```

---

### 8.5 無障礙支援

```python
# ✅ 設定可訪問名稱和描述
self.race_combo.setAccessibleName(tr('race_selector_accessible', 'Race Selector'))
self.race_combo.setAccessibleDescription(
    tr('race_selector_description', 
       'Choose a Formula 1 race event from the current season')
)

# ✅ 鍵盤導航支援（AnalysisComboBox 已實現）
# - Tab: 切換焦點
# - Space/Enter: 展開下拉選單
# - 方向鍵: 選擇項目
# - Esc: 關閉下拉選單
```

---

## ❓ 常見問題解答

### Q1: 為什麼 Race ComboBox 需要 250px 寬度？

**A**: 最長的賽事名稱 + 日期格式需要此寬度：
```
"Great Britain (2025-07-06)" = 28 字元
250px ÷ 8pt 字型 ≈ 31 字元容量（含邊距）
```

如果使用更窄的寬度，文字會被截斷為 "Great Britain (2025-0..."

---

### Q2: 為什麼要禁用滑鼠滾輪？

**A**: 防止使用者在滾動頁面時無意間改變下拉選單的值：

```python
# 場景：使用者想滾動 MDI 工作區
# 滑鼠游標意外停留在工具列的 Race ComboBox 上
# 滾動滾輪 → Race 從 "Japan" 變成 "China"
# 所有分析視窗重新載入錯誤的資料！

# 解決方案：禁用滾輪事件
def wheelEvent(self, event):
    event.ignore()  # 將事件傳遞給父元件
```

---

### Q3: currentIndexChanged 和 activated 有什麼區別？

**A**: 
- **currentIndexChanged**: 任何索引變更都觸發（包括程式設定）
- **activated**: 僅使用者操作（滑鼠點擊、鍵盤選擇）觸發

```python
# 範例
self.race_combo.currentIndexChanged.connect(self._handler1)  # 程式+使用者
self.race_combo.activated.connect(self._handler2)            # 僅使用者

self.race_combo.setCurrentIndex(5)  # ✅ 觸發 _handler1，❌ 不觸發 _handler2
# 使用者點擊選擇                      # ✅ 觸發 _handler1，✅ 觸發 _handler2
```

---

### Q4: 如何實現分隔線（不可選擇的項目）？

**A**: 使用 `QStandardItemModel` 禁用特定項目：

```python
# 方法 1: 使用 model().item() 禁用（推薦）
separator_text = "─" * 30
self.race_combo.addItem(separator_text, None)
separator_index = self.race_combo.count() - 1
self.race_combo.model().item(separator_index).setEnabled(False)

# 方法 2: 在事件處理中忽略 None 資料
def _on_race_changed(self, index: int):
    if self.race_combo.itemData(index) is None:
        return  # 忽略分隔線
```

---

### Q5: 如何處理載入失敗的情況？

**A**: 提供友善的錯誤訊息並禁用 ComboBox：

```python
def _load_drivers_for_year(self, year: int):
    drivers = self.get_drivers_for_year(year)
    
    self.driver_combo.blockSignals(True)
    self.driver_combo.clear()
    
    if not drivers:
        # 載入失敗處理
        error_msg = tr('load_drivers_failed', 
                      f'Unable to load drivers for {year}')
        self.driver_combo.addItem(f"❌ {error_msg}", None)
        self.driver_combo.setEnabled(False)  # 禁用防止誤操作
        self.driver_combo.setStyleSheet("color: #CC0000;")  # 紅色文字
        
        logger.error(f"[DRIVER_COMBO] 載入失敗: {year}")
    else:
        # 正常載入
        self.driver_combo.addItems(drivers)
        self.driver_combo.setEnabled(True)
        self.driver_combo.setStyleSheet("")  # 恢復預設樣式
    
    self.driver_combo.blockSignals(False)
```

---

### Q6: 如何實現多語言支援？

**A**: 使用 `tr()` 翻譯函數：

```python
from core.gui_i18n import tr

# 所有顯示文字使用 tr() 包裹
self.session_combo.addItem(
    tr('session_race', 'Race'),      # 英文: Race, 中文: 正賽
    'R'
)

self.session_combo.addItem(
    tr('session_qualifying', 'Qualifying'),  # 英文: Qualifying, 中文: 排位賽
    'Q'
)

# 動態生成的文字也要翻譯
upcoming_suffix = tr('upcoming_race', '未開賽')
display = f"{race_key} ({race_date}) [{upcoming_suffix}]"
```

---

### Q7: ComboBox 在 MDI 子視窗中如何同步主視窗參數？

**A**: 使用參數廣播機制：

```python
# 主視窗：廣播參數變更
def _broadcast_pending_parameters(self):
    payload = {
        'year': int(self.year_combo.currentText()),
        'race': self.race_combo.currentData().race_key,
        'session': self.session_combo.currentData()
    }
    
    for window in self.active_subwindows:
        if hasattr(window, 'on_parameters_changed'):
            window.on_parameters_changed(payload)

# MDI 子視窗：接收參數
class LapAnalysisWindow(QWidget):
    def on_parameters_changed(self, params: dict):
        """接收主視窗參數變更"""
        self.current_year = params['year']
        self.current_race = params['race']
        self.current_session = params['session']
        
        # 重新載入資料
        self.reload_analysis()
```

---

## 📚 參考資源

### 內部文件
- `f1t_gui_main.py` (lines 8777-9300) - 工具列 ComboBox 初始化
- `f1t_gui_main.py` (lines 1624-1750) - QSS 樣式定義
- `season_calendar_provider.py` - Race ComboBox 資料提供者
- `core/gui_i18n.py` - 翻譯系統

### 外部參考
- [Qt ComboBox 官方文件](https://doc.qt.io/qt-5/qcombobox.html)
- [QSS ComboBox 樣式參考](https://doc.qt.io/qt-5/stylesheet-examples.html#customizing-qcombobox)
- [Material Design - Selection Controls](https://material.io/components/menus)

---

## 🔄 版本歷史

| 版本 | 日期 | 變更內容 |
|------|------|----------|
| **V1.0** | 2025-12-11 | 初始版本，完整記錄 4 種 ComboBox 設計規格 |

---

**文件維護者**: Telemetry Station 核心團隊  
**審核狀態**: ✅ 已審核  
**適用版本**: F1T GUI V0.11.0+
