#!/usr/bin/env python3
"""
從 FIA Entry List 文件建立正確的 2025 車號映射表
"""
import PyPDF2
import re
from pathlib import Path


def extract_entry_list(pdf_path):
    """從 Entry List PDF 提取車號映射"""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = reader.pages[0].extract_text()
            
            print(f"\n📄 分析: {pdf_path.name}")
            print("="*100)
            print(text)
            print("="*100)
            
            return text
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return ""


def main():
    # 從澳洲站 Entry List 開始
    fiadoc = Path("fiadoc")
    entry_list_files = list(fiadoc.glob("*Entry List*.pdf"))
    
    print(f"\n找到 {len(entry_list_files)} 個 Entry List 文件")
    
    # 選擇澳洲站或巴林站 Entry List
    for pdf_file in sorted(entry_list_files):
        if "Australian" in pdf_file.name or "Bahrain" in pdf_file.name:
            extract_entry_list(pdf_file)
            break


if __name__ == '__main__':
    main()
