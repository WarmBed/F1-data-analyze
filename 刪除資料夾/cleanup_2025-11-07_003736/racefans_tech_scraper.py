"""
RaceFans 技術更新爬蟲 - 測試版
抓取 F1 車隊升級套件資訊
"""
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re

class RaceFansTechScraper:
    def __init__(self):
        self.base_url = "https://www.racefans.net"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def get_tech_update_articles(self, year=2024, limit=30):
        """
        獲取技術更新文章列表
        """
        print(f"\n🔍 搜索 {year} 年的技術更新文章...")
        
        # 使用搜索功能查找技術更新
        search_terms = [
            f"technical updates {year}",
            f"upgrade {year}",
            f"car updates {year}"
        ]
        
        all_articles = []
        
        for term in search_terms:
            url = f"{self.base_url}/?s={term.replace(' ', '+')}"
            
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尋找文章列表
            articles = []
            
            # RaceFans 使用 article 標籤
            article_elements = soup.find_all('article', limit=limit)
            
            print(f"✅ 找到 {len(article_elements)} 篇文章")
            
            for article in article_elements:
                # 標題和連結
                title_elem = article.find('h2') or article.find('h3')
                if not title_elem:
                    continue
                
                link_elem = title_elem.find('a')
                if not link_elem:
                    continue
                
                title = link_elem.get_text().strip()
                article_url = link_elem.get('href')
                
                # 確保是完整 URL
                if not article_url.startswith('http'):
                    article_url = self.base_url + article_url
                
                # 日期
                date_elem = article.find('time')
                date = date_elem.get('datetime') if date_elem else None
                
                # 過濾年份
                if date and str(year) not in date:
                    continue
                
                # 過濾技術更新相關
                if 'tech' in title.lower() or 'update' in title.lower() or 'upgrade' in title.lower():
                    articles.append({
                        'title': title,
                        'url': article_url,
                        'date': date
                    })
            
            return articles
            
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            return []
    
    def parse_tech_update_article(self, article_url):
        """
        解析單篇技術更新文章，提取升級表格
        """
        print(f"\n📄 解析文章: {article_url}")
        
        try:
            response = self.session.get(article_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取文章標題
            title_elem = soup.find('h1', class_=re.compile(r'entry-title|article-title|post-title'))
            title = title_elem.get_text().strip() if title_elem else "Unknown"
            
            # 從標題提取賽事名稱
            race = self._extract_race_from_title(title)
            
            print(f"   標題: {title}")
            print(f"   賽事: {race}")
            
            # 尋找表格（升級資訊通常在表格中）
            tables = soup.find_all('table')
            
            upgrades = []
            
            for table in tables:
                # 解析表格
                rows = table.find_all('tr')
                
                headers = []
                header_row = rows[0] if rows else None
                
                if header_row:
                    headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]
                
                # 跳過標題行
                for row in rows[1:]:
                    cells = row.find_all(['td', 'th'])
                    
                    if len(cells) >= 2:
                        # 假設格式: Team | Component | Description
                        team = cells[0].get_text().strip()
                        
                        # 跳過空行或標題
                        if not team or team.lower() in ['team', 'constructor']:
                            continue
                        
                        component = cells[1].get_text().strip() if len(cells) > 1 else ""
                        description = cells[2].get_text().strip() if len(cells) > 2 else ""
                        
                        upgrades.append({
                            'team': team,
                            'component': component,
                            'description': description,
                            'race': race
                        })
            
            print(f"   ✅ 找到 {len(upgrades)} 個升級項目")
            
            return {
                'title': title,
                'race': race,
                'url': article_url,
                'upgrades': upgrades
            }
            
        except Exception as e:
            print(f"   ❌ 解析失敗: {e}")
            return None
    
    def _extract_race_from_title(self, title):
        """從標題提取賽事名稱"""
        # 常見賽事名稱
        races = [
            'Bahrain', 'Saudi Arabia', 'Australian', 'Japan', 'Chinese', 
            'Miami', 'Emilia Romagna', 'Monaco', 'Spanish', 'Canadian',
            'Austrian', 'British', 'Hungarian', 'Belgian', 'Dutch',
            'Italian', 'Singapore', 'United States', 'Mexican', 'Brazilian',
            'Las Vegas', 'Qatar', 'Abu Dhabi'
        ]
        
        for race in races:
            if race.lower() in title.lower():
                return race
        
        return "Unknown"
    
    def get_team_upgrades(self, year=2024, team_name="Red Bull"):
        """
        獲取特定車隊的所有升級
        """
        print(f"\n🏎️  查詢 {team_name} {year} 年的升級套件...")
        print("="*70)
        
        # 獲取文章列表
        articles = self.get_tech_update_articles(year=year, limit=30)
        
        all_upgrades = []
        
        # 解析每篇文章
        for i, article in enumerate(articles, 1):
            print(f"\n[{i}/{len(articles)}] 處理: {article['title']}")
            
            result = self.parse_tech_update_article(article['url'])
            
            if result and result['upgrades']:
                # 過濾特定車隊
                team_upgrades = [
                    upgrade for upgrade in result['upgrades']
                    if team_name.lower() in upgrade['team'].lower()
                ]
                
                if team_upgrades:
                    all_upgrades.extend([{
                        **upgrade,
                        'date': article['date'],
                        'article_title': article['title'],
                        'article_url': article['url']
                    } for upgrade in team_upgrades])
                    
                    print(f"   🎯 找到 {len(team_upgrades)} 個 {team_name} 升級")
        
        return all_upgrades

# 執行測試
if __name__ == "__main__":
    scraper = RaceFansTechScraper()
    
    # 測試：獲取 Red Bull 2024 年的升級
    print("\n" + "="*70)
    print("🏁 RaceFans 技術更新爬蟲 - 測試運行")
    print("="*70)
    
    # 先測試 2024（確定有數據）
    upgrades_2024 = scraper.get_team_upgrades(year=2024, team_name="Red Bull")
    
    print("\n" + "="*70)
    print(f"📊 統計結果 - Red Bull 2024 賽季")
    print("="*70)
    
    if upgrades_2024:
        # 按賽事分組
        races = {}
        for upgrade in upgrades_2024:
            race = upgrade['race']
            if race not in races:
                races[race] = []
            races[race].append(upgrade)
        
        print(f"\n總計: {len(upgrades_2024)} 個升級套件，涉及 {len(races)} 場比賽\n")
        
        for race, items in races.items():
            print(f"🏁 {race} Grand Prix:")
            print(f"   升級數量: {len(items)}")
            for item in items:
                print(f"   • {item['component']}: {item['description'][:60]}...")
            print()
        
        # 保存到 JSON
        output_file = 'red_bull_2024_upgrades.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(upgrades_2024, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 數據已保存到: {output_file}")
    else:
        print("\n⚠️  未找到 Red Bull 2024 的升級數據")
        print("這可能是因為:")
        print("  1. RaceFans 網站結構改變")
        print("  2. 2024 數據尚未完整")
        print("  3. 需要調整解析邏輯")
    
    # 測試 2025（可能還沒有數據）
    print("\n" + "="*70)
    print("測試 2025 賽季（可能尚無數據）...")
    print("="*70)
    
    upgrades_2025 = scraper.get_team_upgrades(year=2025, team_name="Red Bull")
    
    if upgrades_2025:
        print(f"\n✅ 找到 {len(upgrades_2025)} 個 Red Bull 2025 升級")
    else:
        print("\n⚠️  2025 賽季數據尚未發布或尚未開始")
