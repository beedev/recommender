import React, { useState } from 'react'
// import { useTranslation } from 'react-i18next'
import { Zap } from 'lucide-react'
import { SparkyChat } from '../../components/chat'
import { useEnhancedConversation } from '@hooks/useEnhancedConversation'

const SparkyPage: React.FC = () => {
  // const { t } = useTranslation(['sparky', 'common']) // Commented out until used
  
  // Enhanced conversation hooks
  const {
    packages,
    selectPackage
  } = useEnhancedConversation()

  // Local UI state
  const [conversationMode, setConversationMode] = useState<'guided' | 'expert'>('expert')

  // Helper function to calculate package total price from API data
  const calculatePackageTotal = (pkg: any): number => {
    // Use API-provided total price if available
    if (pkg.total_price) return pkg.total_price
    
    // Calculate from individual components if total not provided
    let total = 0
    
    // Add component prices if available
    if (pkg.powersource?.price) total += pkg.powersource.price
    if (pkg.feeder?.price) total += pkg.feeder.price
    if (pkg.cooler?.price) total += pkg.cooler.price
    
    // Add accessories if available
    if (pkg.accessories && Array.isArray(pkg.accessories)) {
      pkg.accessories.forEach((accessory: any) => {
        if (accessory.price) total += accessory.price
      })
    }
    
    return total
  }

  return (
    <div className="flex h-full bg-gradient-esab">
      {/* Left Side: Ask Sparky */}
      <div className="flex-1 p-8 flex flex-col">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-white text-3xl font-bold flex items-center gap-3">
            <Zap className="w-8 h-8 text-sparky-gold" />
            Ask Sparky
          </h1>
          
          {/* Conversation Mode Indicator */}
          <div className="text-white text-sm bg-white/10 px-3 py-1 rounded-full">
            Mode: <span className="capitalize font-medium">{conversationMode}</span>
          </div>
        </div>
        
        {/* Chat Interface */}
        <div className="flex-1 bg-white/5 backdrop-blur-sm rounded-lg overflow-hidden">
          <SparkyChat
            onPackageRecommendation={(packages) => {
              console.log('Received package recommendations:', packages)
            }}
            onConversationModeChange={setConversationMode}
            className="h-full"
          />
        </div>
      </div>

      {/* Right Side: Package Recommendations */}
      {packages.length > 0 && (
        <div className="w-96 p-8">
          <h2 className="text-white text-xl font-bold mb-6">Recommended Packages</h2>
          <div className="space-y-4">
            {packages.map((pkg) => (
              <div
                key={pkg.package_id}
                className="package-card cursor-pointer hover:shadow-xl transition-all duration-300"
                onClick={() => selectPackage(pkg)}
              >
                <div className="package-header">
                  <div className="sparky-icon">
                    <Zap className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-bold text-lg">{pkg.powersource.product_name}</h3>
                    <p className="text-sm opacity-80">
                      {(pkg.compatibility_confidence * 100).toFixed(0)}% Match
                    </p>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div className="component-item">
                    <div>
                      <div className="component-name">Power Source</div>
                      <div className="component-description">{pkg.powersource.description}</div>
                    </div>
                    <div className="component-price">
                      ${pkg.powersource.price?.toLocaleString() || 'N/A'}
                    </div>
                  </div>
                  
                  {pkg.feeder && (
                    <div className="component-item">
                      <div>
                        <div className="component-name">Feeder</div>
                        <div className="component-description">{pkg.feeder.description}</div>
                      </div>
                      <div className="component-price">
                        ${pkg.feeder.price?.toLocaleString() || 'N/A'}
                      </div>
                    </div>
                  )}
                  
                  {pkg.cooler && (
                    <div className="component-item">
                      <div>
                        <div className="component-name">Cooler</div>
                        <div className="component-description">{pkg.cooler.description}</div>
                      </div>
                      <div className="component-price">
                        ${pkg.cooler.price?.toLocaleString() || 'N/A'}
                      </div>
                    </div>
                  )}
                </div>
                
                <div className="total-section">
                  <div className="total-price">
                    <span>Total Package Price</span>
                    <span>${calculatePackageTotal(pkg).toLocaleString()}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default SparkyPage