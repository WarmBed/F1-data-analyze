"""檢查 PDF 文字編碼"""
from pathlib import Path
import PyPDF2

pdf_path = Path('FIAdoc/2025/2025 São Paulo Grand Prix - Parts and parameters been replaced and or changed during Parc Fermé.pdf')

with open(pdf_path, 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    text = reader.pages[0].extract_text()

# 查找 "Parc Ferm" 相關字串
import re
matches = re.findall(r'.{0,20}Parc.{0,20}', text, re.IGNORECASE)
print("包含 'Parc' 的字串:")
for m in matches:
    print(f"  - '{m}'")
    print(f"    字節: {[hex(ord(c)) for c in m]}")

# 查找 "parts and parameters"
matches2 = re.findall(r'.{0,10}parts.{0,30}parameters.{0,10}', text, re.IGNORECASE)
print("\n包含 'parts...parameters' 的字串:")
for m in matches2:
    print(f"  - '{m}'")
    print(f"    包含空格數: {m.count(' ')}")

# 檢查特殊字元
print(f"\ntext.lower() 包含:")
print(f"  'parts and parameters': {'parts and parameters' in text.lower()}")
print(f"  'parts': {'parts' in text.lower()}")
print(f"  'parameters': {'parameters' in text.lower()}")
print(f"  'fermé': {'fermé' in text.lower()}")
print(f"  'ferme': {'ferme' in text.lower()}")
print(f"  'ferm': {'ferm' in text.lower()}")
