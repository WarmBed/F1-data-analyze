#!/usr/bin/env python3
"""
PDF 文本提取工具
用於分析 F1 研究論文並提取關鍵資訊
"""
import sys
from pathlib import Path

def extract_pdf_text(pdf_path):
    """提取 PDF 文字內容"""
    try:
        import PyPDF2
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            print(f"📄 檔案: {pdf_path.name}")
            print(f"📊 總頁數: {len(pdf_reader.pages)}")
            print("="*70)
            
            full_text = []
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                full_text.append(f"\n{'='*70}\n第 {page_num} 頁\n{'='*70}\n{text}")
                
            return "\n".join(full_text)
            
    except ImportError:
        print("❌ 需要安裝 PyPDF2")
        print("執行: pip install PyPDF2")
        return None
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return None


def analyze_f1_paper(text):
    """分析 F1 論文內容"""
    
    # 關鍵章節
    sections = {
        'Features': ['feature', 'variable', 'predictor', 'input'],
        'Model': ['xgboost', 'random forest', 'neural network', 'regression', 'classifier'],
        'Evaluation': ['accuracy', 'mae', 'rmse', 'spearman', 'r2', 'correlation'],
        'Results': ['result', 'performance', 'prediction', 'test'],
        'Dataset': ['data', 'ergast', 'fastf1', 'season', 'race']
    }
    
    print("\n🔍 關鍵字搜尋結果:")
    print("="*70)
    
    for section, keywords in sections.items():
        print(f"\n📌 {section}:")
        matches = []
        for keyword in keywords:
            count = text.lower().count(keyword)
            if count > 0:
                matches.append(f"  - '{keyword}': {count} 次")
        
        if matches:
            print("\n".join(matches))
        else:
            print("  (未找到相關內容)")


def extract_tables_and_figures(text):
    """提取表格和圖表標題"""
    import re
    
    print("\n📊 表格與圖表:")
    print("="*70)
    
    # 搜尋 Table X, Figure X
    tables = re.findall(r'Table\s+\d+[:\.]?\s*([^\n]+)', text, re.IGNORECASE)
    figures = re.findall(r'Figure\s+\d+[:\.]?\s*([^\n]+)', text, re.IGNORECASE)
    
    if tables:
        print("\n📋 表格:")
        for i, table in enumerate(tables[:10], 1):
            print(f"  {i}. {table.strip()}")
    
    if figures:
        print("\n📈 圖表:")
        for i, figure in enumerate(figures[:10], 1):
            print(f"  {i}. {figure.strip()}")


def main():
    # 檢查參考文件目錄
    docs_dir = Path("docs/參考文件")
    
    if not docs_dir.exists():
        print(f"❌ 找不到目錄: {docs_dir}")
        return
    
    # 列出所有 PDF
    pdf_files = list(docs_dir.glob("*.pdf"))
    pdf_files += list(docs_dir.glob("**/*.pdf"))
    
    if not pdf_files:
        print(f"❌ 找不到 PDF 檔案在 {docs_dir}")
        return
    
    print(f"找到 {len(pdf_files)} 個 PDF 檔案:")
    for i, pdf in enumerate(pdf_files, 1):
        print(f"  {i}. {pdf.name}")
    
    # 選擇要分析的 PDF
    print("\n" + "="*70)
    choice = input("請輸入要分析的檔案編號 (或按 Enter 分析第一個): ").strip()
    
    if not choice:
        choice = 1
    else:
        try:
            choice = int(choice)
        except:
            print("❌ 無效的選擇")
            return
    
    if choice < 1 or choice > len(pdf_files):
        print("❌ 編號超出範圍")
        return
    
    selected_pdf = pdf_files[choice - 1]
    
    print(f"\n🔍 正在分析: {selected_pdf.name}")
    print("="*70)
    
    # 提取文字
    text = extract_pdf_text(selected_pdf)
    
    if not text:
        return
    
    # 儲存提取的文字
    output_file = Path(f"extracted_{selected_pdf.stem}.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(text)
    
    print(f"\n✅ 文字已儲存至: {output_file}")
    
    # 分析內容
    analyze_f1_paper(text)
    extract_tables_and_figures(text)
    
    # 顯示前 2000 字元
    print("\n📖 內容預覽 (前 2000 字元):")
    print("="*70)
    print(text[:2000])
    print("\n... (更多內容請查看輸出檔案)")


if __name__ == '__main__':
    main()
