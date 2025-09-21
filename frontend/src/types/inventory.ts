export interface Product {
  id: string
  name: string
  description: string
  category: string
  subcategory?: string
  brand: string
  model: string
  sku: string
  images: Array<{
    id: string
    url: string
    alt: string
    isPrimary: boolean
  }>
  specifications: Record<string, unknown>
  features: string[]
  applications: string[]
  compatibility: string[]
  certifications: string[]
  dimensions: {
    length?: number
    width?: number
    height?: number
    weight?: number
    unit: string
  }
  pricing: {
    msrp: number
    current: number
    currency: string
    discounts?: Array<{
      type: 'percentage' | 'fixed'
      value: number
      validFrom: string
      validTo: string
      conditions?: string[]
    }>
  }
  availability: {
    status: 'in_stock' | 'low_stock' | 'out_of_stock' | 'discontinued'
    quantity?: number
    leadTime?: number
    suppliers: string[]
  }
  seo: {
    slug: string
    metaTitle: string
    metaDescription: string
    keywords: string[]
  }
  createdAt: string
  updatedAt: string
  isActive: boolean
  rating: {
    average: number
    count: number
  }
  tags: string[]
}

export interface InventoryItem {
  id: string
  productId: string
  product: Product
  location: {
    warehouse: string
    zone?: string
    aisle?: string
    shelf?: string
    bin?: string
  }
  quantity: {
    available: number
    reserved: number
    onOrder: number
    minimum: number
    maximum: number
    reorderPoint: number
  }
  costs: {
    unitCost: number
    totalValue: number
    averageCost: number
    lastCost: number
  }
  tracking: {
    serialNumbers?: string[]
    batchNumbers?: string[]
    expirationDates?: string[]
    receivedDate: string
    lastMovement: string
  }
  supplier: {
    id: string
    name: string
    partNumber?: string
    leadTime: number
    minimumOrder: number
  }
  status: 'active' | 'inactive' | 'quarantine' | 'damaged'
  notes?: string
  lastUpdated: string
  updatedBy: string
}

export interface ProductFilter {
  category: string | null
  brand: string | null
  availability: 'in_stock' | 'all' | null
  priceRange: {
    min: number
    max: number
  } | null
  features?: string[]
  applications?: string[]
  rating?: number
  tags?: string[]
}

export interface InventoryMovement {
  id: string
  productId: string
  type: 'in' | 'out' | 'adjustment' | 'transfer'
  quantity: number
  reason: string
  reference?: string
  fromLocation?: string
  toLocation?: string
  cost?: number
  timestamp: string
  performedBy: string
  notes?: string
}

export interface StockAlert {
  id: string
  productId: string
  product: Product
  type: 'low_stock' | 'out_of_stock' | 'overstocked' | 'expiring'
  severity: 'low' | 'medium' | 'high' | 'critical'
  message: string
  currentLevel: number
  targetLevel: number
  actionRequired: string
  createdAt: string
  resolvedAt?: string
  resolvedBy?: string
}

export interface ProductSearchResult {
  products: Product[]
  total: number
  page: number
  limit: number
  totalPages: number
  filters: {
    categories: Array<{ name: string; count: number }>
    brands: Array<{ name: string; count: number }>
    priceRange: { min: number; max: number }
    features: Array<{ name: string; count: number }>
  }
}

export interface ProductComparison {
  products: Product[]
  comparisonMatrix: {
    [key: string]: {
      [productId: string]: string | number | boolean
    }
  }
  recommendations: {
    best: string
    reasons: string[]
  }
}

export interface ProductReview {
  id: string
  productId: string
  userId: string
  user: {
    name: string
    avatar?: string
    verified: boolean
  }
  rating: number
  title: string
  content: string
  pros: string[]
  cons: string[]
  images?: string[]
  helpfulVotes: number
  verifiedPurchase: boolean
  createdAt: string
  updatedAt: string
}