import React, { useState } from 'react'
import { 
  PackageCard, 
  ComponentList, 
  PricingTotal, 
  CompatibilityScore,
  AgentRecommendationDisplay,
  PackageComparison,
  PackageAlternatives,
  PackageCustomizer,
  QuoteRequest
} from '../index'
import { EnhancedWeldingPackage, EnhancedOrchestratorResponse } from '../../../types/enhanced-orchestrator'
import Button from '../../common/Button'

// Mock data for demonstration
const mockPackage: EnhancedWeldingPackage = {
  package_id: 'pkg-001',
  package_name: 'Professional MIG Welding Package',
  description: 'Complete MIG welding solution for professional applications',
  powersource: {
    product_id: 'ps-001',
    product_name: 'Warrior 500i',
    category: 'Power Source',
    manufacturer: 'ESAB',
    description: 'Advanced inverter-based power source with digital controls',
    price: 8500,
    compatibility_score: 0.95,
    sales_frequency: 'high',
    sales_count: 150
  },
  feeder: {
    product_id: 'wf-001',
    product_name: 'Aristo Feed 3004',
    category: 'Wire Feeder',
    manufacturer: 'ESAB',
    description: 'Professional 4-roll wire feeder with precise control',
    price: 2200,
    compatibility_score: 0.92
  },
  cooler: {
    product_id: 'cool-001',
    product_name: 'Cool Arc 40',
    category: 'Cooling System',
    manufacturer: 'ESAB',
    description: 'High-capacity cooling system for continuous operation',
    price: 1800,
    compatibility_score: 0.88
  },
  torch: {
    product_id: 'torch-001',
    product_name: 'PT-36 Torch',
    category: 'Welding Torch',
    manufacturer: 'ESAB',
    description: 'Professional MIG torch with ergonomic design',
    price: 450,
    compatibility_score: 0.90
  },
  accessories: [
    {
      product_id: 'acc-001',
      product_name: 'Welding Helmet',
      category: 'Safety Equipment',
      price: 350,
      compatibility_score: 1.0
    },
    {
      product_id: 'acc-002',
      product_name: 'Ground Cable Set',
      category: 'Accessories',
      price: 120,
      compatibility_score: 1.0
    }
  ],
  total_price: 13420,
  compatibility_confidence: 0.92,
  recommendation_reason: 'This package provides excellent performance for professional MIG welding applications with high compatibility scores across all components.',
  sales_evidence: 'Popular choice among professional welders with 150+ units sold this quarter',
  metadata: {
    validation_score: 0.88,
    recommendation_method: 'agent_based'
  }
}

const mockResponse: EnhancedOrchestratorResponse = {
  status: 'success',
  timestamp: new Date().toISOString(),
  session_id: 'session-123',
  user_id: 'user-456',
  processing_time_ms: 1250,
  flow_type: 'quick_package',
  data: {
    packages: [mockPackage],
    package_count: 1,
    selected_language: 'en',
    ui_translations: {}
  },
  metadata: {
    orchestrator_type: 'enhanced',
    orchestrator_version: '2.0.0',
    current_flow_state: 'completed',
    validation_score: 0.88,
    recommendation_confidence: 0.92,
    compatibility_confidence: 0.92,
    agent_decisions_count: 6,
    enhanced_features: {
      flow_manager_used: true,
      error_handler_used: false,
      hierarchical_state: true,
      observability_enabled: true
    }
  }
}

const PackageDemo: React.FC = () => {
  const [selectedPackage, setSelectedPackage] = useState<EnhancedWeldingPackage | undefined>()
  const [showComparison, setShowComparison] = useState(false)
  const [showAlternatives, setShowAlternatives] = useState(false)
  const [showCustomizer, setShowCustomizer] = useState(false)
  const [showQuoteRequest, setShowQuoteRequest] = useState(false)

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100 mb-4">
          Package Display System Demo
        </h1>
        <p className="text-neutral-600 dark:text-neutral-400 mb-8">
          Demonstration of the dynamic package display components with agent-based recommendations
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-4 justify-center">
        <Button
          variant="primary"
          onClick={() => setSelectedPackage(mockPackage)}
        >
          Select Package
        </Button>
        <Button
          variant="outline"
          onClick={() => setShowComparison(!showComparison)}
        >
          {showComparison ? 'Hide' : 'Show'} Comparison
        </Button>
        <Button
          variant="outline"
          onClick={() => setShowAlternatives(!showAlternatives)}
        >
          {showAlternatives ? 'Hide' : 'Show'} Alternatives
        </Button>
        <Button
          variant="outline"
          onClick={() => setShowCustomizer(!showCustomizer)}
        >
          {showCustomizer ? 'Hide' : 'Show'} Customizer
        </Button>
        <Button
          variant="outline"
          onClick={() => setShowQuoteRequest(true)}
        >
          Request Quote
        </Button>
      </div>

      {/* Agent Recommendation Display */}
      <section>
        <h2 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
          Agent-Based Recommendations
        </h2>
        <AgentRecommendationDisplay
          response={mockResponse}
          selectedPackage={selectedPackage}
          onPackageSelect={setSelectedPackage}
          onViewDetails={(pkg) => console.log('View details:', pkg)}
        />
      </section>

      {/* Package Card */}
      <section>
        <h2 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
          Package Card
        </h2>
        <div className="max-w-2xl">
          <PackageCard
            package={mockPackage}
            selected={selectedPackage?.package_id === mockPackage.package_id}
            onSelect={setSelectedPackage}
            onViewDetails={(pkg) => console.log('View details:', pkg)}
            showComparison={true}
          />
        </div>
      </section>

      {/* Component List */}
      <section>
        <h2 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
          Component Breakdown
        </h2>
        <ComponentList
          components={{
            powersource: mockPackage.powersource,
            feeder: mockPackage.feeder,
            cooler: mockPackage.cooler,
            torch: mockPackage.torch,
            accessories: mockPackage.accessories
          }}
          showPricing={true}
          showSpecifications={true}
          expandable={true}
        />
      </section>

      {/* Pricing and Compatibility */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <section>
          <h2 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
            Pricing Total
          </h2>
          <PricingTotal
            package={mockPackage}
            showBreakdown={true}
            showSavings={true}
            showActions={true}
            onRequestQuote={() => setShowQuoteRequest(true)}
            onCustomize={() => setShowCustomizer(true)}
          />
        </section>

        <section>
          <h2 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
            Compatibility Score
          </h2>
          <CompatibilityScore
            package={mockPackage}
            showDetails={true}
            showRecommendationReason={true}
          />
        </section>
      </div>

      {/* Package Comparison */}
      {showComparison && (
        <section>
          <h2 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
            Package Comparison
          </h2>
          <PackageComparison
            packages={[mockPackage, { ...mockPackage, package_id: 'pkg-002', package_name: 'Alternative Package' }]}
            selectedPackage={selectedPackage}
            onPackageSelect={setSelectedPackage}
            onClose={() => setShowComparison(false)}
          />
        </section>
      )}

      {/* Package Alternatives */}
      {showAlternatives && (
        <section>
          <h2 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
            Package Alternatives
          </h2>
          <PackageAlternatives
            currentPackage={mockPackage}
            alternatives={[]}
            onSelectAlternative={setSelectedPackage}
            onViewDetails={(pkg) => console.log('View details:', pkg)}
            onRequestAlternatives={(criteria) => console.log('Request alternatives:', criteria)}
          />
        </section>
      )}

      {/* Package Customizer */}
      {showCustomizer && (
        <section>
          <h2 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
            Package Customizer
          </h2>
          <PackageCustomizer
            package={mockPackage}
            onCustomizationChange={(customized) => console.log('Customization changed:', customized)}
            onSaveCustomization={(customized) => {
              console.log('Save customization:', customized)
              setShowCustomizer(false)
            }}
            onResetCustomization={() => console.log('Reset customization')}
          />
        </section>
      )}

      {/* Quote Request Modal */}
      <QuoteRequest
        package={mockPackage}
        isOpen={showQuoteRequest}
        onClose={() => setShowQuoteRequest(false)}
        onSubmit={(quoteData) => {
          console.log('Quote submitted:', quoteData)
          setShowQuoteRequest(false)
        }}
      />
    </div>
  )
}

export default PackageDemo