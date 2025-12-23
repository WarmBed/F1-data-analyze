"""
測試 DRS=0 是否會被 position_processor 的邏輯過濾掉
"""

# 模擬 position_processor.py 第 505 行的邏輯
def test_channel_get_logic():
    """測試 channels.get() or channels.get() 的行為"""
    
    print("="*60)
    print("測試 1: channels.get(channel_id) or channels.get(int(channel_id))")
    print("="*60)
    
    # 測試案例 1: DRS = 0 (字串 key)
    channels_1 = {'45': 0}
    channel_id = '45'
    value = channels_1.get(channel_id) or channels_1.get(int(channel_id))
    print(f"Case 1: channels={channels_1}, channel_id='{channel_id}'")
    print(f"  → value = {value} (type: {type(value).__name__})")
    print(f"  ⚠️  問題：0 被 'or' 運算符當作 False，會再查找 int(channel_id)")
    
    # 測試案例 2: DRS = 0 (整數 key)
    channels_2 = {45: 0}
    channel_id = '45'
    value = channels_2.get(channel_id) or channels_2.get(int(channel_id))
    print(f"\nCase 2: channels={channels_2}, channel_id='{channel_id}'")
    print(f"  → value = {value} (type: {type(value).__name__})")
    print(f"  ⚠️  第一次 get('{channel_id}') 返回 None，第二次 get(45) 返回 0")
    
    # 測試案例 3: DRS = 12 (正常值)
    channels_3 = {'45': 12}
    channel_id = '45'
    value = channels_3.get(channel_id) or channels_3.get(int(channel_id))
    print(f"\nCase 3: channels={channels_3}, channel_id='{channel_id}'")
    print(f"  → value = {value} (type: {type(value).__name__})")
    print(f"  ✅ 正常：12 是 truthy，不會觸發第二個 get()")
    
    # 測試案例 4: 空字串 (應該被過濾)
    channels_4 = {'45': ''}
    channel_id = '45'
    value = channels_4.get(channel_id) or channels_4.get(int(channel_id))
    print(f"\nCase 4: channels={channels_4}, channel_id='{channel_id}'")
    print(f"  → value = {value} (type: {type(value).__name__})")
    print(f"  ⚠️  空字串也被當作 False")
    
    print("\n" + "="*60)
    print("測試 2: 完整的過濾條件")
    print("="*60)
    
    def should_record(value):
        """模擬 position_processor 的條件"""
        return value is not None and value != ''
    
    test_cases = [
        (0, "DRS=0"),
        (1, "DRS=1"),
        (12, "DRS=12"),
        ('', "空字串"),
        (None, "None"),
        ('0', "字串 '0'"),
    ]
    
    for val, desc in test_cases:
        result = should_record(val)
        print(f"{desc:15s} → should_record({val!r:5s}) = {result}")
    
    print("\n" + "="*60)
    print("結論")
    print("="*60)
    print("1. ⚠️  `get(channel_id) or get(int(channel_id))` 會把 0 當作 False")
    print("2. ⚠️  但 DRS=0 在 Live Timing API 中是整數 0，不是字串 '0'")
    print("3. ✅ 條件 `value is not None and value != ''` 不會過濾 0")
    print("4. ❌ 問題可能在：")
    print("   - channels dict 的 key 類型不匹配（'45' vs 45）")
    print("   - 或者 `or` 運算符導致 0 被跳過")
    print("   - 需要改為：value = channels.get(channel_id)")
    print("                if value is None:")
    print("                    value = channels.get(int(channel_id))")


if __name__ == "__main__":
    test_channel_get_logic()
