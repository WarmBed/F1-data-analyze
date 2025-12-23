"""正確抓取 FIA 文件主頁面的所有文件"""
import requests
from bs4 import BeautifulSoup

url = "https://www.fia.com/documents/championships/fia-formula-one-world-championship-14"
print(f"🔍 抓取: {url}\n")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

response = requests.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(response.text, 'html.parser')

# 找出所有文件行
document_rows = soup.find_all('li', class_='document-row')
print(f"✅ 找到 {len(document_rows)} 個文件\n")

documents = []

for i, row in enumerate(document_rows, 1):
    # 找到 PDF 連結
    link = row.find('a', href=True)
    if not link:
        continue
    
    pdf_url = link.get('href')
    if not pdf_url.startswith('http'):
        pdf_url = 'https://www.fia.com' + pdf_url
    
    # 標題
    title_div = row.find('div', class_='title')
    title = title_div.get_text().strip() if title_div else 'Unknown'
    
    # 發布日期
    published_div = row.find('div', class_='published')
    published = published_div.get_text().strip() if published_div else 'Unknown'
    
    # 分站名稱（從檔名推斷）
    filename = pdf_url.split('/')[-1]
    race = 'Unknown'
    if 'grand_prix' in filename.lower():
        parts = filename.lower().replace('.pdf', '').split('_')
        if 'grand' in parts:
            idx = parts.index('grand')
            race = ' '.join(parts[:idx]).replace('2025', '').strip().title()
    
    doc_info = {
        'title': title,
        'url': pdf_url,
        'published': published,
        'race': race,
        'filename': filename
    }
    
    documents.append(doc_info)
    
    # 顯示前20個
    if i <= 20:
        print(f"{i:3d}. {title[:60]}")
        print(f"     Race: {race} | Published: {published}")
        print(f"     📄 {filename}")
        print()

print(f"\n📊 總計: {len(documents)} 個文件")

# 統計分站
races = {}
for doc in documents:
    race = doc['race']
    races[race] = races.get(race, 0) + 1

print(f"\n🏁 涉及分站數: {len(races)}")
for race, count in sorted(races.items(), key=lambda x: -x[1])[:10]:
    print(f"   {race}: {count} 個文件")

# 檢查是否有升級相關文件
upgrade_docs = [d for d in documents if 'upgrade' in d['title'].lower() or 'technical' in d['title'].lower()]
print(f"\n🔧 技術/升級相關文件: {len(upgrade_docs)} 個")

if upgrade_docs:
    print("\n升級相關文件範例:")
    for doc in upgrade_docs[:10]:
        print(f"  - {doc['title']}")
        print(f"    {doc['race']} | {doc['published']}")
