"""
測試 logger 的 print patch 如何影響 stdout 捕獲
以及我們的修復方案是否有效
"""
import io
import sys
import builtins

# 模擬 logger 的 print patch
def setup_logger_patch():
    """模擬 core.logger 的 print patch"""
    global _ORIGINAL_PRINT, _PRINT_PATCHED
    
    _ORIGINAL_PRINT = builtins.print
    _PRINT_PATCHED = False
    
    def logged_print(*args, **kwargs):
        file_arg = kwargs.get("file", sys.stdout)
        
        # 關鍵：如果 file 是 sys.stdout，走 logger 路徑
        if file_arg is not None and file_arg is not sys.stdout:
            _ORIGINAL_PRINT(*args, **kwargs)
            return
        
        # 否則記錄到假的 logger（這裡簡化為直接 print）
        sep = kwargs.get("sep", " ")
        message = sep.join(str(arg) for arg in args)
        _ORIGINAL_PRINT(f"[LOGGER] {message}")  # 模擬 logger 輸出
    
    builtins.print = logged_print
    _PRINT_PATCHED = True
    
    return _ORIGINAL_PRINT, _PRINT_PATCHED

print("=" * 60)
print("測試 1: 未 patch 時的 stdout 捕獲（基準）")
print("=" * 60)

code1 = 'print("Hello World")'
buffer1 = io.StringIO()
old_stdout = sys.stdout
sys.stdout = buffer1
exec(code1)
sys.stdout = old_stdout
result1 = buffer1.getvalue()
print(f"✅ 結果: '{result1.strip()}'")
print()

print("=" * 60)
print("測試 2: logger patch 後，不繞過 patch（會失敗）")
print("=" * 60)

_ORIGINAL_PRINT, _PRINT_PATCHED = setup_logger_patch()

code2 = 'print("Hello with logger patch")'
buffer2 = io.StringIO()
old_stdout = sys.stdout
sys.stdout = buffer2  # 替換 stdout
exec(code2)  # ❌ print 會檢測到 file_arg is sys.stdout，走 logger 路徑
sys.stdout = old_stdout
result2 = buffer2.getvalue()
print(f"❌ 結果: '{result2.strip()}'（應該為空）")
print(f"   原因: print 被 patch 後，會檢查 file_arg is sys.stdout")
print(f"   由於 file_arg 默認是新的 sys.stdout（StringIO），判斷為 True")
print(f"   所以走 logger 路徑，不會寫入 buffer")
print()

print("=" * 60)
print("測試 3: 繞過 logger patch（我們的修復方案）")
print("=" * 60)

code3 = 'print("Hello bypassing logger")'
buffer3 = io.StringIO()
old_stdout = sys.stdout
old_print = builtins.print

# 關鍵：恢復原始 print
if _PRINT_PATCHED:
    builtins.print = _ORIGINAL_PRINT

sys.stdout = buffer3
exec(code3)  # ✅ 使用原始 print
sys.stdout = old_stdout
builtins.print = old_print  # 恢復 patch

result3 = buffer3.getvalue()
print(f"✅ 結果: '{result3.strip()}'")
print(f"   成功！通過恢復原始 print，繞過了 logger patch")
print()

print("=" * 60)
print("測試 4: 模擬 objgraph 診斷代碼")
print("=" * 60)

try:
    import objgraph
    code4 = '''
import objgraph, gc
gc.collect()
count = objgraph.count("_DummyThread")
print(f"DummyThread 數量: {count}")
'''
    buffer4 = io.StringIO()
    old_stdout = sys.stdout
    old_print = builtins.print
    
    if _PRINT_PATCHED:
        builtins.print = _ORIGINAL_PRINT
    
    sys.stdout = buffer4
    exec(code4, {'__builtins__': __builtins__, 'objgraph': objgraph, 'gc': __import__('gc')})
    sys.stdout = old_stdout
    builtins.print = old_print
    
    result4 = buffer4.getvalue()
    print(f"✅ 結果: '{result4.strip()}'")
except ImportError:
    print("⚠️ objgraph 未安裝，跳過測試")
print()

print("=" * 60)
print("總結")
print("=" * 60)
print("問題核心：")
print("  core.logger 會 patch builtins.print 為 logged_print")
print("  logged_print 會檢查 file 是否為 sys.stdout")
print("  當我們替換 sys.stdout 為 StringIO 時：")
print("    - file_arg 默認值是新的 sys.stdout（StringIO）")
print("    - 判斷 'file_arg is sys.stdout' 為 True")
print("    - 走 logger 路徑，不寫入 StringIO")
print()
print("解決方案：")
print("  在執行代碼前，臨時恢復 builtins.print = _ORIGINAL_PRINT")
print("  這樣 print 就會正常寫入 StringIO")
print("  執行完成後，再恢復 builtins.print = logged_print")
print("=" * 60)
