from celery import Celery, signals
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

from worker.core.config import settings

# Set up OpenTelemetry
resource = Resource.create({
    "service.name": "doc_evaluator",
    "deployment.environment": settings.ENVIRONMENT  # Optional: add environment info
})
trace.set_tracer_provider(TracerProvider(resource=resource))

# Configure the OTLP exporter
otlp_exporter = OTLPSpanExporter(
    endpoint=settings.OTLP_ENDPOINT,
    insecure=True  # Set to False in production
)

# Add the exporter to the TracerProvider
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(otlp_exporter)
)

# Instrument Redis - this will automatically instrument all Redis clients
RedisInstrumentor().instrument(
    trace_internal_commands=True,  # Optional: trace Redis internal commands
    sanitize_query=True  # Optional: remove sensitive data from spans
)

# Create Celery app
celery_app = Celery(
    "doc_evaluator",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Add Celery task ID to trace
@signals.task_prerun.connect
def add_task_id_to_span(task_id, task, *args, **kwargs):
    current_span = trace.get_current_span()
    if current_span:
        current_span.set_attribute("celery.task_id", task_id)
        # Optional: add more task information
        current_span.set_attribute("celery.task_name", task.name)
        current_span.set_attribute("celery.task_routing_key", task.request.delivery_info.get('routing_key'))

# Instrument Celery after setting up the signal
CeleryInstrumentor().instrument()

celery_app.autodiscover_tasks(['worker.services'])