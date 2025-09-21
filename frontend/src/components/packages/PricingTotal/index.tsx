import React from 'react'
import clsx from 'clsx'
import { useTranslation } from 'react-i18next'
import { EnhancedWeldingPackage } from '../../../types/enhanced-orchestrator'
import { useLocalization } from '../../../hooks/useLocalization'
import Card from '../../common/Card'
import Badge from '../../common/Badge'
import Button from '../../common/Button'
import { 
  CurrencyDollarIcon,
  CalculatorIcon,
  TagIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'

interface PricingTotalProps {
  package: EnhancedWeldingPackage
  showBreakdown?: boolean
  showSavings?: boolean
  showActions?: boolean
  onRequestQuote?: (packageData: EnhancedWeldingPackage) => void
  onCustomize?: (packageData: EnhancedWeldingPackage) => void
  className?: string
}

const PricingTotal: React.FC<PricingTotalProps> = ({
  package: packageData,
  showBreakdown = true,
  showSavings = true,
  showActions = true,
  onRequestQuote,
  onCustomize,
  className
}) => {
  const { t } = useTranslation(['inventory', 'common'])
  const { formatCurrency, formatPercentage } = useLocalization()
  
  // Calculate component prices
  const componentPrices = {
    powersource: packageData.powersource.price || 0,
    feeder: packageData.feeder?.price || 0,
    cooler: packageData.cooler?.price || 0,
    torch: packageData.torch?.price || 0,
    accessories: packageData.accessories.reduce((sum, acc) => sum + (acc.price || 0), 0)
  }

  const calculatedTotal = Object.values(componentPrices).reduce((sum, price) => sum + price, 0)
  const displayTotal = packageData.total_price || calculatedTotal
  const hasPriceDiscrepancy = packageData.total_price && Math.abs(calculatedTotal - packageData.total_price) > 1
  const savings = calculatedTotal > displayTotal ? calculatedTotal - displayTotal : 0

  // Format price using localization
  const formatPrice = (price: number) => {
    return formatCurrency(price, 'USD', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    })
  }

  const handleRequestQuote = () => {
    onRequestQuote?.(packageData)
  }

  const handleCustomize = () => {
    onCustomize?.(packageData)
  }

  return (
    <Card
      variant="default"
      shadow="md"
      className={clsx('sticky top-4', className)}
    >
      <Card.Header>
        <Card.Title className="flex items-center">
          <CurrencyDollarIcon className="w-5 h-5 mr-2 text-sparky-gold" />
          {t('inventory:price')} {t('inventory:packages')}
        </Card.Title>
      </Card.Header>

      <Card.Content>
        {/* Price Breakdown */}
        {showBreakdown && (
          <div className="space-y-3 mb-6">
            <h4 className="font-medium text-neutral-900 dark:text-neutral-100 flex items-center">
              <CalculatorIcon className="w-4 h-4 mr-1 text-neutral-500" />
              {t('inventory:price')} {t('common:breakdown', 'Breakdown')}
            </h4>
            
            <div className="space-y-2">
              {/* Power Source */}
              <div className="flex justify-between items-center py-2 border-b border-neutral-100 dark:border-neutral-800">
                <div>
                  <div className="font-medium text-sm text-neutral-900 dark:text-neutral-100">
                    {packageData.powersource.product_name}
                  </div>
                  <div className="text-xs text-neutral-500">Power Source</div>
                </div>
                <div className="font-medium text-neutral-900 dark:text-neutral-100">
                  {formatPrice(componentPrices.powersource)}
                </div>
              </div>

              {/* Optional Components */}
              {packageData.feeder && componentPrices.feeder > 0 && (
                <div className="flex justify-between items-center py-2 border-b border-neutral-100 dark:border-neutral-800">
                  <div>
                    <div className="font-medium text-sm text-neutral-900 dark:text-neutral-100">
                      {packageData.feeder.product_name}
                    </div>
                    <div className="text-xs text-neutral-500">Wire Feeder</div>
                  </div>
                  <div className="font-medium text-neutral-900 dark:text-neutral-100">
                    {formatPrice(componentPrices.feeder)}
                  </div>
                </div>
              )}

              {packageData.cooler && componentPrices.cooler > 0 && (
                <div className="flex justify-between items-center py-2 border-b border-neutral-100 dark:border-neutral-800">
                  <div>
                    <div className="font-medium text-sm text-neutral-900 dark:text-neutral-100">
                      {packageData.cooler.product_name}
                    </div>
                    <div className="text-xs text-neutral-500">Cooling System</div>
                  </div>
                  <div className="font-medium text-neutral-900 dark:text-neutral-100">
                    {formatPrice(componentPrices.cooler)}
                  </div>
                </div>
              )}

              {packageData.torch && componentPrices.torch > 0 && (
                <div className="flex justify-between items-center py-2 border-b border-neutral-100 dark:border-neutral-800">
                  <div>
                    <div className="font-medium text-sm text-neutral-900 dark:text-neutral-100">
                      {packageData.torch.product_name}
                    </div>
                    <div className="text-xs text-neutral-500">Welding Torch</div>
                  </div>
                  <div className="font-medium text-neutral-900 dark:text-neutral-100">
                    {formatPrice(componentPrices.torch)}
                  </div>
                </div>
              )}

              {/* Accessories */}
              {componentPrices.accessories > 0 && (
                <div className="flex justify-between items-center py-2 border-b border-neutral-100 dark:border-neutral-800">
                  <div>
                    <div className="font-medium text-sm text-neutral-900 dark:text-neutral-100">
                      Accessories
                    </div>
                    <div className="text-xs text-neutral-500">
                      {packageData.accessories.length} items
                    </div>
                  </div>
                  <div className="font-medium text-neutral-900 dark:text-neutral-100">
                    {formatPrice(componentPrices.accessories)}
                  </div>
                </div>
              )}

              {/* Subtotal */}
              <div className="flex justify-between items-center py-2 font-medium text-neutral-900 dark:text-neutral-100">
                <span>{t('inventory:product_detail.subtotal')}</span>
                <span>{formatPrice(calculatedTotal)}</span>
              </div>
            </div>
          </div>
        )}

        {/* Savings */}
        {showSavings && savings > 0 && (
          <div className="mb-6 p-3 bg-success-50 dark:bg-success-900/20 border border-success-200 dark:border-success-800 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <TagIcon className="w-4 h-4 text-success-500" />
                <span className="font-medium text-success-700 dark:text-success-300">
                  {t('inventory:packages')} {t('inventory:product_detail.savings')}
                </span>
              </div>
              <span className="font-bold text-success-700 dark:text-success-300">
                -{formatPrice(savings)}
              </span>
            </div>
            <div className="text-sm text-success-600 dark:text-success-400 mt-1">
              {t('common:save')} {formatPercentage(savings / calculatedTotal)} {t('common:with_package_deal', 'with this package deal')}
            </div>
          </div>
        )}

        {/* Price Discrepancy Warning */}
        {hasPriceDiscrepancy && (
          <div className="mb-6 p-3 bg-warning-50 dark:bg-warning-900/20 border border-warning-200 dark:border-warning-800 rounded-lg">
            <div className="flex items-start space-x-2">
              <ExclamationTriangleIcon className="w-4 h-4 text-warning-500 mt-0.5 flex-shrink-0" />
              <div>
                <div className="font-medium text-warning-700 dark:text-warning-300 text-sm">
                  Price Verification Needed
                </div>
                <div className="text-sm text-warning-600 dark:text-warning-400 mt-1">
                  Component total differs from package price. Final pricing will be confirmed during quote.
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Total Price */}
        <div className="border-t border-neutral-200 dark:border-neutral-700 pt-4 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <div className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
                {t('inventory:product_detail.total')} {t('inventory:packages')} {t('inventory:price')}
              </div>
              {displayTotal === 0 && (
                <div className="text-sm text-neutral-500">
                  {t('inventory:product_detail.contact_for_pricing')}
                </div>
              )}
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-sparky-gold">
                {displayTotal > 0 ? formatPrice(displayTotal) : t('inventory:product_detail.quote_required')}
              </div>
              {savings > 0 && (
                <div className="text-sm text-success-600 dark:text-success-400">
                  {t('common:you_save', 'You save')} {formatPrice(savings)}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Confidence Indicators */}
        <div className="space-y-2 mb-6">
          <div className="flex items-center justify-between p-2 bg-neutral-50 dark:bg-neutral-800 rounded">
            <div className="flex items-center space-x-2">
              <CheckCircleIcon className="w-4 h-4 text-success-500" />
              <span className="text-sm font-medium">{t('inventory:compatibility')}</span>
            </div>
            <Badge variant="success" size="sm">
              {formatPercentage(packageData.compatibility_confidence)}
            </Badge>
          </div>
          
          {packageData.metadata?.validation_score && (
            <div className="flex items-center justify-between p-2 bg-neutral-50 dark:bg-neutral-800 rounded">
              <div className="flex items-center space-x-2">
                <CheckCircleIcon className="w-4 h-4 text-info-500" />
                <span className="text-sm font-medium">{t('common:validation', 'Validation')}</span>
              </div>
              <Badge variant="info" size="sm">
                {formatPercentage(packageData.metadata.validation_score)}
              </Badge>
            </div>
          )}
        </div>

        {/* Pricing Notes */}
        <div className="p-3 bg-info-50 dark:bg-info-900/20 border border-info-200 dark:border-info-800 rounded-lg mb-6">
          <div className="flex items-start space-x-2">
            <InformationCircleIcon className="w-4 h-4 text-info-500 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-info-700 dark:text-info-300">
              <div className="font-medium mb-1">Pricing Information</div>
              <ul className="space-y-1 text-xs">
                <li>• Prices shown are MSRP and may vary by dealer</li>
                <li>• Installation and training not included</li>
                <li>• Financing options available</li>
                <li>• Bulk discounts may apply for multiple units</li>
              </ul>
            </div>
          </div>
        </div>
      </Card.Content>

      {/* Actions */}
      {showActions && (
        <Card.Footer>
          <div className="flex flex-col space-y-2 w-full">
            {onRequestQuote && (
              <Button
                variant="primary"
                size="lg"
                fullWidth
                onClick={handleRequestQuote}
                leftIcon={<CurrencyDollarIcon className="w-4 h-4" />}
              >
                {t('inventory:product_detail.request_quote')}
              </Button>
            )}
            
            {onCustomize && (
              <Button
                variant="outline"
                size="md"
                fullWidth
                onClick={handleCustomize}
              >
                {t('inventory:product_detail.customize_package')}
              </Button>
            )}
          </div>
        </Card.Footer>
      )}
    </Card>
  )
}

export default PricingTotal