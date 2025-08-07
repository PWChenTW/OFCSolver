#!/usr/bin/env python3
"""
Demo API Server - 繞過數據庫初始化的簡化版本
演示 TASK-015 REST API 功能
"""

import logging
import sys
from typing import Optional

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# Import API routers
from src.infrastructure.web.api.game_controller import router as game_router
from src.infrastructure.web.api.analysis_controller import router as analysis_router
from src.infrastructure.web.api.training_controller import router as training_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def create_demo_app() -> FastAPI:
    """
    創建演示版應用 - 無數據庫依賴
    """
    app = FastAPI(
        title="OFC Solver API - Demo",
        description="Open Face Chinese Poker Solver REST API (Demo Version)",
        version="0.1.0-demo",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Demo: Allow all origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Include API routers
    app.include_router(game_router, prefix="/api/v1/games", tags=["games"])
    app.include_router(analysis_router, prefix="/api/v1/analysis", tags=["analysis"])
    app.include_router(training_router, prefix="/api/v1/training", tags=["training"])

    # Root endpoint
    @app.get("/")
    async def root():
        """根端點 - API 資訊"""
        return {
            "name": "OFC Solver API - Demo",
            "version": "0.1.0-demo",
            "status": "active",
            "environment": "demo",
            "docs": "/api/docs",
            "features": {
                "games": "✅ Game Management (8 endpoints)",
                "analysis": "✅ Strategy Analysis (6 endpoints)",
                "training": "✅ Training System (8 endpoints)",
                "total_endpoints": 22
            },
            "note": "Demo version - bypasses database connections"
        }

    # Health check
    @app.get("/health")
    async def health_check():
        """健康檢查"""
        return {
            "service": "ofc-solver-api",
            "status": "healthy",
            "version": "0.1.0-demo",
            "endpoints_available": 22,
            "database": "bypassed (demo mode)"
        }

    # API info endpoint
    @app.get("/api/v1")
    async def api_info():
        """API 版本資訊"""
        return {
            "version": "v1",
            "endpoints": {
                "games": "/api/v1/games",
                "analysis": "/api/v1/analysis",
                "training": "/api/v1/training"
            },
            "authentication": "disabled (demo mode)",
            "rate_limiting": "disabled (demo mode)",
            "features": {
                "game_management": "8 endpoints",
                "strategy_analysis": "6 endpoints", 
                "training_system": "8 endpoints"
            }
        }

    return app


def run_demo_server():
    """運行演示服務器"""
    
    app = create_demo_app()
    
    logger.info("🚀 Starting OFC Solver Demo API Server...")
    logger.info("📚 API Documentation: http://localhost:8001/api/docs")
    logger.info("🔍 Alternative docs: http://localhost:8001/api/redoc")
    logger.info("❤️  Health check: http://localhost:8001/health")
    logger.info("🎯 22 REST API endpoints available!")
    
    # Start server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info",
        access_log=True,
        reload=False,  # Disable reload for demo
    )


if __name__ == "__main__":
    run_demo_server()