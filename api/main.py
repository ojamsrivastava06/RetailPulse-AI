from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.config import get_settings
from api.core.exceptions import register_exception_handlers
from api.core.logging import configure_logging
from api.core.middleware import RateLimitMiddleware, RequestContextMiddleware, SecurityHeadersMiddleware
from api.routers import analytics, churn, customer, decision, forecast, health, inventory, reports
from api.schemas.common import APIResponse
from api.utils.response import success_response


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description=(
            "Secure read-only REST API over completed RetailPulse AI artifacts. "
            "The service exposes forecasting, inventory, customer intelligence, churn, "
            "decision intelligence, analytics, and report endpoints without retraining models "
            "or rewriting datasets."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        contact={"name": "RetailPulse – AI-Powered Customer Analytics & Demand Forecasting Platform Team"},

        license_info={"name": "MIT"},
        openapi_tags=[
            {"name": "Health", "description": "Service health, version, and artifact readiness."},
            {"name": "Forecast", "description": "Demand forecasting outputs and model metrics."},
            {"name": "Inventory", "description": "Inventory optimization, recommendations, and risk."},
            {"name": "Customer", "description": "Customer segmentation, RFM, CLV, and health."},
            {"name": "Churn", "description": "Customer churn predictions, probabilities, and actions."},
            {"name": "Decision Intelligence", "description": "Cross-domain business decisions, alerts, and scenarios."},
            {"name": "Analytics", "description": "Enterprise overview KPIs and artifact summaries."},
            {"name": "Reports", "description": "Report catalog and artifact downloads."},
        ],
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestContextMiddleware)

    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(forecast.router)
    app.include_router(inventory.router)
    app.include_router(customer.router)
    app.include_router(churn.router)
    app.include_router(decision.router)
    app.include_router(analytics.router)
    app.include_router(reports.router)

    @app.get("/", response_model=APIResponse, tags=["Health"], summary="API root")
    def root() -> dict:
        return success_response(
            {
                "service": settings.app_name,
                "version": settings.version,
                "docs": "/docs",
                "openapi": "/openapi.json",
                "redoc": "/redoc",
            },
            message="RetailPulse Enterprise API is running.",
        )

    return app


app = create_app()

