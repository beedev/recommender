import React, { useState } from 'react'
import clsx from 'clsx'
import { EnhancedWeldingPackage } from '../../../types/enhanced-orchestrator'
import Card from '../../common/Card'
import Badge from '../../common/Badge'
import Button from '../../common/Button'
import { 
  ScaleIcon,
  CheckCircleIcon,
  XMarkIcon,
  StarIcon,
  CurrencyDollarIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline'

interface PackageComparisonProps {
  packages: EnhancedWeldingPackage[]
  selectedPackage?: EnhancedWeldingPackage
  onPackageSelect?: (packageData: EnhancedWeldingPackage) => void
  onClose?: () => void
  className?: string
}

interface ComparisonRowProps {
  label: string
  values: (string | number | boolean | undefined)[]
  type?: 'text' | 'price' | 'score' | 'boolean' | 'badge'
  highlight?: boolean
}

const ComparisonRow: React.FC<ComparisonRowProps> = ({
  label,
  values,
  type = 'text',
  highlight = false
}) => {
  const formatValue = (value: string | number | boolean | undefined, _index: number) => {
    if (value === undefined || value === null) {
      return <span className="text-neutral-400">—</span>
    }

    switch (type) {
      case 'price':
        return (
          <span className="font-semibold text-sparky-gold">
            {typeof value === 'number' 
              ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value)
              : value
            }
          </span>
        )
      
      case 'score':
        const score = typeof value === 'number' ? value : parseFloat(String(value))
        const percentage = Math.round(score * 100)
        const getScoreColor = (score: number) => {
          if (score >= 0.8) return 'text-success-600'
          if (score >= 0.6) return 'text-warning-600'
          return 'text-error-600'
        }
        return (
          <div className="flex items-center space-x-2">
            <span className={clsx('font-semibold', getScoreColor(score))}>
              {percentage}%
            </span>
            <div className="w-16 bg-neutral-200 dark:bg-neutral-700 rounded-full h-1.5">
              <div
                className={clsx(
                  'h-1.5 rounded-full',
                  score >= 0.8 && 'bg-success-500',
                  score >= 0.6 && score < 0.8 && 'bg-warning-500',
                  score < 0.6 && 'bg-error-500'
                )}
                style={{ width: `${percentage}%` }}
              />
            </div>
          </div>
        )
      
      case 'boolean':
        return value ? (
          <CheckCircleIcon className="w-5 h-5 text-success-500" />
        ) : (
          <XMarkIcon className="w-5 h-5 text-neutral-400" />
        )
      
      case 'badge':
        const badgeVariant = typeof value === 'string' && value.toLowerCase() === 'high' ? 'success' :
                            typeof value === 'string' && value.toLowerCase() === 'medium' ? 'warning' : 'secondary'
        return (
          <Badge variant={badgeVariant as any} size="sm">
            {String(value)}
          </Badge>
        )
      
      default:
        return <span>{String(value)}</span>
    }
  }

  return (
    <div className={clsx(
      'grid gap-4 py-3 border-b border-neutral-100 dark:border-neutral-800',
      `grid-cols-${values.length + 1}`,
      highlight && 'bg-sparky-gold/5'
    )}>
      <div className="font-medium text-neutral-900 dark:text-neutral-100">
        {label}
      </div>
      {values.map((value, index) => (
        <div key={index} className="flex items-center justify-center">
          {formatValue(value, index)}
        </div>
      ))}
    </div>
  )
}

const PackageComparison: React.FC<PackageComparisonProps> = ({
  packages,
  selectedPackage,
  onPackageSelect,
  onClose,
  className
}) => {
  const [selectedPackages, setSelectedPackages] = useState<Set<string>>(
    new Set(packages.slice(0, 3).map(pkg => pkg.package_id))
  )

  const packagesToCompare = packages.filter(pkg => selectedPackages.has(pkg.package_id))

  const togglePackageSelection = (packageId: string) => {
    const newSelected = new Set(selectedPackages)
    if (newSelected.has(packageId)) {
      if (newSelected.size > 2) { // Keep at least 2 packages for comparison
        newSelected.delete(packageId)
      }
    } else {
      if (newSelected.size < 4) { // Max 4 packages for comparison
        newSelected.add(packageId)
      }
    }
    setSelectedPackages(newSelected)
  }

  const formatPrice = (price?: number) => {
    if (!price) return 'Quote Required'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price)
  }

  return (
    <div className={clsx('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <ScaleIcon className="w-6 h-6 text-sparky-gold" />
          <div>
            <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
              Package Comparison
            </h2>
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              Compare up to 4 packages side by side
            </p>
          </div>
        </div>
        
        {onClose && (
          <Button variant="ghost" size="sm" onClick={onClose}>
            <XMarkIcon className="w-4 h-4" />
          </Button>
        )}
      </div>

      {/* Package Selection */}
      <Card variant="outlined">
        <Card.Header>
          <Card.Title>Select Packages to Compare</Card.Title>
          <Card.Description>
            Choose 2-4 packages for detailed comparison
          </Card.Description>
        </Card.Header>
        
        <Card.Content>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {packages.map((pkg) => (
              <div
                key={pkg.package_id}
                className={clsx(
                  'p-3 border rounded-lg cursor-pointer transition-all',
                  selectedPackages.has(pkg.package_id)
                    ? 'border-sparky-gold bg-sparky-gold/10'
                    : 'border-neutral-200 dark:border-neutral-700 hover:border-neutral-300'
                )}
                onClick={() => togglePackageSelection(pkg.package_id)}
              >
                <div className="flex items-center space-x-2">
                  <div className={clsx(
                    'w-4 h-4 rounded border-2 flex items-center justify-center',
                    selectedPackages.has(pkg.package_id)
                      ? 'border-sparky-gold bg-sparky-gold'
                      : 'border-neutral-300'
                  )}>
                    {selectedPackages.has(pkg.package_id) && (
                      <CheckCircleIcon className="w-3 h-3 text-black" />
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-sm text-neutral-900 dark:text-neutral-100">
                      {pkg.package_name || `Package ${pkg.package_id}`}
                    </div>
                    <div className="text-xs text-neutral-500">
                      {formatPrice(pkg.total_price)}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card.Content>
      </Card>

      {/* Comparison Table */}
      {packagesToCompare.length >= 2 && (
        <Card variant="default" shadow="md">
          <Card.Header>
            <Card.Title>Detailed Comparison</Card.Title>
          </Card.Header>
          
          <Card.Content className="p-0">
            <div className="overflow-x-auto">
              <div className="min-w-full">
                {/* Package Headers */}
                <div className={clsx(
                  'grid gap-4 p-4 bg-neutral-50 dark:bg-neutral-800 border-b border-neutral-200 dark:border-neutral-700',
                  `grid-cols-${packagesToCompare.length + 1}`
                )}>
                  <div className="font-semibold text-neutral-900 dark:text-neutral-100">
                    Package
                  </div>
                  {packagesToCompare.map((pkg) => (
                    <div key={pkg.package_id} className="text-center">
                      <div className="font-semibold text-neutral-900 dark:text-neutral-100 mb-1">
                        {pkg.package_name || `Package ${pkg.package_id}`}
                      </div>
                      <div className="text-lg font-bold text-sparky-gold">
                        {formatPrice(pkg.total_price)}
                      </div>
                      {selectedPackage?.package_id === pkg.package_id && (
                        <Badge variant="success" size="sm" className="mt-1">
                          Selected
                        </Badge>
                      )}
                    </div>
                  ))}
                </div>

                <div className="p-4 space-y-0">
                  {/* Basic Information */}
                  <div className="mb-6">
                    <h4 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-3 flex items-center">
                      <InformationCircleIcon className="w-4 h-4 mr-1" />
                      Basic Information
                    </h4>
                    
                    <ComparisonRow
                      label="Power Source"
                      values={packagesToCompare.map(pkg => pkg.powersource.product_name)}
                    />
                    
                    <ComparisonRow
                      label="Wire Feeder"
                      values={packagesToCompare.map(pkg => pkg.feeder?.product_name || 'Not included')}
                    />
                    
                    <ComparisonRow
                      label="Cooling System"
                      values={packagesToCompare.map(pkg => pkg.cooler?.product_name || 'Not included')}
                    />
                    
                    <ComparisonRow
                      label="Welding Torch"
                      values={packagesToCompare.map(pkg => pkg.torch?.product_name || 'Not included')}
                    />
                    
                    <ComparisonRow
                      label="Accessories"
                      values={packagesToCompare.map(pkg => `${pkg.accessories.length} items`)}
                    />
                  </div>

                  {/* Pricing Breakdown */}
                  <div className="mb-6">
                    <h4 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-3 flex items-center">
                      <CurrencyDollarIcon className="w-4 h-4 mr-1" />
                      Pricing
                    </h4>
                    
                    <ComparisonRow
                      label="Power Source Price"
                      values={packagesToCompare.map(pkg => pkg.powersource.price)}
                      type="price"
                    />
                    
                    <ComparisonRow
                      label="Total Package Price"
                      values={packagesToCompare.map(pkg => pkg.total_price)}
                      type="price"
                      highlight
                    />
                  </div>

                  {/* Performance Metrics */}
                  <div className="mb-6">
                    <h4 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-3 flex items-center">
                      <ShieldCheckIcon className="w-4 h-4 mr-1" />
                      Performance & Compatibility
                    </h4>
                    
                    <ComparisonRow
                      label="Compatibility Score"
                      values={packagesToCompare.map(pkg => pkg.compatibility_confidence)}
                      type="score"
                      highlight
                    />
                    
                    <ComparisonRow
                      label="Validation Score"
                      values={packagesToCompare.map(pkg => pkg.metadata?.validation_score)}
                      type="score"
                    />
                    
                    <ComparisonRow
                      label="Sales Frequency"
                      values={packagesToCompare.map(pkg => pkg.powersource.sales_frequency)}
                      type="badge"
                    />
                  </div>

                  {/* Recommendations */}
                  <div className="mb-6">
                    <h4 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-3 flex items-center">
                      <StarIcon className="w-4 h-4 mr-1" />
                      AI Recommendations
                    </h4>
                    
                    {packagesToCompare.map((pkg, _index) => (
                      <div key={pkg.package_id} className="mb-3 p-3 bg-neutral-50 dark:bg-neutral-800 rounded-lg">
                        <div className="font-medium text-neutral-900 dark:text-neutral-100 mb-1">
                          {pkg.package_name || `Package ${pkg.package_id}`}
                        </div>
                        <p className="text-sm text-neutral-600 dark:text-neutral-400">
                          {pkg.recommendation_reason || 'No specific recommendation reason provided.'}
                        </p>
                        {pkg.sales_evidence && (
                          <p className="text-xs text-neutral-500 mt-1">
                            <ChartBarIcon className="w-3 h-3 inline mr-1" />
                            {pkg.sales_evidence}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </Card.Content>
          
          {/* Action Buttons */}
          <Card.Footer>
            <div className="flex justify-between items-center w-full">
              <div className="text-sm text-neutral-600 dark:text-neutral-400">
                Comparing {packagesToCompare.length} packages
              </div>
              
              <div className="flex space-x-2">
                {packagesToCompare.map((pkg) => (
                  <Button
                    key={pkg.package_id}
                    variant={selectedPackage?.package_id === pkg.package_id ? "primary" : "outline"}
                    size="sm"
                    onClick={() => onPackageSelect?.(pkg)}
                  >
                    {selectedPackage?.package_id === pkg.package_id ? 'Selected' : 'Select'}
                  </Button>
                ))}
              </div>
            </div>
          </Card.Footer>
        </Card>
      )}
    </div>
  )
}

export default PackageComparison