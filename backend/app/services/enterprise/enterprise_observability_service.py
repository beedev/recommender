"""
Enterprise Observability Service
Comprehensive monitoring and alerting for enterprise deployment
Tracks agent performance, quality metrics, and system health
"""

import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .enhanced_state_models import EnterpriseRecommendationResponse

logger = logging.getLogger(__name__)


@dataclass
class TraceRecord:
    """Individual trace record for distributed tracing"""
    trace_id: str
    session_id: str
    user_id: str
    start_time: float
    end_time: Optional[float] = None
    total_duration_ms: Optional[float] = None
    
    # Agent performance tracking
    agent_spans: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Quality metrics
    overall_confidence: float = 0.0
    packages_returned: int = 0
    trinity_formation_rate: float = 0.0
    
    # Error tracking
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Business metrics
    user_satisfaction_prediction: float = 0.0
    business_insights_count: int = 0


@dataclass
class AgentPerformanceMetrics:
    """Performance metrics for individual agents"""
    agent_name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    
    # Timing metrics
    avg_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    
    # Quality metrics
    avg_confidence: float = 0.0
    success_rate: float = 0.0
    
    # Recent performance
    recent_durations: List[float] = field(default_factory=list)
    recent_confidences: List[float] = field(default_factory=list)


@dataclass
class SystemHealthMetrics:
    """Overall system health metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    avg_response_time_ms: float = 0.0
    avg_confidence: float = 0.0
    avg_trinity_formation_rate: float = 0.0
    
    # Performance percentiles
    p50_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    
    # Quality trends
    high_confidence_rate: float = 0.0  # % of requests with confidence > 0.8
    low_confidence_rate: float = 0.0   # % of requests with confidence < 0.4
    
    # Recent trends
    recent_response_times: List[float] = field(default_factory=list)
    recent_confidences: List[float] = field(default_factory=list)


class MetricsCollector:
    """Collects and aggregates performance metrics"""
    
    def __init__(self):
        self.agent_metrics: Dict[str, AgentPerformanceMetrics] = {}
        self.system_metrics = SystemHealthMetrics()
        self.active_traces: Dict[str, TraceRecord] = {}
        self.completed_traces: List[TraceRecord] = []
        
        # Keep only recent traces in memory
        self.max_completed_traces = 1000
        self.max_recent_samples = 100
    
    def start_trace(self, trace_id: str, metadata: Dict[str, Any]) -> TraceRecord:
        """Start a new trace record"""
        
        trace_record = TraceRecord(
            trace_id=trace_id,
            session_id=metadata.get("session_id", "unknown"),
            user_id=metadata.get("user_id", "anonymous"),
            start_time=time.time()
        )
        
        self.active_traces[trace_id] = trace_record
        logger.debug(f"Started trace {trace_id}")
        
        return trace_record
    
    def record_agent_start(self, trace_id: str, agent_name: str) -> None:
        """Record agent execution start"""
        
        if trace_id in self.active_traces:
            self.active_traces[trace_id].agent_spans[agent_name] = {
                "start_time": time.time(),
                "status": "running"
            }
            
            logger.debug(f"Agent {agent_name} started for trace {trace_id}")
    
    def record_agent_success(
        self, 
        trace_id: str, 
        agent_name: str, 
        duration_ms: float, 
        metrics: Dict[str, Any]
    ) -> None:
        """Record successful agent execution"""
        
        # Update trace record
        if trace_id in self.active_traces:
            span = self.active_traces[trace_id].agent_spans.get(agent_name, {})
            span.update({
                "end_time": time.time(),
                "duration_ms": duration_ms,
                "status": "success",
                "metrics": metrics
            })
        
        # Update agent metrics
        if agent_name not in self.agent_metrics:
            self.agent_metrics[agent_name] = AgentPerformanceMetrics(agent_name=agent_name)
        
        agent_metric = self.agent_metrics[agent_name]
        agent_metric.total_executions += 1
        agent_metric.successful_executions += 1
        
        # Update timing metrics
        agent_metric.recent_durations.append(duration_ms)
        if len(agent_metric.recent_durations) > self.max_recent_samples:
            agent_metric.recent_durations.pop(0)
        
        agent_metric.avg_duration_ms = sum(agent_metric.recent_durations) / len(agent_metric.recent_durations)
        agent_metric.min_duration_ms = min(agent_metric.min_duration_ms, duration_ms)
        agent_metric.max_duration_ms = max(agent_metric.max_duration_ms, duration_ms)
        
        # Update quality metrics
        confidence = metrics.get("confidence", 0.0)
        if confidence > 0:
            agent_metric.recent_confidences.append(confidence)
            if len(agent_metric.recent_confidences) > self.max_recent_samples:
                agent_metric.recent_confidences.pop(0)
            
            agent_metric.avg_confidence = sum(agent_metric.recent_confidences) / len(agent_metric.recent_confidences)
        
        agent_metric.success_rate = agent_metric.successful_executions / agent_metric.total_executions
        
        logger.debug(f"Agent {agent_name} completed successfully for trace {trace_id} in {duration_ms:.1f}ms")
    
    def record_agent_error(self, trace_id: str, agent_name: str, error: str, duration_ms: float) -> None:
        """Record agent execution error"""
        
        # Update trace record
        if trace_id in self.active_traces:
            span = self.active_traces[trace_id].agent_spans.get(agent_name, {})
            span.update({
                "end_time": time.time(),
                "duration_ms": duration_ms,
                "status": "error",
                "error": error
            })
            
            self.active_traces[trace_id].errors.append(f"{agent_name}: {error}")
        
        # Update agent metrics
        if agent_name not in self.agent_metrics:
            self.agent_metrics[agent_name] = AgentPerformanceMetrics(agent_name=agent_name)
        
        agent_metric = self.agent_metrics[agent_name]
        agent_metric.total_executions += 1
        agent_metric.failed_executions += 1
        agent_metric.success_rate = agent_metric.successful_executions / agent_metric.total_executions
        
        logger.error(f"Agent {agent_name} failed for trace {trace_id}: {error}")
    
    def complete_trace(
        self, 
        trace_id: str, 
        response: EnterpriseRecommendationResponse,
        total_duration_ms: float,
        metadata: Dict[str, Any]
    ) -> None:
        """Complete a trace record"""
        
        if trace_id in self.active_traces:
            trace_record = self.active_traces[trace_id]
            trace_record.end_time = time.time()
            trace_record.total_duration_ms = total_duration_ms
            trace_record.overall_confidence = response.overall_confidence
            trace_record.packages_returned = len(response.packages)
            trace_record.trinity_formation_rate = len([p for p in response.packages if p.trinity_compliance]) / max(len(response.packages), 1)
            trace_record.user_satisfaction_prediction = response.satisfaction_prediction
            trace_record.business_insights_count = len(response.business_insights)
            
            # Move to completed traces
            self.completed_traces.append(trace_record)
            if len(self.completed_traces) > self.max_completed_traces:
                self.completed_traces.pop(0)
            
            del self.active_traces[trace_id]
            
            # Update system metrics
            self._update_system_metrics(trace_record)
            
            logger.debug(f"Completed trace {trace_id} in {total_duration_ms:.1f}ms with confidence {response.overall_confidence:.2f}")
    
    def record_critical_error(self, trace_id: str, error: str, duration_ms: float) -> None:
        """Record critical system error"""
        
        if trace_id in self.active_traces:
            trace_record = self.active_traces[trace_id]
            trace_record.end_time = time.time()
            trace_record.total_duration_ms = duration_ms
            trace_record.errors.append(f"CRITICAL: {error}")
            
            self.completed_traces.append(trace_record)
            del self.active_traces[trace_id]
        
        self.system_metrics.failed_requests += 1
        
        logger.critical(f"Critical error for trace {trace_id}: {error}")
    
    def _update_system_metrics(self, trace_record: TraceRecord) -> None:
        """Update overall system metrics"""
        
        self.system_metrics.total_requests += 1
        
        if trace_record.errors:
            self.system_metrics.failed_requests += 1
        else:
            self.system_metrics.successful_requests += 1
        
        # Update response time tracking
        if trace_record.total_duration_ms:
            self.system_metrics.recent_response_times.append(trace_record.total_duration_ms)
            if len(self.system_metrics.recent_response_times) > self.max_recent_samples:
                self.system_metrics.recent_response_times.pop(0)
            
            self.system_metrics.avg_response_time_ms = (
                sum(self.system_metrics.recent_response_times) / 
                len(self.system_metrics.recent_response_times)
            )
            
            # Calculate percentiles
            sorted_times = sorted(self.system_metrics.recent_response_times)
            if sorted_times:
                self.system_metrics.p50_response_time_ms = sorted_times[len(sorted_times) // 2]
                self.system_metrics.p95_response_time_ms = sorted_times[int(len(sorted_times) * 0.95)]
                self.system_metrics.p99_response_time_ms = sorted_times[int(len(sorted_times) * 0.99)]
        
        # Update confidence tracking
        if trace_record.overall_confidence > 0:
            self.system_metrics.recent_confidences.append(trace_record.overall_confidence)
            if len(self.system_metrics.recent_confidences) > self.max_recent_samples:
                self.system_metrics.recent_confidences.pop(0)
            
            self.system_metrics.avg_confidence = (
                sum(self.system_metrics.recent_confidences) / 
                len(self.system_metrics.recent_confidences)
            )
            
            # Calculate confidence distribution
            high_confidence = len([c for c in self.system_metrics.recent_confidences if c > 0.8])
            low_confidence = len([c for c in self.system_metrics.recent_confidences if c < 0.4])
            
            total_confidences = len(self.system_metrics.recent_confidences)
            self.system_metrics.high_confidence_rate = high_confidence / total_confidences
            self.system_metrics.low_confidence_rate = low_confidence / total_confidences


class AlertingSystem:
    """Handles alerting for system issues"""
    
    def __init__(self):
        self.alert_thresholds = {
            "response_time_ms": 5000,      # Alert if response time > 5s
            "error_rate": 0.1,             # Alert if error rate > 10%
            "low_confidence_rate": 0.3,    # Alert if >30% requests have low confidence
            "agent_failure_rate": 0.2      # Alert if agent failure rate > 20%
        }
        
        self.recent_alerts: List[Dict[str, Any]] = []
        self.max_recent_alerts = 100
    
    def check_system_health(self, metrics: SystemHealthMetrics) -> List[Dict[str, Any]]:
        """Check system health and generate alerts"""
        
        alerts = []
        
        # Response time alerts
        if metrics.avg_response_time_ms > self.alert_thresholds["response_time_ms"]:
            alerts.append({
                "type": "HIGH_RESPONSE_TIME",
                "severity": "WARNING",
                "message": f"Average response time {metrics.avg_response_time_ms:.0f}ms exceeds threshold",
                "timestamp": datetime.utcnow(),
                "metric_value": metrics.avg_response_time_ms,
                "threshold": self.alert_thresholds["response_time_ms"]
            })
        
        # Error rate alerts
        if metrics.total_requests > 0:
            error_rate = metrics.failed_requests / metrics.total_requests
            if error_rate > self.alert_thresholds["error_rate"]:
                alerts.append({
                    "type": "HIGH_ERROR_RATE",
                    "severity": "CRITICAL",
                    "message": f"Error rate {error_rate:.1%} exceeds threshold",
                    "timestamp": datetime.utcnow(),
                    "metric_value": error_rate,
                    "threshold": self.alert_thresholds["error_rate"]
                })
        
        # Low confidence alerts
        if metrics.low_confidence_rate > self.alert_thresholds["low_confidence_rate"]:
            alerts.append({
                "type": "HIGH_LOW_CONFIDENCE_RATE",
                "severity": "WARNING",
                "message": f"Low confidence rate {metrics.low_confidence_rate:.1%} exceeds threshold",
                "timestamp": datetime.utcnow(),
                "metric_value": metrics.low_confidence_rate,
                "threshold": self.alert_thresholds["low_confidence_rate"]
            })
        
        # Store alerts
        for alert in alerts:
            self.recent_alerts.append(alert)
            logger.warning(f"ALERT: {alert['type']} - {alert['message']}")
        
        if len(self.recent_alerts) > self.max_recent_alerts:
            self.recent_alerts = self.recent_alerts[-self.max_recent_alerts:]
        
        return alerts
    
    def check_agent_health(self, agent_metrics: Dict[str, AgentPerformanceMetrics]) -> List[Dict[str, Any]]:
        """Check individual agent health"""
        
        alerts = []
        
        for agent_name, metrics in agent_metrics.items():
            if metrics.total_executions > 0:
                failure_rate = metrics.failed_executions / metrics.total_executions
                
                if failure_rate > self.alert_thresholds["agent_failure_rate"]:
                    alerts.append({
                        "type": "AGENT_HIGH_FAILURE_RATE",
                        "severity": "CRITICAL",
                        "message": f"Agent {agent_name} failure rate {failure_rate:.1%} exceeds threshold",
                        "timestamp": datetime.utcnow(),
                        "agent": agent_name,
                        "metric_value": failure_rate,
                        "threshold": self.alert_thresholds["agent_failure_rate"]
                    })
        
        return alerts


class EnterpriseObservabilityService:
    """
    Enterprise Observability Service
    Comprehensive monitoring and alerting for enterprise deployment
    """
    
    def __init__(self):
        """Initialize enterprise observability components"""
        
        self.metrics_collector = MetricsCollector()
        self.alerting_system = AlertingSystem()
        
        logger.info("Enterprise Observability Service initialized")
    
    def start_trace(self, session_id: str, metadata: Dict[str, Any] = None) -> str:
        """Start distributed tracing for recommendation flow"""
        
        trace_id = f"rec_{session_id}_{int(time.time())}"
        
        self.metrics_collector.start_trace(trace_id, metadata or {})
        
        return trace_id
    
    def record_agent_start(self, trace_id: str, agent_name: str) -> None:
        """Record agent execution start"""
        
        self.metrics_collector.record_agent_start(trace_id, agent_name)
    
    def record_agent_success(
        self, 
        trace_id: str, 
        agent_name: str, 
        duration_ms: float,
        metrics: Dict[str, Any]
    ) -> None:
        """Record successful agent execution"""
        
        self.metrics_collector.record_agent_success(trace_id, agent_name, duration_ms, metrics)
    
    def record_agent_error(self, trace_id: str, agent_name: str, error: str, duration_ms: float) -> None:
        """Record agent execution error"""
        
        self.metrics_collector.record_agent_error(trace_id, agent_name, error, duration_ms)
    
    def complete_trace(
        self, 
        trace_id: str, 
        response: EnterpriseRecommendationResponse,
        total_duration_ms: float,
        metadata: Dict[str, Any] = None
    ) -> None:
        """Complete tracing and record quality metrics"""
        
        self.metrics_collector.complete_trace(trace_id, response, total_duration_ms, metadata or {})
        
        # Check for alerts
        alerts = self.alerting_system.check_system_health(self.metrics_collector.system_metrics)
        agent_alerts = self.alerting_system.check_agent_health(self.metrics_collector.agent_metrics)
        
        # Log critical alerts
        for alert in alerts + agent_alerts:
            if alert["severity"] == "CRITICAL":
                logger.critical(f"CRITICAL ALERT: {alert['message']}")
    
    def record_critical_error(self, trace_id: str, error: str, duration_ms: float) -> None:
        """Record critical system error"""
        
        self.metrics_collector.record_critical_error(trace_id, error, duration_ms)
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health status"""
        
        metrics = self.metrics_collector.system_metrics
        
        # Determine overall health status
        if metrics.total_requests == 0:
            status = "unknown"
        elif (metrics.failed_requests / metrics.total_requests) > 0.1:
            status = "unhealthy"
        elif metrics.avg_response_time_ms > 3000:
            status = "degraded"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "total_requests": metrics.total_requests,
            "successful_requests": metrics.successful_requests,
            "failed_requests": metrics.failed_requests,
            "success_rate": metrics.successful_requests / max(metrics.total_requests, 1),
            "avg_response_time_ms": metrics.avg_response_time_ms,
            "avg_confidence": metrics.avg_confidence,
            "high_confidence_rate": metrics.high_confidence_rate,
            "recent_alerts": self.alerting_system.recent_alerts[-10:]  # Last 10 alerts
        }
    
    def get_agent_performance(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        
        performance = {}
        
        for agent_name, metrics in self.metrics_collector.agent_metrics.items():
            performance[agent_name] = {
                "total_executions": metrics.total_executions,
                "success_rate": metrics.success_rate,
                "avg_duration_ms": metrics.avg_duration_ms,
                "avg_confidence": metrics.avg_confidence,
                "min_duration_ms": metrics.min_duration_ms,
                "max_duration_ms": metrics.max_duration_ms
            }
        
        return performance
    
    def get_quality_metrics(self) -> Dict[str, Any]:
        """Get quality metrics for enterprise monitoring"""
        
        metrics = self.metrics_collector.system_metrics
        
        return {
            "avg_confidence": metrics.avg_confidence,
            "high_confidence_rate": metrics.high_confidence_rate,
            "low_confidence_rate": metrics.low_confidence_rate,
            "avg_trinity_formation_rate": metrics.avg_trinity_formation_rate,
            "response_time_percentiles": {
                "p50": metrics.p50_response_time_ms,
                "p95": metrics.p95_response_time_ms,
                "p99": metrics.p99_response_time_ms
            }
        }
    
    def get_business_metrics(self) -> Dict[str, Any]:
        """Get business-relevant metrics"""
        
        completed_traces = self.metrics_collector.completed_traces
        
        if not completed_traces:
            return {
                "total_recommendations": 0,
                "avg_packages_per_request": 0,
                "avg_satisfaction_prediction": 0,
                "trinity_formation_success_rate": 0
            }
        
        total_packages = sum(trace.packages_returned for trace in completed_traces)
        total_satisfaction = sum(trace.user_satisfaction_prediction for trace in completed_traces)
        trinity_successful = len([trace for trace in completed_traces if trace.trinity_formation_rate > 0.8])
        
        return {
            "total_recommendations": len(completed_traces),
            "avg_packages_per_request": total_packages / len(completed_traces),
            "avg_satisfaction_prediction": total_satisfaction / len(completed_traces),
            "trinity_formation_success_rate": trinity_successful / len(completed_traces),
            "avg_business_insights_per_request": sum(trace.business_insights_count for trace in completed_traces) / len(completed_traces)
        }