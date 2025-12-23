"""
簡化版預測測試 - 直接測試預測器
"""
from CLI_modules.cli.prediction.overtake_prediction.predictor import OvertakePredictor
from CLI_modules.cli.prediction.overtake_prediction.close_combat_predictor import CloseCombatPredictor

def test_predictors_directly():
    """直接測試預測器"""
    print("="*60)
    print("測試預測器是否能產生非零預測")
    print("="*60)
    
    # 初始化預測器
    print("\n⏳ Loading predictors...")
    ot_predictor = OvertakePredictor(verbose=False)
    cc_predictor = CloseCombatPredictor(verbose=False)
    
    print(f"✅ OT predictor loaded: {ot_predictor.model is not None} (v{ot_predictor.model_version})")
    print(f"✅ CC predictor loaded: {cc_predictor.model is not None} (v{cc_predictor.model_version})")
    
    # 測試場景：追近前車的情況
    test_scenarios = [
        {
            "name": "近距離追逐 (0.5s)",
            "gap_seconds": 0.5,
            "gap_delta": -0.05,  # 正在拉近
            "is_catching": True,
            "drs_available": True,
            "attacker_tyre": "SOFT",
            "defender_tyre": "MEDIUM",
            "tyre_age_diff": 5,  # 防守者輪胎老 5 圈
            "track_status_green": True,
            "attacker_position": 3,
            "race_progress": 0.5
        },
        {
            "name": "中距離接近 (1.5s)",
            "gap_seconds": 1.5,
            "gap_delta": -0.08,
            "is_catching": True,
            "drs_available": False,
            "attacker_tyre": "MEDIUM",
            "defender_tyre": "MEDIUM",
            "tyre_age_diff": 3,
            "track_status_green": True,
            "attacker_position": 5,
            "race_progress": 0.6
        },
        {
            "name": "遠距離 (3.0s)",
            "gap_seconds": 3.0,
            "gap_delta": -0.03,
            "is_catching": True,
            "drs_available": False,
            "attacker_tyre": "MEDIUM",
            "defender_tyre": "HARD",
            "tyre_age_diff": 0,
            "track_status_green": True,
            "attacker_position": 10,
            "race_progress": 0.7
        }
    ]
    
    print("\n" + "="*60)
    print("測試結果：")
    print("="*60)
    
    for scenario in test_scenarios:
        print(f"\n📊 場景: {scenario['name']}")
        print(f"   間距: {scenario['gap_seconds']}s, DRS: {scenario['drs_available']}, 輪胎: {scenario['attacker_tyre']} vs {scenario['defender_tyre']}")
        
        # 測試 OT%
        try:
            ot_result = ot_predictor.predict(
                gap_seconds=scenario['gap_seconds'],
                gap_delta=scenario['gap_delta'],
                is_catching=scenario['is_catching'],
                drs_available=scenario['drs_available'],
                attacker_tyre=scenario['attacker_tyre'],
                defender_tyre=scenario['defender_tyre'],
                tyre_age_diff=scenario['tyre_age_diff'],
                track_status_green=scenario['track_status_green'],
                attacker_position=scenario['attacker_position'],
                race_progress=scenario['race_progress']
            )
            ot_prob = int(round(ot_result.probability * 100))
            print(f"   ✅ OT% = {ot_prob}%")
        except Exception as e:
            print(f"   ❌ OT% 失敗: {e}")
            ot_prob = 0
        
        # 測試 CC%
        try:
            cc_result = cc_predictor.predict(
                gap_seconds=scenario['gap_seconds'],
                gap_delta=scenario['gap_delta'],
                is_catching=scenario['is_catching'],
                drs_available=scenario['drs_available'],
                attacker_tyre=scenario['attacker_tyre'],
                defender_tyre=scenario['defender_tyre'],
                tyre_age_diff=scenario['tyre_age_diff'],
                track_status_green=scenario['track_status_green'],
                attacker_position=scenario['attacker_position'],
                race_progress=scenario['race_progress'],
                gap_trend_3lap=scenario['gap_delta'],
                min_gap_last_5lap=scenario['gap_seconds'],
                consecutive_catching_laps=2
            )
            cc_prob = int(round(cc_result.probability * 100))
            print(f"   ✅ CC% = {cc_prob}%")
        except Exception as e:
            print(f"   ❌ CC% 失敗: {e}")
            cc_prob = 0
    
    print("\n" + "="*60)
    print("測試完成")
    print("="*60)

if __name__ == "__main__":
    test_predictors_directly()
