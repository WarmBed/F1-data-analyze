"""檢查 FIA 分站頁面結構"""
import requests
from bs4 import BeautifulSoup

url = 'https://www.fia.com/decision-document-list/nojs/140726'
print(f"檢查頁面: {url}\n")

response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
soup = BeautifulSoup(response.text, 'html.parser')

# 檢查表格
tables = soup.find_all('table')
print(f"✓ 表格數量: {len(tables)}")

if tables:
    print("\n前3行內容:")
    rows = tables[0].find_all('tr')[:3]
    for i, row in enumerate(rows, 1):
        text = row.get_text().strip().replace('\n', ' ')[:120]
        print(f"  {i}. {text}")

# 檢查所有連結
all_links = soup.find_all('a', href=True)
pdf_links = [a for a in all_links if a.get('href', '').lower().endswith('.pdf')]
print(f"\n✓ PDF 連結數量: {len(pdf_links)}")

if pdf_links:
    print("前5個 PDF:")
    for i, link in enumerate(pdf_links[:5], 1):
        print(f"  {i}. {link.get('href')}")
        print(f"     標題: {link.get_text().strip()[:80]}")

# 檢查 iframe 或動態內容
iframes = soup.find_all('iframe')
print(f"\n✓ iframe 數量: {len(iframes)}")

# 檢查 script 標籤（可能包含數據）
scripts = soup.find_all('script')
print(f"✓ script 標籤數量: {len(scripts)}")

# 保存 HTML 供檢查
with open('fia_page_sample.html', 'w', encoding='utf-8') as f:
    f.write(soup.prettify())
print("\n✓ HTML 已保存到 fia_page_sample.html")
