"""完整輸出 PDF 內容以診斷解析失敗"""
import PyPDF2
from pathlib import Path
import sys

# 設定輸出編碼
sys.stdout.reconfigure(encoding='utf-8')

pdf_path = Path('FIAdoc/2025/2025 São Paulo Grand Prix - Parts and parameters been replaced and or changed during Parc Fermé.pdf')

with open(pdf_path, 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    print(f"PDF 總頁數: {len(reader.pages)}")
    
    # 輸出前 3 頁的完整內容
    for page_num in range(min(3, len(reader.pages))):
        print(f"\n{'='*80}")
        print(f"第 {page_num + 1} 頁內容:")
        print(f"{'='*80}")
        text = reader.pages[page_num].extract_text()
        print(text)
        print(f"\n字數: {len(text)}")
