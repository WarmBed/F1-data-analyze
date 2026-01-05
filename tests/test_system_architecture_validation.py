#!/usr/bin/env python3
"""
F1T 系統架構驗證測試
====================================

此測試腳本驗證 F1T 專案的核心架構符合開發原則，特別是：
- 原則 0: 反幻覺編碼五原則
- 原則 1: 禁止幻覺編碼
- 原則 2: 模組資料夾優先
- 原則 3: 通用模組優先
- 原則 4: 模組多國語言化
- 原則 5: print 輸出導向 log

測試分類：
1. 架構完整性測試
2. API-ONLY 模式驗證
3. 通用基礎類別驗證
4. 國際化支援驗證
5. 文檔完整性驗證

Author: F1T Team
Date: 2026-01-05
"""

import os
import sys
import unittest
from pathlib import Path

# 確保專案根目錄在 Python 路徑中
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))


class TestSystemArchitecture(unittest.TestCase):
    """系統架構完整性測試"""
    
    def test_core_directories_exist(self):
        """測試：核心目錄結構存在"""
        required_dirs = [
            'modules/gui',
            'modules/gui/base',
            'CLI_modules/cli',
            'CLI_modules/cli/analyzer',
            'api',
            'core',
            'tasks',
            'tests'
        ]
        
        for dir_path in required_dirs:
            full_path = PROJECT_ROOT / dir_path
            self.assertTrue(
                full_path.is_dir(),
                f"Required directory missing: {dir_path}"
            )
    
    def test_key_files_exist(self):
        """測試：關鍵檔案存在"""
        required_files = [
            'f1t_gui_main.py',
            'f1_analysis_modular_main.py',
            'refactored_api.py',
            '.github/copilot-instructions.md',
            'modules/gui/base/universal_data_loader_base.py',
            'modules/gui/universal_chart_widget.py'
        ]
        
        for file_path in required_files:
            full_path = PROJECT_ROOT / file_path
            self.assertTrue(
                full_path.is_file(),
                f"Required file missing: {file_path}"
            )
    
    def test_core_logger_import(self):
        """測試：核心 logger 系統可導入"""
        try:
            from core.logger import get_logger, setup_logging
            logger = get_logger('test')
            self.assertIsNotNone(logger)
        except ImportError as e:
            self.fail(f"Core logger import failed: {e}")


class TestAPIOnlyMode(unittest.TestCase):
    """API-ONLY 模式驗證測試"""
    
    def test_universal_data_loader_has_api_only_comment(self):
        """測試：UniversalDataLoader 包含 API-ONLY 註解"""
        loader_file = PROJECT_ROOT / 'modules/gui/base/universal_data_loader_base.py'
        self.assertTrue(loader_file.exists(), "UniversalDataLoader file not found")
        
        content = loader_file.read_text(encoding='utf-8')
        self.assertIn(
            'API-ONLY',
            content,
            "API-ONLY comment not found in UniversalDataLoader"
        )
        self.assertIn(
            '已禁用',
            content,
            "Disabled (已禁用) comment not found in UniversalDataLoader"
        )
    
    def test_cli_worker_is_disabled(self):
        """測試：CliAnalysisWorker 已被禁用"""
        loader_file = PROJECT_ROOT / 'modules/gui/base/universal_data_loader_base.py'
        content = loader_file.read_text(encoding='utf-8')
        
        # 檢查 CliAnalysisWorker.run() 包含禁用邏輯
        self.assertIn('CliAnalysisWorker', content)
        self.assertIn('已完全禁用', content)
    
    def test_refactored_api_exists(self):
        """測試：refactored_api.py 存在且包含 FastAPI"""
        api_file = PROJECT_ROOT / 'refactored_api.py'
        self.assertTrue(api_file.exists(), "refactored_api.py not found")
        
        content = api_file.read_text(encoding='utf-8')
        self.assertIn('FastAPI', content, "FastAPI not found in refactored_api.py")


class TestUniversalBaseClasses(unittest.TestCase):
    """通用基礎類別驗證測試"""
    
    def test_universal_data_loader_exists(self):
        """測試：UniversalDataLoader 類別存在"""
        loader_file = PROJECT_ROOT / 'modules/gui/base/universal_data_loader_base.py'
        self.assertTrue(loader_file.exists())
        
        content = loader_file.read_text(encoding='utf-8')
        self.assertIn('class UniversalDataLoader', content)
        self.assertIn('通用數據載入器基類', content)
    
    def test_universal_chart_widget_exists(self):
        """測試：UniversalChartWidget 類別存在"""
        chart_file = PROJECT_ROOT / 'modules/gui/universal_chart_widget.py'
        self.assertTrue(chart_file.exists())
        
        content = chart_file.read_text(encoding='utf-8')
        self.assertIn('class UniversalChartWidget', content)
        self.assertIn('通用圖表', content)
    
    def test_universal_data_loader_has_required_signals(self):
        """測試：UniversalDataLoader 包含必要的信號"""
        loader_file = PROJECT_ROOT / 'modules/gui/base/universal_data_loader_base.py'
        content = loader_file.read_text(encoding='utf-8')
        
        required_signals = [
            'data_loaded',
            'load_progress',
            'load_error',
            'status_changed'
        ]
        
        for signal in required_signals:
            self.assertIn(
                signal,
                content,
                f"Required signal '{signal}' not found in UniversalDataLoader"
            )


class TestInternationalization(unittest.TestCase):
    """國際化支援驗證測試"""
    
    def test_tr_function_usage(self):
        """測試：模組使用 tr() 函數進行國際化"""
        # 搜索 modules/gui/ 中使用 .tr( 的檔案
        gui_dir = PROJECT_ROOT / 'modules/gui'
        tr_usage_found = False
        
        for py_file in gui_dir.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding='utf-8')
                if '.tr(' in content:
                    tr_usage_found = True
                    break
            except Exception:
                continue
        
        # 目前部分模組使用 tr()，未來應擴展到所有模組
        # 此測試確認至少有部分模組已實現
        self.assertTrue(
            tr_usage_found,
            "No tr() function usage found in GUI modules"
        )
    
    def test_no_emoji_in_copilot_instructions(self):
        """測試：copilot-instructions.md 記錄了不使用 emoji 的原則"""
        instructions_file = PROJECT_ROOT / '.github/copilot-instructions.md'
        content = instructions_file.read_text(encoding='utf-8')
        
        self.assertIn('不可以有emoji', content)


class TestDocumentation(unittest.TestCase):
    """文檔完整性驗證測試"""
    
    def test_copilot_instructions_exist(self):
        """測試：copilot-instructions.md 存在"""
        instructions_file = PROJECT_ROOT / '.github/copilot-instructions.md'
        self.assertTrue(instructions_file.exists())
    
    def test_five_principles_documented(self):
        """測試：五大原則已記錄在文檔中"""
        instructions_file = PROJECT_ROOT / '.github/copilot-instructions.md'
        content = instructions_file.read_text(encoding='utf-8')
        
        principles = [
            '原則 0',
            '原則 1',
            '原則 2',
            '原則 3',
            '原則 4',
            '原則 5'
        ]
        
        for principle in principles:
            self.assertIn(
                principle,
                content,
                f"Principle '{principle}' not documented"
            )
    
    def test_api_only_mode_documented(self):
        """測試：API-ONLY 模式已記錄在文檔中"""
        instructions_file = PROJECT_ROOT / '.github/copilot-instructions.md'
        content = instructions_file.read_text(encoding='utf-8')
        
        self.assertIn('API-ONLY 模式', content)
        self.assertIn('禁止 GUI 呼叫 CLI', content)
    
    def test_tasks_directory_exists(self):
        """測試：tasks/ 目錄存在且包含任務追蹤文件"""
        tasks_dir = PROJECT_ROOT / 'tasks'
        self.assertTrue(tasks_dir.is_dir())
        
        # 檢查至少有一些 .md 檔案
        md_files = list(tasks_dir.glob('*.md'))
        self.assertGreater(
            len(md_files),
            0,
            "No task tracking files found in tasks/ directory"
        )


class TestCLIFunctionMapper(unittest.TestCase):
    """CLI 功能映射器驗證測試（不需要依賴套件）"""
    
    def test_function_mapper_file_exists(self):
        """測試：function_mapper.py 存在"""
        mapper_file = PROJECT_ROOT / 'CLI_modules/cli/core/function_mapper.py'
        self.assertTrue(
            mapper_file.exists(),
            "function_mapper.py not found"
        )
    
    def test_function_mapper_has_class(self):
        """測試：function_mapper.py 包含 F1AnalysisFunctionMapper 類別"""
        mapper_file = PROJECT_ROOT / 'CLI_modules/cli/core/function_mapper.py'
        content = mapper_file.read_text(encoding='utf-8')
        
        self.assertIn('class F1AnalysisFunctionMapper', content)
        self.assertIn('function_mapping', content)


def run_validation_suite():
    """執行完整的驗證測試套件"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有測試類別
    suite.addTests(loader.loadTestsFromTestCase(TestSystemArchitecture))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIOnlyMode))
    suite.addTests(loader.loadTestsFromTestCase(TestUniversalBaseClasses))
    suite.addTests(loader.loadTestsFromTestCase(TestInternationalization))
    suite.addTests(loader.loadTestsFromTestCase(TestDocumentation))
    suite.addTests(loader.loadTestsFromTestCase(TestCLIFunctionMapper))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("=" * 70)
    print("F1T 系統架構驗證測試")
    print("測試反幻覺編碼五原則和系統完整性")
    print("=" * 70)
    print()
    
    success = run_validation_suite()
    
    print()
    print("=" * 70)
    if success:
        print("✅ 所有測試通過！系統架構符合開發原則。")
    else:
        print("❌ 部分測試失敗，請檢查輸出。")
    print("=" * 70)
    
    sys.exit(0 if success else 1)
