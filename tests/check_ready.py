from config.version import APP_VERSION, APP_FULL_TITLE
import os

print("=" * 60)
print("F1T GUI - EXE Build Ready Check")
print("=" * 60)

print("\n[Version]")
print(f"  Version: {APP_VERSION}")
print(f"  Title: {APP_FULL_TITLE}")

print("\n[Files]")
files = [
    "F1T_GUI.spec",
    "pyinstaller_runtime_hook.py",
    "f1t_gui_main.py",
    "image/logo.png",
    "image/logo.ico"
]

all_exist = True
for f in files:
    exists = os.path.exists(f)
    status = "OK" if exists else "MISSING"
    print(f"  {status}: {f}")
    if not exists:
        all_exist = False

print("\n[Result]")
if all_exist:
    print("  ✓ All checks passed!")
    print("  ✓ Ready to build EXE")
    print("\n[Commands]")
    print("  Full:  .\\build_exe.ps1")
    print("  Quick: .\\build_exe_quick.ps1")
else:
    print("  × Some files are missing")
    print("  × Please fix before building")
    
print("=" * 60)
