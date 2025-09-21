import React from 'react'
import clsx from 'clsx'
import { EnhancedWeldingPackage } from '../../../types/enhanced-orchestrator'
import Card from '../../common/Card'
import Badge from '../../common/Badge'
import Button from '../../common/Button'
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon,
  InformationCircleIcon,

  ChartBarIcon,
  StarIcon
} from '@heroicons/react/24/outline'

interface PackageCardProps {
  package: EnhancedWeldingPackage
  selected?: boolean
  onSelect?: ((packageData: EnhancedWeldingPackage) => void) | undefined
  onViewDetails?: (packageData: EnhancedWeldingPackage) => void
  showComparison?: boolean
  className?: string
}

const PackageCard: React.FC<PackageCardProps> = ({
  package: packageData,
  selected = false,
  onSelect,
  onViewDetails,
  showComparison = false,
  className
}) => {
  const handleSelect = () => {
    onSelect?.(packageData)
  }

  const handleViewDetails = () => {
    onViewDetails?.(packageData)
  }

  // Calculate confidence level for display
  const getConfidenceLevel = (score: number) => {
    if (score >= 0.8) return { level: 'high', color: 'success', icon: CheckCircleIcon }
    if (score >= 0.6) return { level: 'medium', color: 'warning', icon: ExclamationTriangleIcon }
    return { level: 'low', color: 'error', icon: InformationCircleIcon }
  }

  const compatibilityInfo = getConfidenceLevel(packageData.compatibility_confidence)
  const validationInfo = packageData.metadata?.validation_score 
    ? getConfidenceLevel(packageData.metadata.validation_score) 
    : null

  // Format price
  const formatPrice = (price?: number) => {
    if (!price) return 'Price on request'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price)
  }

  // Get sales frequency badge variant
  const getSalesFrequencyVariant = (frequency?: string) => {
    switch (frequency?.toLowerCase()) {
      case 'high': return 'success'
      case 'medium': return 'warning'
      case 'low': return 'secondary'
      default: return 'secondary'
    }
  }

  return (
    <Card
      variant="default"
      shadow="esab"
      hover={!selected}
      interactive={!!onSelect}
      className={clsx(
        'relative transition-all duration-200',
        selected && 'ring-2 ring-sparky-gold ring-offset-2 shadow-esab-lg',
        className
      )}
      onClick={onSelect ? handleSelect : undefined}
    >
      {/* Selection indicator */}
      {selected && (
        <div className="absolute -top-2 -right-2 z-10">
          <div className="bg-sparky-gold text-black rounded-full p-1">
            <CheckCircleIcon className="w-5 h-5" />
          </div>
        </div>
      )}

      <Card.Header>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <Card.Title className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
              {packageData.package_name || `Package ${packageData.package_id}`}
            </Card.Title>
            {packageData.description && (
              <Card.Description className="mt-1">
                {packageData.description}
              </Card.Description>
            )}
          </div>
          
          {/* Price */}
          <div className="text-right ml-4">
            <div className="text-2xl font-bold text-sparky-gold">
              {formatPrice(packageData.total_price)}
            </div>
            {packageData.powersource.sales_frequency && (
              <Badge 
                variant={getSalesFrequencyVariant(packageData.powersource.sales_frequency)}
                size="sm"
                className="mt-1"
              >
                {packageData.powersource.sales_frequency} demand
              </Badge>
            )}
          </div>
        </div>
      </Card.Header>

      <Card.Content>
        {/* Main Components */}
        <div className="space-y-3 mb-4">
          {/* Power Source */}
          <div className="flex items-center justify-between p-3 bg-neutral-50 dark:bg-neutral-800 rounded-lg">
            <div className="flex-1">
              <div className="font-medium text-neutral-900 dark:text-neutral-100">
                {packageData.powersource.product_name}
              </div>
              <div className="text-sm text-neutral-600 dark:text-neutral-400">
                Power Source • {packageData.powersource.category}
              </div>
            </div>
            {packageData.powersource.price && (
              <div className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                {formatPrice(packageData.powersource.price)}
              </div>
            )}
          </div>

          {/* Optional Components */}
          {packageData.feeder && (
            <div className="flex items-center justify-between p-3 bg-neutral-50 dark:bg-neutral-800 rounded-lg">
              <div className="flex-1">
                <div className="font-medium text-neutral-900 dark:text-neutral-100">
                  {packageData.feeder.product_name}
                </div>
                <div className="text-sm text-neutral-600 dark:text-neutral-400">
                  Feeder • {packageData.feeder.category}
                </div>
              </div>
              {packageData.feeder.price && (
                <div className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                  {formatPrice(packageData.feeder.price)}
                </div>
              )}
            </div>
          )}

          {packageData.cooler && (
            <div className="flex items-center justify-between p-3 bg-neutral-50 dark:bg-neutral-800 rounded-lg">
              <div className="flex-1">
                <div className="font-medium text-neutral-900 dark:text-neutral-100">
                  {packageData.cooler.product_name}
                </div>
                <div className="text-sm text-neutral-600 dark:text-neutral-400">
                  Cooler • {packageData.cooler.category}
                </div>
              </div>
              {packageData.cooler.price && (
                <div className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                  {formatPrice(packageData.cooler.price)}
                </div>
              )}
            </div>
          )}

          {packageData.torch && (
            <div className="flex items-center justify-between p-3 bg-neutral-50 dark:bg-neutral-800 rounded-lg">
              <div className="flex-1">
                <div className="font-medium text-neutral-900 dark:text-neutral-100">
                  {packageData.torch.product_name}
                </div>
                <div className="text-sm text-neutral-600 dark:text-neutral-400">
                  Torch • {packageData.torch.category}
                </div>
              </div>
              {packageData.torch.price && (
                <div className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                  {formatPrice(packageData.torch.price)}
                </div>
              )}
            </div>
          )}

          {/* Accessories */}
          {packageData.accessories.length > 0 && (
            <div className="p-3 bg-neutral-50 dark:bg-neutral-800 rounded-lg">
              <div className="font-medium text-neutral-900 dark:text-neutral-100 mb-2">
                Accessories ({packageData.accessories.length})
              </div>
              <div className="space-y-1">
                {packageData.accessories.slice(0, 3).map((accessory, index) => (
                  <div key={index} className="flex items-center justify-between text-sm">
                    <span className="text-neutral-600 dark:text-neutral-400">
                      {accessory.product_name}
                    </span>
                    {accessory.price && (
                      <span className="text-neutral-700 dark:text-neutral-300">
                        {formatPrice(accessory.price)}
                      </span>
                    )}
                  </div>
                ))}
                {packageData.accessories.length > 3 && (
                  <div className="text-sm text-neutral-500 dark:text-neutral-400">
                    +{packageData.accessories.length - 3} more accessories
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Confidence Scores */}
        <div className="space-y-2 mb-4">
          {/* Compatibility Score */}
          <div className="flex items-center justify-between p-2 bg-white dark:bg-neutral-900 rounded border">
            <div className="flex items-center space-x-2">
              <compatibilityInfo.icon className={clsx(
                'w-4 h-4',
                compatibilityInfo.color === 'success' && 'text-success-500',
                compatibilityInfo.color === 'warning' && 'text-warning-500',
                compatibilityInfo.color === 'error' && 'text-error-500'
              )} />
              <span className="text-sm font-medium">Compatibility</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="text-sm text-neutral-600 dark:text-neutral-400">
                {Math.round(packageData.compatibility_confidence * 100)}%
              </div>
              <Badge 
                variant={compatibilityInfo.color as any}
                size="sm"
              >
                {compatibilityInfo.level}
              </Badge>
            </div>
          </div>

          {/* Validation Score */}
          {validationInfo && (
            <div className="flex items-center justify-between p-2 bg-white dark:bg-neutral-900 rounded border">
              <div className="flex items-center space-x-2">
                <validationInfo.icon className={clsx(
                  'w-4 h-4',
                  validationInfo.color === 'success' && 'text-success-500',
                  validationInfo.color === 'warning' && 'text-warning-500',
                  validationInfo.color === 'error' && 'text-error-500'
                )} />
                <span className="text-sm font-medium">Validation</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="text-sm text-neutral-600 dark:text-neutral-400">
                  {Math.round((packageData.metadata?.validation_score || 0) * 100)}%
                </div>
                <Badge 
                  variant={validationInfo.color as any}
                  size="sm"
                >
                  {validationInfo.level}
                </Badge>
              </div>
            </div>
          )}
        </div>

        {/* Recommendation Reason */}
        {packageData.recommendation_reason && (
          <div className="p-3 bg-sparky-gold/10 border border-sparky-gold/20 rounded-lg mb-4">
            <div className="flex items-start space-x-2">
              <StarIcon className="w-4 h-4 text-sparky-gold mt-0.5 flex-shrink-0" />
              <div>
                <div className="text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-1">
                  Why this package?
                </div>
                <div className="text-sm text-neutral-700 dark:text-neutral-300">
                  {packageData.recommendation_reason}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Sales Evidence */}
        {packageData.sales_evidence && (
          <div className="p-3 bg-info-50 dark:bg-info-900/20 border border-info-200 dark:border-info-800 rounded-lg mb-4">
            <div className="flex items-start space-x-2">
              <ChartBarIcon className="w-4 h-4 text-info-500 mt-0.5 flex-shrink-0" />
              <div>
                <div className="text-sm font-medium text-neutral-900 dark:text-neutral-100 mb-1">
                  Market Intelligence
                </div>
                <div className="text-sm text-neutral-700 dark:text-neutral-300">
                  {packageData.sales_evidence}
                </div>
              </div>
            </div>
          </div>
        )}
      </Card.Content>

      <Card.Footer>
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center space-x-2">
            {showComparison && (
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation()
                  // TODO: Implement comparison functionality
                }}
              >
                Compare
              </Button>
            )}
            {onViewDetails && (
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation()
                  handleViewDetails()
                }}
              >
                View Details
              </Button>
            )}
          </div>
          
          {onSelect && !selected && (
            <Button
              variant="primary"
              size="sm"
              onClick={(e) => {
                e.stopPropagation()
                handleSelect()
              }}
            >
              Select Package
            </Button>
          )}
          
          {selected && (
            <Badge variant="success" size="md">
              <CheckCircleIcon className="w-4 h-4 mr-1" />
              Selected
            </Badge>
          )}
        </div>
      </Card.Footer>
    </Card>
  )
}

export default PackageCard