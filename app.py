# app.py - Enterprise MLOps Version
import asyncio
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from agent import ConversationManager
from vertex_ai import get_mental_health_response
from enterprise_monitoring import enterprise_monitor, generate_latest, CONTENT_TYPE_LATEST
import logging

# Configure structured logging
logger = logging.getLogger("mental_health_companion")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting Mental Health Companion with Enterprise MLOps")
    await enterprise_monitor.start_background_tasks()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Mental Health Companion")

app = FastAPI(
    title="Mental Health Companion API",
    description="Enterprise-grade AI companion for mental health support with comprehensive MLOps",
    version="1.2.0",
    lifespan=lifespan
)

# Instrument FastAPI with OpenTelemetry
app = enterprise_monitor.instrument_fastapi(app)

conversation_manager = ConversationManager()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserInput(BaseModel):
    prompt: str
    session_id: str = None
    user_agent: str = None

class MentalHealthResponse(BaseModel):
    response: str
    session_id: str
    model_version: str
    quality_score: float
    response_time_ms: float

@app.post("/api/mental-health", response_model=MentalHealthResponse)
@enterprise_monitor.track_request
async def mental_health(input: UserInput, request: Request):
    """Enhanced mental health endpoint with comprehensive monitoring"""
    import time
    start_time = time.time()
    
    # Generate session ID if not provided
    session_id = input.session_id or str(uuid.uuid4())
    user_agent = input.user_agent or request.headers.get('user-agent', 'unknown')
    
    user_input = input.prompt
    if not user_input:
        logger.warning("Empty input received", session_id=session_id)
        raise HTTPException(status_code=400, detail="No input provided")

    # Update session tracking
    enterprise_monitor.update_session_count(session_id, 'start')
    
    try:
        # AI request with monitoring
        response = await get_monitored_ai_response(user_input)
        
        # Calculate metrics
        response_time_ms = (time.time() - start_time) * 1000
        quality_score = enterprise_monitor._calculate_quality_score(response)
        
        # Track conversation
        # Simulate message count (in real app, get from conversation manager)
        message_count = 1
        enterprise_monitor.track_conversation(session_id, message_count, quality_score)
        
        logger.info(f"Request completed successfully in session {session_id} with response time {response_time_ms:.2f} ms and quality score {quality_score:.2f}")
        
        return MentalHealthResponse(
            response=response,
            session_id=session_id,
            model_version="gemini-2.5-flash-preview-05-20",
            quality_score=quality_score,
            response_time_ms=response_time_ms
        )
        
    except Exception as e:
        logger.error(f"Error processing mental health request in session {session_id}. The error is {str(e)}")
        enterprise_monitor.update_session_count(session_id, 'end')
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request. Please try again."
        )

@enterprise_monitor.track_ai_request("gemini-2.5-flash-preview-05-20")
async def get_monitored_ai_response(user_input: str) -> str:
    """AI response with monitoring wrapper"""
    return await conversation_manager.process_input(user_input, get_mental_health_response)

@app.post("/api/end-conversation")
async def end_conversation(request: dict):
    """End conversation with tracking"""
    session_id = request.get("session_id")
    satisfaction_score = request.get("satisfaction_score")
    
    if session_id:
        enterprise_monitor.update_session_count(session_id, 'end')
        if satisfaction_score:
            enterprise_monitor.track_conversation(session_id, 1, satisfaction_score)
        
        logger.info("Conversation ended", session_id=session_id, satisfaction=satisfaction_score)
        return {"message": "Conversation ended successfully"}
    else:
        raise HTTPException(status_code=400, detail="Session ID required")

# MLOps Endpoints
@app.get("/health")
async def comprehensive_health():
    """Comprehensive health check with detailed system status"""
    import psutil
    from datetime import datetime
    
    # System health
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)
    disk = psutil.disk_usage('/')
    
    # Application health
    active_sessions = len(enterprise_monitor.active_sessions)
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": {
            "name": "mental-health-companion",
            "version": "1.2.0",
            "uptime_seconds": time.time() - start_time if 'start_time' in globals() else 0
        },
        "system": {
            "memory_usage_percent": memory.percent,
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "cpu_usage_percent": cpu_percent,
            "disk_usage_percent": round((disk.used / disk.total) * 100, 2)
        },
        "application": {
            "active_sessions": active_sessions,
            "ai_service_status": "healthy"  # Could add actual AI service check
        },
        "dependencies": {
            "vertex_ai": "healthy",
            "prometheus": "healthy",
            "opentelemetry": "healthy"
        }
    }
    
    # Determine overall status
    if memory.percent > 90 or cpu_percent > 90:
        health_status["status"] = "warning"
    
    return health_status

@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    # Update system metrics before returning
    enterprise_monitor.update_system_metrics()
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/metrics/custom")
async def custom_metrics():
    """Custom application metrics in JSON format"""
    return {
        "active_sessions": len(enterprise_monitor.active_sessions),
        "total_requests": "see_prometheus",
        "average_response_time": "see_prometheus",
        "error_rate": "see_prometheus",
        "user_satisfaction": "see_prometheus"
    }

@app.get("/debug/trace")
async def debug_trace():
    """Debug endpoint to test distributed tracing"""
    with enterprise_monitor.tracer.start_as_current_span("debug_trace") as span:
        span.set_attribute("debug.test", True)
        await asyncio.sleep(0.1)  # Simulate work
        logger.info("Debug trace executed")
        return {"message": "Trace generated", "trace_id": hex(span.get_span_context().trace_id)}

@app.get("/stats/dashboard")
async def dashboard_stats():
    """Stats endpoint for custom dashboards"""
    import time
    from datetime import datetime, timedelta
    
    return {
        "timestamp": datetime.now().isoformat(),
        "service_info": {
            "name": "mental-health-companion",
            "version": "1.2.0",
            "environment": "production"
        },
        "current_metrics": {
            "active_sessions": len(enterprise_monitor.active_sessions),
            "requests_per_minute": "calculated_by_prometheus",
            "average_response_time": "calculated_by_prometheus",
            "error_rate_percent": "calculated_by_prometheus"
        },
        "monitoring_stack": {
            "prometheus": "enabled",
            "grafana": "enabled",
            "jaeger": "enabled",
            "opentelemetry": "enabled"
        }
    }

# Serve static files
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == '__main__':
    import uvicorn
    import time
    
    start_time = time.time()
    
    logger.info("Starting Mental Health Companion with Enterprise MLOps Version 1.2.0")

    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_config=None  # Use standard logger configuration
    )
