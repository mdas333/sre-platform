"""
OpenTelemetry bootstrap.

Sets up a TracerProvider and MeterProvider exporting OTLP/gRPC to the
configured collector endpoint. Auto-instruments FastAPI and HTTPX.
Silent if the endpoint is unreachable so the app still starts in a
disconnected dev environment.
"""

from __future__ import annotations

import logging

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from config import get_settings

logger = logging.getLogger(__name__)


def setup_telemetry() -> None:
    s = get_settings()
    resource = Resource.create({"service.name": s.service_name})

    try:
        tp = TracerProvider(resource=resource)
        tp.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=s.otlp_endpoint, insecure=True)))
        trace.set_tracer_provider(tp)

        mp = MeterProvider(
            resource=resource,
            metric_readers=[
                PeriodicExportingMetricReader(
                    OTLPMetricExporter(endpoint=s.otlp_endpoint, insecure=True),
                    export_interval_millis=15_000,
                )
            ],
        )
        metrics.set_meter_provider(mp)
        logger.info("OTel configured (endpoint=%s)", s.otlp_endpoint)
    except Exception:
        logger.exception("OTel setup failed; continuing without telemetry")
