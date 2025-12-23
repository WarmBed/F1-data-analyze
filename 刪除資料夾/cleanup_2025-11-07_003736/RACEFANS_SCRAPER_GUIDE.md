# RaceFans.net F1 升級追蹤爬蟲 - 使用指南

## 🎯 功能說明

這個爬蟲工具能夠從 RaceFans.net 自動抓取 F1 車隊的技術升級資訊，支援：

✅ 搜索特定賽季的技術更新文章  
✅ 解析升級表格（車隊、賽事、升級部件）  
✅ 過濾特定車隊的升級記錄  
✅ 導出 JSON 格式數據  
✅ 生成統計報告

---

## 📋 系統需求

```bash
python >= 3.7
requests >= 2.28.0
beautifulsoup4 >= 4.11.0
```

安裝依賴：
```powershell
pip install requests beautifulsoup4
```

---

## 🚀 快速開始

### 方法 1: 直接執行預設查詢（Red Bull 2025）

```powershell
python racefans_tech_scraper_v2.py
```

**輸出**:
- 終端顯示統計摘要
- 生成 `Red_Bull_2025_upgrades.json`

### 方法 2: 自訂查詢

```python
from racefans_tech_scraper_v2 import RaceFansTechScraper

# 初始化爬蟲
scraper = RaceFansTechScraper()

# 查詢特定車隊和賽季
team_data = scraper.get_team_upgrades("Ferrari", 2024)

# 導出數據
scraper.export_to_json(team_data, "Ferrari_2024_upgrades.json")
```

---

## 📊 輸出格式

### JSON 結構

```json
{
  "team": "Red Bull",
  "year": 2025,
  "total_upgrades": 64,
  "races": [
    {
      "race": "Unknown Race",
      "date": "2025-10-22T10:03:31+01:00",
      "title": "Red Bull again hint Verstappen will get...",
      "upgrades": [
        {
          "team": "Red Bull",
          "race": "Austrian Grand Prix",
          "component": "Floor edge"
        },
        {
          "team": "Red Bull",
          "race": "British Grand Prix",
          "component": "Front wing"
        }
      ]
    }
  ]
}
```

---

## 🔧 核心方法說明

### 1. `get_tech_update_articles(year, limit)`

搜索技術更新文章。

**參數**:
- `year` (int): 賽季年份（例如 2024, 2025）
- `limit` (int): 最大文章數量（預設 30）

**返回**: 文章列表 `[{'title': str, 'url': str, 'date': str}]`

**範例**:
```python
articles = scraper.get_tech_update_articles(2025, limit=50)
print(f"找到 {len(articles)} 篇文章")
```

---

### 2. `parse_tech_update_article(article_url)`

解析單篇文章的升級表格。

**參數**:
- `article_url` (str): 文章完整 URL

**返回**:
```python
{
    'race': str,           # 主要賽事名稱
    'title': str,          # 文章標題
    'url': str,            # 文章 URL
    'upgrades': [          # 升級列表
        {
            'team': str,       # 車隊名稱
            'race': str,       # 賽事名稱
            'component': str   # 升級部件
        }
    ]
}
```

**範例**:
```python
url = "https://www.racefans.net/2025/10/24/verstappen-to-benefit..."
data = scraper.parse_tech_update_article(url)
print(f"找到 {len(data['upgrades'])} 個升級")
```

---

### 3. `get_team_upgrades(team_name, year)`

獲取特定車隊在特定賽季的所有升級。

**參數**:
- `team_name` (str): 車隊名稱（支援部分匹配）
  - 有效範例: "Red Bull", "Ferrari", "McLaren", "Mercedes", "Aston Martin"
- `year` (int): 賽季年份

**返回**:
```python
{
    'team': str,
    'year': int,
    'total_upgrades': int,
    'races': [...]
}
```

**範例**:
```python
# 查詢 Ferrari 2024 升級
ferrari_data = scraper.get_team_upgrades("Ferrari", 2024)

# 查詢 McLaren 2025 升級
mclaren_data = scraper.get_team_upgrades("McLaren", 2025)
```

---

### 4. `export_to_json(data, filename)`

導出數據到 JSON 檔案。

**參數**:
- `data` (dict): 要導出的數據
- `filename` (str): 檔案名稱

**範例**:
```python
scraper.export_to_json(team_data, "my_upgrades.json")
```

---

## 📝 使用範例

### 範例 1: 比較多車隊

```python
from racefans_tech_scraper_v2 import RaceFansTechScraper

scraper = RaceFansTechScraper()
teams = ["Red Bull", "Ferrari", "McLaren", "Mercedes"]
year = 2025

for team in teams:
    data = scraper.get_team_upgrades(team, year)
    print(f"\n{team}: {data['total_upgrades']} 個升級")
    
    # 導出各車隊數據
    filename = f"{team.replace(' ', '_')}_{year}_upgrades.json"
    scraper.export_to_json(data, filename)
```

---

### 範例 2: 獲取特定賽事的升級

```python
from racefans_tech_scraper_v2 import RaceFansTechScraper

scraper = RaceFansTechScraper()
team_data = scraper.get_team_upgrades("Red Bull", 2025)

# 過濾墨西哥大獎賽的升級
for race_data in team_data['races']:
    for upgrade in race_data['upgrades']:
        if "Mexican" in upgrade['race']:
            print(f"{upgrade['race']}: {upgrade['component']}")
```

**輸出**:
```
Mexican Grand Prix: Front brake ducts
Mexican Grand Prix: Engine cover
Mexican Grand Prix: Floor body
Mexican Grand Prix: Floor edge wing
```

---

### 範例 3: 統計升級部件類型

```python
from collections import Counter
from racefans_tech_scraper_v2 import RaceFansTechScraper

scraper = RaceFansTechScraper()
team_data = scraper.get_team_upgrades("Red Bull", 2025)

# 收集所有部件
components = []
for race_data in team_data['races']:
    for upgrade in race_data['upgrades']:
        components.append(upgrade['component'])

# 統計頻率
component_counts = Counter(components)

print("\n升級部件頻率排名:")
for component, count in component_counts.most_common(10):
    print(f"  {component}: {count} 次")
```

---

## ⚙️ 配置選項

### 修改搜索關鍵詞

在 `get_tech_update_articles()` 方法中修改 `search_queries`:

```python
search_queries = [
    f"technical updates {year}",
    f"car upgrades {year}",
    f"development {year}",
    f"new parts {year}",  # 新增
    f"aero update {year}"  # 新增
]
```

### 修改 User-Agent

在 `__init__()` 方法中修改:

```python
self.session.headers.update({
    'User-Agent': '你的自訂 User-Agent'
})
```

---

## 🐛 常見問題

### Q1: 找不到數據怎麼辦？

**原因**: RaceFans 可能還沒發布該賽季的升級追蹤文章。

**解決方法**: 
- 檢查 RaceFans.net 是否有相關文章
- 嘗試搜索前一個賽季（例如 2024）
- 增加 `limit` 參數以搜索更多文章

---

### Q2: 升級數量重複怎麼辦？

**原因**: RaceFans 在多篇文章中嵌入相同的累積升級表格。

**解決方法**: 
對 `upgrades` 去重：

```python
seen = set()
unique_upgrades = []

for race_data in team_data['races']:
    for upgrade in race_data['upgrades']:
        key = (upgrade['race'], upgrade['component'])
        if key not in seen:
            seen.add(key)
            unique_upgrades.append(upgrade)
```

---

### Q3: 特定車隊名稱找不到？

**原因**: 車隊名稱部分匹配可能失敗。

**解決方法**: 
使用完整或官方名稱：
- ✅ "Red Bull"（正確）
- ❌ "RB"（可能失敗）
- ✅ "Aston Martin"（正確）
- ❌ "AM"（可能失敗）

---

## 📜 授權與免責聲明

- 本工具僅供教育和個人研究使用
- 數據來源為 RaceFans.net，版權歸原作者所有
- 請遵守 RaceFans.net 的服務條款和 robots.txt
- 建議在爬取時加入適當的延遲，避免過度請求

---

## 🔗 相關資源

- **RaceFans.net**: https://www.racefans.net
- **FastF1 API**: https://github.com/theOehrly/Fast-F1
- **OpenF1 API**: https://openf1.org

---

**版本**: 2.0  
**最後更新**: 2025-01-XX  
**作者**: F1 Data Analyze Project
