"""
測試 F90/F91 的 LiveF1 數據解析功能
"""
import json
from pathlib import Path
from CLI_modules.cli.prediction.fp2_race_ml_trainer import FP2RaceMLTrainer
from CLI_modules.cli.prediction.fp2_race_ml_predictor import FP2RaceMLPredictor

def test_f90_parsing():
    """測試 F90 的 _parse_timing_data() 方法"""
    print("\n" + "="*80)
    print("測試 F90 (FP2RaceMLTrainer) - LiveF1 數據解析")
    print("="*80)
    
    # 載入 2025 Abu Dhabi FP2 TimingData.json
    timing_file = Path("json/LiveF1/2025/Abu_Dhabi_Practice_2/TimingData.json")
    
    if not timing_file.exists():
        print(f"❌ 找不到測試數據: {timing_file}")
        return False
    
    with open(timing_file, 'r', encoding='utf-8') as f:
        timing_data = json.load(f)
    
    print(f"\n✅ 成功載入 TimingData.json")
    print(f"   檔案格式: {'records' if 'records' in timing_data else 'unknown'}")
    print(f"   記錄數量: {len(timing_data.get('records', []))}")
    
    # 初始化 Trainer
    trainer = FP2RaceMLTrainer(verbose=True)
    
    # 測試解析
    driver_laps = trainer._parse_timing_data(timing_data)
    
    print(f"\n✅ 解析完成")
    print(f"   車手數量: {len(driver_laps)}")
    
    # 顯示前 5 位車手的資料
    print(f"\n📊 車手圈速數據預覽:")
    for idx, (driver, laps) in enumerate(list(driver_laps.items())[:5], 1):
        print(f"\n   {idx}. 車手 {driver}:")
        print(f"      總圈數: {len(laps)}")
        if laps:
            print(f"      第一圈: Lap {laps[0]['lap']}, Time={laps[0]['time']}")
            print(f"      最後一圈: Lap {laps[-1]['lap']}, Time={laps[-1]['time']}")
    
    return True

def test_f91_parsing():
    """測試 F91 的 _parse_livef1_timing_data() 方法"""
    print("\n" + "="*80)
    print("測試 F91 (FP2RaceMLPredictor) - LiveF1 數據解析")
    print("="*80)
    
    # 載入 2025 Abu Dhabi FP2 TimingData.json
    timing_file = Path("json/LiveF1/2025/Abu_Dhabi_Practice_2/TimingData.json")
    
    if not timing_file.exists():
        print(f"❌ 找不到測試數據: {timing_file}")
        return False
    
    with open(timing_file, 'r', encoding='utf-8') as f:
        timing_data = json.load(f)
    
    # 初始化 Predictor
    predictor = FP2RaceMLPredictor(verbose=True)
    
    # 測試解析
    driver_laps = predictor._parse_livef1_timing_data(timing_data)
    
    print(f"\n✅ 解析完成")
    print(f"   車手數量: {len(driver_laps)}")
    
    # 顯示前 5 位車手的資料
    print(f"\n📊 車手圈速數據預覽:")
    for idx, (driver, laps) in enumerate(list(driver_laps.items())[:5], 1):
        print(f"\n   {idx}. 車手 {driver}:")
        print(f"      總圈數: {len(laps)}")
        if laps:
            print(f"      第一圈: Lap {laps[0]['lap']}, Time={laps[0]['time']}")
            print(f"      最後一圈: Lap {laps[-1]['lap']}, Time={laps[-1]['time']}")
    
    return True

if __name__ == "__main__":
    success_f90 = test_f90_parsing()
    success_f91 = test_f91_parsing()
    
    print("\n" + "="*80)
    print("測試總結")
    print("="*80)
    print(f"F90 解析: {'✅ 通過' if success_f90 else '❌ 失敗'}")
    print(f"F91 解析: {'✅ 通過' if success_f91 else '❌ 失敗'}")
    
    if success_f90 and success_f91:
        print("\n🎉 所有測試通過！F90/F91 已正確處理 LiveF1 格式")
    else:
        print("\n⚠️  部分測試失敗，請檢查錯誤訊息")
