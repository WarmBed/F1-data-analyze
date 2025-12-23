from PyQt5.QtWidgets import QApplication, QMenu
from windows.managers.live_timing_manager import LiveTimingManager
import sys

app = QApplication(sys.argv)

class FakeMainWindow:
    pass

main_win = FakeMainWindow()
ltm = LiveTimingManager(main_win)

# 檢查 MODULES 配置
print('=== MODULES 配置 ===')
print(f'throttle_history in MODULES: {"throttle_history" in ltm.MODULES}')
if 'throttle_history' in ltm.MODULES:
    print(f'throttle_history config: {ltm.MODULES["throttle_history"]}')

# 創建測試選單
menu = QMenu()
print('\n=== 調用 setup_menu 前 ===')
print(f'Menu actions count: {len(menu.actions())}')

# 調用 setup_menu
ltm.setup_menu(menu)

print('\n=== 調用 setup_menu 後 ===')
print(f'Menu actions count: {len(menu.actions())}')

# 檢查 Lap History 子選單
for action in menu.actions():
    if action.menu() and 'Lap History' in action.text():
        lap_menu = action.menu()
        print(f'\nLap History 子選單項目數: {len(lap_menu.actions())}')
        print('Lap History 子選單內容:')
        for i, lap_action in enumerate(lap_menu.actions()):
            if lap_action.isSeparator():
                print(f'  [{i}] --- (separator) ---')
            else:
                print(f'  [{i}] {lap_action.text()}')
