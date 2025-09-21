import React, { useState } from 'react'
import clsx from 'clsx'
import { EnhancedWeldingPackage } from '../../../types/enhanced-orchestrator'
import Card from '../../common/Card'
import Badge from '../../common/Badge'
import Button from '../../common/Button'
import PackageCard from '../PackageCard'
import { 
  LightBulbIcon,
  ArrowPathIcon,
  FunnelIcon,
  AdjustmentsHorizontalIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  StarIcon
} from '@heroicons/react/24/outline'

interface PackageAlternativesProps {
  currentPackage: EnhancedWeldingPackage
  alternatives?: EnhancedWeldingPackage[]
  onSelectAlternative?: (packageData: EnhancedWeldingPackage) => void
  onRequestAlternatives?: (criteria: AlternativeCriteria) => void
  onViewDetails?: (packageData: EnhancedWeldingPackage) => void
  className?: string
}

interface AlternativeCriteria {
  priceRange?: 'lower' | 'similar' | 'higher'
  performanceLevel?: 'basic' | 'standard' | 'premium'
  features?: string[]
  manufacturer?: string
}

interface AlternativeFilterProps {
  criteria: AlternativeCriteria
  onCriteriaChange: (criteria: AlternativeCriteria) => void
  onApply: () => void
}

const AlternativeFilter: React.FC<AlternativeFilterProps> = ({
  criteria,
  onCriteriaChange,
  onApply
}) => {
  const updateCriteria = (updates: Partial<AlternativeCriteria>) => {
    onCriteriaChange({ ...criteria, ...updates })
  }

  return (
    <Card variant="outlined" className="mb-4">
      <Card.Header>
        <Card.Title className="flex items-center text-sm">
          <FunnelIcon className="w-4 h-4 mr-2" />
          Alternative Filters
        </Card.Title>
      </Card.Header>
      
      <Card.Content>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Price Range */}
          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
              Price Range
            </label>
            <div className="space-y-2">
              {[
                { value: 'lower', label: 'Lower Cost', icon: '💰' },
                { value: 'similar', label: 'Similar Price', icon: '⚖️' },
                { value: 'higher', label: 'Premium Options', icon: '⭐' }
              ].map(option => (
                <label key={option.value} className="flex items-center space-x-2">
                  <input
                    type="radio"
                    name="priceRange"
                    value={option.value}
                    checked={criteria.priceRange === option.value}
                    onChange={(e) => updateCriteria({ priceRange: e.target.value as any })}
                    className="text-sparky-gold focus:ring-sparky-gold"
                  />
                  <span className="text-sm text-neutral-700 dark:text-neutral-300">
                    {option.icon} {option.label}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Performance Level */}
          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
              Performance Level
            </label>
            <div className="space-y-2">
              {[
                { value: 'basic', label: 'Basic Features', icon: '🔧' },
                { value: 'standard', label: 'Standard Features', icon: '⚙️' },
                { value: 'premium', label: 'Premium Features', icon: '🚀' }
              ].map(option => (
                <label key={option.value} className="flex items-center space-x-2">
                  <input
                    type="radio"
                    name="performanceLevel"
                    value={option.value}
                    checked={criteria.performanceLevel === option.value}
                    onChange={(e) => updateCriteria({ performanceLevel: e.target.value as any })}
                    className="text-sparky-gold focus:ring-sparky-gold"
                  />
                  <span className="text-sm text-neutral-700 dark:text-neutral-300">
                    {option.icon} {option.label}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Features */}
          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
              Preferred Features
            </label>
            <div className="space-y-2">
              {[
                'Water Cooling',
                'Digital Display',
                'Pulse Welding',
                'Remote Control',
                'Multi-Process'
              ].map(feature => (
                <label key={feature} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={criteria.features?.includes(feature) || false}
                    onChange={(e) => {
                      const features = criteria.features || []
                      if (e.target.checked) {
                        updateCriteria({ features: [...features, feature] })
                      } else {
                        updateCriteria({ features: features.filter(f => f !== feature) })
                      }
                    }}
                    className="text-sparky-gold focus:ring-sparky-gold"
                  />
                  <span className="text-sm text-neutral-700 dark:text-neutral-300">
                    {feature}
                  </span>
                </label>
              ))}
            </div>
          </div>
        </div>
        
        <div className="mt-4 pt-4 border-t border-neutral-200 dark:border-neutral-700">
          <Button
            variant="primary"
            size="sm"
            onClick={onApply}
            leftIcon={<ArrowPathIcon className="w-4 h-4" />}
          >
            Find Alternatives
          </Button>
        </div>
      </Card.Content>
    </Card>
  )
}

const PackageAlternatives: React.FC<PackageAlternativesProps> = ({
  currentPackage,
  alternatives = [],
  onSelectAlternative,
  onRequestAlternatives,
  onViewDetails,
  className
}) => {
  const [showFilters, setShowFilters] = useState(false)
  const [criteria, setCriteria] = useState<AlternativeCriteria>({
    priceRange: 'similar',
    performanceLevel: 'standard',
    features: []
  })

  const handleRequestAlternatives = () => {
    onRequestAlternatives?.(criteria)
  }

  // Generate suggested alternatives based on current package
  const getSuggestedAlternatives = () => {
    const suggestions = [
      {
        type: 'budget',
        title: 'Budget-Friendly Option',
        description: 'Similar functionality at a lower price point',
        icon: CurrencyDollarIcon,
        color: 'success'
      },
      {
        type: 'premium',
        title: 'Premium Upgrade',
        description: 'Enhanced features and performance',
        icon: StarIcon,
        color: 'warning'
      },
      {
        type: 'compact',
        title: 'Compact Alternative',
        description: 'Space-saving design with similar capabilities',
        icon: AdjustmentsHorizontalIcon,
        color: 'info'
      },
      {
        type: 'performance',
        title: 'High-Performance Option',
        description: 'Maximum output and advanced features',
        icon: ChartBarIcon,
        color: 'primary'
      }
    ]

    return suggestions
  }

  const suggestedAlternatives = getSuggestedAlternatives()

  return (
    <div className={clsx('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <LightBulbIcon className="w-6 h-6 text-sparky-gold" />
          <div>
            <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
              Package Alternatives
            </h2>
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              Explore other options that might better fit your needs
            </p>
          </div>
        </div>
        
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowFilters(!showFilters)}
          leftIcon={<FunnelIcon className="w-4 h-4" />}
        >
          {showFilters ? 'Hide Filters' : 'Show Filters'}
        </Button>
      </div>

      {/* Current Package Summary */}
      <Card variant="outlined">
        <Card.Header>
          <Card.Title>Current Selection</Card.Title>
        </Card.Header>
        
        <Card.Content>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-neutral-900 dark:text-neutral-100">
                {currentPackage.package_name || `Package ${currentPackage.package_id}`}
              </h3>
              <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
                {currentPackage.description || 'No description available'}
              </p>
              <div className="flex items-center space-x-4 mt-2">
                <Badge variant="success" size="sm">
                  <ShieldCheckIcon className="w-3 h-3 mr-1" />
                  {Math.round(currentPackage.compatibility_confidence * 100)}% compatible
                </Badge>
                {currentPackage.total_price && (
                  <span className="text-lg font-semibold text-sparky-gold">
                    {new Intl.NumberFormat('en-US', { 
                      style: 'currency', 
                      currency: 'USD' 
                    }).format(currentPackage.total_price)}
                  </span>
                )}
              </div>
            </div>
          </div>
        </Card.Content>
      </Card>

      {/* Alternative Filters */}
      {showFilters && (
        <AlternativeFilter
          criteria={criteria}
          onCriteriaChange={setCriteria}
          onApply={handleRequestAlternatives}
        />
      )}

      {/* Suggested Alternative Types */}
      {alternatives.length === 0 && (
        <Card variant="default">
          <Card.Header>
            <Card.Title>Suggested Alternative Types</Card.Title>
            <Card.Description>
              Click on any option to find similar packages
            </Card.Description>
          </Card.Header>
          
          <Card.Content>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {suggestedAlternatives.map((suggestion) => {
                const IconComponent = suggestion.icon
                return (
                  <div
                    key={suggestion.type}
                    className="p-4 border border-neutral-200 dark:border-neutral-700 rounded-lg hover:border-sparky-gold/50 cursor-pointer transition-colors"
                    onClick={() => {
                      // Set criteria based on suggestion type
                      let newCriteria: AlternativeCriteria = { ...criteria }
                      
                      switch (suggestion.type) {
                        case 'budget':
                          newCriteria.priceRange = 'lower'
                          newCriteria.performanceLevel = 'basic'
                          break
                        case 'premium':
                          newCriteria.priceRange = 'higher'
                          newCriteria.performanceLevel = 'premium'
                          break
                        case 'compact':
                          newCriteria.features = ['Compact Design']
                          break
                        case 'performance':
                          newCriteria.performanceLevel = 'premium'
                          newCriteria.features = ['High Output', 'Advanced Controls']
                          break
                      }
                      
                      setCriteria(newCriteria)
                      handleRequestAlternatives()
                    }}
                  >
                    <div className="flex items-start space-x-3">
                      <div className={clsx(
                        'p-2 rounded-lg',
                        suggestion.color === 'success' && 'bg-success-100 dark:bg-success-900/20',
                        suggestion.color === 'warning' && 'bg-warning-100 dark:bg-warning-900/20',
                        suggestion.color === 'info' && 'bg-info-100 dark:bg-info-900/20',
                        suggestion.color === 'primary' && 'bg-sparky-gold/20'
                      )}>
                        <IconComponent className={clsx(
                          'w-5 h-5',
                          suggestion.color === 'success' && 'text-success-600',
                          suggestion.color === 'warning' && 'text-warning-600',
                          suggestion.color === 'info' && 'text-info-600',
                          suggestion.color === 'primary' && 'text-sparky-gold'
                        )} />
                      </div>
                      <div>
                        <h4 className="font-medium text-neutral-900 dark:text-neutral-100">
                          {suggestion.title}
                        </h4>
                        <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
                          {suggestion.description}
                        </p>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </Card.Content>
        </Card>
      )}

      {/* Alternative Packages */}
      {alternatives.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
              Alternative Packages ({alternatives.length})
            </h3>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleRequestAlternatives}
              leftIcon={<ArrowPathIcon className="w-4 h-4" />}
            >
              Refresh Alternatives
            </Button>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {alternatives.map((alternative) => (
              <div key={alternative.package_id} className="relative">
                <PackageCard
                  package={alternative}
                  onSelect={onSelectAlternative || undefined}
                  onViewDetails={onViewDetails}
                  showComparison={true}
                />
                
                {/* Comparison Badge */}
                <div className="absolute -top-2 -left-2 z-10">
                  <Badge variant="info" size="sm">
                    Alternative
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Alternatives Found */}
      {alternatives.length === 0 && showFilters && (
        <Card variant="outlined" className="text-center py-8">
          <div className="flex flex-col items-center space-y-3">
            <LightBulbIcon className="w-12 h-12 text-neutral-400" />
            <div>
              <h3 className="font-medium text-neutral-900 dark:text-neutral-100 mb-1">
                No Alternatives Found
              </h3>
              <p className="text-sm text-neutral-600 dark:text-neutral-400">
                Try adjusting your filter criteria or contact our experts for personalized recommendations.
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setCriteria({
                  priceRange: 'similar',
                  performanceLevel: 'standard',
                  features: []
                })
                handleRequestAlternatives()
              }}
            >
              Reset Filters
            </Button>
          </div>
        </Card>
      )}
    </div>
  )
}

export default PackageAlternatives