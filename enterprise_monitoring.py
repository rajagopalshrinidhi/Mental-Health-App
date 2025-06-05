# enterprise_monitoring.py - Fixed with robust Jaeger connection
import time
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Optional, Any
from functools import wraps
import logging
from prometheus_client import (
    Counter, Histogram, Gauge, Summary, Info,
    generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry
)

# OpenTelemetry imports
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Try multiple exporter options
try:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    OTLP_AVAILABLE = True
except ImportError:
    OTLP_AVAILABLE = False

try:
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    JAEGER_AVAILABLE = True
except ImportError:
    JAEGER_AVAILABLE = False

try:
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
    PROMETHEUS_READER_AVAILABLE = True
except ImportError:
    PROMETHEUS_READER_AVAILABLE = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("enterprise_monitoring")

# Prometheus Metrics
REQUEST_COUNT = Counter(
    'mental_health_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code', 'user_agent']
)

REQUEST_DURATION = Histogram(
    'mental_health_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

AI_MODEL_REQUESTS = Counter(
    'mental_health_ai_requests_total',
    'Total AI model requests',
    ['model_name', 'status']
)

AI_MODEL_LATENCY = Histogram(
    'mental_health_ai_latency_seconds',
    'AI model response latency',
    ['model_name'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

CONVERSATION_METRICS = Counter(
    'mental_health_conversations_total',
    'Total conversations',
    ['conversation_type', 'completion_status']
)

ACTIVE_SESSIONS = Gauge(
    'mental_health_active_sessions',
    'Number of active user sessions'
)

RESPONSE_QUALITY_SCORE = Histogram(
    'mental_health_response_quality',
    'Response quality scores',
    ['quality_dimension'],
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

USER_SATISFACTION = Summary(
    'mental_health_user_satisfaction',
    'User satisfaction scores'
)

ERROR_RATE = Counter(
    'mental_health_errors_total',
    'Total application errors',
    ['error_type', 'severity', 'component']
)

SYSTEM_RESOURCES = Gauge(
    'mental_health_system_resources',
    'System resource usage',
    ['resource_type']
)

APP_INFO = Info(
    'mental_health_app_info',
    'Application information'
)

class EnterpriseMonitoring:
    """Enterprise-grade monitoring with robust OpenTelemetry setup"""
    
    def __init__(self, service_name: str = "mental-health-companion"):
        self.service_name = service_name
        self.active_sessions = set()
        self.tracing_enabled = False
        self.setup_telemetry()
        
        # Set application info
        APP_INFO.info({
            'version': '1.2.0',
            'service': service_name,
            'environment': os.getenv('ENVIRONMENT', 'production'),
            'build_date': datetime.now().isoformat()
        })
    
    def setup_telemetry(self):
        """Setup OpenTelemetry with multiple fallback options"""
        try:
            # Check if tracing should be disabled
            if os.getenv('OTEL_TRACES_EXPORTER') == 'none' or os.getenv('ENVIRONMENT') == 'local':
                logger.info("Tracing disabled by environment configuration")
                trace.set_tracer_provider(TracerProvider())
                self.tracer = trace.get_tracer(__name__)
                self.tracing_enabled = False
                return
            
            # Create resource
            resource = Resource.create({
                "service.name": self.service_name,
                "service.version": "1.2.0",
                "service.instance.id": f"{self.service_name}-001",
                "deployment.environment": os.getenv('ENVIRONMENT', 'production')
            })
            
            # Setup tracing
            trace.set_tracer_provider(TracerProvider(resource=resource))
            self.tracer = trace.get_tracer(__name__)
            
            metrics.set_meter_provider(MeterProvider(resource=resource))
            self.meter = metrics.get_meter(__name__)

                        
            # Try different exporters in order of preference
            span_processor = None
            
            # Option 1: OTLP HTTP (most reliable)
            if OTLP_AVAILABLE and not span_processor:
                try:
                    jaeger_endpoint = os.getenv('JAEGER_ENDPOINT', 'http://jaeger:14268/api/traces')
                    logger.info(f"Attempting OTLP HTTP exporter to {jaeger_endpoint}")
                    
                    otlp_exporter = OTLPSpanExporter(
                        endpoint=jaeger_endpoint,
                        headers={}
                    )
                    span_processor = BatchSpanProcessor(otlp_exporter)
                    logger.info(" OTLP HTTP exporter configured successfully")
                    self.tracing_enabled = True
                    
                except Exception as e:
                    logger.warning(f"OTLP HTTP exporter failed: {e}")
            
            # Option 2: Jaeger Thrift UDP (fallback)
            if JAEGER_AVAILABLE and not span_processor:
                try:
                    jaeger_host = os.getenv('JAEGER_AGENT_HOST', 'jaeger')
                    jaeger_port = int(os.getenv('JAEGER_AGENT_PORT', '6831'))
                    logger.info(f"Attempting Jaeger UDP exporter to {jaeger_host}:{jaeger_port}")
                    
                    jaeger_exporter = JaegerExporter(
                        agent_host_name=jaeger_host,
                        agent_port=jaeger_port
                    )
                    span_processor = BatchSpanProcessor(jaeger_exporter)
                    logger.info(" Jaeger UDP exporter configured successfully")
                    self.tracing_enabled = True
                    
                except Exception as e:
                    logger.warning(f"Jaeger UDP exporter failed: {e}")
            
            # Option 3: Console exporter (development fallback)
            if not span_processor:
                logger.info("Using console exporter for development")
                console_exporter = ConsoleSpanExporter()
                span_processor = BatchSpanProcessor(console_exporter)
                self.tracing_enabled = True
            
            # Add span processor
            if span_processor:
                trace.get_tracer_provider().add_span_processor(span_processor)
            
            # Setup metrics
            if PROMETHEUS_READER_AVAILABLE:
                try:
                    prometheus_reader = PrometheusMetricReader()
                    metrics.set_meter_provider(MeterProvider(
                        resource=resource,
                        metric_readers=[prometheus_reader]
                    ))
                    self.meter = metrics.get_meter(__name__)
                    logger.info("Prometheus metrics reader configured")
                except Exception as e:
                    logger.warning(f"Prometheus reader failed: {e}")
                    metrics.set_meter_provider(MeterProvider(resource=resource))
                    self.meter = metrics.get_meter(__name__)
            else:
                metrics.set_meter_provider(MeterProvider(resource=resource))
                self.meter = metrics.get_meter(__name__)
                        
            self.setup_metrics()

            logger.info(f"OpenTelemetry setup complete for {self.service_name} (tracing: {self.tracing_enabled})")
            
        except Exception as e:
            logger.error(f"OpenTelemetry setup failed: {e}")
            # Minimal fallback setup
            trace.set_tracer_provider(TracerProvider())
            self.tracer = trace.get_tracer(__name__)
            metrics.set_meter_provider(MeterProvider())
            self.meter = metrics.get_meter(__name__)
            self.tracing_enabled = False
    
    def setup_metrics(self):
        """Setup custom OpenTelemetry metrics"""
        try:
            # Check if meter is available before using it
            if not hasattr(self, 'meter') or self.meter is None:
                logger.warning("Meter not available, skipping custom OTel metrics setup")
                return
                
            self.otel_request_counter = self.meter.create_counter(
                "http_requests_total",
                description="Total HTTP requests",
                unit="1"
            )
            
            self.otel_ai_latency = self.meter.create_histogram(
                "ai_model_latency",
                description="AI model response latency",
                unit="s"
            )
            
            self.otel_conversation_length = self.meter.create_histogram(
                "conversation_length",
                description="Length of conversations in messages",
                unit="1"
            )
            logger.info("✅ Custom OTel metrics configured")
        except Exception as e:
            logger.warning(f"Failed to setup OTel metrics: {e}")
    
    def instrument_fastapi(self, app):
        """Instrument FastAPI with OpenTelemetry"""
        try:
            if self.tracing_enabled:
                FastAPIInstrumentor.instrument_app(app, tracer_provider=trace.get_tracer_provider())
                RequestsInstrumentor().instrument()
                logger.info(" FastAPI instrumented with OpenTelemetry")
            else:
                logger.info("FastAPI instrumentation skipped (tracing disabled)")
        except Exception as e:
            logger.warning(f"Failed to instrument FastAPI: {e}")
        
        return app
    
    def track_request(self, func):
        """Request tracking decorator with robust error handling"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Create span only if tracing is enabled
            if self.tracing_enabled:
                span = self.tracer.start_span(
                    f"{func.__name__}",
                    attributes={
                        "service.name": self.service_name,
                        "operation.name": func.__name__
                    }
                )
            else:
                span = None
            
            try:
                # Extract request details
                user_input = ""
                user_agent = "unknown"
                
                if args and hasattr(args[0], 'prompt'):
                    user_input = args[0].prompt
                    if span:
                        span.set_attribute("request.input_length", len(user_input))
                
                if len(args) > 1 and hasattr(args[1], 'headers'):
                    user_agent = args[1].headers.get('user-agent', 'unknown')
                    if span:
                        span.set_attribute("http.user_agent", user_agent)
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Calculate metrics
                duration = time.time() - start_time
                response_length = len(result.get('response', '')) if isinstance(result, dict) else 0
                
                # Update Prometheus metrics
                REQUEST_COUNT.labels(
                    method='POST',
                    endpoint='/api/mental-health',
                    status_code='200',
                    user_agent=user_agent[:20]
                ).inc()
                
                REQUEST_DURATION.labels(
                    method='POST',
                    endpoint='/api/mental-health'
                ).observe(duration)
                
                # Update OpenTelemetry metrics
                try:
                    self.otel_request_counter.add(1, {
                        "method": "POST",
                        "status": "success",
                        "endpoint": "/api/mental-health"
                    })
                except Exception:
                    pass
                
                # Update span attributes
                if span:
                    span.set_attribute("http.status_code", 200)
                    span.set_attribute("response.length", response_length)
                    span.set_attribute("request.duration", duration)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    span.end()
                
                logger.info(
                    f" Request completed - duration: {duration:.2f}s, "
                    f"input: {len(user_input)} chars, response: {response_length} chars"
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                error_type = type(e).__name__
                
                # Update error metrics
                ERROR_RATE.labels(
                    error_type=error_type,
                    severity='high',
                    component='api'
                ).inc()
                
                REQUEST_COUNT.labels(
                    method='POST',
                    endpoint='/api/mental-health',
                    status_code='500',
                    user_agent=user_agent[:20]
                ).inc()
                
                # Update span with error
                if span:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    span.set_attribute("error.type", error_type)
                    span.end()
                
                logger.error(f" Request failed: {e}")
                raise
        
        return wrapper
    
    def track_ai_request(self, model_name: str):
        """Track AI model requests"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                
                span = None
                if self.tracing_enabled:
                    span = self.tracer.start_span(
                        f"ai_request_{model_name}",
                        attributes={
                            "ai.model.name": model_name,
                            "ai.request.type": "text_generation"
                        }
                    )
                
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Update metrics
                    AI_MODEL_REQUESTS.labels(
                        model_name=model_name,
                        status='success'
                    ).inc()
                    
                    AI_MODEL_LATENCY.labels(
                        model_name=model_name
                    ).observe(duration)
                    
                    try:
                        self.otel_ai_latency.record(duration, {
                            "model_name": model_name,
                            "status": "success"
                        })
                    except Exception:
                        pass
                    
                    # Quality scoring
                    quality_score = self._calculate_quality_score(result)
                    RESPONSE_QUALITY_SCORE.labels(
                        quality_dimension='overall'
                    ).observe(quality_score)
                    
                    if span:
                        span.set_attribute("ai.response.length", len(str(result)))
                        span.set_attribute("ai.response.quality", quality_score)
                        span.set_attribute("ai.latency", duration)
                        span.set_status(trace.Status(trace.StatusCode.OK))
                        span.end()
                    
                    logger.info(f" AI request completed - {model_name} - {duration:.2f}s")
                    
                    return result
                    
                except Exception as e:
                    duration = time.time() - start_time
                    
                    AI_MODEL_REQUESTS.labels(
                        model_name=model_name,
                        status='error'
                    ).inc()
                    
                    ERROR_RATE.labels(
                        error_type=type(e).__name__,
                        severity='high',
                        component='ai_model'
                    ).inc()
                    
                    if span:
                        span.record_exception(e)
                        span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                        span.end()
                    
                    logger.error(f" AI request failed: {e}")
                    raise
            
            return wrapper
        return decorator
    
    def track_conversation(self, session_id: str, message_count: int, satisfaction_score: Optional[float] = None):
        """Track conversation-level metrics"""
        if self.tracing_enabled:
            with self.tracer.start_as_current_span(
                "conversation_tracking",
                attributes={
                    "conversation.session_id": session_id,
                    "conversation.message_count": message_count
                }
            ) as span:
                if satisfaction_score is not None:
                    span.set_attribute("conversation.satisfaction", satisfaction_score)
        
        CONVERSATION_METRICS.labels(
            conversation_type='mental_health_support',
            completion_status='ongoing' if satisfaction_score is None else 'completed'
        ).inc()
        
        try:
            self.otel_conversation_length.record(message_count, {
                "session_id": session_id,
                "conversation_type": "mental_health_support"
            })
        except Exception:
            pass
        
        if satisfaction_score is not None:
            USER_SATISFACTION.observe(satisfaction_score)
        
        logger.info(f" Conversation tracked - {session_id} - {message_count} messages")
    
    def update_session_count(self, session_id: str, action: str):
        """Update active session count"""
        if action == 'start':
            self.active_sessions.add(session_id)
        elif action == 'end':
            self.active_sessions.discard(session_id)
        
        ACTIVE_SESSIONS.set(len(self.active_sessions))
    
    def update_system_metrics(self):
        """Update system resource metrics"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            SYSTEM_RESOURCES.labels(resource_type='memory_percent').set(memory.percent)
            SYSTEM_RESOURCES.labels(resource_type='memory_available_gb').set(
                memory.available / (1024**3)
            )
            
            cpu_percent = psutil.cpu_percent(interval=1)
            SYSTEM_RESOURCES.labels(resource_type='cpu_percent').set(cpu_percent)
            
            disk = psutil.disk_usage('/')
            SYSTEM_RESOURCES.labels(resource_type='disk_percent').set(
                (disk.used / disk.total) * 100
            )
            
        except ImportError:
            logger.warning("psutil not available, skipping system metrics")
        except Exception as e:
            logger.warning(f"Error updating system metrics: {e}")
    
    def _calculate_quality_score(self, response: str) -> float:
        """Calculate response quality score"""
        if len(response) < 10:
            return 0.2
        elif len(response) > 500:
            return 0.7
        else:
            empathy_words = ['understand', 'feel', 'support', 'help', 'care']
            score = 0.5 + (sum(1 for word in empathy_words if word in response.lower()) * 0.1)
            return min(score, 1.0)
    
    async def start_background_tasks(self):
        """Start background monitoring tasks"""
        asyncio.create_task(self._system_metrics_updater())
        logger.info(" Background monitoring tasks started")
    
    async def _system_metrics_updater(self):
        """Background task to update system metrics"""
        while True:
            try:
                self.update_system_metrics()
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Error updating system metrics: {e}")
                await asyncio.sleep(60)

# Global monitoring instance
enterprise_monitor = EnterpriseMonitoring()