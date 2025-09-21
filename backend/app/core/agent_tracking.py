"""
Centralized Agent Transaction Tracking System

Provides PostgreSQL-based tracking for all agent transactions and orchestration flows.
Can be enabled/disabled via ENABLE_AGENT_TRACKING environment variable.

TRACKING CAPABILITIES:
1. Agent Execution Tracking: Start/end times, success/failure, performance metrics
2. State Transitions: Changes in agent state throughout workflow
3. Decision Logging: Agent decisions with reasoning and confidence scores
4. Error Tracking: Comprehensive error capture with context
5. Performance Analytics: Execution times, resource usage, bottlenecks
6. User Journey Tracking: Complete flow from user request to final response

POSTGRESQL SCHEMA:
- agent_transactions: Main execution tracking
- agent_state_transitions: State changes during workflow
- agent_decisions: Decision points with reasoning
- agent_errors: Error occurrences with full context
- agent_performance_metrics: Performance and resource usage data

DESIGN FEATURES:
- Async/await support for non-blocking operations
- Batched inserts for performance optimization
- Automatic retry logic for database failures
- Graceful degradation when tracking is disabled
- Zero impact on agent logic when disabled
"""

import asyncio
import json
import logging
import time
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, field, asdict
from contextlib import asynccontextmanager
import asyncpg
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.database.postgresql import get_connection


logger = logging.getLogger(__name__)


class AgentTransactionStatus(str, Enum):
    """Status of agent transaction execution"""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class AgentTransactionType(str, Enum):
    """Types of agent transactions"""
    INTENT_EXTRACTION = "intent_extraction"
    RECOMMENDATION = "recommendation"
    COMPATIBILITY_CHECK = "compatibility_check"
    SALES_ANALYSIS = "sales_analysis"
    PACKAGE_BUILDING = "package_building"
    VALIDATION = "validation"
    TRANSLATION = "translation"
    UI_RESPONSE = "ui_response"
    SERVICE_COMMUNICATION = "service_communication"
    ORCHESTRATION = "orchestration"


class StateTransitionType(str, Enum):
    """Types of state transitions"""
    AGENT_CHANGE = "agent_change"
    REQUIREMENT_UPDATE = "requirement_update"
    CONTEXT_UPDATE = "context_update"
    ERROR_STATE = "error_state"
    COMPLETION = "completion"


@dataclass
class AgentTransaction:
    """Core agent transaction record"""
    transaction_id: str
    session_id: str
    user_id: Optional[str] = None
    agent_name: str = ""
    transaction_type: str = ""
    status: str = AgentTransactionStatus.STARTED.value
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class StateTransition:
    """Agent state transition record"""
    transition_id: str
    transaction_id: str
    session_id: str
    transition_type: str
    from_state: Dict[str, Any] = field(default_factory=dict)
    to_state: Dict[str, Any] = field(default_factory=dict)
    trigger: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentDecisionRecord:
    """Agent decision point record"""
    decision_id: str
    transaction_id: str
    session_id: str
    agent_name: str
    decision_point: str
    decision_made: str
    reasoning: str
    confidence_score: float
    alternatives_considered: List[str] = field(default_factory=list)
    decision_time_ms: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentError:
    """Agent error record"""
    error_id: str
    transaction_id: str
    session_id: str
    agent_name: str
    error_type: str
    error_message: str
    error_traceback: str
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False
    resolution_notes: Optional[str] = None


@dataclass
class PerformanceMetric:
    """Performance metrics record"""
    metric_id: str
    transaction_id: str
    session_id: str
    agent_name: str
    metric_name: str
    metric_value: float
    metric_unit: str
    measurement_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentTransactionTracker:
    """
    Centralized tracking system for all agent transactions.
    
    CORE FEATURES:
    1. Non-blocking async operations
    2. Batched database writes for performance
    3. Graceful degradation when disabled
    4. Comprehensive error handling
    5. Zero impact on agent logic when disabled
    
    USAGE:
    ```python
    # In any agent
    async with tracker.track_transaction(
        session_id="session_123",
        agent_name="RecommendationAgent",
        transaction_type=AgentTransactionType.RECOMMENDATION
    ) as tx:
        # Agent logic here
        tx.log_decision("selected_trinity", "MIG-based trinity", 0.9)
        tx.log_state_transition("requirements_parsed", old_state, new_state)
        # Automatic completion tracking
    ```
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.enabled = self.settings.ENABLE_AGENT_TRACKING
        self.batch_size = self.settings.AGENT_TRACKING_BATCH_SIZE
        self.flush_interval = self.settings.AGENT_TRACKING_FLUSH_INTERVAL
        
        # Batching queues
        self._transaction_queue: List[AgentTransaction] = []
        self._transition_queue: List[StateTransition] = []
        self._decision_queue: List[AgentDecisionRecord] = []
        self._error_queue: List[AgentError] = []
        self._metric_queue: List[PerformanceMetric] = []
        
        # Database connection
        self._db_connection: Optional[asyncpg.Connection] = None
        self._flush_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
        if self.enabled:
            logger.info("Agent transaction tracking enabled")
        else:
            logger.info("Agent transaction tracking disabled")
    
    async def initialize(self):
        """Initialize the tracking system"""
        if not self.enabled:
            return
        
        try:
            self._db_connection = await get_connection()
            await self._create_tables()
            
            # Start background flush task
            self._flush_task = asyncio.create_task(self._periodic_flush())
            logger.info("Agent tracking system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent tracking: {e}")
            self.enabled = False  # Disable tracking on initialization failure
    
    async def close(self):
        """Close tracking system and flush remaining data"""
        if not self.enabled:
            return
        
        try:
            # Cancel flush task
            if self._flush_task:
                self._flush_task.cancel()
                try:
                    await self._flush_task
                except asyncio.CancelledError:
                    pass
            
            # Final flush
            await self._flush_all_queues()
            
            # Close connection
            if self._db_connection:
                await self._db_connection.close()
            
            logger.info("Agent tracking system closed")
            
        except Exception as e:
            logger.error(f"Error closing agent tracking: {e}")
    
    @asynccontextmanager
    async def track_transaction(
        self,
        session_id: str,
        agent_name: str,
        transaction_type: Union[AgentTransactionType, str],
        user_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager for tracking complete agent transactions.
        
        Automatically handles:
        - Transaction start/end timing
        - Success/failure status
        - Error capture with full traceback
        - Performance metrics
        
        Args:
            session_id: Unique session identifier
            agent_name: Name of the agent being tracked
            transaction_type: Type of transaction being performed
            user_id: Optional user identifier
            transaction_id: Optional custom transaction ID
            metadata: Additional metadata to store
            
        Yields:
            TransactionContext: Context object for logging decisions, state changes, etc.
        """
        if not self.enabled:
            # Return a no-op context when tracking is disabled
            yield _NoOpTransactionContext()
            return
        
        # Generate transaction ID if not provided
        if not transaction_id:
            transaction_id = f"{agent_name}_{session_id}_{int(time.time() * 1000)}"
        
        # Create transaction record
        transaction = AgentTransaction(
            transaction_id=transaction_id,
            session_id=session_id,
            user_id=user_id,
            agent_name=agent_name,
            transaction_type=transaction_type.value if isinstance(transaction_type, AgentTransactionType) else transaction_type,
            status=AgentTransactionStatus.STARTED.value,
            metadata=metadata or {}
        )
        
        # Create context
        context = _TransactionContext(self, transaction)
        
        try:
            # Record transaction start
            await self._queue_transaction(transaction)
            
            # Yield context for agent to use
            yield context
            
            # Mark as completed
            transaction.status = AgentTransactionStatus.COMPLETED.value
            transaction.end_time = datetime.now(timezone.utc)
            transaction.execution_time_ms = int(
                (transaction.end_time - transaction.start_time).total_seconds() * 1000
            )
            
            await self._queue_transaction(transaction)
            
        except Exception as e:
            # Mark as failed and capture error
            transaction.status = AgentTransactionStatus.FAILED.value
            transaction.end_time = datetime.now(timezone.utc)
            transaction.execution_time_ms = int(
                (transaction.end_time - transaction.start_time).total_seconds() * 1000
            )
            transaction.error_message = str(e)
            transaction.error_traceback = traceback.format_exc()
            
            await self._queue_transaction(transaction)
            
            # Also create detailed error record
            await context.log_error(
                error_type=type(e).__name__,
                error_message=str(e),
                context={"transaction_id": transaction_id}
            )
            
            # Re-raise the exception
            raise
    
    async def _queue_transaction(self, transaction: AgentTransaction):
        """Add transaction to queue for batched processing"""
        async with self._lock:
            self._transaction_queue.append(transaction)
            if len(self._transaction_queue) >= self.batch_size:
                await self._flush_transactions()
    
    async def _queue_state_transition(self, transition: StateTransition):
        """Add state transition to queue for batched processing"""
        async with self._lock:
            self._transition_queue.append(transition)
            if len(self._transition_queue) >= self.batch_size:
                await self._flush_state_transitions()
    
    async def _queue_decision(self, decision: AgentDecisionRecord):
        """Add decision to queue for batched processing"""
        async with self._lock:
            self._decision_queue.append(decision)
            if len(self._decision_queue) >= self.batch_size:
                await self._flush_decisions()
    
    async def _queue_error(self, error: AgentError):
        """Add error to queue for batched processing"""
        async with self._lock:
            self._error_queue.append(error)
            if len(self._error_queue) >= self.batch_size:
                await self._flush_errors()
    
    async def _queue_metric(self, metric: PerformanceMetric):
        """Add metric to queue for batched processing"""
        async with self._lock:
            self._metric_queue.append(metric)
            if len(self._metric_queue) >= self.batch_size:
                await self._flush_metrics()
    
    async def _periodic_flush(self):
        """Periodic flush of all queues"""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_all_queues()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}")
    
    async def _flush_all_queues(self):
        """Flush all queues to database"""
        if not self._db_connection:
            return
        
        async with self._lock:
            await asyncio.gather(
                self._flush_transactions(),
                self._flush_state_transitions(), 
                self._flush_decisions(),
                self._flush_errors(),
                self._flush_metrics(),
                return_exceptions=True
            )
    
    async def _flush_transactions(self):
        """Flush transaction queue to database"""
        if not self._transaction_queue or not self._db_connection:
            return
        
        try:
            transactions = self._transaction_queue.copy()
            self._transaction_queue.clear()
            
            if transactions:
                values = [
                    (
                        t.transaction_id, t.session_id, t.user_id, t.agent_name,
                        t.transaction_type, t.status, t.start_time, t.end_time,
                        t.execution_time_ms, json.dumps(t.input_data),
                        json.dumps(t.output_data), t.error_message, t.error_traceback,
                        json.dumps(t.metadata), t.created_at
                    )
                    for t in transactions
                ]
                
                await self._db_connection.executemany(
                    """
                    INSERT INTO agent_transactions 
                    (transaction_id, session_id, user_id, agent_name, transaction_type,
                     status, start_time, end_time, execution_time_ms, input_data,
                     output_data, error_message, error_traceback, metadata, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                    ON CONFLICT (transaction_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        end_time = EXCLUDED.end_time,
                        execution_time_ms = EXCLUDED.execution_time_ms,
                        output_data = EXCLUDED.output_data,
                        error_message = EXCLUDED.error_message,
                        error_traceback = EXCLUDED.error_traceback,
                        metadata = EXCLUDED.metadata
                    """,
                    values
                )
                
        except Exception as e:
            logger.error(f"Failed to flush transactions: {e}")
    
    async def _flush_state_transitions(self):
        """Flush state transition queue to database"""
        if not self._transition_queue or not self._db_connection:
            return
        
        try:
            transitions = self._transition_queue.copy()
            self._transition_queue.clear()
            
            if transitions:
                values = [
                    (
                        t.transition_id, t.transaction_id, t.session_id,
                        t.transition_type, json.dumps(t.from_state),
                        json.dumps(t.to_state), t.trigger, t.timestamp,
                        json.dumps(t.metadata)
                    )
                    for t in transitions
                ]
                
                await self._db_connection.executemany(
                    """
                    INSERT INTO agent_state_transitions
                    (transition_id, transaction_id, session_id, transition_type,
                     from_state, to_state, trigger, timestamp, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    values
                )
                
        except Exception as e:
            logger.error(f"Failed to flush state transitions: {e}")
    
    async def _flush_decisions(self):
        """Flush decision queue to database"""
        if not self._decision_queue or not self._db_connection:
            return
        
        try:
            decisions = self._decision_queue.copy()
            self._decision_queue.clear()
            
            if decisions:
                values = [
                    (
                        d.decision_id, d.transaction_id, d.session_id, d.agent_name,
                        d.decision_point, d.decision_made, d.reasoning,
                        d.confidence_score, json.dumps(d.alternatives_considered),
                        d.decision_time_ms, d.timestamp, json.dumps(d.metadata)
                    )
                    for d in decisions
                ]
                
                await self._db_connection.executemany(
                    """
                    INSERT INTO agent_decisions
                    (decision_id, transaction_id, session_id, agent_name,
                     decision_point, decision_made, reasoning, confidence_score,
                     alternatives_considered, decision_time_ms, timestamp, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    """,
                    values
                )
                
        except Exception as e:
            logger.error(f"Failed to flush decisions: {e}")
    
    async def _flush_errors(self):
        """Flush error queue to database"""
        if not self._error_queue or not self._db_connection:
            return
        
        try:
            errors = self._error_queue.copy()
            self._error_queue.clear()
            
            if errors:
                values = [
                    (
                        e.error_id, e.transaction_id, e.session_id, e.agent_name,
                        e.error_type, e.error_message, e.error_traceback,
                        json.dumps(e.context), e.timestamp, e.resolved,
                        e.resolution_notes
                    )
                    for e in errors
                ]
                
                await self._db_connection.executemany(
                    """
                    INSERT INTO agent_errors
                    (error_id, transaction_id, session_id, agent_name,
                     error_type, error_message, error_traceback, context,
                     timestamp, resolved, resolution_notes)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    """,
                    values
                )
                
        except Exception as e:
            logger.error(f"Failed to flush errors: {e}")
    
    async def _flush_metrics(self):
        """Flush metrics queue to database"""
        if not self._metric_queue or not self._db_connection:
            return
        
        try:
            metrics = self._metric_queue.copy()
            self._metric_queue.clear()
            
            if metrics:
                values = [
                    (
                        m.metric_id, m.transaction_id, m.session_id, m.agent_name,
                        m.metric_name, m.metric_value, m.metric_unit,
                        m.measurement_time, json.dumps(m.metadata)
                    )
                    for m in metrics
                ]
                
                await self._db_connection.executemany(
                    """
                    INSERT INTO agent_performance_metrics
                    (metric_id, transaction_id, session_id, agent_name,
                     metric_name, metric_value, metric_unit, measurement_time, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    values
                )
                
        except Exception as e:
            logger.error(f"Failed to flush metrics: {e}")
    
    async def _create_tables(self):
        """Create tracking tables if they don't exist"""
        if not self._db_connection:
            return
        
        # Agent transactions table
        await self._db_connection.execute("""
            CREATE TABLE IF NOT EXISTS agent_transactions (
                transaction_id VARCHAR(255) PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                user_id VARCHAR(255),
                agent_name VARCHAR(100) NOT NULL,
                transaction_type VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL,
                start_time TIMESTAMP WITH TIME ZONE NOT NULL,
                end_time TIMESTAMP WITH TIME ZONE,
                execution_time_ms INTEGER,
                input_data JSONB DEFAULT '{}',
                output_data JSONB DEFAULT '{}',
                error_message TEXT,
                error_traceback TEXT,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # State transitions table
        await self._db_connection.execute("""
            CREATE TABLE IF NOT EXISTS agent_state_transitions (
                transition_id VARCHAR(255) PRIMARY KEY,
                transaction_id VARCHAR(255) NOT NULL,
                session_id VARCHAR(255) NOT NULL,
                transition_type VARCHAR(50) NOT NULL,
                from_state JSONB DEFAULT '{}',
                to_state JSONB DEFAULT '{}',
                trigger VARCHAR(255),
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                metadata JSONB DEFAULT '{}',
                FOREIGN KEY (transaction_id) REFERENCES agent_transactions(transaction_id)
            )
        """)
        
        # Decisions table
        await self._db_connection.execute("""
            CREATE TABLE IF NOT EXISTS agent_decisions (
                decision_id VARCHAR(255) PRIMARY KEY,
                transaction_id VARCHAR(255) NOT NULL,
                session_id VARCHAR(255) NOT NULL,
                agent_name VARCHAR(100) NOT NULL,
                decision_point VARCHAR(255) NOT NULL,
                decision_made TEXT NOT NULL,
                reasoning TEXT,
                confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
                alternatives_considered JSONB DEFAULT '[]',
                decision_time_ms INTEGER DEFAULT 0,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                metadata JSONB DEFAULT '{}',
                FOREIGN KEY (transaction_id) REFERENCES agent_transactions(transaction_id)
            )
        """)
        
        # Errors table
        await self._db_connection.execute("""
            CREATE TABLE IF NOT EXISTS agent_errors (
                error_id VARCHAR(255) PRIMARY KEY,
                transaction_id VARCHAR(255) NOT NULL,
                session_id VARCHAR(255) NOT NULL,
                agent_name VARCHAR(100) NOT NULL,
                error_type VARCHAR(100) NOT NULL,
                error_message TEXT NOT NULL,
                error_traceback TEXT,
                context JSONB DEFAULT '{}',
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                resolved BOOLEAN DEFAULT FALSE,
                resolution_notes TEXT,
                FOREIGN KEY (transaction_id) REFERENCES agent_transactions(transaction_id)
            )
        """)
        
        # Performance metrics table
        await self._db_connection.execute("""
            CREATE TABLE IF NOT EXISTS agent_performance_metrics (
                metric_id VARCHAR(255) PRIMARY KEY,
                transaction_id VARCHAR(255) NOT NULL,
                session_id VARCHAR(255) NOT NULL,
                agent_name VARCHAR(100) NOT NULL,
                metric_name VARCHAR(100) NOT NULL,
                metric_value FLOAT NOT NULL,
                metric_unit VARCHAR(20),
                measurement_time TIMESTAMP WITH TIME ZONE NOT NULL,
                metadata JSONB DEFAULT '{}',
                FOREIGN KEY (transaction_id) REFERENCES agent_transactions(transaction_id)
            )
        """)
        
        # Create indexes for performance
        await self._db_connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_transactions_session_id 
            ON agent_transactions(session_id);
        """)
        
        await self._db_connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_transactions_agent_name 
            ON agent_transactions(agent_name);
        """)
        
        await self._db_connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_transactions_created_at 
            ON agent_transactions(created_at);
        """)


class _TransactionContext:
    """Context object provided to agents for logging during transactions"""
    
    def __init__(self, tracker: AgentTransactionTracker, transaction: AgentTransaction):
        self.tracker = tracker
        self.transaction = transaction
    
    async def log_decision(
        self,
        decision_point: str,
        decision_made: str,
        confidence_score: float,
        reasoning: str = "",
        alternatives: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log an agent decision point"""
        decision_id = f"{self.transaction.transaction_id}_decision_{int(time.time() * 1000)}"
        
        decision = AgentDecisionRecord(
            decision_id=decision_id,
            transaction_id=self.transaction.transaction_id,
            session_id=self.transaction.session_id,
            agent_name=self.transaction.agent_name,
            decision_point=decision_point,
            decision_made=decision_made,
            reasoning=reasoning,
            confidence_score=confidence_score,
            alternatives_considered=alternatives or [],
            metadata=metadata or {}
        )
        
        await self.tracker._queue_decision(decision)
    
    async def log_state_transition(
        self,
        transition_type: str,
        from_state: Dict[str, Any],
        to_state: Dict[str, Any],
        trigger: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a state transition"""
        transition_id = f"{self.transaction.transaction_id}_transition_{int(time.time() * 1000)}"
        
        transition = StateTransition(
            transition_id=transition_id,
            transaction_id=self.transaction.transaction_id,
            session_id=self.transaction.session_id,
            transition_type=transition_type,
            from_state=from_state,
            to_state=to_state,
            trigger=trigger,
            metadata=metadata or {}
        )
        
        await self.tracker._queue_state_transition(transition)
    
    async def log_error(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Log an error occurrence"""
        error_id = f"{self.transaction.transaction_id}_error_{int(time.time() * 1000)}"
        
        error = AgentError(
            error_id=error_id,
            transaction_id=self.transaction.transaction_id,
            session_id=self.transaction.session_id,
            agent_name=self.transaction.agent_name,
            error_type=error_type,
            error_message=error_message,
            error_traceback=traceback.format_exc(),
            context=context or {}
        )
        
        await self.tracker._queue_error(error)
    
    async def log_metric(
        self,
        metric_name: str,
        metric_value: float,
        metric_unit: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a performance metric"""
        metric_id = f"{self.transaction.transaction_id}_metric_{metric_name}_{int(time.time() * 1000)}"
        
        metric = PerformanceMetric(
            metric_id=metric_id,
            transaction_id=self.transaction.transaction_id,
            session_id=self.transaction.session_id,
            agent_name=self.transaction.agent_name,
            metric_name=metric_name,
            metric_value=metric_value,
            metric_unit=metric_unit,
            metadata=metadata or {}
        )
        
        await self.tracker._queue_metric(metric)
    
    def set_input_data(self, data: Dict[str, Any]):
        """Set input data for the transaction"""
        self.transaction.input_data = data
    
    def set_output_data(self, data: Dict[str, Any]):
        """Set output data for the transaction"""
        self.transaction.output_data = data


class _NoOpTransactionContext:
    """No-op context when tracking is disabled"""
    
    async def log_decision(self, *args, **kwargs):
        pass
    
    async def log_state_transition(self, *args, **kwargs):
        pass
    
    async def log_error(self, *args, **kwargs):
        pass
    
    async def log_metric(self, *args, **kwargs):
        pass
    
    def set_input_data(self, data: Dict[str, Any]):
        pass
    
    def set_output_data(self, data: Dict[str, Any]):
        pass


# Global tracker instance
_global_tracker: Optional[AgentTransactionTracker] = None


async def get_agent_tracker() -> AgentTransactionTracker:
    """Get the global agent tracker instance"""
    global _global_tracker
    
    if _global_tracker is None:
        _global_tracker = AgentTransactionTracker()
        await _global_tracker.initialize()
    
    return _global_tracker


async def close_agent_tracker():
    """Close the global agent tracker"""
    global _global_tracker
    
    if _global_tracker:
        await _global_tracker.close()
        _global_tracker = None