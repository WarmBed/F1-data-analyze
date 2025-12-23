#!/usr/bin/env python3
"""
F1T 預載畫面完整測試腳本
Complete Splash Screen Test Suite

測試階段：
1. Import 測試 - 驗證所有類別可正確導入
2. 創建測試 - 驗證 5 個版本都能正確創建
3. 方法驗證 - 驗證所有必要方法存在
4. 視覺測試 - 依序展示 5 個版本（需要視覺確認）
"""

import sys
import traceback
from pathlib import Path

# 添加專案根目錄
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# ⚠️ 必須在導入 Qt 組件前初始化 QApplication
from PyQt5.QtWidgets import QApplication
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

print("=" * 80)
print("F1T 預載畫面完整測試")
print("=" * 80)
print()

test_results = []


# ========================================
# 測試 1: Import 測試
# ========================================
def test_import():
    """測試 1: 導入所有 Splash Screen 類別"""
    print("測試 1: Import 測試")
    print("-" * 80)
    
    try:
        from modules.gui.splash_screen import (
            BaseSplashScreen,
            SplashScreenV1_Racing,
            SplashScreenV2_Minimal,
            SplashScreenV3_Cyber,
            SplashScreenV4_Professional,
            SplashScreenV5_Track,
            create_splash_screen,
        )
        
        print("✅ BaseSplashScreen 導入成功")
        print("✅ SplashScreenV1_Racing 導入成功")
        print("✅ SplashScreenV2_Minimal 導入成功")
        print("✅ SplashScreenV3_Cyber 導入成功")
        print("✅ SplashScreenV4_Professional 導入成功")
        print("✅ SplashScreenV5_Track 導入成功")
        print("✅ create_splash_screen 工廠函數導入成功")
        
        test_results.append(("Import 測試", True, ""))
        return True
        
    except Exception as e:
        print(f"❌ Import 失敗: {e}")
        traceback.print_exc()
        test_results.append(("Import 測試", False, str(e)))
        return False


# ========================================
# 測試 2: 基類方法驗證
# ========================================
def test_base_class_methods():
    """測試 2: 驗證基類方法"""
    print("\n測試 2: 基類方法驗證")
    print("-" * 80)
    
    try:
        from modules.gui.splash_screen import BaseSplashScreen
        
        required_methods = [
            '__init__',
            'set_progress',
            'drawContents',
            'paintEvent',
            'closeEvent',
        ]
        
        required_attributes = [
            'progress_updated',  # pyqtSignal
        ]
        
        print("檢查必要方法:")
        all_methods_exist = True
        for method in required_methods:
            exists = hasattr(BaseSplashScreen, method)
            status = "✅" if exists else "❌"
            print(f"  {status} {method}")
            if not exists:
                all_methods_exist = False
        
        print("\n檢查必要屬性:")
        for attr in required_attributes:
            exists = hasattr(BaseSplashScreen, attr)
            status = "✅" if exists else "❌"
            print(f"  {status} {attr}")
            if not exists:
                all_methods_exist = False
        
        if all_methods_exist:
            print("\n✅ 所有必要方法和屬性都存在")
            test_results.append(("基類方法驗證", True, ""))
            return True
        else:
            print("\n❌ 部分方法或屬性缺失")
            test_results.append(("基類方法驗證", False, "缺少必要方法或屬性"))
            return False
            
    except Exception as e:
        print(f"❌ 基類方法驗證失敗: {e}")
        traceback.print_exc()
        test_results.append(("基類方法驗證", False, str(e)))
        return False


# ========================================
# 測試 3: 創建所有版本
# ========================================
def test_create_all_versions():
    """測試 3: 創建所有 5 個版本"""
    print("\n測試 3: 創建所有版本")
    print("-" * 80)
    
    try:
        from modules.gui.splash_screen import create_splash_screen
        
        logo_path = project_root / "image" / "logo.png"
        
        if not logo_path.exists():
            print(f"⚠️  Logo 檔案不存在: {logo_path}")
            print("   將使用預設空白畫布")
        
        versions = {
            1: "經典賽車風格 (F1 Red Racing)",
            2: "現代極簡風格 (Minimal Dark)",
            3: "科技未來風格 (Cyber Tech)",
            4: "優雅專業風格 (Professional)",
            5: "動態賽道風格 (Dynamic Track)",
        }
        
        all_created = True
        for version_num, version_name in versions.items():
            try:
                splash = create_splash_screen(version_num, str(logo_path))
                
                # 驗證實例屬性
                assert hasattr(splash, 'width'), f"版本 {version_num} 缺少 width 屬性"
                assert hasattr(splash, 'height'), f"版本 {version_num} 缺少 height 屬性"
                assert hasattr(splash, 'progress'), f"版本 {version_num} 缺少 progress 屬性"
                assert hasattr(splash, 'message'), f"版本 {version_num} 缺少 message 屬性"
                assert hasattr(splash, 'version'), f"版本 {version_num} 缺少 version 屬性"
                
                # 測試 set_progress 方法
                splash.set_progress(50, "測試訊息")
                assert splash.progress == 50, f"版本 {version_num} 進度設置失敗"
                assert splash.message == "測試訊息", f"版本 {version_num} 訊息設置失敗"
                
                print(f"✅ 版本 {version_num}: {version_name} - 創建成功")
                
                # 清理
                splash.close()
                splash.deleteLater()
                
            except Exception as e:
                print(f"❌ 版本 {version_num}: {version_name} - 創建失敗: {e}")
                all_created = False
        
        if all_created:
            print("\n✅ 所有 5 個版本都創建成功")
            test_results.append(("創建所有版本", True, ""))
            return True
        else:
            print("\n❌ 部分版本創建失敗")
            test_results.append(("創建所有版本", False, "部分版本創建失敗"))
            return False
            
    except Exception as e:
        print(f"❌ 創建版本測試失敗: {e}")
        traceback.print_exc()
        test_results.append(("創建所有版本", False, str(e)))
        return False


# ========================================
# 測試 4: 進度設置邊界測試
# ========================================
def test_progress_bounds():
    """測試 4: 進度設置邊界測試"""
    print("\n測試 4: 進度設置邊界測試")
    print("-" * 80)
    
    try:
        from modules.gui.splash_screen import create_splash_screen
        
        splash = create_splash_screen(1)
        
        # 測試正常範圍
        splash.set_progress(0)
        assert splash.progress == 0, "進度 0 設置失敗"
        print("✅ 進度 0% 設置正確")
        
        splash.set_progress(50)
        assert splash.progress == 50, "進度 50 設置失敗"
        print("✅ 進度 50% 設置正確")
        
        splash.set_progress(100)
        assert splash.progress == 100, "進度 100 設置失敗"
        print("✅ 進度 100% 設置正確")
        
        # 測試超出範圍（應該自動修正）
        splash.set_progress(150)
        assert splash.progress == 100, "進度上限修正失敗"
        print("✅ 進度超過 100% 自動修正為 100%")
        
        splash.set_progress(-10)
        assert splash.progress == 0, "進度下限修正失敗"
        print("✅ 進度低於 0% 自動修正為 0%")
        
        splash.close()
        splash.deleteLater()
        
        print("\n✅ 進度邊界測試通過")
        test_results.append(("進度邊界測試", True, ""))
        return True
        
    except Exception as e:
        print(f"❌ 進度邊界測試失敗: {e}")
        traceback.print_exc()
        test_results.append(("進度邊界測試", False, str(e)))
        return False


# ========================================
# 測試 5: 視覺測試（需要 GUI）
# ========================================
def test_visual_display():
    """測試 5: 視覺測試 - 依序展示 5 個版本"""
    print("\n測試 5: 視覺測試")
    print("-" * 80)
    print("即將依序展示 5 個版本的預載畫面")
    print("每個版本將自動展示 5 秒後關閉")
    print()
    
    try:
        from PyQt5.QtCore import QTimer
        from modules.gui.splash_screen import create_splash_screen
        
        versions = {
            1: "經典賽車風格 (F1 Red Racing)",
            2: "現代極簡風格 (Minimal Dark)",
            3: "科技未來風格 (Cyber Tech)",
            4: "優雅專業風格 (Professional)",
            5: "動態賽道風格 (Dynamic Track)",
        }
        
        current_version = [1]  # 使用列表以便在閉包中修改
        current_splash = [None]
        
        def show_next_version():
            """顯示下一個版本"""
            # 關閉當前 splash
            if current_splash[0]:
                current_splash[0].close()
                current_splash[0].deleteLater()
                current_splash[0] = None
            
            version = current_version[0]
            
            if version <= 5:
                print(f"\n{'='*60}")
                print(f"展示版本 {version}: {versions[version]}")
                print(f"{'='*60}")
                
                # 創建新的 splash
                splash = create_splash_screen(version)
                current_splash[0] = splash
                splash.show()
                
                # 模擬進度
                progress_steps = [
                    (20, f"Loading {versions[version]}..."),
                    (40, "Initializing components..."),
                    (60, "Setting up display..."),
                    (80, "Finalizing..."),
                    (100, "Complete!"),
                ]
                
                def update_progress():
                    if not hasattr(update_progress, 'index'):
                        update_progress.index = 0
                    
                    if update_progress.index < len(progress_steps):
                        progress, message = progress_steps[update_progress.index]
                        if current_splash[0]:
                            current_splash[0].set_progress(progress, message)
                        update_progress.index += 1
                    else:
                        progress_timer.stop()
                
                # 進度定時器
                progress_timer = QTimer()
                progress_timer.timeout.connect(update_progress)
                progress_timer.start(800)  # 每 800ms 更新
                
                # 5 秒後顯示下一個版本
                current_version[0] += 1
                QTimer.singleShot(5000, show_next_version)
                
            else:
                # 所有版本展示完畢
                print("\n" + "="*60)
                print("✅ 所有版本視覺測試完成")
                print("="*60)
                test_results.append(("視覺測試", True, ""))
                app.quit()
        
        # 開始展示
        show_next_version()
        
        # 執行應用程式
        app.exec_()
        
        return True
        
    except Exception as e:
        print(f"❌ 視覺測試失敗: {e}")
        traceback.print_exc()
        test_results.append(("視覺測試", False, str(e)))
        return False


# ========================================
# 主測試函數
# ========================================
def main():
    """執行所有測試"""
    print("開始執行測試...\n")
    
    # 階段 1: Import 和方法驗證（無需 GUI）
    test_import()
    test_base_class_methods()
    test_create_all_versions()
    test_progress_bounds()
    
    # 輸出階段 1 結果
    print("\n" + "="*80)
    print("階段 1 測試結果（無需 GUI）")
    print("="*80)
    
    passed = sum(1 for _, success, _ in test_results if success)
    failed = sum(1 for _, success, _ in test_results if not success)
    
    for test_name, success, error in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:<10} {test_name}")
        if error:
            print(f"           錯誤: {error}")
    
    print(f"\n總計: {passed} 通過, {failed} 失敗")
    
    # 如果階段 1 全部通過，執行階段 2（需要 GUI）
    if failed == 0:
        print("\n" + "="*80)
        print("階段 1 全部通過！")
        print("="*80)
        print("\n準備進入階段 2: 視覺測試（需要 GUI）")
        
        response = input("\n是否要執行視覺測試？(y/n): ").strip().lower()
        
        if response == 'y':
            test_visual_display()
            
            # 輸出最終結果
            print("\n" + "="*80)
            print("最終測試結果")
            print("="*80)
            
            passed = sum(1 for _, success, _ in test_results if success)
            failed = sum(1 for _, success, _ in test_results if not success)
            
            for test_name, success, error in test_results:
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"{status:<10} {test_name}")
                if error:
                    print(f"           錯誤: {error}")
            
            print(f"\n總計: {passed} 通過, {failed} 失敗")
            
            if failed == 0:
                print("\n" + "="*80)
                print("🎉 所有測試通過！預載畫面功能完全正常！")
                print("="*80)
                return 0
            else:
                print("\n" + "="*80)
                print("⚠️  部分測試失敗，請檢查上述錯誤訊息")
                print("="*80)
                return 1
        else:
            print("\n跳過視覺測試")
            print("階段 1 測試完成，程式碼功能正常")
            return 0
    else:
        print("\n" + "="*80)
        print("❌ 階段 1 測試失敗，請先修正錯誤")
        print("="*80)
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 測試過程發生未預期錯誤: {e}")
        traceback.print_exc()
        sys.exit(1)
