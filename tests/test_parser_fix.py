"""測試 PDF 解析器修正"""
from CLI_modules.cli.core.fia_parts_pdf_parser import F1UpgradeAnalyzerByYear
from pathlib import Path

analyzer = F1UpgradeAnalyzerByYear(2025)
pdf_path = Path('FIAdoc/2025/2025 São Paulo Grand Prix - Parts and parameters been replaced and or changed during Parc Fermé.pdf')

print("🔍 測試 PDF 解析器...")
changes = analyzer.parse_parc_ferme_document(pdf_path)

print(f"\n✅ 提取到 {len(changes)} 筆記錄")

if changes:
    print("\n📊 前 10 筆記錄:")
    for i, c in enumerate(changes[:10], 1):
        print(f"  {i}. {c['車隊']} (車號 {c['車號']}): {c['更換部件']}")
    
    print(f"\n✅ 測試通過！PDF 解析器已修正")
else:
    print("\n❌ 測試失敗：仍無法提取記錄")
