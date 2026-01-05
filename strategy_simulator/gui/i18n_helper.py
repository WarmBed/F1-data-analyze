#!/usr/bin/env python3
"""
Strategy Simulator - Internationalization Helper

This module provides a lazy-loading tr() function that ensures
the translation system is imported AFTER sys.path is properly configured
by the main entry point.

Author: F1T Team
Date: 2026-01-04
"""

_tr_func = None

def _get_tr():
    """Get translation function with lazy import."""
    global _tr_func
    if _tr_func is None:
        try:
            from core.gui_i18n import tr as _imported_tr
            _tr_func = _imported_tr
        except ImportError:
            def _fallback(key, default=None):
                return default if default else key
            _tr_func = _fallback
    return _tr_func

def tr(key, default=None):
    """
    Translate a key to the current language.
    
    Uses lazy loading to ensure core.gui_i18n is imported
    after sys.path is properly configured.
    
    Args:
        key: Translation key
        default: Fallback value if key not found
        
    Returns:
        Translated string
    """
    return _get_tr()(key, default)
