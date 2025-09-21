// Package Display Components
export { default as PackageCard } from './PackageCard'
export { default as ComponentList } from './ComponentList'
export { default as PricingTotal } from './PricingTotal'
export { default as CompatibilityScore } from './CompatibilityScore'
export { default as AgentRecommendationDisplay } from './AgentRecommendationDisplay'
export { default as PackageComparison } from './PackageComparison'
export { SelectedItemsPanel } from './SelectedItemsPanel'

// Advanced Package Features
export { default as PackageAlternatives } from './PackageAlternatives'
export { default as PackageCustomizer } from './PackageCustomizer'
export { default as QuoteRequest } from './QuoteRequest'

// Demo Component
export { default as PackageDemo } from './PackageDemo'

// Re-export types for convenience
export type {
  EnhancedWeldingPackage,
  EnhancedPackageComponent,
  AgentDecision,
  EnhancedOrchestratorResponse
} from '../../types/enhanced-orchestrator'