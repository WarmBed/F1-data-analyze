"""深度調試 PDF 解析器"""
from CLI_modules.cli.core.fia_parts_pdf_parser import F1UpgradeAnalyzerByYear
from pathlib import Path
import re

pdf_path = Path('FIAdoc/2025/2025 São Paulo Grand Prix - Parts and parameters been replaced and or changed during Parc Fermé.pdf')

# 手動執行解析邏輯
analyzer = F1UpgradeAnalyzerByYear(2025)
text = analyzer.extract_text_from_pdf(pdf_path)

print("=" * 80)
print("檢查 1: PDF 文字提取")
print("=" * 80)
print(f"文字長度: {len(text)}")
print(f"前 500 字元:\n{text[:500]}")

print("\n" + "=" * 80)
print("檢查 2: 關鍵字搜索")
print("=" * 80)
print(f"'parts and parameters' 存在: {'parts and parameters' in text.lower()}")
print(f"'parc ferm' 存在: {'parc ferm' in text.lower()}")

print("\n" + "=" * 80)
print("檢查 3: 按行分析（前 30 行）")
print("=" * 80)
lines = text.split('\n')
for i, line in enumerate(lines[:30], 1):
    line_stripped = line.strip()
    if line_stripped:
        print(f"第 {i:2d} 行: {line_stripped}")
        
        # 檢測車隊標題
        if line_stripped.endswith(':') and not line_stripped.startswith('Car'):
            print(f"       >>> 檢測到車隊標題!")
        
        # 檢測車號行
        car_match = re.match(r'Car\s+(\d+):\s*(.*)', line_stripped, re.IGNORECASE)
        if car_match:
            print(f"       >>> 檢測到車號 {car_match.group(1)}, 部件: '{car_match.group(2)}'")

print("\n" + "=" * 80)
print("檢查 4: 執行實際解析")
print("=" * 80)
changes = analyzer.parse_parc_ferme_document(pdf_path)
print(f"提取到 {len(changes)} 筆記錄")

if changes:
    for i, c in enumerate(changes[:5], 1):
        print(f"  {i}. {c['車隊']} (車號 {c['車號']}): {c['更換部件']}")
