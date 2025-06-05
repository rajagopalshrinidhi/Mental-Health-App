# enterprise_monitoring.py - Fixed version
import time
import asyncio
import json
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
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("enterprise_monitoring")


# Prometheus Metrics with detailed labeling
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

# Application Info
APP_INFO = Info(
    'mental_health_app_info',
    'Application information'
)

class EnterpriseMonitoring:
    """Enterprise-grade monitoring with OpenTelemetry and Prometheus"""
    
    def __init__(self, service_name: str = "mental-health-companion"):
        self.service_name = service_name
        self.active_sessions = set()
        self.setup_telemetry()
        self.setup_metrics()
        
        # Set application info
        APP_INFO.info({
            'version': '1.2.0',
            'service': service_name,
            'environment': 'production',
            'build_date': datetime.now().isoformat()
        })
    
    def setup_telemetry(self):
        """Setup OpenTelemetry tracing and metrics - FIXED"""
        try:
            # Create resource
            resource = Resource.create({
                "service.name": self.service_name,
                "service.version": "1.2.0",
                "service.instance.id": f"{self.service_name}-001"
            })
            
            # Setup tracing
            trace.set_tracer_provider(TracerProvider(resource=resource))
            self.tracer = trace.get_tracer(__name__)
            
            # FIXED: Use Jaeger exporter instead of OTLP
            jaeger_exporter = JaegerExporter(
                agent_host_name="jaeger",  # Docker service name
                agent_port=6831,          # UDP port for Jaeger agent
            )
            span_processor = BatchSpanProcessor(jaeger_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)
            
            # Setup metrics (simplified)
            try:
                from opentelemetry.exporter.prometheus import PrometheusMetricReader
                prometheus_reader = PrometheusMetricReader()
                metrics.set_meter_provider(MeterProvider(
                    resource=resource,
                    metric_readers=[prometheus_reader]
                ))
                self.meter = metrics.get_meter(__name__)
            except ImportError:
                logger.warning("PrometheusMetricReader not available, using basic metrics")
                metrics.set_meter_provider(MeterProvider(resource=resource))
                self.meter = metrics.get_meter(__name__)
            
            logger.info(f"OpenTelemetry configured successfully for service:{self.service_name}")
            
        except Exception as e:
            logger.error(f"Failed to setup OpenTelemetry: {str(e)}")
            # Fallback to basic setup
            trace.set_tracer_provider(TracerProvider())
            self.tracer = trace.get_tracer(__name__)
            metrics.set_meter_provider(MeterProvider())
            self.meter = metrics.get_meter(__name__)
    
    def setup_metrics(self):
        """Setup custom OpenTelemetry metrics"""
        try:
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
        except Exception as e:
            logger.warning(f"Failed to setup OTel metrics: {str(e)}")
    
    def instrument_fastapi(self, app):
        """Instrument FastAPI with OpenTelemetry"""
        try:
            FastAPIInstrumentor.instrument_app(app, tracer_provider=trace.get_tracer_provider())
            RequestsInstrumentor().instrument()
            LoggingInstrumentor().instrument(set_logging_format=True)
            logger.info("FastAPI instrumented with OpenTelemetry")
        except Exception as e:
            logger.warning(f"Failed to instrument FastAPI: {str(e)}")
        
        return app
    
    def track_request(self, func):
        """Advanced request tracking decorator with distributed tracing"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Start a new span
            with self.tracer.start_as_current_span(
                f"{func.__name__}",
                attributes={
                    "service.name": self.service_name,
                    "operation.name": func.__name__
                }
            ) as span:
                try:
                    # Extract request details
                    user_input = ""
                    user_agent = "unknown"
                    
                    if args and hasattr(args[0], 'prompt'):
                        user_input = args[0].prompt
                        span.set_attribute("request.input_length", len(user_input))
                    
                    if len(args) > 1 and hasattr(args[1], 'headers'):
                        user_agent = args[1].headers.get('user-agent', 'unknown')
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
                        user_agent=user_agent[:20]  # Truncate to avoid cardinality explosion
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
                    except:
                        pass  # Ignore OTel metric errors
                    
                    # Add span attributes
                    span.set_attribute("http.status_code", 200)
                    span.set_attribute("response.length", response_length)
                    span.set_attribute("request.duration", duration)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    
                    logger.info(f"Request completed successfully in duration {duration:.2f} seconds, user_input_length={len(user_input)}, response_length={response_length} with trace_id={hex(span.get_span_context().trace_id)}")

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
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    span.set_attribute("error.type", error_type)
                    
                    logger.error(f"Request failed:{str(e)}")
                    
                    raise
        
        return wrapper
    
    def track_ai_request(self, model_name: str):
        """Track AI model requests with detailed metrics"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                
                with self.tracer.start_as_current_span(
                    f"ai_request_{model_name}",
                    attributes={
                        "ai.model.name": model_name,
                        "ai.request.type": "text_generation"
                    }
                ) as span:
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
                        except:
                            pass  # Ignore OTel metric errors
                        
                        # Quality scoring (mock implementation)
                        quality_score = self._calculate_quality_score(result)
                        RESPONSE_QUALITY_SCORE.labels(
                            quality_dimension='overall'
                        ).observe(quality_score)
                        
                        span.set_attribute("ai.response.length", len(str(result)))
                        span.set_attribute("ai.response.quality", quality_score)
                        span.set_attribute("ai.latency", duration)
                        
                        logger.info("AI request completed")
                        
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
                        
                        span.record_exception(e)
                        span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                        
                        logger.error(f"AI request failed: {str(e)}")
                        
                        raise
            
            return wrapper
        return decorator
    
    def track_conversation(self, session_id: str, message_count: int, satisfaction_score: Optional[float] = None):
        """Track conversation-level metrics"""
        with self.tracer.start_as_current_span(
            "conversation_tracking",
            attributes={
                "conversation.session_id": session_id,
                "conversation.message_count": message_count
            }
        ) as span:
            
            CONVERSATION_METRICS.labels(
                conversation_type='mental_health_support',
                completion_status='ongoing' if satisfaction_score is None else 'completed'
            ).inc()
            
            try:
                self.otel_conversation_length.record(message_count, {
                    "session_id": session_id,
                    "conversation_type": "mental_health_support"
                })
            except:
                pass
            
            if satisfaction_score is not None:
                USER_SATISFACTION.observe(satisfaction_score)
                span.set_attribute("conversation.satisfaction", satisfaction_score)
            
            logger.info(f"Conversation tracked - sesssion: {session_id}, messages: {message_count}, satisfaction: {satisfaction_score}")
    
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
            
            # Memory usage
            memory = psutil.virtual_memory()
            SYSTEM_RESOURCES.labels(resource_type='memory_percent').set(memory.percent)
            SYSTEM_RESOURCES.labels(resource_type='memory_available_gb').set(
                memory.available / (1024**3)
            )
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            SYSTEM_RESOURCES.labels(resource_type='cpu_percent').set(cpu_percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            SYSTEM_RESOURCES.labels(resource_type='disk_percent').set(
                (disk.used / disk.total) * 100
            )
            
        except ImportError:
            logger.warning("psutil not available, skipping system metrics")
        except Exception as e:
            logger.warning(f"Error updating system metrics:{str(e)}")
    
    def _calculate_quality_score(self, response: str) -> float:
        """Calculate response quality score (mock implementation)"""
        # Simple heuristic - in production, use ML models
        if len(response) < 10:
            return 0.2
        elif len(response) > 500:
            return 0.7
        else:
            # Check for empathy keywords
            empathy_words = ['understand', 'feel', 'support', 'help', 'care']
            score = 0.5 + (sum(1 for word in empathy_words if word in response.lower()) * 0.1)
            return min(score, 1.0)
    
    async def start_background_tasks(self):
        """Start background monitoring tasks"""
        asyncio.create_task(self._system_metrics_updater())
        logger.info("Background monitoring tasks started")
    
    async def _system_metrics_updater(self):
        """Background task to update system metrics"""
        while True:
            try:
                self.update_system_metrics()
                await asyncio.sleep(30)  # Update every 30 seconds
            except Exception as e:
                logger.error(f"Error updating system metrics:{str(e)}")
                await asyncio.sleep(60)  # Retry in 1 minute

# Global monitoring instance
enterprise_monitor = EnterpriseMonitoring()