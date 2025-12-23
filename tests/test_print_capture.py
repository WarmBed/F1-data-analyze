"""
測試 print 輸出捕獲
"""

import io
import sys

def test_print_capture():
    print("測試 1: 原始的 print")
    
    # 方法 1: redirect_stdout
    from contextlib import redirect_stdout
    buffer1 = io.StringIO()
    with redirect_stdout(buffer1):
        print("測試 2: redirect_stdout")
    print(f"方法 1 捕獲到: '{buffer1.getvalue()}'")
    
    # 方法 2: 直接替換 sys.stdout
    buffer2 = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buffer2
    print("測試 3: 直接替換 sys.stdout")
    sys.stdout = old_stdout
    print(f"方法 2 捕獲到: '{buffer2.getvalue()}'")
    
    # 測試 objgraph
    try:
        import objgraph
        import gc
        
        buffer3 = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buffer3
        
        gc.collect()
        count = objgraph.count("_DummyThread")
        print(f"DummyThread 數量: {count}")
        
        sys.stdout = old_stdout
        result = buffer3.getvalue()
        print(f"方法 3 (objgraph) 捕獲到: '{result}'")
        
    except Exception as e:
        print(f"測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_print_capture()
