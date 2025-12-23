#!/usr/bin/env python3
"""
FIA 文件下載系統 - 快速演示
展示如何下載和分析升級套件文件
"""
from pathlib import Path
import sys

def demo_workflow():
    """演示完整工作流程"""
    
    print("="*70)
    print("🏎️  FIA 文件下載與升級套件識別系統 - 快速演示")
    print("="*70)
    
    print("\n📌 本系統提供以下功能:\n")
    
    print("1️⃣  **FIA 文件下載器** (fia_document_scraper.py)")
    print("   • 自動從 FIA 官網下載 F1 技術文件")
    print("   • 智能分類: 技術報告、處罰決定、賽事須知、輪胎分析")
    print("   • 識別升級相關文件")
    
    print("\n2️⃣  **升級套件追蹤器** (upgrade_tracker.py)")
    print("   • 分析 PDF 文件，提取升級資訊")
    print("   • 建立車隊升級資料庫")
    print("   • 生成時間線和統計報告")
    
    print("\n" + "="*70)
    print("🚀 使用範例")
    print("="*70)
    
    examples = [
        {
            "title": "搜尋 2025 年 Japan GP 的技術文件",
            "command": "python fia_document_scraper.py -y 2025 -r Japan -c technical --list-only"
        },
        {
            "title": "下載所有升級相關文件",
            "command": "python fia_document_scraper.py -y 2025 --upgrade-only -d"
        },
        {
            "title": "分析已下載的 PDF 文件",
            "command": 'python upgrade_tracker.py -a "fia_documents/technical/2025_japan_technical_report.pdf"'
        },
        {
            "title": "手動新增升級記錄",
            "command": 'python upgrade_tracker.py --add "Red Bull Racing" "Japan" "front_wing" "aerodynamic" "新前翼設計"'
        },
        {
            "title": "查詢 Red Bull 的所有升級",
            "command": 'python upgrade_tracker.py -t "Red Bull Racing"'
        },
        {
            "title": "查詢 Monaco GP 的所有升級",
            "command": 'python upgrade_tracker.py -r Monaco'
        },
        {
            "title": "匯出 JSON 資料供 GUI/API 使用",
            "command": "python upgrade_tracker.py -e"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n📝 範例 {i}: {example['title']}")
        print(f"   命令: {example['command']}")
    
    print("\n" + "="*70)
    print("🔍 升級套件識別邏輯")
    print("="*70)
    
    print("\n系統會搜尋以下升級關鍵字:\n")
    
    categories = {
        "空氣動力學": ["front wing", "rear wing", "floor", "diffuser", "sidepod"],
        "機械系統": ["suspension", "brake duct", "cooling", "gearbox"],
        "動力單元": ["engine", "MGU-K", "MGU-H", "turbo", "ERS"],
        "其他": ["weight reduction", "reliability update", "carbon fiber"]
    }
    
    for category, components in categories.items():
        print(f"  🔧 {category}:")
        for component in components:
            print(f"     • {component}")
    
    print("\n" + "="*70)
    print("📊 資料輸出格式")
    print("="*70)
    
    print("\n下載的文件會分類到:")
    print("  fia_documents/")
    print("  ├── technical/      # 技術報告")
    print("  ├── sporting/       # 處罰決定")
    print("  ├── event/          # 賽事須知")
    print("  ├── tire/           # 輪胎分析")
    print("  └── upgrade/        # 升級文件")
    
    print("\n升級資料庫:")
    print("  upgrade_data/")
    print("  ├── upgrades_database.json  # 主資料庫")
    print("  └── upgrades_export.json    # 匯出資料（含統計）")
    
    print("\n" + "="*70)
    print("💡 整合到 F1T 專案")
    print("="*70)
    
    print("\n建議的整合方式:\n")
    
    integrations = [
        "CLI 功能擴展: 新增功能 75-76（車隊升級時間線、分站升級對比）",
        "GUI 模組: modules/gui/upgrade_tracker/ （視覺化升級時間線）",
        "API 端點: GET /api/upgrades （提供升級資料查詢）",
        "數據驗證: 結合 FastF1 遙測驗證升級效果"
    ]
    
    for i, integration in enumerate(integrations, 1):
        print(f"  {i}. {integration}")
    
    print("\n" + "="*70)
    print("⚠️  注意事項")
    print("="*70)
    
    notes = [
        "FIA 文件版權歸 FIA 所有，僅供個人研究使用",
        "PDF 解析準確率取決於文件格式，建議人工驗證",
        "某些技術文件為圖片型 PDF，需要 OCR 處理",
        "升級資訊可能不完整，建議結合媒體報導補充"
    ]
    
    print()
    for note in notes:
        print(f"  ⚠️  {note}")
    
    print("\n" + "="*70)
    print("🎯 立即開始")
    print("="*70)
    
    print("\n推薦的入門步驟:\n")
    print("  1️⃣  手動新增幾筆測試資料:")
    print('     python upgrade_tracker.py --add "Red Bull Racing" "Bahrain" "front_wing" "aerodynamic" "開季升級"')
    print()
    print("  2️⃣  查看摘要:")
    print("     python upgrade_tracker.py -s")
    print()
    print("  3️⃣  匯出資料:")
    print("     python upgrade_tracker.py -e")
    print()
    print("  4️⃣  搜尋 FIA 文件（需要網路連線）:")
    print("     python fia_document_scraper.py -y 2025 --upgrade-only --list-only")
    
    print("\n" + "="*70)
    print("📚 詳細文件")
    print("="*70)
    
    print("\n完整使用指南請參考:")
    print("  docs/FIA_DOCUMENT_SCRAPER_GUIDE.md")
    
    print("\n" + "="*70)
    print("✅ 演示完成!")
    print("="*70 + "\n")


def create_sample_data():
    """建立範例資料"""
    from upgrade_tracker import UpgradeTracker
    
    print("\n🎯 建立範例升級資料...")
    
    tracker = UpgradeTracker()
    
    # 範例升級資料
    sample_upgrades = [
        ("Red Bull Racing", "Bahrain", "front_wing", "aerodynamic", "開季前翼升級包"),
        ("Red Bull Racing", "Japan", "floor", "aerodynamic", "新地板設計"),
        ("Ferrari", "Bahrain", "sidepod", "aerodynamic", "側箱改良"),
        ("Ferrari", "Monaco", "cooling", "mechanical", "街道賽散熱升級"),
        ("Mercedes", "Spain", "rear_wing", "aerodynamic", "高下壓力後翼"),
        ("McLaren", "Singapore", "brake_duct", "mechanical", "高溫煞車散熱"),
        ("Aston Martin", "Italy", "diffuser", "aerodynamic", "擴散器優化"),
    ]
    
    for team, race, component, category, desc in sample_upgrades:
        tracker.add_manual_upgrade(team, race, component, category, desc)
    
    print("\n✅ 範例資料建立完成!")
    print("\n現在可以執行:")
    print("  python upgrade_tracker.py -s")
    print("  python upgrade_tracker.py -e")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='FIA 文件系統演示')
    parser.add_argument('--create-sample', action='store_true', 
                       help='建立範例升級資料')
    
    args = parser.parse_args()
    
    if args.create_sample:
        create_sample_data()
    else:
        demo_workflow()
