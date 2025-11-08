"""測試 RaceFans 網站結構"""
import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# 測試不同的 URL
urls_to_test = [
    "https://www.racefans.net",
    "https://www.racefans.net/category/f1-news/",
    "https://www.racefans.net/f1-news/",
    "https://racefans.net",
]

print("🔍 測試 RaceFans URL...\n")

for url in urls_to_test:
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"✅ {url}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('title')
            print(f"   Title: {title.get_text() if title else 'N/A'}")
            
            # 檢查是否有技術相關連結
            tech_links = soup.find_all('a', href=True, string=lambda s: s and 'tech' in s.lower())
            if tech_links:
                print(f"   找到 {len(tech_links)} 個技術相關連結")
                for link in tech_links[:3]:
                    print(f"     • {link.get_text()}: {link.get('href')}")
        print()
        
    except Exception as e:
        print(f"❌ {url}")
        print(f"   Error: {e}\n")

# 搜索技術更新文章
print("\n🔍 搜索技術更新文章...")
try:
    search_url = "https://www.racefans.net/?s=technical+updates"
    response = requests.get(search_url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('article')[:5]
        
        print(f"✅ 找到 {len(articles)} 篇文章\n")
        
        for i, article in enumerate(articles, 1):
            title_elem = article.find(['h2', 'h3'])
            if title_elem:
                link = title_elem.find('a')
                if link:
                    print(f"{i}. {link.get_text().strip()}")
                    print(f"   {link.get('href')}\n")
    
except Exception as e:
    print(f"❌ 搜索失敗: {e}")
