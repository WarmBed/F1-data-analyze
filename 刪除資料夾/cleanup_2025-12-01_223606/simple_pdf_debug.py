"""簡化調試 - 只顯示關鍵資訊"""
import PyPDF2
from pathlib import Path

pdf_path = Path('FIAdoc/2025/2025 São Paulo Grand Prix - Parts and parameters been replaced and or changed during Parc Fermé.pdf')

with open(pdf_path, 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    text = reader.pages[0].extract_text()
    
    # 按行處理
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    with open('pdf_lines.txt', 'w', encoding='utf-8') as f:
        f.write(f"總行數: {len(lines)}\n\n")
        for i, line in enumerate(lines, 1):
            f.write(f"第 {i:2d} 行: {line}\n")
            
print("已輸出到 pdf_lines.txt")
