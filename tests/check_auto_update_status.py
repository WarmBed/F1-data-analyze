#!/usr/bin/env python3
"""
測試自動更新功能的示範腳本
模擬新增 PDF 文件的場景
"""
import json
from pathlib import Path


def show_cache_status():
    """顯示當前緩存狀態"""
    cache_file = Path(".pdf_cache.json")
    
    print("\n" + "="*80)
    print("📊 當前緩存狀態")
    print("="*80)
    
    if cache_file.exists():
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        
        print(f"上次更新: {cache.get('last_update', '從未更新')}")
        print(f"處理文件: {cache.get('total_pdfs', 0)} 個 PDF")
        print(f"\n已處理的文件列表:")
        
        for filename, info in list(cache.get('processed_files', {}).items())[:5]:
            print(f"  • {filename[:60]}...")
            print(f"    - MD5: {info.get('hash', 'N/A')[:16]}...")
            print(f"    - 首次發現: {info.get('first_seen', 'N/A')}")
        
        if len(cache.get('processed_files', {})) > 5:
            print(f"  ... 還有 {len(cache['processed_files']) - 5} 個文件")
    else:
        print("❌ 緩存文件不存在")
        print("提示: 執行 'python auto_update_upgrades.py' 來創建緩存")
    
    print("="*80 + "\n")


def show_output_files():
    """顯示生成的輸出文件"""
    files = [
        "2025_f1_parts_changes_complete.json",
        "2025_f1_major_upgrades.json",
        "2025_f1_major_upgrades_organized.json"
    ]
    
    print("\n" + "="*80)
    print("📁 生成的輸出文件")
    print("="*80)
    
    for filename in files:
        filepath = Path(filename)
        if filepath.exists():
            size = filepath.stat().st_size / 1024  # KB
            print(f"✅ {filename:<50} ({size:.1f} KB)")
        else:
            print(f"❌ {filename:<50} (不存在)")
    
    print("="*80 + "\n")


def main():
    print("\n" + "="*80)
    print("🔍 自動更新功能狀態檢查")
    print("="*80)
    
    show_cache_status()
    show_output_files()
    
    print("💡 使用提示:")
    print("="*80)
    print("1. 首次執行:")
    print("   python auto_update_upgrades.py")
    print()
    print("2. 有新 PDF 時:")
    print("   - 將新 PDF 放入 fiadoc/ 資料夾")
    print("   - 執行: python auto_update_upgrades.py")
    print("   - 腳本會自動檢測並分析新文件")
    print()
    print("3. 強制重新分析:")
    print("   python auto_update_upgrades.py --force")
    print()
    print("4. 清除緩存:")
    print("   python auto_update_upgrades.py --clear-cache")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
