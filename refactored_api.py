#!/usr/bin/env python3
"""
F1 Analysis API Server (Refactored)

Provides a FastAPI application that wraps the CLI analysis entry points and
exposes them over HTTP for the GUI and external clients. This entry script is
intended for local development / debugging and keeps backwards compatibility
with the existing JSON-driven workflow.
"""

from __future__ import annotations

import logging
import os
from typing import Final

import uvicorn
from fastapi import FastAPI

import core.dependency_guard  # noqa: F401  # 確保可選依賴存在
from core.logger import setup_logging, get_logger  # 整合統一日誌系統

from api.middleware.cors import RateLimitMiddleware
from api.middleware.handlers import setup_cors_middleware, setup_custom_middleware
from api.routers import api_router
from api.routers import main as main_routes

API_TITLE: Final[str] = "F1 Analysis API"
API_DESCRIPTION: Final[str] = (
    "Formula 1 telemetry and strategy analysis REST bridge for the modular CLI"
)
API_VERSION: Final[str] = "2.0.0"


def create_app() -> FastAPI:
    """Instantiate and configure the FastAPI application."""
    
    # 🆕 初始化統一的日誌系統 (component="api")
    setup_logging(
        component="api",
        level=os.getenv("F1_LOG_LEVEL", "INFO"),
        patch_print=False,  # API 不需要 patch print
    )
    
    app = FastAPI(
        title=API_TITLE,
        description=API_DESCRIPTION,
        version=API_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Core routers (root/system) and versioned API namespace
    app.include_router(main_routes.router)
    app.include_router(api_router)

    # Middleware stack (logging, error handling, security headers, CORS, rate limit)
    setup_custom_middleware(app)
    setup_cors_middleware(app)
    app.add_middleware(RateLimitMiddleware, calls_per_minute=120)

    # 🔄 初始化賽事事件監控器
    race_monitor = None

    @app.on_event("startup")
    async def _on_startup() -> None:  # pragma: no cover - light side effect
        nonlocal race_monitor
        logger = get_logger(component="api")
        logger.info("🚀 F1 Analysis API v%s 已啟動 | 日誌系統: core.logger (統一配置)", API_VERSION)
        logger.info("📂 日誌檔案: logs/f1_api_YYYY-MM-DD.log")
        logger.info("📊 API 端點: /docs (Swagger), /redoc (ReDoc)")
        
        # 🔄 啟動賽事事件監控器
        try:
            from api.services.race_event_monitor import RaceEventMonitor
            from api.services.simple_analysis_service import SimpleF1AnalysisService
            
            analysis_service = SimpleF1AnalysisService()
            race_monitor = RaceEventMonitor(analysis_service)
            await race_monitor.start()
            
            # 將監控器存儲到 app.state 供其他路由使用
            app.state.race_monitor = race_monitor
            
            logger.info("✅ 賽事事件監控器已啟動")
        except Exception as e:
            logger.error(f"❌ 無法啟動賽事事件監控器: {e}")
            import traceback
            traceback.print_exc()
    
    @app.on_event("shutdown")
    async def _on_shutdown() -> None:  # pragma: no cover - light side effect
        logger = get_logger(component="api")
        logger.info("🛑 F1 Analysis API 正在關閉...")
        
        # 停止賽事事件監控器
        if race_monitor:
            try:
                await race_monitor.stop()
                logger.info("✅ 賽事事件監控器已停止")
            except Exception as e:
                logger.error(f"❌ 停止監控器時發生錯誤: {e}")
        
        logger.info("👋 F1 Analysis API 已關閉")

    return app


app = create_app()


def main() -> None:
    """Run the development server using uvicorn."""

    host = os.getenv("F1_API_HOST", "127.0.0.1")
    port = int(os.getenv("F1_API_PORT", "8000"))
    reload_enabled = os.getenv("F1_API_RELOAD", "0").lower() in {"1", "true", "yes"}

    uvicorn.run(
        "refactored_api:app",
        host=host,
        port=port,
        reload=reload_enabled,
        log_level="info",
        factory=False,
    )


if __name__ == "__main__":
    main()
