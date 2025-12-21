"""
為 F1 Parts 數據添加主分類與子分類
根據部件名稱自動分類並輸出新的 JSON

版本: 1.0
日期: 2025-11-08
"""

import json
import re
from collections import defaultdict


def classify_part(part_name: str) -> tuple[str, str]:
    """
    根據部件名稱返回 (主分類, 子分類)
    
    Args:
        part_name: 標準化後的部件名稱
        
    Returns:
        (main_category, sub_category) 元組
    """
    
    part_lower = part_name.lower()
    
    # ========== 1️⃣ 前翼相關 ==========
    if re.search(r'front\s*wing|nose\s*assembly|nosebox', part_lower):
        return ("前翼相關", "前翼總成")
    
    # ========== 2️⃣ 後翼相關 ==========
    if 'rear wing assembly' in part_lower:
        return ("後翼相關", "後翼總成")
    if 'rear' in part_lower and ('beam wing' in part_lower or 'main beam' in part_lower):
        return ("後翼相關", "主翼組件")
    
    # ========== 3️⃣ 底板相關 ==========
    # 底板總成
    if 'floor assembly' in part_lower or 'bib structure to skid' in part_lower:
        return ("底板相關", "底板總成")
    
    # Plank 與 Skid
    if any(x in part_lower for x in ['plank', 'skid']):
        return ("底板相關", "Plank 與 Skid")
    
    # Floor 空力組件
    if 'floor' in part_lower and ('winglet' in part_lower or 'edge' in part_lower):
        return ("底板相關", "Floor 空力組件")
    
    # Floor 結構件（其他 floor 相關）
    if 'floor' in part_lower:
        return ("底板相關", "Floor 結構件")
    
    # ========== 4️⃣ 煞車系統 ==========
    # 煞車片
    if 'brake friction' in part_lower or 'friction material' in part_lower:
        if 'parameter' in part_lower:
            return ("煞車系統", "參數調整")
        return ("煞車系統", "煞車片")
    
    # 煞車卡鉗
    if 'caliper' in part_lower:
        return ("煞車系統", "煞車卡鉗")
    
    # 煞車導管
    if 'brake duct' in part_lower:
        return ("煞車系統", "煞車導管")
    
    # 煞車鼓
    if 'brake drum' in part_lower:
        return ("煞車系統", "煞車鼓")
    
    # 煞車感測器
    if 'brake' in part_lower and ('sensor' in part_lower or 'temperature' in part_lower or 'ir sensor' in part_lower):
        return ("煞車系統", "煞車感測器")
    
    # 煞車踏板與零件
    if any(x in part_lower for x in ['brake pedal', 'brake line', 'rim seal', 'brake drum seal']):
        return ("煞車系統", "煞車踏板與零件")
    
    # BBW 和其他煞車
    if 'bbw' in part_lower or ('brake' in part_lower and 'throttle' in part_lower):
        if 'parameter' in part_lower:
            return ("煞車系統", "參數調整")
        return ("煞車系統", "其他煞車相關")
    
    # ========== 5️⃣ 懸吊系統 ==========
    # 完整懸吊總成
    if 'suspension' in part_lower and ('assemblies' in part_lower or 'assembly' in part_lower):
        if any(x in part_lower for x in ['inboard', 'outboard', 'complete']):
            return ("懸吊系統", "完整懸吊總成")
    
    # 前懸吊組件
    if 'suspension' in part_lower and 'front' in part_lower:
        return ("懸吊系統", "前懸吊組件")
    if any(x in part_lower for x in ['front heave', 'front pullrod', 'front wishbone', 'front top wishbone', 'front lower wishbone']):
        return ("懸吊系統", "前懸吊組件")
    
    # 後懸吊組件
    if 'suspension' in part_lower and 'rear' in part_lower:
        return ("懸吊系統", "後懸吊組件")
    if 'rear' in part_lower and any(x in part_lower for x in ['wishbone', 'upright', 'leg']):
        return ("懸吊系統", "後懸吊組件")
    
    # 其他懸吊
    if 'anti roll bar' in part_lower or 'suspension fairing' in part_lower:
        return ("懸吊系統", "其他")
    
    # ========== 6️⃣ 動力單元 ==========
    # ICE
    if any(x in part_lower for x in ['ice ', 'internal combustion', 'ice sump', 'ice water', 'ice cooling']):
        return ("動力單元", "ICE")
    
    # MGU
    if 'mgu-' in part_lower or 'mgu-k' in part_lower or 'mgu-h' in part_lower:
        return ("動力單元", "MGU")
    
    # 排氣系統
    if any(x in part_lower for x in ['exhaust', 'ex (previously']):
        return ("動力單元", "排氣系統")
    
    # 引擎相關
    if any(x in part_lower for x in ['engine cover', 'spark plug', 'fuel injector', 'cylinder']):
        return ("動力單元", "引擎相關")
    
    # 其他 PU 組件
    if any(x in part_lower for x in ['es (previously', 'ce (', 'powerbox']):
        return ("動力單元", "其他 PU 組件")
    
    # ========== 7️⃣ 變速箱 ==========
    # 離合器
    if 'clutch' in part_lower:
        if 'parameter' in part_lower:
            return ("變速箱", "參數調整")
        return ("變速箱", "離合器")
    
    # 變速箱本體
    if 'gearbox' in part_lower:
        if 'parameter' in part_lower:
            return ("變速箱", "參數調整")
        if any(x in part_lower for x in ['assembly', 'barrel', 'hydraulic']):
            return ("變速箱", "變速箱本體")
        return ("變速箱", "零件與配件")
    
    # 傳動軸
    if 'driveshaft' in part_lower:
        return ("變速箱", "傳動軸")
    
    # ========== 8️⃣ 轉向系統 ==========
    # 方向盤
    if 'steering wheel' in part_lower or 'wheel grip' in part_lower:
        return ("轉向系統", "方向盤")
    
    # 轉向柱
    if 'steering column' in part_lower:
        return ("轉向系統", "轉向柱")
    
    # 轉向齒條
    if any(x in part_lower for x in ['steering rack', 'pas assembly', 'pas rack']):
        return ("轉向系統", "轉向齒條")
    
    # 轉向拉桿
    if 'track rod' in part_lower or 'trackrod' in part_lower:
        return ("轉向系統", "轉向拉桿")
    
    # ========== 9️⃣ 電子系統 ==========
    # 線束
    if 'harness' in part_lower or 'wiring harness' in part_lower:
        return ("電子系統", "線束")
    
    # 電子控制單元
    if any(x in part_lower for x in ['ecu', 'secu', 'tag320', 'hiu', 'electronic box']):
        return ("電子系統", "電子控制單元")
    
    # 電池與感測器
    if any(x in part_lower for x in ['battery', 'lv battery', 'strain gauge', 'trumpet position sensor']):
        return ("電子系統", "電池與感測器")
    
    # ========== 🔟 車體結構 ==========
    # Bib 結構
    if 'bib' in part_lower and any(x in part_lower for x in ['assembly', 'structure', 'tower', 'strut']):
        return ("車體結構", "Bib 結構")
    
    # 底盤
    if any(x in part_lower for x in ['chassis', 'survival cell', 'pitot']):
        return ("車體結構", "底盤")
    
    # 側箱與其他
    if any(x in part_lower for x in ['sidepod', 'halo shroud']):
        return ("車體結構", "側箱與其他")
    
    # ========== 1️⃣1️⃣ 冷卻系統 ==========
    # 水冷系統
    if 'water radiator' in part_lower or 'radiator' in part_lower:
        return ("冷卻系統", "水冷系統")
    
    # 油冷系統
    if 'oil cooler' in part_lower:
        return ("冷卻系統", "油冷系統")
    
    # 充氣冷卻
    if 'charge air cooler' in part_lower:
        return ("冷卻系統", "充氣冷卻")
    
    # 車手冷卻
    if 'dcs cooling' in part_lower or 'driver cooling' in part_lower:
        return ("冷卻系統", "車手冷卻")
    
    # 電子冷卻 或其他冷卻
    if 'cooling' in part_lower or 'radiator skirt' in part_lower:
        return ("冷卻系統", "其他冷卻")
    
    # ========== 1️⃣2️⃣ 安全裝備 ==========
    # 頭枕
    if 'headrest' in part_lower:
        return ("安全裝備", "頭枕")
    
    # 安全帶
    if any(x in part_lower for x in ['seatbelt', 'seat belt', 'crotch belt']):
        return ("安全裝備", "安全帶")
    
    # 滅火器
    if 'fire extinguisher' in part_lower:
        return ("安全裝備", "滅火器")
    
    # ========== 1️⃣3️⃣ 感測器 ==========
    # 車高感測器
    if any(x in part_lower for x in ['ride height laser', 'laser lens']):
        return ("感測器", "車高感測器")
    
    # 位置感測器
    if 'potentiometer' in part_lower and 'parameter' not in part_lower:
        return ("感測器", "位置感測器")
    if 'pitot assembly' in part_lower:
        return ("感測器", "位置感測器")
    
    # 通訊設備
    if 'transponder' in part_lower or 'ris transponder' in part_lower:
        return ("感測器", "通訊設備")
    
    # 參數調整
    if 'parameter' in part_lower and 'potentiometer' in part_lower:
        return ("感測器", "參數調整")
    
    # ========== 1️⃣4️⃣ 參數調整 ==========
    if 'parameter changes' in part_lower:
        # 已在其他分類中處理的參數調整不會到這裡
        return ("參數調整", "通用參數")
    
    # ========== 1️⃣5️⃣ 其他部件 ==========
    # FOM 設備
    if 'fom' in part_lower:
        return ("其他部件", "FOM 設備")
    
    # 導流板與空力組件
    if 'deflector' in part_lower or ('wheel' in part_lower and 'deflector' in part_lower):
        return ("其他部件", "導流板與空力組件")
    
    # 鏡子
    if 'mirror' in part_lower:
        return ("其他部件", "鏡子")
    
    # 輪軸與輪圈
    if any(x in part_lower for x in ['axle', 'wheel nut', 'wheel retention', 'wheel retainer', 'disc mounting']):
        return ("其他部件", "輪軸與輪圈")
    
    # 油門系統
    if 'throttle' in part_lower and 'brake' not in part_lower:
        return ("其他部件", "油門系統")
    
    # 燃油系統
    if any(x in part_lower for x in ['fuel cell', 'fuel system', 'lift pump', 'fuel injector']):
        return ("其他部件", "燃油系統")
    
    # 廢氣閥
    if 'wastegate' in part_lower:
        return ("其他部件", "廢氣閥")
    
    # 車身面板
    if any(x in part_lower for x in ['bodywork', 't-tray', 'umbilical', 'windscreen', 'closing panel', 'sealing panel']):
        return ("其他部件", "車身面板")
    
    # 導管與管路
    if any(x in part_lower for x in ['duct', 'seal hoop', 'pushrod seal']) and 'brake' not in part_lower:
        return ("其他部件", "導管與管路")
    
    # 其他小部件（默認）
    return ("其他部件", "其他小部件")


def main():
    """主程序"""
    
    print("="*70)
    print("F1 Parts Classification Tool v1.0")
    print("為部件數據添加主分類與子分類")
    print("="*70)
    
    # 讀取標準化數據
    input_file = "2025_f1_parts_changes_v2_normalized.json"
    output_file = "2025_f1_parts_changes_v2_classified_with_categories.json"
    
    print(f"\n📂 讀取數據: {input_file}")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            records = json.load(f)
    except FileNotFoundError:
        print(f"❌ 錯誤: 找不到檔案 {input_file}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ 錯誤: JSON 格式錯誤 - {e}")
        return
    
    print(f"✅ 成功載入 {len(records)} 筆記錄")
    
    # 分類統計
    category_stats = defaultdict(lambda: defaultdict(int))
    classified_count = 0
    
    print(f"\n🔄 開始分類...")
    
    # 為每筆記錄添加分類
    for record in records:
        part_name = record.get('部件', '')
        
        if not part_name or any(x in part_name for x in ['Date ', 'Time ', 'To The Stewards']):
            # 跳過噪音數據
            record['主分類'] = '噪音數據'
            record['子分類'] = '噪音數據'
            continue
        
        main_cat, sub_cat = classify_part(part_name)
        record['主分類'] = main_cat
        record['子分類'] = sub_cat
        
        category_stats[main_cat][sub_cat] += 1
        classified_count += 1
    
    print(f"✅ 完成分類 {classified_count} 筆有效記錄")
    
    # 輸出統計
    print(f"\n📊 分類統計：")
    print("-"*70)
    
    # 按主分類排序
    category_order = [
        "前翼相關", "後翼相關", "底板相關", "煞車系統", "懸吊系統",
        "動力單元", "變速箱", "轉向系統", "電子系統", "車體結構",
        "冷卻系統", "安全裝備", "感測器", "參數調整", "其他部件", "噪音數據"
    ]
    
    total_parts = 0
    for main_cat in category_order:
        if main_cat in category_stats:
            subs = category_stats[main_cat]
            main_total = sum(subs.values())
            total_parts += main_total
            print(f"\n【{main_cat}】 總計: {main_total} 種")
            for sub_cat, count in sorted(subs.items()):
                print(f"  ├─ {sub_cat}: {count} 種")
    
    print(f"\n{'='*70}")
    print(f"總計: {total_parts} 筆記錄已分類")
    print(f"{'='*70}")
    
    # 保存結果
    print(f"\n💾 保存結果: {output_file}")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 成功保存 {len(records)} 筆記錄到 {output_file}")
        
        # 顯示文件大小
        import os
        file_size = os.path.getsize(output_file) / 1024 / 1024
        print(f"📦 檔案大小: {file_size:.2f} MB")
        
    except Exception as e:
        print(f"❌ 保存失敗: {e}")
        return
    
    print(f"\n{'='*70}")
    print("✅ 分類完成！")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
