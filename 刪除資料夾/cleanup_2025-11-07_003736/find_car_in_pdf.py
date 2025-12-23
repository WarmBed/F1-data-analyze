#!/usr/bin/env python3
"""
搜索特定車號在 PDF 中的頁碼
"""
import PyPDF2
import sys

def find_car_in_pdf(pdf_path, car_number, component):
    """在 PDF 中尋找特定車號和部件"""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            total_pages = len(reader.pages)
            
            print(f"\n📄 檔案: {pdf_path}")
            print(f"📊 總頁數: {total_pages}")
            print(f"🔍 搜尋目標: Car {car_number} - {component}\n")
            print("="*80)
            
            found = False
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                page_num = i + 1
                
                # 搜索 Car XX
                if f"Car {car_number}" in text:
                    print(f"\n✅ 找到 Car {car_number} 在第 {page_num} 頁")
                    print("-"*80)
                    
                    # 提取該車號相關的段落
                    lines = text.split('\n')
                    car_section = []
                    capture = False
                    
                    for line in lines:
                        if f"Car {car_number}" in line:
                            capture = True
                        
                        if capture:
                            car_section.append(line)
                            
                            # 如果遇到下一個 Car 或空行太多，停止
                            if len(car_section) > 1 and line.strip().startswith("Car ") and f"Car {car_number}" not in line:
                                break
                    
                    print("內容摘錄:")
                    print('\n'.join(car_section[:10]))  # 顯示前 10 行
                    print("-"*80)
                    found = True
            
            if not found:
                print(f"\n❌ 未找到 Car {car_number}")
            
            return found
            
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return False


if __name__ == '__main__':
    # Australian GP - Car 14 - Floor
    pdf_file = "fiadoc/2025 Australian Grand Prix - Parts and Parameters been replaced and or changed during Parc Fermé.pdf"
    find_car_in_pdf(pdf_file, "14", "Floor assembly")
