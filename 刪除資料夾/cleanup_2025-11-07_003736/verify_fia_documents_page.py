"""驗證 FIA F1 文件主頁面結構"""
import requests
from bs4 import BeautifulSoup
import re

url = "https://www.fia.com/documents/championships/fia-formula-one-world-championship-14"
print(f"🔍 訪問: {url}\n")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

try:
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    print(f"✅ HTTP 狀態: {response.status_code}\n")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 1. 檢查頁面標題
    title = soup.find('h1')
    print(f"📄 頁面標題: {title.get_text().strip() if title else 'Not found'}\n")
    
    # 2. 檢查是否有賽季/年份選擇器
    season_selectors = soup.find_all(['select', 'div'], class_=re.compile(r'season|year', re.I))
    print(f"📅 賽季選擇器: {len(season_selectors)} 個")
    
    # 3. 檢查是否有分站列表
    race_links = soup.find_all('a', href=re.compile(r'/event/|grand-prix', re.I))
    print(f"🏁 分站連結: {len(race_links)} 個")
    
    if race_links:
        print("\n前10個分站:")
        for i, link in enumerate(race_links[:10], 1):
            text = link.get_text().strip()
            href = link.get('href')
            print(f"  {i}. {text[:50]}")
            print(f"     → {href[:80]}")
    
    # 4. 檢查 PDF 連結
    pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
    print(f"\n📑 PDF 連結: {len(pdf_links)} 個")
    
    if pdf_links:
        print("\n前10個 PDF:")
        for i, link in enumerate(pdf_links[:10], 1):
            text = link.get_text().strip()
            href = link.get('href')
            print(f"  {i}. {text[:60]}")
            print(f"     → {href[:100]}")
    
    # 5. 檢查文件分類
    categories = soup.find_all(['div', 'section'], class_=re.compile(r'category|filter|type', re.I))
    print(f"\n🗂️  文件分類容器: {len(categories)} 個")
    
    # 6. 檢查是否有表格（文件列表）
    tables = soup.find_all('table')
    print(f"📊 表格數量: {len(tables)}")
    
    if tables:
        print("\n第一個表格的前5行:")
        rows = tables[0].find_all('tr')[:5]
        for i, row in enumerate(rows, 1):
            cells = row.find_all(['td', 'th'])
            cell_texts = [cell.get_text().strip()[:30] for cell in cells]
            print(f"  Row {i}: {' | '.join(cell_texts)}")
    
    # 7. 檢查 JavaScript 數據
    scripts = soup.find_all('script')
    print(f"\n🔧 Script 標籤: {len(scripts)} 個")
    
    # 尋找包含 'documents' 或 'files' 的 script
    data_scripts = []
    for script in scripts:
        if script.string and ('documents' in script.string.lower() or 'files' in script.string.lower()):
            data_scripts.append(script.string[:200])
    
    if data_scripts:
        print(f"   包含數據的 script: {len(data_scripts)} 個")
        print(f"   範例: {data_scripts[0][:150]}...")
    
    # 8. 檢查是否有 Vue/React 應用
    vue_app = soup.find(id=re.compile(r'app|vue|react', re.I))
    if vue_app:
        print(f"\n⚛️  檢測到前端框架應用: {vue_app.get('id')}")
    
    # 9. 保存完整 HTML
    with open('fia_main_documents_page.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    print(f"\n✅ 完整 HTML 已保存到 fia_main_documents_page.html")
    
    # 10. 檢查特定關鍵字
    html_text = response.text.lower()
    keywords = ['upgrade', 'technical directive', 'technical report', '2025', 'red bull']
    print(f"\n🔑 關鍵字檢測:")
    for kw in keywords:
        count = html_text.count(kw)
        print(f"   '{kw}': {count} 次")

except Exception as e:
    print(f"❌ 錯誤: {e}")
