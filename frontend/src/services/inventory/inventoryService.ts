import { api } from '@services/api/client'
import { API_ENDPOINTS, buildUrl } from '@services/api/endpoints'
import type { 
  Product, 
  InventoryItem, 
  ProductFilter, 
  ProductSearchResult,
  InventoryMovement,
  StockAlert 
} from '../../types/inventory'

interface GetProductsParams {
  page?: number
  limit?: number
  search?: string
  filters?: ProductFilter
}

interface InventoryResponse {
  items: InventoryItem[]
  total: number
  page: number
  limit: number
  totalPages: number
}

class InventoryService {
  /**
   * Get products with pagination and filtering
   */
  async getProducts(params: GetProductsParams = {}): Promise<ProductSearchResult> {
    const queryParams = {
      page: params.page || 1,
      limit: params.limit || 20,
      search: params.search || '',
      category: params.filters?.category || undefined,
      brand: params.filters?.brand || undefined,
      availability: params.filters?.availability || undefined,
      min_price: params.filters?.priceRange?.min || undefined,
      max_price: params.filters?.priceRange?.max || undefined,
    }

    const url = buildUrl(API_ENDPOINTS.PRODUCTS.LIST, queryParams)
    const response = await api.get<ProductSearchResult>(url)
    return response
  }

  /**
   * Get single product by ID
   */
  async getProductById(productId: string): Promise<Product> {
    const response = await api.get<Product>(API_ENDPOINTS.PRODUCTS.DETAIL(productId))
    return response
  }

  /**
   * Search products by query
   */
  async searchProducts(query: string, limit = 20): Promise<ProductSearchResult> {
    const url = buildUrl(API_ENDPOINTS.PRODUCTS.SEARCH, { q: query, limit })
    const response = await api.get<ProductSearchResult>(url)
    return response
  }

  /**
   * Get product categories
   */
  async getCategories(): Promise<Array<{ name: string; count: number }>> {
    const response = await api.get<Array<{ name: string; count: number }>>(
      API_ENDPOINTS.PRODUCTS.CATEGORIES
    )
    return response
  }

  /**
   * Get product brands
   */
  async getBrands(): Promise<Array<{ name: string; count: number }>> {
    const response = await api.get<Array<{ name: string; count: number }>>(
      API_ENDPOINTS.PRODUCTS.BRANDS
    )
    return response
  }

  /**
   * Get inventory items
   */
  async getInventory(params: { page?: number; limit?: number } = {}): Promise<InventoryItem[]> {
    const queryParams = {
      page: params.page || 1,
      limit: params.limit || 50,
    }

    const url = buildUrl(API_ENDPOINTS.INVENTORY.LIST, queryParams)
    const response = await api.get<InventoryResponse>(url)
    return response.items
  }

  /**
   * Get inventory item by ID
   */
  async getInventoryItemById(itemId: string): Promise<InventoryItem> {
    const response = await api.get<InventoryItem>(API_ENDPOINTS.INVENTORY.DETAIL(itemId))
    return response
  }

  /**
   * Update inventory item
   */
  async updateInventoryItem(itemId: string, updates: Partial<InventoryItem>): Promise<InventoryItem> {
    const response = await api.put<InventoryItem>(
      API_ENDPOINTS.INVENTORY.UPDATE(itemId),
      updates
    )
    return response
  }

  /**
   * Create new inventory item
   */
  async createInventoryItem(item: Omit<InventoryItem, 'id' | 'lastUpdated' | 'updatedBy'>): Promise<InventoryItem> {
    const response = await api.post<InventoryItem>(API_ENDPOINTS.INVENTORY.CREATE, item)
    return response
  }

  /**
   * Delete inventory item
   */
  async deleteInventoryItem(itemId: string): Promise<void> {
    await api.delete(API_ENDPOINTS.INVENTORY.DELETE(itemId))
  }

  /**
   * Get stock levels summary
   */
  async getStockLevels(): Promise<{
    total: number
    inStock: number
    lowStock: number
    outOfStock: number
    categories: Record<string, number>
  }> {
    const response = await api.get(API_ENDPOINTS.INVENTORY.STOCK_LEVELS)
    return response
  }

  /**
   * Get low stock items
   */
  async getLowStockItems(): Promise<InventoryItem[]> {
    const response = await api.get<{ items: InventoryItem[] }>(API_ENDPOINTS.INVENTORY.LOW_STOCK)
    return response.items
  }

  /**
   * Get inventory movements
   */
  async getMovements(params: {
    productId?: string
    type?: string
    page?: number
    limit?: number
    startDate?: string
    endDate?: string
  } = {}): Promise<{
    movements: InventoryMovement[]
    total: number
    page: number
    totalPages: number
  }> {
    const url = buildUrl(API_ENDPOINTS.INVENTORY.MOVEMENTS, params)
    const response = await api.get(url)
    return response
  }

  /**
   * Record inventory movement
   */
  async recordMovement(movement: Omit<InventoryMovement, 'id' | 'timestamp' | 'performedBy'>): Promise<InventoryMovement> {
    const response = await api.post<InventoryMovement>(API_ENDPOINTS.INVENTORY.MOVEMENTS, movement)
    return response
  }

  /**
   * Bulk update inventory items
   */
  async bulkUpdateItems(updates: Array<{
    id: string
    updates: Partial<InventoryItem>
  }>): Promise<InventoryItem[]> {
    const response = await api.post<InventoryItem[]>(
      API_ENDPOINTS.INVENTORY.BULK_UPDATE,
      { updates }
    )
    return response
  }

  /**
   * Get stock alerts
   */
  async getStockAlerts(): Promise<StockAlert[]> {
    const response = await api.get<StockAlert[]>(API_ENDPOINTS.DASHBOARD.ALERTS)
    return response
  }

  /**
   * Resolve stock alert
   */
  async resolveAlert(alertId: string): Promise<void> {
    await api.post(`/alerts/${alertId}/resolve`)
  }

  /**
   * Get product recommendations based on current inventory
   */
  async getProductRecommendations(productId: string): Promise<Product[]> {
    const response = await api.get<Product[]>(API_ENDPOINTS.PRODUCTS.RECOMMENDATIONS(productId))
    return response
  }

  /**
   * Compare multiple products
   */
  async compareProducts(productIds: string[]): Promise<{
    products: Product[]
    comparisonMatrix: Record<string, Record<string, any>>
    recommendations: { best: string; reasons: string[] }
  }> {
    const response = await api.post(API_ENDPOINTS.PRODUCTS.COMPARE, { productIds })
    return response
  }
}

export const inventoryService = new InventoryService()
export default inventoryService