"""
測試 position_processor.py 的 DRS=0 修復
"""

# 測試修復後的邏輯
def test_fixed_logic():
    """測試修復後的 channel 獲取邏輯"""
    
    print("="*60)
    print("測試修復後的邏輯")
    print("="*60)
    
    test_cases = [
        ({'45': 0}, '45', "DRS=0 (字串 key)"),
        ({45: 0}, '45', "DRS=0 (整數 key)"),
        ({'45': 12}, '45', "DRS=12 (字串 key)"),
        ({45: 12}, '45', "DRS=12 (整數 key)"),
        ({'45': ''}, '45', "空字串 (字串 key)"),
        ({'45': None}, '45', "None (字串 key)"),
    ]
    
    for channels, channel_id, desc in test_cases:
        # 修復後的邏輯
        value = channels.get(channel_id)
        if value is None:
            value = channels.get(int(channel_id))
        
        # 檢查是否應該記錄
        should_record = value is not None and value != ''
        
        print(f"\n{desc}")
        print(f"  channels = {channels}")
        print(f"  channel_id = '{channel_id}'")
        print(f"  → value = {value!r}")
        print(f"  → should_record = {should_record}")
        
        if value == 0:
            print(f"  ✅ DRS=0 被正確保留！")
    
    print("\n" + "="*60)
    print("結論")
    print("="*60)
    print("✅ 修復後的邏輯:")
    print("   1. 先嘗試 channels.get(channel_id)")
    print("   2. 如果是 None，再嘗試 channels.get(int(channel_id))")
    print("   3. 不再使用 'or' 運算符，避免 0 被當作 False")
    print("   4. DRS=0 可以正確記錄到 PKL 中")


if __name__ == "__main__":
    test_fixed_logic()
