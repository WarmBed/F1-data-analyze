"""抓取 FIA 2025 賽季的所有文件"""
import requests
from bs4 import BeautifulSoup

url = "https://www.fia.com/documents/championships/fia-formula-one-world-championship-14/season/season-2025-2071"
print(f"🔍 抓取 2025 賽季: {url}\n")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

response = requests.get(url, headers=headers, timeout=30)
soup = BeautifulSoup(response.text, 'html.parser')

# 找出所有文件行
document_rows = soup.find_all('li', class_='document-row')
print(f"✅ 找到 {len(document_rows)} 個 2025 賽季文件\n")

documents = []

for i, row in enumerate(document_rows, 1):
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
    
    # 分站名稱
    filename = pdf_url.split('/')[-1]
    race = 'Unknown'
    if 'grand_prix' in filename.lower():
        parts = filename.lower().replace('.pdf', '').split('_')
        if 'grand' in parts:
            idx = parts.index('grand')
            race_name = ' '.join(parts[:idx]).replace('2025', '').strip()
            race = race_name.title()
    
    doc_info = {
        'title': title,
        'url': pdf_url,
        'published': published,
        'race': race,
        'filename': filename
    }
    
    documents.append(doc_info)

print(f"顯示前30個文件:\n")
for i, doc in enumerate(documents[:30], 1):
    print(f"{i:3d}. {doc['title'][:70]}")
    print(f"     Race: {doc['race']:<25} | {doc['published']}")

print(f"\n\n📊 總計: {len(documents)} 個 2025 賽季文件")

# 統計分站
races = {}
for doc in documents:
    race = doc['race']
    races[race] = races.get(race, 0) + 1

print(f"\n🏁 涉及分站: {len(races)} 個")
for race, count in sorted(races.items(), key=lambda x: -x[1])[:15]:
    print(f"   {race:<30}: {count:3d} 個文件")

# 檢查升級相關
upgrade_keywords = ['upgrade', 'technical', 'directive', 'clarification', 'modification']
upgrade_docs = []

for doc in documents:
    title_lower = doc['title'].lower()
    if any(kw in title_lower for kw in upgrade_keywords):
        upgrade_docs.append(doc)

print(f"\n🔧 技術/升級相關文件: {len(upgrade_docs)} 個")

if upgrade_docs:
    print("\n升級相關文件範例（前20個）:")
    for i, doc in enumerate(upgrade_docs[:20], 1):
        print(f"\n{i}. {doc['title']}")
        print(f"   Race: {doc['race']} | {doc['published']}")
        print(f"   📄 {doc['filename']}")

# 檢查是否有 Red Bull 相關
rb_docs = [d for d in documents if 'red bull' in d['title'].lower()]
if rb_docs:
    print(f"\n🏎️  Red Bull 相關文件: {len(rb_docs)} 個")
    for doc in rb_docs:
        print(f"  - {doc['title']}")
else:
    print(f"\n⚠️  未找到明確提及 Red Bull 的文件")
    print("   (車隊升級資訊可能在 Technical Directive 或賽會文件中)")
