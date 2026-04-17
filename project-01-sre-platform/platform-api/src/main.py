"""
Platform API — FastAPI composition.

Wires together routes, OTel, and auto-instrumentation. Graceful when
Kubernetes, Vault, or the LLM backend are unreachable: endpoints
degrade rather than fail the whole server.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from config import get_settings
from routes import audit, explain, health, metrics, nodes, workloads
from telemetry import setup_telemetry

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)

    setup_telemetry()

    app = FastAPI(
        title="Platform API",
        description="Internal developer platform API for the sre-platform project",
        version="0.1.0",
    )

    for router in (
        health.router,
        nodes.router,
        workloads.router,
        audit.router,
        explain.router,
        metrics.router,
    ):
        app.include_router(router)

    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()

    @app.on_event("startup")
    def _startup() -> None:
        logger.info("Platform API starting (service=%s)", settings.service_name)

    return app


app = create_app()
