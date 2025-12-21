#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RaceFans.net 技術更新爬蟲
抓取 F1 車隊升級資訊
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

class RaceFansTechScraper:
    """
    RaceFans 技術更新爬蟲
    """
    
    def __init__(self):
        self.base_url = "https://www.racefans.net"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def get_tech_update_articles(self, year=2025, limit=30):
        """
        使用搜索功能獲取技術更新文章列表
        
        參數:
            year: 賽季年份
            limit: 最大文章數量
        
        返回:
            文章列表 [{'title': str, 'url': str, 'date': str}]
        """
        print(f"\n🔍 搜索 {year} 年的技術更新文章...")
        
        # 搜索關鍵詞組合
        search_queries = [
            f"technical updates {year}",
            f"car upgrades {year}",
            f"development {year}"
        ]
        
        all_articles = []
        seen_urls = set()
        
        for query in search_queries:
            if len(all_articles) >= limit:
                break
            
            # 構建搜索 URL
            search_url = f"{self.base_url}/?s={query.replace(' ', '+')}"
            
            try:
                print(f"  🔎 搜索: {query}")
                response = self.session.get(search_url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 查找文章元素
                # RaceFans 使用多種格式，嘗試不同選擇器
                article_containers = soup.find_all(['article', 'div'], class_=lambda x: x and any(
                    cls in str(x).lower() for cls in ['post', 'entry', 'article', 'item']
                ))
                
                for container in article_containers:
                    if len(all_articles) >= limit:
                        break
                    
                    # 尋找標題和連結
                    title_elem = container.find(['h1', 'h2', 'h3', 'h4'], class_=lambda x: x and any(
                        cls in str(x).lower() for cls in ['title', 'heading', 'entry']
                    ))
                    
                    if not title_elem:
                        # 備用方法：查找任何帶連結的標題
                        title_elem = container.find(['h1', 'h2', 'h3'])
                    
                    if not title_elem:
                        continue
                    
                    # 提取連結
                    link_elem = title_elem.find('a', href=True)
                    if not link_elem:
                        link_elem = container.find('a', href=True)
                    
                    if not link_elem:
                        continue
                    
                    article_url = link_elem.get('href', '')
                    title = title_elem.get_text(strip=True)
                    
                    # 確保是完整 URL
                    if article_url.startswith('/'):
                        article_url = self.base_url + article_url
                    
                    # 驗證是否為技術更新相關文章
                    tech_keywords = ['technical', 'update', 'upgrade', 'develop', 'car changes', 'new parts']
                    if not any(keyword in title.lower() for keyword in tech_keywords):
                        continue
                    
                    # 驗證年份（從 URL 或標題）
                    if str(year) not in article_url and str(year) not in title:
                        # 嘗試從日期元素驗證
                        date_elem = container.find('time')
                        if date_elem:
                            date_str = date_elem.get('datetime', '')
                            if str(year) not in date_str:
                                continue
                        else:
                            continue
                    
                    # 避免重複
                    if article_url in seen_urls:
                        continue
                    
                    seen_urls.add(article_url)
                    
                    # 提取日期
                    date = None
                    date_elem = container.find('time')
                    if date_elem:
                        date = date_elem.get('datetime')
                    
                    all_articles.append({
                        'title': title,
                        'url': article_url,
                        'date': date
                    })
                    
                    print(f"    ✓ {title}")
                
            except Exception as e:
                print(f"    ⚠️ 搜索 '{query}' 時發生錯誤: {e}")
                continue
        
        print(f"\n📊 總計找到 {len(all_articles)} 篇文章")
        return all_articles[:limit]
    
    def parse_tech_update_article(self, article_url):
        """
        解析單篇技術更新文章，提取升級表格
        
        RaceFans 表格格式:
        - 行表頭：賽事名稱 (Austrian GP, Mexican GP...)
        - 列表頭：車隊名稱 (McLaren, Red Bull, Ferrari, Mercedes...)
        - 儲存格：升級部件（可能多個擠在一起）
        
        參數:
            article_url: 文章 URL
        
        返回:
            {
                'race': str,
                'upgrades': [{'team': str, 'race': str, 'component': str}]
            }
        """
        print(f"\n📄 解析文章: {article_url}")
        
        try:
            response = self.session.get(article_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取標題
            title_elem = soup.find(['h1', 'h2'], class_=lambda x: x and 'title' in str(x).lower())
            if not title_elem:
                title_elem = soup.find('h1')
            
            title = title_elem.get_text(strip=True) if title_elem else "Unknown"
            
            # 從標題提取主要賽事名稱（文章發布時的賽事）
            main_race = self._extract_race_from_title(title)
            
            print(f"  標題: {title}")
            print(f"  主要賽事: {main_race}")
            
            # 尋找表格
            tables = soup.find_all('table')
            
            all_upgrades = []
            
            for table in tables:
                rows = table.find_all('tr')
                if not rows:
                    continue
                
                # 提取表頭（第一行 = 車隊名稱）
                header_row = rows[0]
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
                
                # 第一欄通常是 "Event"，其餘是車隊名稱
                if not headers:
                    continue
                
                team_names = headers[1:]  # 跳過第一欄（Event）
                
                # 解析數據行（每行 = 一場賽事）
                for row in rows[1:]:
                    cells = row.find_all(['td', 'th'])
                    
                    if len(cells) < 2:
                        continue
                    
                    # 第一欄 = 賽事名稱
                    race_name = cells[0].get_text(strip=True)
                    
                    # 其餘欄位 = 各車隊的升級
                    for i, team_name in enumerate(team_names):
                        cell_index = i + 1
                        
                        if cell_index >= len(cells):
                            continue
                        
                        # 提取升級部件文字
                        upgrades_text = cells[cell_index].get_text(strip=True)
                        
                        # 跳過空白儲存格
                        if not upgrades_text:
                            continue
                        
                        # 嘗試分割多個升級部件
                        # RaceFans 沒有明確分隔符，使用大寫字母啟動的單詞作為分界
                        components = re.findall(r'[A-Z][a-z\s]*(?=[A-Z]|$)', upgrades_text)
                        
                        # 如果正則分割失敗，直接使用完整文字
                        if not components:
                            components = [upgrades_text]
                        
                        # 建立每個升級記錄
                        for component in components:
                            component = component.strip()
                            if component:
                                all_upgrades.append({
                                    'team': team_name,
                                    'race': race_name,
                                    'component': component
                                })
            
            print(f"  ✓ 找到 {len(all_upgrades)} 個升級項目")
            
            return {
                'race': main_race,
                'title': title,
                'url': article_url,
                'upgrades': all_upgrades
            }
            
        except Exception as e:
            print(f"  ❌ 解析文章時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return {
                'race': 'Unknown',
                'title': '',
                'url': article_url,
                'upgrades': []
            }
    
    def _extract_race_from_title(self, title):
        """
        從標題提取賽事名稱
        
        參數:
            title: 文章標題
        
        返回:
            賽事名稱字串
        """
        # 常見賽事名稱模式
        race_patterns = [
            r'(Bahrain|Saudi Arabia|Australian|Miami|Emilia Romagna|Monaco|Spanish|Canadian|Austrian|British|Hungarian|Belgian|Dutch|Italian|Azerbaijan|Singapore|Japanese|Qatar|United States|Mexico|Brazilian|Abu Dhabi)\s+(Grand Prix|GP)',
            r'(Bahrain|Saudi|Australia|Miami|Imola|Monaco|Spain|Canada|Austria|Britain|Hungary|Belgium|Netherlands|Italy|Baku|Singapore|Japan|Qatar|USA|Austin|Mexico|Brazil|Abu Dhabi)'
        ]
        
        for pattern in race_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return "Unknown Race"
    
    def get_team_upgrades(self, team_name, year=2025):
        """
        獲取特定車隊在特定年份的所有升級
        
        參數:
            team_name: 車隊名稱 (例如: "Red Bull", "Ferrari")
            year: 賽季年份
        
        返回:
            {
                'team': str,
                'year': int,
                'total_upgrades': int,
                'races': [
                    {
                        'race': str,
                        'date': str,
                        'upgrades': [...]
                    }
                ]
            }
        """
        print(f"\n🎯 查詢 {team_name} 在 {year} 年的升級資訊...")
        
        # 獲取所有技術更新文章
        articles = self.get_tech_update_articles(year=year)
        
        if not articles:
            print(f"⚠️ 未找到 {year} 年的技術更新文章")
            return {
                'team': team_name,
                'year': year,
                'total_upgrades': 0,
                'races': []
            }
        
        # 解析每篇文章
        all_race_data = []
        total_upgrades = 0
        
        for article in articles:
            article_data = self.parse_tech_update_article(article['url'])
            
            # 過濾該車隊的升級
            team_upgrades = [
                upgrade for upgrade in article_data['upgrades']
                if team_name.lower() in upgrade['team'].lower()
            ]
            
            if team_upgrades:
                all_race_data.append({
                    'race': article_data['race'],
                    'date': article.get('date'),
                    'title': article_data['title'],
                    'upgrades': team_upgrades
                })
                total_upgrades += len(team_upgrades)
                
                print(f"  ✓ {article_data['race']}: {len(team_upgrades)} 個升級")
        
        result = {
            'team': team_name,
            'year': year,
            'total_upgrades': total_upgrades,
            'races': all_race_data
        }
        
        return result
    
    def export_to_json(self, data, filename):
        """
        導出數據到 JSON 檔案
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 數據已保存至: {filename}")


def main():
    """
    主函數：示範使用爬蟲
    """
    scraper = RaceFansTechScraper()
    
    # 示範：查詢 Red Bull 2025 年的升級
    print("=" * 60)
    print("🏎️ F1 技術更新爬蟲 - RaceFans.net")
    print("=" * 60)
    
    team = "Red Bull"
    year = 2025
    
    # 獲取升級數據
    upgrades_data = scraper.get_team_upgrades(team, year)
    
    # 顯示結果
    print("\n" + "=" * 60)
    print(f"📊 {team} {year} 賽季升級統計")
    print("=" * 60)
    print(f"總升級套件數: {upgrades_data['total_upgrades']}")
    print(f"升級場次數: {len(upgrades_data['races'])}")
    print("\n📋 詳細列表:")
    
    # 按賽事分組統計
    race_stats = {}
    for race_data in upgrades_data['races']:
        article_title = race_data['title']
        
        # 按實際賽事名稱分組
        for upgrade in race_data['upgrades']:
            race_name = upgrade['race']
            
            if race_name not in race_stats:
                race_stats[race_name] = {
                    'count': 0,
                    'components': []
                }
            
            race_stats[race_name]['count'] += 1
            race_stats[race_name]['components'].append({
                'component': upgrade['component'],
                'source': article_title
            })
    
    # 顯示按賽事分組的結果
    for race_name, stats in race_stats.items():
        print(f"\n  🏁 {race_name}")
        print(f"     升級數: {stats['count']}")
        print(f"     升級套件:")
        
        for i, item in enumerate(stats['components'], 1):
            print(f"       {i}. {item['component']}")
            if i == 1:  # 只在第一個顯示來源
                print(f"          (數據來源: {item['source'][:60]}...)")
    
    # 導出 JSON
    output_file = f"{team.replace(' ', '_')}_{year}_upgrades.json"
    scraper.export_to_json(upgrades_data, output_file)
    
    print("\n" + "=" * 60)
    print("✅ 爬取完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
