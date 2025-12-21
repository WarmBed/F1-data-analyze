# fia_f1_parse_fiadoc.py
# 專為 FIAdoc 資料夾設計：解析 2025 F1 墨西哥 & 美國 GP scrutineering PDF
# 輸出 FIA 官方重新認證升級證據

import os
import re
import pdfplumber
import pandas as pd
from datetime import datetime

# ==================== 設定區 ====================
PDF_FOLDER = "FIAdoc"          # 您的資料夾名稱
OUTPUT_CSV = "fia_2025_upgrades_from_FIAdoc.csv"

# F1 車隊完整名稱（含官方名稱）
TEAMS = [
    "Oracle Red Bull Racing", "Red Bull Racing", "Red Bull",
    "Mercedes-AMG PETRONAS", "Mercedes",
    "Scuderia Ferrari", "Ferrari",
    "McLaren Formula 1 Team", "McLaren",
    "Aston Martin Aramco", "Aston Martin",
    "BWT Alpine", "Alpine",
    "Williams Racing", "Williams",
    "Visa Cash App RB", "RB",
    "MoneyGram Haas", "Haas",
    "Stake F1 Team KICK Sauber", "Sauber"
]

# 部件對應升級推測（FIA 官方術語）
COMPONENT_MAP = {
    "Side Impact Structure": "側箱/地板升級",
    "Front Impact Structure": "前翼/鼻錐升級",
    "Survival Cell": "底盤大改",
    "Roll Hoop": "進氣口/防滾架優化",
    "Floor": "地板升級",
    "Front Wing": "前翼升級",
    "Rear Wing": "後翼升級",
    "Chassis": "底盤升級",
    "Suspension": "懸吊升級",
    "Engine Cover": "引擎蓋升級",
    "Gearbox": "變速箱升級"
}
# ================================================

def extract_date_from_filename(filename):
    """從檔名推斷比賽日期（如 2025-10-24）"""
    match = re.search(r'2025[_\-]?(\d{2}[_\-]?\d{2})', filename)
    if match:
        date_str = match.group(1).replace("_", "-").replace("/", "-")
        try:
            return f"2025-{date_str[:2]}-{date_str[2:4]}"
        except:
            pass
    return "未知日期"

def parse_pdf(pdf_path):
    """解析單一 PDF，提取 re-homologation 紀錄"""
    upgrades = []
    filename = os.path.basename(pdf_path)
    default_date = extract_date_from_filename(filename)

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue

                lines = text.split('\n')
                current_team = None
                current_comp = None

                for line in lines:
                    line_low = line.lower().strip()

                    # 關鍵字觸發
                    if not any(kw in line_low for kw in ['re-presented', 're-homologated', 're-test', 're-present', 'passed', 'failed']):
                        continue

                    # 找車隊（Car 1, Car 11, Car 16...）
                    car_match = re.search(r'car\s+(\d{1,2})', line_low)
                    team = None
                    if car_match:
                        car_num = car_match.group(1)
                        # 常見車號對應
                        car_to_team = {
                            "1": "Red Bull", "11": "Red Bull",
                            "4": "McLaren", "81": "McLaren",
                            "16": "Ferrari", "55": "Ferrari",
                            "44": "Mercedes", "63": "Mercedes",
                            "14": "Aston Martin", "18": "Aston Martin",
                            "10": "Alpine", "31": "Alpine",
                            "23": "Williams", "2": "Williams",
                            "22": "RB", "3": "RB",
                            "27": "Haas", "20": "Haas",
                            "24": "Sauber", "77": "Sauber"
                        }
                        team_key = car_to_team.get(car_num, "未知車隊")
                        team = next((t for t in TEAMS if team_key.lower() in t.lower()), team_key)

                    # 若無車號，找括號內車隊名
                    if not team:
                        for t in TEAMS:
                            if '(' + t.split()[-1].lower() + ')' in line_low or t.lower() in line_low:
                                team = t
                                break

                    if not team:
                        continue

                    # 找部件
                    comp = None
                    for c in COMPONENT_MAP:
                        if c.lower() in line_low:
                            comp = c
                            break

                    if not comp:
                        continue

                    # 找日期（PDF 內）
                    date_match = re.search(r'\d{4}-\d{2}-\d{2}', line)
                    date = date_match.group() if date_match else default_date

                    upgrades.append({
                        "車隊": team.split()[-1] if len(team.split()) > 1 else team,  # 簡稱
                        "完整車隊名": team,
                        "日期": date,
                        "部件": comp,
                        "推測升級": COMPONENT_MAP[comp],
                        "原文": line.strip()[:100] + "..." if len(line.strip()) > 100 else line.strip(),
                        "來源文件": filename,
                        "頁碼": page_num + 1
                    })

    except Exception as e:
        print(f"解析錯誤 {filename}: {e}")

    return upgrades

def main():
    print("="*90)
    print("  FIA 2025 F1 零件升級偵測系統（讀取 FIAdoc 資料夾）")
    print("="*90)

    if not os.path.exists(PDF_FOLDER):
        print(f"錯誤：找不到資料夾 '{PDF_FOLDER}'")
        print("請確認資料夾名稱正確，並放在腳本同目錄下")
        return

    print(f"正在掃描資料夾: {PDF_FOLDER}")
    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print("資料夾內無 PDF 檔案")
        return

    print(f"發現 {len(pdf_files)} 個 PDF 檔案：")
    for f in pdf_files:
        print(f"  - {f}")

    all_upgrades = []
    for file in pdf_files:
        path = os.path.join(PDF_FOLDER, file)
        print(f"\n正在解析: {file}")
        upgrades = parse_pdf(path)
        if upgrades:
            print(f"  發現 {len(upgrades)} 筆升級紀錄")
            all_upgrades.extend(upgrades)
        else:
            print("  未發現升級紀錄")

    if all_upgrades:
        df = pd.DataFrame(all_upgrades)
        df = df.drop_duplicates(subset=["車隊", "日期", "部件"]).sort_values(["日期", "車隊"])

        print("\n" + "="*90)
        print("  2025 F1 零件更新彙總（FIA 官方重新認證證據）")
        print("="*90)
        print(df[["車隊", "日期", "部件", "推測升級", "來源文件", "頁碼"]].to_string(index=False))

        # 匯出 CSV
        df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
        print(f"\n已匯出完整資料至: {OUTPUT_CSV}")
    else:
        print("\n未發現任何重新認證紀錄。")
        print("可能原因：PDF 內無 're-presented' 字樣，或需更新關鍵字")

if __name__ == "__main__":
    main()