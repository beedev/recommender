import React from 'react'
import { useTranslation } from 'react-i18next'
import { EnhancedWeldingPackage } from '../../../types/enhanced-orchestrator'

interface SelectedItemsPanelProps {
  packages: EnhancedWeldingPackage[]
  className?: string
}

interface ComponentItem {
  name: string
  description: string
  price: number
}

// Mock data structure for demonstration (this should come from packages)
const mockSelectedItems: ComponentItem[] = [
  { name: 'Wire Feeder', description: 'Standard Wire Feeder', price: 2850.00 },
  { name: 'Connection Cable', description: '3m Cable Set', price: 145.00 },
  { name: 'Cooling Unit', description: 'Standard Cooling Unit', price: 1890.00 },
  { name: 'Torches', description: 'Standard MIG Torch', price: 475.00 },
  { name: 'Trolley', description: 'Standard Trolley', price: 320.00 },
  { name: 'Accessories', description: 'Basic Accessory Kit', price: 285.00 },
  { name: 'Wear Parts', description: 'Standard Wear Parts Kit', price: 284.92 },
  { name: 'Power Source', description: 'Multipurpose MIG/MMA Welder 400A', price: 4500.00 },
]

export const SelectedItemsPanel: React.FC<SelectedItemsPanelProps> = ({
  packages,
  className = ''
}) => {
  const { t } = useTranslation(['common', 'sparky'])

  // Calculate total price
  const totalPrice = mockSelectedItems.reduce((sum, item) => sum + item.price, 0)

  // For now, show panel only if there are packages (or use mock data for demo)
  const showPanel = packages.length > 0 || true // Always show for demo purposes

  if (!showPanel) {
    return null
  }

  return (
    <div className={`w-80 bg-white border-l border-gray-200 flex flex-col ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-2xl font-bold text-center text-gray-800">
          SPARKY'S CHOICE
        </h2>
      </div>
      
      {/* Components List */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {mockSelectedItems.map((item, index) => (
          <div 
            key={index}
            className="flex justify-between items-center py-3 border-b border-gray-100 last:border-b-0"
          >
            <div className="flex-1">
              <div className="font-semibold text-gray-800 text-sm">
                {item.name}
              </div>
              <div className="text-gray-600 text-xs opacity-80">
                {item.description}
              </div>
            </div>
            <div className="text-gray-800 font-bold text-sm ml-4">
              ${item.price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>
        ))}
      </div>
      
      {/* Total Section */}
      <div className="p-6 border-t-2 border-dashed border-gray-300 bg-gray-50">
        <div className="flex justify-between items-center">
          <span className="text-xl font-bold text-gray-800">Total Price:</span>
          <span className="text-xl font-bold text-gray-800">
            ${totalPrice.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </div>
      </div>
    </div>
  )
}