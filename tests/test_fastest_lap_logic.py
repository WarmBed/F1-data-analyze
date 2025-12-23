"""
驗證最快圈速計算邏輯

測試 ranking_tower 的最快圈速檢測邏輯是否正確
"""
import sys

def test_fastest_lap_logic():
    """測試最快圈速計算邏輯"""
    print("=" * 80)
    print("測試最快圈速計算邏輯")
    print("=" * 80)
    
    # 模擬車手數據
    test_drivers = {
        '1': {'driver_tla': 'VER', 'best_lap_time': '1:23.456'},
        '16': {'driver_tla': 'LEC', 'best_lap_time': '1:23.123'},  # 最快
        '55': {'driver_tla': 'SAI', 'best_lap_time': '1:23.789'},
        '63': {'driver_tla': 'RUS', 'best_lap_time': '1:24.012'},
        '44': {'driver_tla': 'HAM', 'best_lap_time': '1:23.234'},
        '11': {'driver_tla': 'PER', 'best_lap_time': ''},  # 無圈時
    }
    
    # 模擬 ranking_tower 的最快圈速計算邏輯
    fastest_best_lap_time = None
    fastest_best_lap_seconds = float('inf')
    
    for driver_num, driver_data in test_drivers.items():
        best_lap_time = driver_data.get('best_lap_time', '')
        driver_tla = driver_data.get('driver_tla', '???')
        
        if best_lap_time and best_lap_time.strip():
            # 轉換為秒數進行比較 (格式: "1:23.456")
            try:
                if ':' in best_lap_time:
                    parts = best_lap_time.split(':')
                    minutes = int(parts[0])
                    seconds = float(parts[1])
                    total_seconds = minutes * 60 + seconds
                else:
                    total_seconds = float(best_lap_time)
                
                print(f"  {driver_tla} ({driver_num}): {best_lap_time} = {total_seconds:.3f} 秒")
                
                if total_seconds < fastest_best_lap_seconds:
                    fastest_best_lap_seconds = total_seconds
                    fastest_best_lap_time = best_lap_time
                    print(f"    ✅ 目前最快!")
                    
            except (ValueError, IndexError) as e:
                print(f"  {driver_tla} ({driver_num}): {best_lap_time} - 解析錯誤: {e}")
        else:
            print(f"  {driver_tla} ({driver_num}): 無圈時")
    
    print(f"\n{'='*80}")
    print(f"✅ 全場最快圈速: {fastest_best_lap_time} ({fastest_best_lap_seconds:.3f} 秒)")
    print(f"{'='*80}\n")
    
    # 驗證每位車手是否應該顯示紫色背景
    print("檢查每位車手的顯示顏色:")
    for driver_num, driver_data in test_drivers.items():
        best_lap_time = driver_data.get('best_lap_time', '')
        driver_tla = driver_data.get('driver_tla', '???')
        
        is_fastest_overall = (
            best_lap_time 
            and best_lap_time.strip() 
            and best_lap_time == fastest_best_lap_time
        )
        
        if is_fastest_overall:
            print(f"  🟣 {driver_tla} ({driver_num}): {best_lap_time} - 深紫色背景 #663399")
        elif best_lap_time:
            print(f"  ⚪ {driver_tla} ({driver_num}): {best_lap_time} - 正常白色文字")
        else:
            print(f"  ⚫ {driver_tla} ({driver_num}): 無圈時 - 空白")
    
    print("\n✅ 邏輯測試完成!")
    print("預期: 只有 LEC (16) 應該顯示深紫色背景")

if __name__ == "__main__":
    test_fastest_lap_logic()
