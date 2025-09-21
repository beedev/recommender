import React, { useState, useEffect } from 'react'
import clsx from 'clsx'
import { 
  EnhancedWeldingPackage, 
  EnhancedPackageComponent 
} from '../../../types/enhanced-orchestrator'
import Card from '../../common/Card'
import Badge from '../../common/Badge'
import Button from '../../common/Button'
import SimpleModal from '../../common/SimpleModal'
import { 
  WrenchScrewdriverIcon,
  PlusIcon,
  MinusIcon,
  SwatchIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  CurrencyDollarIcon,
  ShoppingCartIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'

interface PackageCustomizerProps {
  package: EnhancedWeldingPackage
  onCustomizationChange?: (customizedPackage: CustomizedPackage) => void
  onSaveCustomization?: (customizedPackage: CustomizedPackage) => void
  onResetCustomization?: () => void
  className?: string
}

interface CustomizedPackage extends EnhancedWeldingPackage {
  customizations: {
    removedComponents: string[]
    addedComponents: EnhancedPackageComponent[]
    upgradedComponents: { [key: string]: EnhancedPackageComponent }
    customOptions: { [key: string]: any }
  }
  originalPrice: number
  customizedPrice: number
  priceDifference: number
}

interface ComponentCustomizationProps {
  component: EnhancedPackageComponent
  category: string
  isRequired?: boolean
  isRemovable?: boolean
  isUpgradeable?: boolean
  alternatives?: EnhancedPackageComponent[]
  onRemove?: () => void
  onUpgrade?: (newComponent: EnhancedPackageComponent) => void
  onRestore?: () => void
  isRemoved?: boolean
  isUpgraded?: boolean
}

const ComponentCustomization: React.FC<ComponentCustomizationProps> = ({
  component,
  category,
  isRequired = false,
  isRemovable = true,
  isUpgradeable = true,
  alternatives = [],
  onRemove,
  onUpgrade,
  onRestore,
  isRemoved = false,
  isUpgraded = false
}) => {
  const [showAlternatives, setShowAlternatives] = useState(false)

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
    <div className={clsx(
      'border rounded-lg p-4 transition-all',
      isRemoved && 'opacity-50 border-error-300 bg-error-50 dark:bg-error-900/10',
      isUpgraded && 'border-success-300 bg-success-50 dark:bg-success-900/10',
      !isRemoved && !isUpgraded && 'border-neutral-200 dark:border-neutral-700'
    )}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-1">
            <h4 className="font-semibold text-neutral-900 dark:text-neutral-100">
              {component.product_name}
            </h4>
            {isRequired && (
              <Badge variant="error" size="sm">Required</Badge>
            )}
            {isRemoved && (
              <Badge variant="error" size="sm">Removed</Badge>
            )}
            {isUpgraded && (
              <Badge variant="success" size="sm">Upgraded</Badge>
            )}
          </div>
          
          <div className="text-sm text-neutral-600 dark:text-neutral-400 mb-2">
            {category} • {component.manufacturer || 'ESAB'}
          </div>
          
          {component.description && (
            <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-2 line-clamp-2">
              {component.description}
            </p>
          )}
          
          <div className="text-lg font-semibold text-sparky-gold">
            {formatPrice(component.price)}
          </div>
        </div>
        
        <div className="flex flex-col space-y-2 ml-4">
          {/* Remove/Restore Button */}
          {!isRequired && isRemovable && (
            <Button
              variant={isRemoved ? "primary" : "outline"}
              size="sm"
              onClick={isRemoved ? onRestore : onRemove}
              leftIcon={isRemoved ? <PlusIcon className="w-3 h-3" /> : <MinusIcon className="w-3 h-3" />}
            >
              {isRemoved ? 'Restore' : 'Remove'}
            </Button>
          )}
          
          {/* Upgrade Button */}
          {isUpgradeable && alternatives.length > 0 && !isRemoved && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAlternatives(true)}
              leftIcon={<SwatchIcon className="w-3 h-3" />}
            >
              {isUpgraded ? 'Change' : 'Upgrade'}
            </Button>
          )}
        </div>
      </div>
      
      {/* Compatibility Warning */}
      {component.compatibility_score !== undefined && component.compatibility_score < 0.7 && (
        <div className="flex items-start space-x-2 p-2 bg-warning-50 dark:bg-warning-900/20 border border-warning-200 dark:border-warning-800 rounded">
          <ExclamationTriangleIcon className="w-4 h-4 text-warning-500 mt-0.5 flex-shrink-0" />
          <div className="text-sm text-warning-700 dark:text-warning-300">
            This component has lower compatibility ({Math.round(component.compatibility_score * 100)}%). 
            Consider alternatives for better performance.
          </div>
        </div>
      )}
      
      {/* Alternatives Modal */}
      <SimpleModal
        isOpen={showAlternatives}
        onClose={() => setShowAlternatives(false)}
        title={`${category} Alternatives`}
        size="lg"
      >
        <div className="space-y-4">
          <p className="text-sm text-neutral-600 dark:text-neutral-400">
            Choose an alternative component for your package:
          </p>
          
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {alternatives.map((alternative, index) => (
              <div
                key={`${alternative.product_id}-${index}`}
                className="border border-neutral-200 dark:border-neutral-700 rounded-lg p-3 hover:border-sparky-gold/50 cursor-pointer transition-colors"
                onClick={() => {
                  onUpgrade?.(alternative)
                  setShowAlternatives(false)
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h5 className="font-medium text-neutral-900 dark:text-neutral-100">
                      {alternative.product_name}
                    </h5>
                    <div className="text-sm text-neutral-600 dark:text-neutral-400 mb-1">
                      {alternative.manufacturer || 'ESAB'}
                    </div>
                    {alternative.description && (
                      <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-2">
                        {alternative.description}
                      </p>
                    )}
                    
                    {/* Compatibility Score */}
                    {alternative.compatibility_score !== undefined && (
                      <Badge 
                        variant={alternative.compatibility_score >= 0.8 ? 'success' : 
                               alternative.compatibility_score >= 0.6 ? 'warning' : 'error'}
                        size="sm"
                      >
                        {Math.round(alternative.compatibility_score * 100)}% compatible
                      </Badge>
                    )}
                  </div>
                  
                  <div className="text-right ml-4">
                    <div className="text-lg font-semibold text-sparky-gold">
                      {formatPrice(alternative.price)}
                    </div>
                    {alternative.price && component.price && (
                      <div className={clsx(
                        'text-sm',
                        alternative.price > component.price ? 'text-error-600' : 'text-success-600'
                      )}>
                        {alternative.price > component.price ? '+' : ''}
                        {formatPrice(alternative.price - component.price)}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </SimpleModal>
    </div>
  )
}

const PackageCustomizer: React.FC<PackageCustomizerProps> = ({
  package: originalPackage,
  onCustomizationChange,
  onSaveCustomization,
  onResetCustomization,
  className
}) => {
  const [customizedPackage, setCustomizedPackage] = useState<CustomizedPackage>({
    ...originalPackage,
    customizations: {
      removedComponents: [],
      addedComponents: [],
      upgradedComponents: {},
      customOptions: {}
    },
    originalPrice: originalPackage.total_price || 0,
    customizedPrice: originalPackage.total_price || 0,
    priceDifference: 0
  })

  // Mock alternatives data - in real implementation, this would come from API
  const mockAlternatives: { [key: string]: EnhancedPackageComponent[] } = {
    feeder: [
      {
        product_id: 'alt-feeder-1',
        product_name: 'Premium Wire Feeder Pro',
        category: 'Wire Feeder',
        manufacturer: 'ESAB',
        description: 'High-performance wire feeder with advanced controls',
        price: 2500,
        compatibility_score: 0.95
      },
      {
        product_id: 'alt-feeder-2',
        product_name: 'Compact Wire Feeder',
        category: 'Wire Feeder',
        manufacturer: 'ESAB',
        description: 'Space-saving design for mobile applications',
        price: 1800,
        compatibility_score: 0.85
      }
    ],
    cooler: [
      {
        product_id: 'alt-cooler-1',
        product_name: 'Industrial Cooling Unit',
        category: 'Cooling System',
        manufacturer: 'ESAB',
        description: 'Heavy-duty cooling for continuous operation',
        price: 3200,
        compatibility_score: 0.92
      }
    ]
  }

  // Calculate customized price
  useEffect(() => {
    let newPrice = originalPackage.total_price || 0
    
    // Subtract removed components
    customizedPackage.customizations.removedComponents.forEach(componentId => {
      // Find component price and subtract
      if (originalPackage.feeder?.product_id === componentId) {
        newPrice -= originalPackage.feeder.price || 0
      }
      if (originalPackage.cooler?.product_id === componentId) {
        newPrice -= originalPackage.cooler.price || 0
      }
      if (originalPackage.torch?.product_id === componentId) {
        newPrice -= originalPackage.torch.price || 0
      }
    })
    
    // Add upgraded components price difference
    Object.entries(customizedPackage.customizations.upgradedComponents).forEach(([componentId, newComponent]) => {
      let originalPrice = 0
      if (originalPackage.feeder?.product_id === componentId) {
        originalPrice = originalPackage.feeder.price || 0
      }
      if (originalPackage.cooler?.product_id === componentId) {
        originalPrice = originalPackage.cooler.price || 0
      }
      if (originalPackage.torch?.product_id === componentId) {
        originalPrice = originalPackage.torch.price || 0
      }
      
      newPrice = newPrice - originalPrice + (newComponent.price || 0)
    })
    
    // Add new components
    customizedPackage.customizations.addedComponents.forEach(component => {
      newPrice += component.price || 0
    })
    
    const updatedPackage = {
      ...customizedPackage,
      customizedPrice: newPrice,
      priceDifference: newPrice - (originalPackage.total_price || 0)
    }
    
    setCustomizedPackage(updatedPackage)
    onCustomizationChange?.(updatedPackage)
  }, [customizedPackage.customizations])

  const handleRemoveComponent = (componentId: string) => {
    setCustomizedPackage(prev => ({
      ...prev,
      customizations: {
        ...prev.customizations,
        removedComponents: [...prev.customizations.removedComponents, componentId]
      }
    }))
  }

  const handleRestoreComponent = (componentId: string) => {
    setCustomizedPackage(prev => ({
      ...prev,
      customizations: {
        ...prev.customizations,
        removedComponents: prev.customizations.removedComponents.filter(id => id !== componentId)
      }
    }))
  }

  const handleUpgradeComponent = (componentId: string, newComponent: EnhancedPackageComponent) => {
    setCustomizedPackage(prev => ({
      ...prev,
      customizations: {
        ...prev.customizations,
        upgradedComponents: {
          ...prev.customizations.upgradedComponents,
          [componentId]: newComponent
        }
      }
    }))
  }

  const handleResetCustomization = () => {
    setCustomizedPackage({
      ...originalPackage,
      customizations: {
        removedComponents: [],
        addedComponents: [],
        upgradedComponents: {},
        customOptions: {}
      },
      originalPrice: originalPackage.total_price || 0,
      customizedPrice: originalPackage.total_price || 0,
      priceDifference: 0
    })
    onResetCustomization?.()
  }

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price)
  }

  const hasCustomizations = 
    customizedPackage.customizations.removedComponents.length > 0 ||
    customizedPackage.customizations.addedComponents.length > 0 ||
    Object.keys(customizedPackage.customizations.upgradedComponents).length > 0

  return (
    <div className={clsx('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <WrenchScrewdriverIcon className="w-6 h-6 text-sparky-gold" />
          <div>
            <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
              Customize Package
            </h2>
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              Modify components to better fit your specific needs
            </p>
          </div>
        </div>
        
        {hasCustomizations && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleResetCustomization}
            leftIcon={<ArrowPathIcon className="w-4 h-4" />}
          >
            Reset All
          </Button>
        )}
      </div>

      {/* Price Summary */}
      <Card variant="default" shadow="md">
        <Card.Header>
          <Card.Title className="flex items-center">
            <CurrencyDollarIcon className="w-5 h-5 mr-2 text-sparky-gold" />
            Customization Summary
          </Card.Title>
        </Card.Header>
        
        <Card.Content>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-neutral-50 dark:bg-neutral-800 rounded-lg">
              <div className="text-lg font-semibold text-neutral-600 dark:text-neutral-400 mb-1">
                Original Price
              </div>
              <div className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
                {formatPrice(customizedPackage.originalPrice)}
              </div>
            </div>
            
            <div className="text-center p-4 bg-sparky-gold/10 rounded-lg">
              <div className="text-lg font-semibold text-sparky-gold mb-1">
                Customized Price
              </div>
              <div className="text-2xl font-bold text-sparky-gold">
                {formatPrice(customizedPackage.customizedPrice)}
              </div>
            </div>
            
            <div className="text-center p-4 bg-neutral-50 dark:bg-neutral-800 rounded-lg">
              <div className="text-lg font-semibold text-neutral-600 dark:text-neutral-400 mb-1">
                Price Difference
              </div>
              <div className={clsx(
                'text-2xl font-bold',
                customizedPackage.priceDifference > 0 ? 'text-error-600' : 
                customizedPackage.priceDifference < 0 ? 'text-success-600' : 'text-neutral-900 dark:text-neutral-100'
              )}>
                {customizedPackage.priceDifference > 0 ? '+' : ''}
                {formatPrice(customizedPackage.priceDifference)}
              </div>
            </div>
          </div>
        </Card.Content>
      </Card>

      {/* Component Customization */}
      <Card variant="default" shadow="md">
        <Card.Header>
          <Card.Title>Package Components</Card.Title>
          <Card.Description>
            Customize individual components to match your requirements
          </Card.Description>
        </Card.Header>
        
        <Card.Content>
          <div className="space-y-4">
            {/* Power Source (Required) */}
            <ComponentCustomization
              component={customizedPackage.powersource}
              category="Power Source"
              isRequired={true}
              isRemovable={false}
              isUpgradeable={false}
            />
            
            {/* Wire Feeder */}
            {originalPackage.feeder && (
              <ComponentCustomization
                component={
                  customizedPackage.customizations.upgradedComponents[originalPackage.feeder.product_id] ||
                  originalPackage.feeder
                }
                category="Wire Feeder"
                isRemovable={true}
                isUpgradeable={true}
                alternatives={mockAlternatives.feeder || []}
                onRemove={() => handleRemoveComponent(originalPackage.feeder!.product_id)}
                onRestore={() => handleRestoreComponent(originalPackage.feeder!.product_id)}
                onUpgrade={(newComponent) => handleUpgradeComponent(originalPackage.feeder!.product_id, newComponent)}
                isRemoved={customizedPackage.customizations.removedComponents.includes(originalPackage.feeder.product_id)}
                isUpgraded={!!customizedPackage.customizations.upgradedComponents[originalPackage.feeder.product_id]}
              />
            )}
            
            {/* Cooling System */}
            {originalPackage.cooler && (
              <ComponentCustomization
                component={
                  customizedPackage.customizations.upgradedComponents[originalPackage.cooler.product_id] ||
                  originalPackage.cooler
                }
                category="Cooling System"
                isRemovable={true}
                isUpgradeable={true}
                alternatives={mockAlternatives.cooler || []}
                onRemove={() => handleRemoveComponent(originalPackage.cooler!.product_id)}
                onRestore={() => handleRestoreComponent(originalPackage.cooler!.product_id)}
                onUpgrade={(newComponent) => handleUpgradeComponent(originalPackage.cooler!.product_id, newComponent)}
                isRemoved={customizedPackage.customizations.removedComponents.includes(originalPackage.cooler.product_id)}
                isUpgraded={!!customizedPackage.customizations.upgradedComponents[originalPackage.cooler.product_id]}
              />
            )}
            
            {/* Welding Torch */}
            {originalPackage.torch && (
              <ComponentCustomization
                component={
                  customizedPackage.customizations.upgradedComponents[originalPackage.torch.product_id] ||
                  originalPackage.torch
                }
                category="Welding Torch"
                isRemovable={true}
                isUpgradeable={true}
                alternatives={[]}
                onRemove={() => handleRemoveComponent(originalPackage.torch!.product_id)}
                onRestore={() => handleRestoreComponent(originalPackage.torch!.product_id)}
                isRemoved={customizedPackage.customizations.removedComponents.includes(originalPackage.torch.product_id)}
              />
            )}
          </div>
        </Card.Content>
      </Card>

      {/* Customization Notes */}
      {hasCustomizations && (
        <Card variant="outlined">
          <Card.Header>
            <Card.Title className="flex items-center text-info-600">
              <InformationCircleIcon className="w-5 h-5 mr-2" />
              Customization Notes
            </Card.Title>
          </Card.Header>
          
          <Card.Content>
            <div className="space-y-2 text-sm text-neutral-600 dark:text-neutral-400">
              <p>• Customized packages may require additional lead time</p>
              <p>• Final pricing will be confirmed during quote process</p>
              <p>• Some customizations may affect warranty terms</p>
              <p>• Technical compatibility will be verified before shipment</p>
            </div>
          </Card.Content>
        </Card>
      )}

      {/* Action Buttons */}
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-2">
          {hasCustomizations && (
            <Badge variant="info" size="md">
              <CheckCircleIcon className="w-4 h-4 mr-1" />
              {Object.keys(customizedPackage.customizations.upgradedComponents).length + 
               customizedPackage.customizations.removedComponents.length} changes made
            </Badge>
          )}
        </div>
        
        <div className="flex space-x-3">
          <Button
            variant="outline"
            size="md"
            onClick={handleResetCustomization}
            disabled={!hasCustomizations}
          >
            Reset Customization
          </Button>
          
          <Button
            variant="primary"
            size="md"
            onClick={() => onSaveCustomization?.(customizedPackage)}
            leftIcon={<ShoppingCartIcon className="w-4 h-4" />}
          >
            Save Customization
          </Button>
        </div>
      </div>
    </div>
  )
}

export default PackageCustomizer