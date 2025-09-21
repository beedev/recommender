import React, { useState } from 'react'
import clsx from 'clsx'
import { EnhancedPackageComponent } from '../../../types/enhanced-orchestrator'

import Badge from '../../common/Badge'
import Button from '../../common/Button'
import { 
  ChevronDownIcon,
  ChevronRightIcon,
  InformationCircleIcon,
  ChartBarIcon,
  CurrencyDollarIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'

interface ComponentListProps {
  components: {
    powersource: EnhancedPackageComponent
    feeder?: EnhancedPackageComponent
    cooler?: EnhancedPackageComponent
    torch?: EnhancedPackageComponent
    accessories: EnhancedPackageComponent[]
  }
  showPricing?: boolean
  showSpecifications?: boolean
  expandable?: boolean
  className?: string
}

interface ComponentItemProps {
  component: EnhancedPackageComponent
  category: string
  showPricing?: boolean
  showSpecifications?: boolean
  expandable?: boolean
  isRequired?: boolean
}

const ComponentItem: React.FC<ComponentItemProps> = ({
  component,
  category,
  showPricing = true,
  showSpecifications = true,
  expandable = true,
  isRequired = false
}) => {
  const [isExpanded, setIsExpanded] = useState(false)

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

  // Get compatibility score color
  const getCompatibilityColor = (score?: number) => {
    if (!score) return 'secondary'
    if (score >= 0.8) return 'success'
    if (score >= 0.6) return 'warning'
    return 'error'
  }

  // Get sales frequency variant
  const getSalesFrequencyVariant = (frequency?: string) => {
    switch (frequency?.toLowerCase()) {
      case 'high': return 'success'
      case 'medium': return 'warning'
      case 'low': return 'secondary'
      default: return 'secondary'
    }
  }

  const hasSpecifications = component.specifications && Object.keys(component.specifications).length > 0
  const canExpand = expandable && (hasSpecifications || component.description)

  return (
    <div className="border border-neutral-200 dark:border-neutral-700 rounded-lg overflow-hidden">
      {/* Main component info */}
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-1">
              <h4 className="font-semibold text-neutral-900 dark:text-neutral-100">
                {component.product_name}
              </h4>
              {isRequired && (
                <Badge variant="primary" size="sm">
                  Required
                </Badge>
              )}
            </div>
            
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-sm text-neutral-600 dark:text-neutral-400">
                {category}
              </span>
              {component.subcategory && (
                <>
                  <span className="text-neutral-400">•</span>
                  <span className="text-sm text-neutral-600 dark:text-neutral-400">
                    {component.subcategory}
                  </span>
                </>
              )}
              {component.manufacturer && (
                <>
                  <span className="text-neutral-400">•</span>
                  <span className="text-sm text-neutral-600 dark:text-neutral-400">
                    {component.manufacturer}
                  </span>
                </>
              )}
            </div>

            {/* Badges */}
            <div className="flex items-center space-x-2 mb-2">
              {component.compatibility_score !== undefined && (
                <Badge 
                  variant={getCompatibilityColor(component.compatibility_score)}
                  size="sm"
                >
                  <CheckCircleIcon className="w-3 h-3 mr-1" />
                  {Math.round(component.compatibility_score * 100)}% compatible
                </Badge>
              )}
              
              {component.sales_frequency && (
                <Badge 
                  variant={getSalesFrequencyVariant(component.sales_frequency)}
                  size="sm"
                >
                  <ChartBarIcon className="w-3 h-3 mr-1" />
                  {component.sales_frequency} demand
                </Badge>
              )}
              
              {component.sales_count && (
                <Badge variant="secondary" size="sm">
                  {component.sales_count} sold
                </Badge>
              )}
            </div>

            {/* Short description */}
            {component.description && !isExpanded && (
              <p className="text-sm text-neutral-600 dark:text-neutral-400 line-clamp-2">
                {component.description}
              </p>
            )}
          </div>

          {/* Price and actions */}
          <div className="flex flex-col items-end space-y-2 ml-4">
            {showPricing && (
              <div className="text-right">
                <div className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
                  {formatPrice(component.price)}
                </div>
              </div>
            )}
            
            {canExpand && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsExpanded(!isExpanded)}
                className="p-1"
              >
                {isExpanded ? (
                  <ChevronDownIcon className="w-4 h-4" />
                ) : (
                  <ChevronRightIcon className="w-4 h-4" />
                )}
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Expanded content */}
      {isExpanded && (
        <div className="border-t border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-800 p-4">
          {/* Full description */}
          {component.description && (
            <div className="mb-4">
              <h5 className="font-medium text-neutral-900 dark:text-neutral-100 mb-2">
                Description
              </h5>
              <p className="text-sm text-neutral-600 dark:text-neutral-400">
                {component.description}
              </p>
            </div>
          )}

          {/* Specifications */}
          {hasSpecifications && showSpecifications && (
            <div>
              <h5 className="font-medium text-neutral-900 dark:text-neutral-100 mb-2">
                Specifications
              </h5>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {Object.entries(component.specifications!).map(([key, value]) => (
                  <div key={key} className="flex justify-between py-1">
                    <span className="text-sm text-neutral-600 dark:text-neutral-400 capitalize">
                      {key.replace(/_/g, ' ')}:
                    </span>
                    <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                      {String(value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

const ComponentList: React.FC<ComponentListProps> = ({
  components,
  showPricing = true,
  showSpecifications = true,
  expandable = true,
  className
}) => {
  return (
    <div className={clsx('space-y-4', className)}>
      {/* Power Source (Required) */}
      <div>
        <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-3 flex items-center">
          <CurrencyDollarIcon className="w-5 h-5 mr-2 text-sparky-gold" />
          Package Components
        </h3>
        
        <div className="space-y-3">
          <ComponentItem
            component={components.powersource}
            category="Power Source"
            showPricing={showPricing}
            showSpecifications={showSpecifications}
            expandable={expandable}
            isRequired={true}
          />

          {/* Optional Components */}
          {components.feeder && (
            <ComponentItem
              component={components.feeder}
              category="Wire Feeder"
              showPricing={showPricing}
              showSpecifications={showSpecifications}
              expandable={expandable}
            />
          )}

          {components.cooler && (
            <ComponentItem
              component={components.cooler}
              category="Cooling System"
              showPricing={showPricing}
              showSpecifications={showSpecifications}
              expandable={expandable}
            />
          )}

          {components.torch && (
            <ComponentItem
              component={components.torch}
              category="Welding Torch"
              showPricing={showPricing}
              showSpecifications={showSpecifications}
              expandable={expandable}
            />
          )}

          {/* Accessories */}
          {components.accessories.length > 0 && (
            <div>
              <h4 className="font-medium text-neutral-900 dark:text-neutral-100 mb-2 flex items-center">
                <InformationCircleIcon className="w-4 h-4 mr-1 text-neutral-500" />
                Accessories ({components.accessories.length})
              </h4>
              <div className="space-y-2">
                {components.accessories.map((accessory, index) => (
                  <ComponentItem
                    key={`${accessory.product_id}-${index}`}
                    component={accessory}
                    category="Accessory"
                    showPricing={showPricing}
                    showSpecifications={showSpecifications}
                    expandable={expandable}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ComponentList