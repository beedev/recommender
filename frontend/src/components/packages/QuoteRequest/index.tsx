import React, { useState } from 'react'
import clsx from 'clsx'
import { EnhancedWeldingPackage } from '../../../types/enhanced-orchestrator'
import Card from '../../common/Card'

import Button from '../../common/Button'
import Input from '../../common/Input'
import Textarea from '../../common/Textarea'
import SimpleModal from '../../common/SimpleModal'
import { 
  DocumentTextIcon,
  UserIcon,
  BuildingOfficeIcon,
  PhoneIcon,
  EnvelopeIcon,
  MapPinIcon,
  CalendarDaysIcon,
  CurrencyDollarIcon,
  CheckCircleIcon,

  InformationCircleIcon,
  PaperAirplaneIcon
} from '@heroicons/react/24/outline'

interface QuoteRequestProps {
  package: EnhancedWeldingPackage
  isOpen: boolean
  onClose: () => void
  onSubmit?: (quoteData: QuoteRequestData) => void
  className?: string
}

interface QuoteRequestData {
  // Contact Information
  contactInfo: {
    firstName: string
    lastName: string
    email: string
    phone: string
    company: string
    jobTitle: string
  }
  
  // Project Information
  projectInfo: {
    projectName: string
    description: string
    timeline: string
    budget: string
    quantity: number
    location: string
  }
  
  // Package Information
  packageInfo: {
    packageId: string
    packageName: string
    customizations?: string
    additionalRequirements?: string
  }
  
  // Preferences
  preferences: {
    preferredContactMethod: 'email' | 'phone' | 'both'
    bestTimeToContact: string
    needsTraining: boolean
    needsInstallation: boolean
    needsFinancing: boolean
  }
}

const QuoteRequest: React.FC<QuoteRequestProps> = ({
  package: packageData,
  isOpen,
  onClose,
  onSubmit,
  className
}) => {
  const [currentStep, setCurrentStep] = useState(1)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitSuccess, setSubmitSuccess] = useState(false)
  
  const [quoteData, setQuoteData] = useState<QuoteRequestData>({
    contactInfo: {
      firstName: '',
      lastName: '',
      email: '',
      phone: '',
      company: '',
      jobTitle: ''
    },
    projectInfo: {
      projectName: '',
      description: '',
      timeline: '',
      budget: '',
      quantity: 1,
      location: ''
    },
    packageInfo: {
      packageId: packageData.package_id,
      packageName: packageData.package_name || `Package ${packageData.package_id}`,
      customizations: '',
      additionalRequirements: ''
    },
    preferences: {
      preferredContactMethod: 'email',
      bestTimeToContact: '',
      needsTraining: false,
      needsInstallation: false,
      needsFinancing: false
    }
  })

  const updateContactInfo = (updates: Partial<QuoteRequestData['contactInfo']>) => {
    setQuoteData(prev => ({
      ...prev,
      contactInfo: { ...prev.contactInfo, ...updates }
    }))
  }

  const updateProjectInfo = (updates: Partial<QuoteRequestData['projectInfo']>) => {
    setQuoteData(prev => ({
      ...prev,
      projectInfo: { ...prev.projectInfo, ...updates }
    }))
  }

  const updatePackageInfo = (updates: Partial<QuoteRequestData['packageInfo']>) => {
    setQuoteData(prev => ({
      ...prev,
      packageInfo: { ...prev.packageInfo, ...updates }
    }))
  }

  const updatePreferences = (updates: Partial<QuoteRequestData['preferences']>) => {
    setQuoteData(prev => ({
      ...prev,
      preferences: { ...prev.preferences, ...updates }
    }))
  }

  const validateStep = (step: number): boolean => {
    switch (step) {
      case 1:
        return !!(
          quoteData.contactInfo.firstName &&
          quoteData.contactInfo.lastName &&
          quoteData.contactInfo.email &&
          quoteData.contactInfo.phone
        )
      case 2:
        return !!(
          quoteData.projectInfo.projectName &&
          quoteData.projectInfo.description &&
          quoteData.projectInfo.timeline
        )
      case 3:
        return true // Package info is pre-filled
      default:
        return true
    }
  }

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, 4))
    }
  }

  const handlePrevious = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1))
  }

  const handleSubmit = async () => {
    setIsSubmitting(true)
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      onSubmit?.(quoteData)
      setSubmitSuccess(true)
      
      // Auto-close after success
      setTimeout(() => {
        onClose()
        setSubmitSuccess(false)
        setCurrentStep(1)
      }, 3000)
    } catch (error) {
      console.error('Failed to submit quote request:', error)
    } finally {
      setIsSubmitting(false)
    }
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

  const steps = [
    { number: 1, title: 'Contact Information', icon: UserIcon },
    { number: 2, title: 'Project Details', icon: BuildingOfficeIcon },
    { number: 3, title: 'Package Review', icon: DocumentTextIcon },
    { number: 4, title: 'Preferences & Submit', icon: PaperAirplaneIcon }
  ]

  if (submitSuccess) {
    return (
      <SimpleModal isOpen={isOpen} onClose={onClose} title="Quote Request Submitted" size="md">
        <div className="text-center py-8">
          <CheckCircleIcon className="w-16 h-16 text-success-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
            Quote Request Submitted Successfully!
          </h3>
          <p className="text-neutral-600 dark:text-neutral-400 mb-4">
            We've received your quote request and will contact you within 24 hours.
          </p>
          <div className="bg-success-50 dark:bg-success-900/20 border border-success-200 dark:border-success-800 rounded-lg p-4">
            <p className="text-sm text-success-700 dark:text-success-300">
              Reference ID: QR-{Date.now().toString().slice(-6)}
            </p>
          </div>
        </div>
      </SimpleModal>
    )
  }

  return (
    <SimpleModal isOpen={isOpen} onClose={onClose} title="Request Quote" size="xl">
      <div className={clsx('space-y-6', className)}>
        {/* Progress Steps */}
        <div className="flex items-center justify-between">
          {steps.map((step, index) => {
            const StepIcon = step.icon
            const isActive = currentStep === step.number
            const isCompleted = currentStep > step.number
            const isValid = validateStep(step.number)
            
            return (
              <div key={step.number} className="flex items-center">
                <div className={clsx(
                  'flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors',
                  isActive && 'border-sparky-gold bg-sparky-gold text-black',
                  isCompleted && 'border-success-500 bg-success-500 text-white',
                  !isActive && !isCompleted && isValid && 'border-neutral-300 text-neutral-600',
                  !isActive && !isCompleted && !isValid && 'border-error-300 text-error-600'
                )}>
                  {isCompleted ? (
                    <CheckCircleIcon className="w-5 h-5" />
                  ) : (
                    <StepIcon className="w-5 h-5" />
                  )}
                </div>
                
                <div className="ml-3 hidden md:block">
                  <div className={clsx(
                    'text-sm font-medium',
                    isActive && 'text-sparky-gold',
                    isCompleted && 'text-success-600',
                    !isActive && !isCompleted && 'text-neutral-600'
                  )}>
                    {step.title}
                  </div>
                </div>
                
                {index < steps.length - 1 && (
                  <div className={clsx(
                    'w-12 h-0.5 mx-4',
                    isCompleted ? 'bg-success-500' : 'bg-neutral-200'
                  )} />
                )}
              </div>
            )
          })}
        </div>

        {/* Step Content */}
        <div className="min-h-96">
          {/* Step 1: Contact Information */}
          {currentStep === 1 && (
            <Card variant="outlined">
              <Card.Header>
                <Card.Title className="flex items-center">
                  <UserIcon className="w-5 h-5 mr-2 text-sparky-gold" />
                  Contact Information
                </Card.Title>
                <Card.Description>
                  Please provide your contact details so we can reach you with the quote
                </Card.Description>
              </Card.Header>
              
              <Card.Content>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="First Name *"
                    value={quoteData.contactInfo.firstName}
                    onChange={(e) => updateContactInfo({ firstName: e.target.value })}
                    placeholder="Enter your first name"
                    required
                  />
                  
                  <Input
                    label="Last Name *"
                    value={quoteData.contactInfo.lastName}
                    onChange={(e) => updateContactInfo({ lastName: e.target.value })}
                    placeholder="Enter your last name"
                    required
                  />
                  
                  <Input
                    label="Email Address *"
                    type="email"
                    value={quoteData.contactInfo.email}
                    onChange={(e) => updateContactInfo({ email: e.target.value })}
                    placeholder="Enter your email address"
                    leftIcon={<EnvelopeIcon className="w-4 h-4" />}
                    required
                  />
                  
                  <Input
                    label="Phone Number *"
                    type="tel"
                    value={quoteData.contactInfo.phone}
                    onChange={(e) => updateContactInfo({ phone: e.target.value })}
                    placeholder="Enter your phone number"
                    leftIcon={<PhoneIcon className="w-4 h-4" />}
                    required
                  />
                  
                  <Input
                    label="Company"
                    value={quoteData.contactInfo.company}
                    onChange={(e) => updateContactInfo({ company: e.target.value })}
                    placeholder="Enter your company name"
                    leftIcon={<BuildingOfficeIcon className="w-4 h-4" />}
                  />
                  
                  <Input
                    label="Job Title"
                    value={quoteData.contactInfo.jobTitle}
                    onChange={(e) => updateContactInfo({ jobTitle: e.target.value })}
                    placeholder="Enter your job title"
                  />
                </div>
              </Card.Content>
            </Card>
          )}

          {/* Step 2: Project Information */}
          {currentStep === 2 && (
            <Card variant="outlined">
              <Card.Header>
                <Card.Title className="flex items-center">
                  <BuildingOfficeIcon className="w-5 h-5 mr-2 text-sparky-gold" />
                  Project Details
                </Card.Title>
                <Card.Description>
                  Tell us about your project to help us provide the most accurate quote
                </Card.Description>
              </Card.Header>
              
              <Card.Content>
                <div className="space-y-4">
                  <Input
                    label="Project Name *"
                    value={quoteData.projectInfo.projectName}
                    onChange={(e) => updateProjectInfo({ projectName: e.target.value })}
                    placeholder="Enter your project name"
                    required
                  />
                  
                  <Textarea
                    label="Project Description *"
                    value={quoteData.projectInfo.description}
                    onChange={(e) => updateProjectInfo({ description: e.target.value })}
                    placeholder="Describe your welding project, materials, and requirements"
                    rows={4}
                    required
                  />
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                        Project Timeline *
                      </label>
                      <select
                        value={quoteData.projectInfo.timeline}
                        onChange={(e) => updateProjectInfo({ timeline: e.target.value })}
                        className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-sparky-gold focus:border-sparky-gold"
                        required
                      >
                        <option value="">Select timeline</option>
                        <option value="immediate">Immediate (within 1 week)</option>
                        <option value="1-2weeks">1-2 weeks</option>
                        <option value="1month">Within 1 month</option>
                        <option value="3months">Within 3 months</option>
                        <option value="6months">Within 6 months</option>
                        <option value="flexible">Flexible</option>
                      </select>
                    </div>
                    
                    <Input
                      label="Quantity"
                      type="number"
                      min="1"
                      value={quoteData.projectInfo.quantity}
                      onChange={(e) => updateProjectInfo({ quantity: parseInt(e.target.value) || 1 })}
                      placeholder="Number of units needed"
                    />
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Input
                      label="Budget Range"
                      value={quoteData.projectInfo.budget}
                      onChange={(e) => updateProjectInfo({ budget: e.target.value })}
                      placeholder="e.g., $10,000 - $15,000"
                      leftIcon={<CurrencyDollarIcon className="w-4 h-4" />}
                    />
                    
                    <Input
                      label="Location"
                      value={quoteData.projectInfo.location}
                      onChange={(e) => updateProjectInfo({ location: e.target.value })}
                      placeholder="City, State/Country"
                      leftIcon={<MapPinIcon className="w-4 h-4" />}
                    />
                  </div>
                </div>
              </Card.Content>
            </Card>
          )}

          {/* Step 3: Package Review */}
          {currentStep === 3 && (
            <Card variant="outlined">
              <Card.Header>
                <Card.Title className="flex items-center">
                  <DocumentTextIcon className="w-5 h-5 mr-2 text-sparky-gold" />
                  Package Review
                </Card.Title>
                <Card.Description>
                  Review the selected package and add any customizations or special requirements
                </Card.Description>
              </Card.Header>
              
              <Card.Content>
                <div className="space-y-4">
                  {/* Package Summary */}
                  <div className="p-4 bg-sparky-gold/10 border border-sparky-gold/20 rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-semibold text-neutral-900 dark:text-neutral-100">
                        {packageData.package_name || `Package ${packageData.package_id}`}
                      </h4>
                      <div className="text-xl font-bold text-sparky-gold">
                        {formatPrice(packageData.total_price)}
                      </div>
                    </div>
                    
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-neutral-600 dark:text-neutral-400">Power Source:</span>
                        <span className="text-neutral-900 dark:text-neutral-100">
                          {packageData.powersource.product_name}
                        </span>
                      </div>
                      
                      {packageData.feeder && (
                        <div className="flex justify-between">
                          <span className="text-neutral-600 dark:text-neutral-400">Wire Feeder:</span>
                          <span className="text-neutral-900 dark:text-neutral-100">
                            {packageData.feeder.product_name}
                          </span>
                        </div>
                      )}
                      
                      {packageData.cooler && (
                        <div className="flex justify-between">
                          <span className="text-neutral-600 dark:text-neutral-400">Cooling System:</span>
                          <span className="text-neutral-900 dark:text-neutral-100">
                            {packageData.cooler.product_name}
                          </span>
                        </div>
                      )}
                      
                      {packageData.torch && (
                        <div className="flex justify-between">
                          <span className="text-neutral-600 dark:text-neutral-400">Welding Torch:</span>
                          <span className="text-neutral-900 dark:text-neutral-100">
                            {packageData.torch.product_name}
                          </span>
                        </div>
                      )}
                      
                      <div className="flex justify-between">
                        <span className="text-neutral-600 dark:text-neutral-400">Accessories:</span>
                        <span className="text-neutral-900 dark:text-neutral-100">
                          {packageData.accessories.length} items included
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <Textarea
                    label="Customizations or Modifications"
                    value={quoteData.packageInfo.customizations}
                    onChange={(e) => updatePackageInfo({ customizations: e.target.value })}
                    placeholder="Describe any customizations or modifications you need"
                    rows={3}
                  />
                  
                  <Textarea
                    label="Additional Requirements"
                    value={quoteData.packageInfo.additionalRequirements}
                    onChange={(e) => updatePackageInfo({ additionalRequirements: e.target.value })}
                    placeholder="Any additional equipment, accessories, or special requirements"
                    rows={3}
                  />
                </div>
              </Card.Content>
            </Card>
          )}

          {/* Step 4: Preferences & Submit */}
          {currentStep === 4 && (
            <Card variant="outlined">
              <Card.Header>
                <Card.Title className="flex items-center">
                  <PaperAirplaneIcon className="w-5 h-5 mr-2 text-sparky-gold" />
                  Preferences & Submit
                </Card.Title>
                <Card.Description>
                  Set your communication preferences and submit your quote request
                </Card.Description>
              </Card.Header>
              
              <Card.Content>
                <div className="space-y-6">
                  {/* Contact Preferences */}
                  <div>
                    <h4 className="font-medium text-neutral-900 dark:text-neutral-100 mb-3">
                      Contact Preferences
                    </h4>
                    
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                          Preferred Contact Method
                        </label>
                        <div className="space-y-2">
                          {[
                            { value: 'email', label: 'Email', icon: '📧' },
                            { value: 'phone', label: 'Phone', icon: '📞' },
                            { value: 'both', label: 'Both Email and Phone', icon: '📱' }
                          ].map(option => (
                            <label key={option.value} className="flex items-center space-x-2">
                              <input
                                type="radio"
                                name="contactMethod"
                                value={option.value}
                                checked={quoteData.preferences.preferredContactMethod === option.value}
                                onChange={(e) => updatePreferences({ preferredContactMethod: e.target.value as any })}
                                className="text-sparky-gold focus:ring-sparky-gold"
                              />
                              <span className="text-sm text-neutral-700 dark:text-neutral-300">
                                {option.icon} {option.label}
                              </span>
                            </label>
                          ))}
                        </div>
                      </div>
                      
                      <Input
                        label="Best Time to Contact"
                        value={quoteData.preferences.bestTimeToContact}
                        onChange={(e) => updatePreferences({ bestTimeToContact: e.target.value })}
                        placeholder="e.g., Weekdays 9 AM - 5 PM EST"
                        leftIcon={<CalendarDaysIcon className="w-4 h-4" />}
                      />
                    </div>
                  </div>
                  
                  {/* Additional Services */}
                  <div>
                    <h4 className="font-medium text-neutral-900 dark:text-neutral-100 mb-3">
                      Additional Services
                    </h4>
                    
                    <div className="space-y-3">
                      {[
                        { key: 'needsTraining', label: 'Training Services', description: 'Professional training for your team' },
                        { key: 'needsInstallation', label: 'Installation Services', description: 'Professional installation and setup' },
                        { key: 'needsFinancing', label: 'Financing Options', description: 'Flexible payment and financing plans' }
                      ].map(service => (
                        <label key={service.key} className="flex items-start space-x-3 p-3 border border-neutral-200 dark:border-neutral-700 rounded-lg hover:border-sparky-gold/50 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={quoteData.preferences[service.key as keyof typeof quoteData.preferences] as boolean}
                            onChange={(e) => updatePreferences({ [service.key]: e.target.checked })}
                            className="mt-1 text-sparky-gold focus:ring-sparky-gold"
                          />
                          <div>
                            <div className="font-medium text-neutral-900 dark:text-neutral-100">
                              {service.label}
                            </div>
                            <div className="text-sm text-neutral-600 dark:text-neutral-400">
                              {service.description}
                            </div>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                  
                  {/* Important Notes */}
                  <div className="p-4 bg-info-50 dark:bg-info-900/20 border border-info-200 dark:border-info-800 rounded-lg">
                    <div className="flex items-start space-x-3">
                      <InformationCircleIcon className="w-5 h-5 text-info-500 mt-0.5 flex-shrink-0" />
                      <div className="text-sm text-info-700 dark:text-info-300">
                        <div className="font-medium mb-1">Important Notes</div>
                        <ul className="space-y-1 text-xs">
                          <li>• Quote requests are typically processed within 24 hours</li>
                          <li>• Final pricing may vary based on current market conditions</li>
                          <li>• Delivery times depend on product availability and location</li>
                          <li>• All quotes are valid for 30 days from issue date</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </Card.Content>
            </Card>
          )}
        </div>

        {/* Navigation Buttons */}
        <div className="flex justify-between items-center pt-6 border-t border-neutral-200 dark:border-neutral-700">
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={currentStep === 1}
          >
            Previous
          </Button>
          
          <div className="flex items-center space-x-2">
            <span className="text-sm text-neutral-600 dark:text-neutral-400">
              Step {currentStep} of {steps.length}
            </span>
          </div>
          
          {currentStep < steps.length ? (
            <Button
              variant="primary"
              onClick={handleNext}
              disabled={!validateStep(currentStep)}
            >
              Next
            </Button>
          ) : (
            <Button
              variant="primary"
              onClick={handleSubmit}
              loading={isSubmitting}
              leftIcon={<PaperAirplaneIcon className="w-4 h-4" />}
            >
              {isSubmitting ? 'Submitting...' : 'Submit Quote Request'}
            </Button>
          )}
        </div>
      </div>
    </SimpleModal>
  )
}

export default QuoteRequest