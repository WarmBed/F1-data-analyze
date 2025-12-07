#!/usr/bin/env python3
"""
F1 Analysis API 路由模組
包含所有 API 路由的集中管理

版本: 2.0 (重構版)
作者: F1 Analysis Team
"""

from fastapi import APIRouter
from . import analysis, cache, config, system

# 創建主路由器
api_router = APIRouter(prefix="/api/v2")

# 包含所有子路由
api_router.include_router(analysis.router)
api_router.include_router(cache.router)
api_router.include_router(config.router)
api_router.include_router(system.router)

# 導出路由器供主應用程式使用
__all__ = ["api_router", "analysis", "cache", "config", "system"]
