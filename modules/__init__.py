"""
F1 Analysis CLI Modules - 統一映射器版
模組化F1分析系統 - 使用統一函數映射器
"""

__version__ = "6.0.0"
__author__ = "F1 Analysis Team"

# 導入核心模組
from .function_mapper import F1AnalysisFunctionMapper
from .compatible_data_loader import CompatibleF1DataLoader
from .compatible_f1_analysis_instance import create_f1_analysis_instance

# 導入基礎模組 (如果存在)
try:
    from .base import F1AnalysisBase
except ImportError:
    F1AnalysisBase = None

# 導入主要分析模組
try:
    from .rain_intensity_analyzer_json import run_rain_intensity_analysis_json
except ImportError:
    run_rain_intensity_analysis_json = None

try:
    from .accident_analysis_complete import run_accident_analysis_json
except ImportError:
    run_accident_analysis_json = None

try:
    from .pitstop_analysis_complete import run_pitstop_analysis_json
except ImportError:
    run_pitstop_analysis_json = None

try:
    from .single_driver_analysis import run_single_driver_analysis
except ImportError:
    run_single_driver_analysis = None

try:
    from .driver_comparison_advanced import run_driver_comparison_json
except ImportError:
    run_driver_comparison_json = None

try:
    from .single_driver_analysis import run_single_driver_comprehensive_analysis
except ImportError:
    run_single_driver_comprehensive_analysis = None

__all__ = [
    'F1AnalysisFunctionMapper',
    'CompatibleF1DataLoader', 
    'create_f1_analysis_instance',
    'F1AnalysisBase',
    'run_rain_intensity_analysis_json',
    'run_accident_analysis_json',
    'run_pitstop_analysis_json',
    'run_single_driver_analysis',
    'run_driver_comparison_json',
    'run_single_driver_comprehensive_analysis'
]
