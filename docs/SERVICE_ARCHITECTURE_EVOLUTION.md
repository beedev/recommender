# Service Architecture Evolution: Enterprise Agentic System

## Current Service Analysis

### **📊 Existing Services Audit**

#### **Services to Evolve (Keep & Enhance)**
```yaml
✅ embedding_generator.py:
  Purpose: Vector embedding generation for semantic search
  Status: Keep - Essential for Agent 2 hybrid search
  Enhancement: Add multilingual embedding support

✅ auth_service.py:
  Purpose: User authentication and authorization
  Status: Keep - Required for enterprise deployment
  Enhancement: Add role-based access (expert vs guided users)

✅ user_service.py:
  Purpose: User management and profiles
  Status: Keep - Required for personalization
  Enhancement: Add expertise level tracking
```

#### **Services to Archive (Move to /Archive)**
```yaml
❌ simple_orchestrator_service.py:
  Reason: Will be replaced by new 3-agent orchestrator
  Archive: Move to /Archive/services/

❌ sparky_service.py:
  Reason: Old single-agent approach, replaced by Agent 1
  Archive: Move to /Archive/services/

❌ vector_migration.py:
  Reason: One-time migration script, no longer needed
  Archive: Move to /Archive/services/
```

#### **API Endpoints to Archive**
```yaml
❌ enhanced_orchestrator.py:
  Status: Already marked as disabled
  Archive: Move to /Archive/api/

❌ recommendations.py:
  Reason: Phase 1 approach, replaced by agent-based system
  Archive: Move to /Archive/api/

❌ packages.py:
  Reason: Direct package building, replaced by Trinity formation
  Archive: Move to /Archive/api/
```

#### **API Endpoints to Evolve**
```yaml
✅ agent_recommendations.py:
  Purpose: Natural language query interface
  Status: Evolve into enterprise agentic API
  
✅ products.py:
  Purpose: Product catalog access
  Status: Keep for direct product queries
  
✅ health.py:
  Purpose: System health monitoring
  Status: Enhance with enterprise observability
  
✅ system.py:
  Purpose: System information
  Status: Enhance with agentic system metrics
```

---

## **🏗️ New Service Architecture Design**

### **Core Services (New Implementation)**

#### **1. Enterprise Orchestrator Service**
```python
# services/enterprise_orchestrator_service.py
class EnterpriseOrchestratorService:
    """
    Coordinates the 3-agent enterprise recommendation system
    with automatic mode detection and multilingual support
    """
    
    def __init__(self):
        self.agent_1 = IntelligentIntentProcessor()
        self.agent_2 = SmartNeo4jRecommender() 
        self.agent_3 = MultilingualResponseGenerator()
        self.observability = EnterpriseObservability()
    
    async def process_recommendation_request(
        self, 
        query: str, 
        user_context: UserContext,
        session_id: str
    ) -> EnterpriseRecommendationResponse:
        """Main orchestration workflow"""
        
        # Start observability tracking
        trace_id = self.observability.start_trace(session_id)
        
        try:
            # Agent 1: Intelligent Intent Processing
            processed_intent = await self.agent_1.process_query(
                query=query,
                user_context=user_context,
                trace_id=trace_id
            )
            
            # Agent 2: Smart Neo4j Recommendations
            recommendations = await self.agent_2.generate_recommendations(
                processed_intent=processed_intent,
                trace_id=trace_id
            )
            
            # Agent 3: Multilingual Response Generation
            response = await self.agent_3.generate_response(
                recommendations=recommendations,
                original_intent=processed_intent,
                trace_id=trace_id
            )
            
            # Complete observability tracking
            self.observability.complete_trace(trace_id, response)
            
            return response
            
        except Exception as e:
            self.observability.record_error(trace_id, e)
            raise
```

#### **2. Intelligent Intent Service**
```python
# services/intelligent_intent_service.py
class IntelligentIntentService:
    """
    Agent 1: Multilingual intent processing with automatic mode detection
    """
    
    def __init__(self):
        self.mode_detector = AutoModeDetector()
        self.multilingual_processor = MultilingualProcessor()
        self.intent_extractor = WeldingIntentExtractor()
        self.confidence_scorer = ConfidenceScorer()
    
    async def process_query(
        self, 
        query: str, 
        user_context: UserContext,
        trace_id: str
    ) -> ProcessedIntent:
        """Process natural language query into structured intent"""
        
        # Auto-detect language
        detected_language = await self.multilingual_processor.detect_language(query)
        
        # Translate to English if needed
        english_query = await self.multilingual_processor.translate_to_english(
            query, detected_language
        )
        
        # Auto-detect expertise mode
        expertise_mode = self.mode_detector.detect_user_expertise(
            query=english_query,
            user_history=user_context.history
        )
        
        # Extract welding intent
        intent = await self.intent_extractor.extract(
            query=english_query,
            expertise_mode=expertise_mode,
            user_context=user_context
        )
        
        # Calculate confidence
        confidence = self.confidence_scorer.calculate(intent, expertise_mode)
        
        return ProcessedIntent(
            original_query=query,
            processed_query=english_query,
            detected_language=detected_language,
            expertise_mode=expertise_mode,
            intent=intent,
            confidence=confidence,
            trace_id=trace_id
        )
```

#### **3. Smart Neo4j Service**
```python
# services/smart_neo4j_service.py
class SmartNeo4jService:
    """
    Agent 2: Enhanced Neo4j recommendations with graph algorithms
    """
    
    def __init__(self, neo4j_repo: Neo4jRepository):
        self.neo4j_repo = neo4j_repo
        self.embedding_generator = ProductEmbeddingGenerator()
        self.graph_algorithms = {
            "shortest_path": ShortestPathAlgorithm(),
            "pagerank": PageRankAlgorithm(),
            "centrality": CentralityAlgorithm()
        }
        self.trinity_former = TrinityPackageFormer()
    
    async def generate_recommendations(
        self,
        processed_intent: ProcessedIntent,
        trace_id: str
    ) -> ScoredRecommendations:
        """Generate Trinity package recommendations"""
        
        # Intelligent routing decision
        routing_decision = self._make_routing_decision(processed_intent)
        
        # Execute search strategy
        if routing_decision.strategy == "GRAPH_FOCUSED":
            candidates = await self._graph_search(processed_intent, routing_decision)
        else:  # HYBRID
            candidates = await self._hybrid_search(processed_intent, routing_decision)
        
        # Form Trinity packages
        trinity_packages = await self.trinity_former.form_packages(
            candidates=candidates,
            intent=processed_intent.intent,
            business_rules=self._load_business_rules()
        )
        
        # Score and rank packages
        scored_packages = await self._score_packages(trinity_packages, processed_intent)
        
        return ScoredRecommendations(
            packages=scored_packages,
            search_metadata=routing_decision,
            confidence_distribution=self._calculate_confidence_distribution(scored_packages),
            trace_id=trace_id
        )
    
    def _make_routing_decision(self, processed_intent: ProcessedIntent) -> RoutingDecision:
        """Simplified routing logic"""
        if (processed_intent.expertise_mode == "EXPERT" and 
            processed_intent.confidence > 0.8):
            return RoutingDecision(
                strategy="GRAPH_FOCUSED",
                algorithms=["shortest_path", "pagerank"],
                weights={"compatibility": 0.8, "popularity": 0.2}
            )
        else:
            return RoutingDecision(
                strategy="HYBRID", 
                algorithms=["shortest_path"],
                weights={"semantic": 0.4, "compatibility": 0.6}
            )
```

#### **4. Multilingual Response Service**
```python
# services/multilingual_response_service.py
class MultilingualResponseService:
    """
    Agent 3: Intelligent response generation with multilingual support
    """
    
    def __init__(self):
        self.explanation_generator = ExplanationGenerator()
        self.business_reranker = BusinessContextReranker()
        self.multilingual_translator = MultilingualTranslator()
        self.response_formatter = ResponseFormatter()
    
    async def generate_response(
        self,
        recommendations: ScoredRecommendations,
        original_intent: ProcessedIntent,
        trace_id: str
    ) -> EnterpriseRecommendationResponse:
        """Generate final multilingual response"""
        
        # Business context re-ranking
        reranked_packages = await self.business_reranker.rerank(
            packages=recommendations.packages,
            user_context=original_intent.user_context,
            business_priorities=self._load_business_priorities()
        )
        
        # Generate explanations based on expertise mode
        explanations = await self.explanation_generator.generate(
            packages=reranked_packages,
            expertise_mode=original_intent.expertise_mode,
            intent=original_intent.intent
        )
        
        # Format response
        formatted_response = await self.response_formatter.format(
            packages=reranked_packages,
            explanations=explanations,
            expertise_mode=original_intent.expertise_mode
        )
        
        # Translate back to original language if needed
        if original_intent.detected_language != "en":
            formatted_response = await self.multilingual_translator.translate(
                response=formatted_response,
                target_language=original_intent.detected_language
            )
        
        return EnterpriseRecommendationResponse(
            packages=reranked_packages,
            explanations=explanations,
            formatted_response=formatted_response,
            confidence=recommendations.confidence_distribution,
            search_metadata=recommendations.search_metadata,
            trace_id=trace_id
        )
```

#### **5. Enterprise Observability Service**
```python
# services/enterprise_observability_service.py
class EnterpriseObservabilityService:
    """
    Comprehensive observability for enterprise deployment
    """
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.trace_recorder = TraceRecorder()
        self.quality_monitor = QualityMonitor()
        self.alerting_system = AlertingSystem()
    
    def start_trace(self, session_id: str) -> str:
        """Start distributed tracing for recommendation flow"""
        trace_id = f"rec_{session_id}_{int(time.time())}"
        
        self.trace_recorder.start_trace(trace_id)
        self.metrics_collector.increment("recommendations.started")
        
        return trace_id
    
    def record_agent_execution(
        self, 
        trace_id: str, 
        agent_name: str, 
        duration_ms: float,
        success: bool
    ):
        """Record individual agent performance"""
        self.trace_recorder.add_span(trace_id, agent_name, duration_ms)
        self.metrics_collector.record_latency(f"agent.{agent_name}.duration", duration_ms)
        
        if not success:
            self.metrics_collector.increment(f"agent.{agent_name}.errors")
    
    def complete_trace(self, trace_id: str, response: EnterpriseRecommendationResponse):
        """Complete tracing and record quality metrics"""
        self.trace_recorder.complete_trace(trace_id)
        
        # Record quality metrics
        self.quality_monitor.record_recommendation_quality(
            trace_id=trace_id,
            packages_returned=len(response.packages),
            confidence=response.confidence,
            trinity_formation_rate=self._calculate_trinity_rate(response.packages)
        )
        
        # Check for alerts
        if response.confidence < 0.6:
            self.alerting_system.send_alert(
                "LOW_CONFIDENCE_RECOMMENDATION",
                f"Trace {trace_id} has confidence {response.confidence}"
            )
```

---

## **🔄 API Endpoint Evolution**

### **New Enterprise API Endpoints**

#### **1. Main Enterprise Recommendation API**
```python
# api/v1/enterprise_recommendations.py
@router.post("/recommendations/enterprise")
async def enterprise_recommendations(
    request: EnterpriseRecommendationRequest,
    user_context: UserContext = Depends(get_current_user_context),
    orchestrator: EnterpriseOrchestratorService = Depends(get_orchestrator)
) -> EnterpriseRecommendationResponse:
    """
    Enterprise-grade natural language recommendations
    with automatic mode detection and multilingual support
    """
    
    session_id = request.session_id or str(uuid.uuid4())
    
    response = await orchestrator.process_recommendation_request(
        query=request.query,
        user_context=user_context,
        session_id=session_id
    )
    
    return response

class EnterpriseRecommendationRequest(BaseModel):
    query: str = Field(..., min_length=5, max_length=2000)
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    max_results: int = Field(default=10, ge=1, le=50)
    include_explanations: bool = Field(default=True)
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "query": "I need a welding setup for aluminum car parts",
                    "max_results": 5,
                    "include_explanations": True
                },
                {
                    "query": "PowerWave 450 compatible feeder and cooler",
                    "max_results": 10,
                    "include_explanations": True
                },
                {
                    "query": "Necesito una soldadora para acero inoxidable",
                    "max_results": 8,
                    "include_explanations": True
                }
            ]
        }
```

#### **2. System Health & Metrics API**
```python
# api/v1/enterprise_health.py
@router.get("/health/enterprise")
async def enterprise_health(
    observability: EnterpriseObservabilityService = Depends(get_observability)
) -> EnterpriseHealthResponse:
    """Comprehensive system health for enterprise monitoring"""
    
    return EnterpriseHealthResponse(
        status="healthy",
        agents_status={
            "intent_processor": "healthy",
            "neo4j_recommender": "healthy", 
            "response_generator": "healthy"
        },
        performance_metrics=observability.get_performance_summary(),
        quality_metrics=observability.get_quality_metrics(),
        neo4j_status=await check_neo4j_health(),
        embedding_service_status=await check_embedding_service_health()
    )

@router.get("/metrics/enterprise")
async def enterprise_metrics(
    observability: EnterpriseObservabilityService = Depends(get_observability)
) -> EnterpriseMetricsResponse:
    """Real-time enterprise metrics for monitoring dashboards"""
    
    return EnterpriseMetricsResponse(
        recommendation_metrics={
            "total_requests": observability.get_total_requests(),
            "avg_response_time": observability.get_avg_response_time(),
            "success_rate": observability.get_success_rate(),
            "trinity_formation_rate": observability.get_trinity_formation_rate()
        },
        agent_metrics={
            "intent_processing_avg": observability.get_agent_avg_time("intent"),
            "neo4j_query_avg": observability.get_agent_avg_time("neo4j"),
            "response_generation_avg": observability.get_agent_avg_time("response")
        },
        quality_metrics={
            "avg_confidence": observability.get_avg_confidence(),
            "high_confidence_rate": observability.get_high_confidence_rate(),
            "multilingual_usage": observability.get_multilingual_stats()
        }
    )
```

---

## **📋 Migration Plan**

### **Phase 1: Archive Old Services (Week 1)**
```bash
# Move to Archive
mkdir -p /Archive/services
mkdir -p /Archive/api

mv backend/app/services/simple_orchestrator_service.py /Archive/services/
mv backend/app/services/sparky_service.py /Archive/services/
mv backend/app/services/vector_migration.py /Archive/services/

mv backend/app/api/v1/enhanced_orchestrator.py /Archive/api/
mv backend/app/api/v1/recommendations.py /Archive/api/
mv backend/app/api/v1/packages.py /Archive/api/
```

### **Phase 2: Implement Core Services (Week 2-3)**
```python
# Implement new services
services/enterprise_orchestrator_service.py
services/intelligent_intent_service.py
services/smart_neo4j_service.py
services/multilingual_response_service.py
services/enterprise_observability_service.py
```

### **Phase 3: Implement New APIs (Week 4)**
```python
# Implement new API endpoints
api/v1/enterprise_recommendations.py
api/v1/enterprise_health.py
api/v1/enterprise_metrics.py
```

### **Phase 4: Enhanced Existing Services (Week 5)**
```python
# Enhance existing services
embedding_generator.py → Add multilingual support
auth_service.py → Add role-based access
user_service.py → Add expertise tracking
```

This evolution transforms our service architecture from a basic 2-agent system into an enterprise-grade platform while maintaining backward compatibility and adding comprehensive observability.