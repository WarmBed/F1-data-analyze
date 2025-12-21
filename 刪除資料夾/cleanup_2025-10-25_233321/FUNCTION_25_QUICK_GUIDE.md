# 🏁 功能 25 快速使用指南

## 📋 基本資訊

- **功能 ID**: 25
- **功能名稱**: 車手比賽位置分析
- **模組路徑**: `CLI_modules/cli/analyzer/single_driver_position_analysis.py`

---

## 🚀 使用方式

### 1. 單一車手分析

```powershell
python f1_analysis_modular_main.py -f 25 -y 2024 -r Japan -s R -d LEC
```

**輸出**: `cache/position_analysis_2024_Japan_R_LEC.json`

### 2. 全車手分析

```powershell
python f1_analysis_modular_main.py -f 25 -y 2024 -r Japan -s R
```

**輸出**: `cache/position_analysis_2024_Japan_R_all_drivers.json`

---

## 📊 數據結構

### 單一車手模式

```json
{
  "success": true,
  "driver": "LEC",
  "analysis_mode": "single",
  "position_analysis": {
    "starting_position": 8,
    "finishing_position": 4,
    "best_position": 1,
    "worst_position": 8,
    "total_laps": 53,
    "position_changes": {
      "lap_by_lap_changes": [...],
      "total_changes": 13,
      "positions_gained": 11.0,
      "positions_lost": 7.0
    },
    "position_statistics": {
      "average_position": 4.25,
      "median_position": 4.0,
      "time_in_top_5": 37,
      "time_in_top_10": 53
    }
  }
}
```

### 全車手模式

```json
{
  "success": true,
  "drivers_analyzed": ["VER", "PER", "SAI", ...],
  "analysis_mode": "all",
  "all_drivers_position_analysis": {
    "VER": { /* 與單一車手結構相同 */ },
    "LEC": { /* 與單一車手結構相同 */ },
    ...
  }
}
```

---

## 🔧 Python 代碼範例

```python
import json

# 讀取單一車手分析
with open('cache/position_analysis_2024_Japan_R_LEC.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"車手: {data['driver']}")
print(f"起始: P{data['position_analysis']['starting_position']}")
print(f"完賽: P{data['position_analysis']['finishing_position']}")

# 讀取全車手分析
with open('cache/position_analysis_2024_Japan_R_all_drivers.json', 'r', encoding='utf-8') as f:
    all_data = json.load(f)

# 計算名次變化排行
changes = []
for driver, driver_data in all_data['all_drivers_position_analysis'].items():
    start = driver_data.get('starting_position')
    finish = driver_data.get('finishing_position')
    if start and finish:
        changes.append({
            'driver': driver,
            'change': start - finish
        })

changes.sort(key=lambda x: x['change'], reverse=True)
print("\n名次變化 Top 5:")
for i, item in enumerate(changes[:5], 1):
    print(f"{i}. {item['driver']}: {item['change']:+d}")
```

---

## 🎯 常用查詢

### 找出最大進步車手

```python
max_gainer = max(changes, key=lambda x: x['change'])
print(f"最大進步: {max_gainer['driver']} (+{max_gainer['change']})")
```

### 找出最穩定車手

```python
stability = {}
for driver, data in all_data['all_drivers_position_analysis'].items():
    stats = data.get('position_statistics', {})
    if 'position_variance' in stats:
        stability[driver] = stats['position_variance']

most_stable = min(stability.items(), key=lambda x: x[1])
print(f"最穩定: {most_stable[0]} (變異數: {most_stable[1]:.2f})")
```

### 統計前 5 圈數

```python
for driver, data in all_data['all_drivers_position_analysis'].items():
    stats = data.get('position_statistics', {})
    top5_laps = stats.get('time_in_top_5', 0)
    total_laps = data.get('total_laps', 0)
    if total_laps > 0:
        percentage = (top5_laps / total_laps) * 100
        print(f"{driver}: {top5_laps}/{total_laps} ({percentage:.1f}%)")
```

---

## 📈 視覺化範例

```python
import matplotlib.pyplot as plt

# 繪製名次變化
fig, ax = plt.subplots(figsize=(10, 6))

drivers = ['VER', 'LEC', 'SAI']
for driver in drivers:
    data = all_data['all_drivers_position_analysis'][driver]
    changes = data['position_changes']['lap_by_lap_changes']
    
    laps = [c['lap'] for c in changes]
    positions = [c['to_position'] for c in changes]
    
    ax.plot(laps, positions, marker='o', label=driver)

ax.set_xlabel('圈數')
ax.set_ylabel('位置')
ax.set_title('名次變化軌跡')
ax.invert_yaxis()
ax.legend()
ax.grid(True, alpha=0.3)
plt.show()
```

---

## ✅ 檢查清單

- [ ] 確認 FastF1 緩存已啟用
- [ ] 檢查賽事名稱拼寫 (Japan, Italy, Monaco...)
- [ ] 確認會話類型 (R, Q, FP1...)
- [ ] 查看輸出 JSON 檔案
- [ ] 驗證數據完整性

---

## 🐛 常見問題

### Q: 找不到車手數據？
A: 檢查車手代碼拼寫 (VER, LEC, HAM...)

### Q: 分析失敗？
A: 確認 FastF1 緩存目錄存在且有權限

### Q: JSON 檔案過大？
A: 正常現象，全車手模式約 140KB

### Q: 警告訊息？
A: FastF1 棄用警告可忽略，不影響功能

---

**快速測試**:
```powershell
python f1_analysis_modular_main.py -f 25 -y 2024 -r Japan -s R -d LEC
```
