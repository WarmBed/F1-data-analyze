#!/usr/bin/env python3
"""
圈速分析連動模組
統一管理所有圈速分析相關的連動功能
"""

# 連動混合類
from .linkage_mixin import (
    LapAnalysisLinkageMixin,
    LapAnalysisLinkageDrawingMixin
)

# 連動管理器
from .linkage_manager import (
    LinkageManager,
    linkage_manager
)

# 連動UI組件
from .linkage_ui import (
    LinkageButton,
    LinkageStatusIndicator,
    LinkageControlPanel,
    LinkageToolBar,
    create_linkage_button,
    create_linkage_toolbar
)

__all__ = [
    # 混合類
    'LapAnalysisLinkageMixin',
    'LapAnalysisLinkageDrawingMixin',
    
    # 管理器
    'LinkageManager',
    'linkage_manager',
    
    # UI組件
    'LinkageButton',
    'LinkageStatusIndicator', 
    'LinkageControlPanel',
    'LinkageToolBar',
    'create_linkage_button',
    'create_linkage_toolbar'
]

# 版本信息
__version__ = '1.0.0'
__author__ = 'F1T Team'
__description__ = '統一的圈速分析連動功能模組'
