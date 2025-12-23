"""
F101 起跑反應分析模組
Start Reaction Analysis Module

分析起跑 0-50 km/h, 0-100 km/h 加速時間和首圈位置變化
"""

# 延遲導入避免循環依賴問題
def __getattr__(name):
    """延遲導入模組成員"""
    if name == 'StartReactionDataLoader':
        from .start_reaction_loader import StartReactionDataLoader
        return StartReactionDataLoader
    elif name == 'StartReactionWidget':
        from .start_reaction_widget import StartReactionWidget
        return StartReactionWidget
    elif name in ('StartReactionAnalysisMDI', 'StartReactionMDI'):
        from .start_reaction_mdi import StartReactionAnalysisMDI
        return StartReactionAnalysisMDI
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ['StartReactionAnalysisMDI', 'StartReactionMDI', 'StartReactionWidget', 'StartReactionDataLoader']

