import React, { useState } from 'react'
import clsx from 'clsx'
import { 
  EnhancedWeldingPackage, 
  AgentDecision,
  EnhancedOrchestratorResponse 
} from '../../../types/enhanced-orchestrator'
import Card from '../../common/Card'
import Badge from '../../common/Badge'
import Button from '../../common/Button'
import PackageCard from '../PackageCard'
import { 
  CpuChipIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  StarIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  BeakerIcon,
  CurrencyDollarIcon,
  UserGroupIcon
} from '@heroicons/react/24/outline'

interface AgentRecommendationDisplayProps {
  response: EnhancedOrchestratorResponse
  selectedPackage?: EnhancedWeldingPackage
  onPackageSelect?: (packageData: EnhancedWeldingPackage) => void
  onViewDetails?: (packageData: EnhancedWeldingPackage) => void
  showAgentDetails?: boolean
  className?: string
}

interface AgentDecisionCardProps {
  decision: AgentDecision
  expanded?: boolean
  onToggle?: () => void
}

const AgentDecisionCard: React.FC<AgentDecisionCardProps> = ({
  decision,
  expanded = false,
  onToggle
}) => {
  const getAgentIcon = (agentRole: string) => {
    switch (agentRole.toLowerCase()) {
      case 'translation_agent':
      case 'translation agent':
        return UserGroupIcon
      case 'compatibility_agent':
      case 'compatibility agent':
        return ShieldCheckIcon
      case 'sales_agent':
      case 'sales agent':
        return ChartBarIcon
      case 'recommendation_agent':
      case 'recommendation agent':
        return StarIcon
      case 'package_agent':
      case 'package agent':
        return CurrencyDollarIcon
      case 'validation_agent':
      case 'validation agent':
        return BeakerIcon
      default:
        return CpuChipIcon
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'success'
    if (confidence >= 0.6) return 'warning'
    return 'error'
  }

  const AgentIcon = getAgentIcon(decision.agent_role)
  const confidenceColor = getConfidenceColor(decision.confidence)

  return (
    <Card variant="outlined" className="mb-3">
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3 flex-1">
            <div className="p-2 bg-sparky-gold/10 rounded-lg">
              <AgentIcon className="w-5 h-5 text-sparky-gold" />
            </div>
            
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-2">
                <h4 className="font-semibold text-neutral-900 dark:text-neutral-100">
                  {decision.agent_role.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </h4>
                <Badge variant={confidenceColor as any} size="sm">
                  {Math.round(decision.confidence * 100)}% confidence
                </Badge>
              </div>
              
              <p className="text-sm text-neutral-700 dark:text-neutral-300 mb-2">
                {decision.decision}
              </p>
              
              <div className="flex items-center space-x-4 text-xs text-neutral-500">
                <div className="flex items-center space-x-1">
                  <ClockIcon className="w-3 h-3" />
                  <span>{new Date(decision.timestamp).toLocaleTimeString()}</span>
                </div>
                {decision.tools_used.length > 0 && (
                  <div>
                    Tools: {decision.tools_used.join(', ')}
                  </div>
                )}
              </div>
            </div>
          </div>
          
          {onToggle && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onToggle}
              className="p-1 ml-2"
            >
              {expanded ? (
                <ChevronDownIcon className="w-4 h-4" />
              ) : (
                <ChevronRightIcon className="w-4 h-4" />
              )}
            </Button>
          )}
        </div>
        
        {expanded && (
          <div className="mt-4 pt-4 border-t border-neutral-200 dark:border-neutral-700">
            <div className="space-y-3">
              {/* Detailed Reasoning */}
              <div>
                <h5 className="font-medium text-neutral-900 dark:text-neutral-100 mb-2">
                  Reasoning
                </h5>
                <p className="text-sm text-neutral-600 dark:text-neutral-400">
                  {decision.reasoning}
                </p>
              </div>
              
              {/* Data Sources */}
              {decision.data_sources.length > 0 && (
                <div>
                  <h5 className="font-medium text-neutral-900 dark:text-neutral-100 mb-2">
                    Data Sources
                  </h5>
                  <div className="flex flex-wrap gap-1">
                    {decision.data_sources.map((source, index) => (
                      <Badge key={index} variant="secondary" size="sm">
                        {source}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Tools Used */}
              {decision.tools_used.length > 0 && (
                <div>
                  <h5 className="font-medium text-neutral-900 dark:text-neutral-100 mb-2">
                    Tools Used
                  </h5>
                  <div className="flex flex-wrap gap-1">
                    {decision.tools_used.map((tool, index) => (
                      <Badge key={index} variant="outline" size="sm">
                        {tool}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </Card>
  )
}

const AgentRecommendationDisplay: React.FC<AgentRecommendationDisplayProps> = ({
  response,
  selectedPackage,
  onPackageSelect,
  onViewDetails,
  showAgentDetails = true,
  className
}) => {
  const [expandedDecisions, setExpandedDecisions] = useState<Set<number>>(new Set())
  const [showAllDecisions, setShowAllDecisions] = useState(false)

  const toggleDecision = (index: number) => {
    const newExpanded = new Set(expandedDecisions)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedDecisions(newExpanded)
  }

  const packages = response.data.packages
  const agentDecisions = response.metadata ? [] : [] // Agent decisions would come from the response
  const hasDecisions = agentDecisions.length > 0

  // Get processing metrics
  const processingTime = response.processing_time_ms
  const agentCount = response.metadata.agent_decisions_count
  const validationScore = response.metadata.validation_score
  const recommendationConfidence = response.metadata.recommendation_confidence
  const compatibilityConfidence = response.metadata.compatibility_confidence

  return (
    <div className={clsx('space-y-6', className)}>
      {/* Processing Summary */}
      <Card variant="default" shadow="md">
        <Card.Header>
          <Card.Title className="flex items-center">
            <CpuChipIcon className="w-5 h-5 mr-2 text-sparky-gold" />
            AI Recommendation Summary
          </Card.Title>
          <Card.Description>
            Processed by {agentCount} specialized agents in {processingTime}ms
          </Card.Description>
        </Card.Header>
        
        <Card.Content>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Recommendation Confidence */}
            <div className="text-center p-4 bg-sparky-gold/10 rounded-lg">
              <div className="text-2xl font-bold text-sparky-gold mb-1">
                {Math.round(recommendationConfidence * 100)}%
              </div>
              <div className="text-sm text-neutral-600 dark:text-neutral-400">
                Recommendation Confidence
              </div>
            </div>
            
            {/* Compatibility Score */}
            <div className="text-center p-4 bg-success-50 dark:bg-success-900/20 rounded-lg">
              <div className="text-2xl font-bold text-success-600 mb-1">
                {Math.round(compatibilityConfidence * 100)}%
              </div>
              <div className="text-sm text-neutral-600 dark:text-neutral-400">
                Compatibility Score
              </div>
            </div>
            
            {/* Validation Score */}
            <div className="text-center p-4 bg-info-50 dark:bg-info-900/20 rounded-lg">
              <div className="text-2xl font-bold text-info-600 mb-1">
                {Math.round(validationScore * 100)}%
              </div>
              <div className="text-sm text-neutral-600 dark:text-neutral-400">
                Validation Score
              </div>
            </div>
          </div>
          
          {/* Enhanced Features Used */}
          <div className="mt-4 p-3 bg-neutral-50 dark:bg-neutral-800 rounded-lg">
            <h4 className="font-medium text-neutral-900 dark:text-neutral-100 mb-2">
              Enhanced Features Used
            </h4>
            <div className="flex flex-wrap gap-2">
              {response.metadata.enhanced_features.flow_manager_used && (
                <Badge variant="success" size="sm">
                  <CheckCircleIcon className="w-3 h-3 mr-1" />
                  Flow Manager
                </Badge>
              )}
              {response.metadata.enhanced_features.error_handler_used && (
                <Badge variant="warning" size="sm">
                  <ExclamationTriangleIcon className="w-3 h-3 mr-1" />
                  Error Handler
                </Badge>
              )}
              {response.metadata.enhanced_features.hierarchical_state && (
                <Badge variant="info" size="sm">
                  <InformationCircleIcon className="w-3 h-3 mr-1" />
                  Hierarchical State
                </Badge>
              )}
              {response.metadata.enhanced_features.observability_enabled && (
                <Badge variant="secondary" size="sm">
                  <ChartBarIcon className="w-3 h-3 mr-1" />
                  Observability
                </Badge>
              )}
            </div>
          </div>
        </Card.Content>
      </Card>

      {/* Agent Decision Timeline */}
      {showAgentDetails && hasDecisions && (
        <Card variant="default" shadow="md">
          <Card.Header>
            <div className="flex items-center justify-between">
              <div>
                <Card.Title className="flex items-center">
                  <BeakerIcon className="w-5 h-5 mr-2 text-sparky-gold" />
                  Agent Decision Timeline
                </Card.Title>
                <Card.Description>
                  Step-by-step reasoning from each AI agent
                </Card.Description>
              </div>
              
              {agentDecisions.length > 3 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowAllDecisions(!showAllDecisions)}
                >
                  {showAllDecisions ? 'Show Less' : `Show All ${agentDecisions.length}`}
                </Button>
              )}
            </div>
          </Card.Header>
          
          <Card.Content>
            <div className="space-y-3">
              {(showAllDecisions ? agentDecisions : agentDecisions.slice(0, 3)).map((decision, index) => (
                <AgentDecisionCard
                  key={index}
                  decision={decision}
                  expanded={expandedDecisions.has(index)}
                  onToggle={() => toggleDecision(index)}
                />
              ))}
            </div>
          </Card.Content>
        </Card>
      )}

      {/* Package Recommendations */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
            Recommended Packages ({packages.length})
          </h2>
          
          {packages.length > 1 && (
            <Badge variant="info" size="md">
              Multiple options available
            </Badge>
          )}
        </div>
        
        {packages.length === 0 ? (
          <Card variant="outlined" className="text-center py-8">
            <div className="flex flex-col items-center space-y-3">
              <InformationCircleIcon className="w-12 h-12 text-neutral-400" />
              <div>
                <h3 className="font-medium text-neutral-900 dark:text-neutral-100 mb-1">
                  No Packages Found
                </h3>
                <p className="text-sm text-neutral-600 dark:text-neutral-400">
                  The AI agents couldn't find suitable packages for your requirements.
                  Try adjusting your criteria or contact support for assistance.
                </p>
              </div>
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {packages.map((pkg, index) => (
              <PackageCard
                key={pkg.package_id}
                package={pkg}
                selected={selectedPackage?.package_id === pkg.package_id}
                onSelect={onPackageSelect || undefined}
                onViewDetails={onViewDetails}
                showComparison={packages.length > 1}
                className={index === 0 ? 'ring-2 ring-sparky-gold/30' : undefined}
              />
            ))}
          </div>
        )}
      </div>

      {/* Warnings and Errors */}
      {(response.warnings?.length || response.errors?.length) && (
        <Card variant="outlined">
          <Card.Header>
            <Card.Title className="flex items-center text-warning-600">
              <ExclamationTriangleIcon className="w-5 h-5 mr-2" />
              Notices
            </Card.Title>
          </Card.Header>
          
          <Card.Content>
            <div className="space-y-3">
              {response.errors?.map((error, index) => (
                <div key={index} className="p-3 bg-error-50 dark:bg-error-900/20 border border-error-200 dark:border-error-800 rounded-lg">
                  <div className="flex items-start space-x-2">
                    <ExclamationTriangleIcon className="w-4 h-4 text-error-500 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="font-medium text-error-700 dark:text-error-300 text-sm">
                        Error
                      </div>
                      <div className="text-sm text-error-600 dark:text-error-400">
                        {error}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              
              {response.warnings?.map((warning, index) => (
                <div key={index} className="p-3 bg-warning-50 dark:bg-warning-900/20 border border-warning-200 dark:border-warning-800 rounded-lg">
                  <div className="flex items-start space-x-2">
                    <InformationCircleIcon className="w-4 h-4 text-warning-500 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="font-medium text-warning-700 dark:text-warning-300 text-sm">
                        Warning
                      </div>
                      <div className="text-sm text-warning-600 dark:text-warning-400">
                        {warning}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card.Content>
        </Card>
      )}
    </div>
  )
}

export default AgentRecommendationDisplay