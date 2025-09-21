import React from 'react'
import clsx from 'clsx'
import { EnhancedWeldingPackage } from '../../../types/enhanced-orchestrator'
import Card from '../../common/Card'
import Badge from '../../common/Badge'
import { 
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  InformationCircleIcon,
  ChartBarIcon,
  StarIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline'

interface CompatibilityScoreProps {
  package: EnhancedWeldingPackage
  showDetails?: boolean
  showRecommendationReason?: boolean
  className?: string
}

interface ScoreIndicatorProps {
  score: number
  label: string
  description?: string
  icon?: React.ComponentType<any>
}

const ScoreIndicator: React.FC<ScoreIndicatorProps> = ({
  score,
  label,
  description,
  icon: IconComponent = CheckCircleIcon
}) => {
  const getScoreInfo = (score: number) => {
    if (score >= 0.8) {
      return {
        level: 'Excellent',
        color: 'success',
        bgColor: 'bg-success-50 dark:bg-success-900/20',
        borderColor: 'border-success-200 dark:border-success-800',
        textColor: 'text-success-700 dark:text-success-300',
        iconColor: 'text-success-500',
        icon: CheckCircleIcon
      }
    }
    if (score >= 0.6) {
      return {
        level: 'Good',
        color: 'warning',
        bgColor: 'bg-warning-50 dark:bg-warning-900/20',
        borderColor: 'border-warning-200 dark:border-warning-800',
        textColor: 'text-warning-700 dark:text-warning-300',
        iconColor: 'text-warning-500',
        icon: ExclamationTriangleIcon
      }
    }
    return {
      level: 'Needs Review',
      color: 'error',
      bgColor: 'bg-error-50 dark:bg-error-900/20',
      borderColor: 'border-error-200 dark:border-error-800',
      textColor: 'text-error-700 dark:text-error-300',
      iconColor: 'text-error-500',
      icon: XCircleIcon
    }
  }

  const scoreInfo = getScoreInfo(score)
  const ScoreIcon = IconComponent

  return (
    <div className={clsx(
      'p-4 rounded-lg border',
      scoreInfo.bgColor,
      scoreInfo.borderColor
    )}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <ScoreIcon className={clsx('w-5 h-5', scoreInfo.iconColor)} />
          <span className="font-medium text-neutral-900 dark:text-neutral-100">
            {label}
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
            {Math.round(score * 100)}%
          </span>
          <Badge variant={scoreInfo.color as any} size="sm">
            {scoreInfo.level}
          </Badge>
        </div>
      </div>
      
      {description && (
        <p className={clsx('text-sm', scoreInfo.textColor)}>
          {description}
        </p>
      )}
      
      {/* Progress bar */}
      <div className="mt-3">
        <div className="w-full bg-neutral-200 dark:bg-neutral-700 rounded-full h-2">
          <div
            className={clsx(
              'h-2 rounded-full transition-all duration-300',
              score >= 0.8 && 'bg-success-500',
              score >= 0.6 && score < 0.8 && 'bg-warning-500',
              score < 0.6 && 'bg-error-500'
            )}
            style={{ width: `${score * 100}%` }}
          />
        </div>
      </div>
    </div>
  )
}

const CompatibilityScore: React.FC<CompatibilityScoreProps> = ({
  package: packageData,
  showDetails = true,
  showRecommendationReason = true,
  className
}) => {
  const compatibilityScore = packageData.compatibility_confidence
  const validationScore = packageData.metadata?.validation_score
  const hasMultipleScores = validationScore !== undefined

  // Calculate overall score if we have multiple metrics
  const overallScore = hasMultipleScores 
    ? (compatibilityScore + validationScore!) / 2 
    : compatibilityScore

  return (
    <Card
      variant="default"
      shadow="md"
      className={className}
    >
      <Card.Header>
        <Card.Title className="flex items-center">
          <ShieldCheckIcon className="w-5 h-5 mr-2 text-sparky-gold" />
          Compatibility Analysis
        </Card.Title>
        <Card.Description>
          AI-powered compatibility assessment based on your requirements
        </Card.Description>
      </Card.Header>

      <Card.Content>
        <div className="space-y-4">
          {/* Overall Score (if multiple metrics) */}
          {hasMultipleScores && (
            <ScoreIndicator
              score={overallScore}
              label="Overall Compatibility"
              description="Combined assessment of all compatibility factors"
              icon={StarIcon}
            />
          )}

          {/* Compatibility Score */}
          <ScoreIndicator
            score={compatibilityScore}
            label="Technical Compatibility"
            description="How well this package matches your technical requirements"
            icon={CheckCircleIcon}
          />

          {/* Validation Score */}
          {validationScore !== undefined && (
            <ScoreIndicator
              score={validationScore}
              label="Validation Score"
              description="Verification of package completeness and configuration"
              icon={ShieldCheckIcon}
            />
          )}

          {/* Component-level compatibility */}
          {showDetails && (
            <div className="mt-6">
              <h4 className="font-medium text-neutral-900 dark:text-neutral-100 mb-3 flex items-center">
                <ChartBarIcon className="w-4 h-4 mr-1 text-neutral-500" />
                Component Compatibility
              </h4>
              
              <div className="space-y-2">
                {/* Power Source */}
                {packageData.powersource.compatibility_score !== undefined && (
                  <div className="flex items-center justify-between p-3 bg-neutral-50 dark:bg-neutral-800 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 rounded-full bg-sparky-gold" />
                      <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                        {packageData.powersource.product_name}
                      </span>
                      <span className="text-xs text-neutral-500">Power Source</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                        {Math.round(packageData.powersource.compatibility_score * 100)}%
                      </span>
                      <div className="w-16 bg-neutral-200 dark:bg-neutral-700 rounded-full h-1.5">
                        <div
                          className="bg-sparky-gold h-1.5 rounded-full"
                          style={{ width: `${packageData.powersource.compatibility_score * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Other components with compatibility scores */}
                {[
                  { component: packageData.feeder, label: 'Wire Feeder' },
                  { component: packageData.cooler, label: 'Cooling System' },
                  { component: packageData.torch, label: 'Welding Torch' }
                ].map(({ component, label }) => (
                  component?.compatibility_score !== undefined && (
                    <div key={label} className="flex items-center justify-between p-3 bg-neutral-50 dark:bg-neutral-800 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 rounded-full bg-neutral-400" />
                        <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                          {component.product_name}
                        </span>
                        <span className="text-xs text-neutral-500">{label}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                          {Math.round(component.compatibility_score * 100)}%
                        </span>
                        <div className="w-16 bg-neutral-200 dark:bg-neutral-700 rounded-full h-1.5">
                          <div
                            className="bg-neutral-400 h-1.5 rounded-full"
                            style={{ width: `${component.compatibility_score * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  )
                ))}
              </div>
            </div>
          )}

          {/* Recommendation Reason */}
          {showRecommendationReason && packageData.recommendation_reason && (
            <div className="mt-6 p-4 bg-sparky-gold/10 border border-sparky-gold/20 rounded-lg">
              <div className="flex items-start space-x-3">
                <StarIcon className="w-5 h-5 text-sparky-gold mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="font-medium text-neutral-900 dark:text-neutral-100 mb-2">
                    Why This Package?
                  </h4>
                  <p className="text-sm text-neutral-700 dark:text-neutral-300">
                    {packageData.recommendation_reason}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Sales Evidence */}
          {packageData.sales_evidence && (
            <div className="mt-4 p-4 bg-info-50 dark:bg-info-900/20 border border-info-200 dark:border-info-800 rounded-lg">
              <div className="flex items-start space-x-3">
                <ChartBarIcon className="w-5 h-5 text-info-500 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="font-medium text-neutral-900 dark:text-neutral-100 mb-2">
                    Market Intelligence
                  </h4>
                  <p className="text-sm text-neutral-700 dark:text-neutral-300">
                    {packageData.sales_evidence}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Compatibility Tips */}
          <div className="mt-6 p-4 bg-neutral-50 dark:bg-neutral-800 rounded-lg">
            <div className="flex items-start space-x-3">
              <InformationCircleIcon className="w-5 h-5 text-neutral-500 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="font-medium text-neutral-900 dark:text-neutral-100 mb-2">
                  Compatibility Notes
                </h4>
                <ul className="text-sm text-neutral-600 dark:text-neutral-400 space-y-1">
                  <li>• Compatibility scores are based on technical specifications and usage patterns</li>
                  <li>• Higher scores indicate better alignment with your requirements</li>
                  <li>• Scores below 60% may require additional consultation</li>
                  <li>• Final compatibility should be verified with technical specifications</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </Card.Content>
    </Card>
  )
}

export default CompatibilityScore