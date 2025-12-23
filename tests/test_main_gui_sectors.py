"""
測試主 GUI 中 Historical Track Map 的 Sector 邊界顯示

目的：驗證在主 GUI 中打開 Historical Track Map (Brazil) 時，
     Sector 邊界 (S1/S2/S3) 是否正確顯示
"""
import sys
import json
from PyQt5.QtWidgets import QApplication

def test_sector_boundaries_in_main_gui():
    """測試主 GUI 中的 Sector 邊界顯示設定"""
    
    print("=" * 80)
    print("🧪 測試主 GUI Historical Track Map - Sector 邊界顯示")
    print("=" * 80)
    
    # 1. 驗證 JSON 數據存在
    print("\n[步驟 1] 檢查 JSON 數據...")
    json_path = "json/historical_flags_Brazil_2022-2025.json"
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        sector_boundaries = data.get('data', {}).get('sector_boundaries', [])
        print(f"✅ JSON 數據存在")
        print(f"   Sector 邊界數量: {len(sector_boundaries)}")
        for boundary in sector_boundaries:
            print(f"   - {boundary.get('name')}: {boundary.get('distance_m'):.1f}m")
    except Exception as e:
        print(f"❌ 無法載入 JSON: {e}")
        return False
    
    # 2. 測試 TrackMapWidget 的初始設定
    print("\n[步驟 2] 檢查 TrackMapWidget 初始設定...")
    try:
        from modules.gui.track_analysis.track_map_widget import TrackMapWidget
        
        app = QApplication(sys.argv)
        widget = TrackMapWidget()
        
        # 檢查屬性初始值
        print(f"✅ TrackMapWidget 創建成功")
        print(f"   show_sector_boundaries 初始值: {widget.show_sector_boundaries}")
        print(f"   sector_boundaries 初始長度: {len(widget.sector_boundaries)}")
        
        if not widget.show_sector_boundaries:
            print(f"⚠️  WARNING: show_sector_boundaries 預設為 False！")
            return False
            
    except Exception as e:
        print(f"❌ TrackMapWidget 創建失敗: {e}")
        return False
    
    # 3. 測試數據載入後的狀態
    print("\n[步驟 3] 測試數據載入...")
    try:
        # 模擬主 GUI 的數據載入流程
        track_data = data.get('data', {})
        success = widget.load_track_data(track_data)
        
        print(f"   load_track_data 結果: {success}")
        print(f"   sector_boundaries 載入後長度: {len(widget.sector_boundaries)}")
        print(f"   show_sector_boundaries 載入後狀態: {widget.show_sector_boundaries}")
        
        if len(widget.sector_boundaries) == 0:
            print(f"❌ ERROR: Sector 邊界未載入！")
            return False
            
        if not widget.show_sector_boundaries:
            print(f"⚠️  WARNING: show_sector_boundaries 在載入後變為 False！")
            return False
            
    except Exception as e:
        print(f"❌ 數據載入失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. 測試 set_sector_boundaries() 方法
    print("\n[步驟 4] 測試 set_sector_boundaries() 方法...")
    try:
        widget.set_sector_boundaries(sector_boundaries)
        
        print(f"   set_sector_boundaries 調用成功")
        print(f"   sector_boundaries 長度: {len(widget.sector_boundaries)}")
        
        # 強制啟用顯示（模擬 MDI 的設定）
        widget.show_sector_boundaries = True
        print(f"   強制設定 show_sector_boundaries=True")
        print(f"   最終 show_sector_boundaries 狀態: {widget.show_sector_boundaries}")
        
    except Exception as e:
        print(f"❌ set_sector_boundaries 調用失敗: {e}")
        return False
    
    # 5. 驗證 paintEvent 檢查條件
    print("\n[步驟 5] 驗證 paintEvent 檢查條件...")
    condition_check = widget.show_sector_boundaries and widget.sector_boundaries
    print(f"   paintEvent 條件: show_sector_boundaries={widget.show_sector_boundaries} AND sector_boundaries={len(widget.sector_boundaries) > 0}")
    print(f"   條件結果: {condition_check}")
    
    if not condition_check:
        print(f"❌ ERROR: paintEvent 條件不滿足，Sector 邊界不會被繪製！")
        return False
    
    print("\n" + "=" * 80)
    print("✅ 所有測試通過！")
    print("=" * 80)
    print("\n📋 預期行為：")
    print("   1. 打開主 GUI: python f1t_gui_main.py")
    print("   2. 選擇 Historical Track Map → Brazil 2024")
    print("   3. 應該看到賽道上有 3 條橘紅色虛線 (S1/S2/S3)")
    print("   4. Console 應顯示:")
    print("      [TRACK_MAP] ✅ 成功載入 3 個 Sector 邊界")
    print("      [HISTORICAL_TRACK_MAP_MDI] ✅ 已設置 show_sector_boundaries=True")
    print("      [TRACK_MAP] paintEvent: 準備繪製 3 個 Sector 邊界")
    print("\n如果沒有顯示，請檢查 Console 輸出尋找錯誤訊息。")
    
    return True

if __name__ == "__main__":
    success = test_sector_boundaries_in_main_gui()
    sys.exit(0 if success else 1)
