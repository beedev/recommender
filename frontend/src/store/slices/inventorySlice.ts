import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import type { Product, InventoryItem, ProductFilter } from '../../types/inventory'
import { inventoryService } from '@services/inventory/inventoryService'

interface InventoryState {
  products: Product[]
  inventory: InventoryItem[]
  selectedProduct: Product | null
  filters: ProductFilter
  searchQuery: string
  isLoading: boolean
  error: string | null
  pagination: {
    page: number
    limit: number
    total: number
    totalPages: number
  }
}

const initialState: InventoryState = {
  products: [],
  inventory: [],
  selectedProduct: null,
  filters: {
    category: null,
    brand: null,
    availability: null,
    priceRange: null,
  },
  searchQuery: '',
  isLoading: false,
  error: null,
  pagination: {
    page: 1,
    limit: 20,
    total: 0,
    totalPages: 0,
  },
}

// Async thunks
export const fetchProducts = createAsyncThunk(
  'inventory/fetchProducts',
  async (
    params: {
      page?: number
      limit?: number
      search?: string
      filters?: ProductFilter
    },
    { rejectWithValue }
  ) => {
    try {
      const response = await inventoryService.getProducts(params)
      return response
    } catch (error) {
      return rejectWithValue(error as Error)
    }
  }
)

export const fetchProductById = createAsyncThunk(
  'inventory/fetchProductById',
  async (productId: string, { rejectWithValue }) => {
    try {
      const response = await inventoryService.getProductById(productId)
      return response
    } catch (error) {
      return rejectWithValue(error as Error)
    }
  }
)

export const fetchInventory = createAsyncThunk(
  'inventory/fetchInventory',
  async (_, { rejectWithValue }) => {
    try {
      const response = await inventoryService.getInventory()
      return response
    } catch (error) {
      return rejectWithValue(error as Error)
    }
  }
)

export const updateInventoryItem = createAsyncThunk(
  'inventory/updateInventoryItem',
  async (
    { id, updates }: { id: string; updates: Partial<InventoryItem> },
    { rejectWithValue }
  ) => {
    try {
      const response = await inventoryService.updateInventoryItem(id, updates)
      return response
    } catch (error) {
      return rejectWithValue(error as Error)
    }
  }
)

export const searchProducts = createAsyncThunk(
  'inventory/searchProducts',
  async (query: string, { rejectWithValue }) => {
    try {
      const response = await inventoryService.searchProducts(query)
      return response
    } catch (error) {
      return rejectWithValue(error as Error)
    }
  }
)

const inventorySlice = createSlice({
  name: 'inventory',
  initialState,
  reducers: {
    setSelectedProduct: (state, action: PayloadAction<Product | null>) => {
      state.selectedProduct = action.payload
    },
    setFilters: (state, action: PayloadAction<ProductFilter>) => {
      state.filters = action.payload
    },
    updateFilter: (state, action: PayloadAction<Partial<ProductFilter>>) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    clearFilters: state => {
      state.filters = {
        category: null,
        brand: null,
        availability: null,
        priceRange: null,
      }
    },
    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.searchQuery = action.payload
    },
    setPagination: (state, action: PayloadAction<Partial<InventoryState['pagination']>>) => {
      state.pagination = { ...state.pagination, ...action.payload }
    },
    addProduct: (state, action: PayloadAction<Product>) => {
      const existingIndex = state.products.findIndex(p => p.id === action.payload.id)
      if (existingIndex >= 0) {
        state.products[existingIndex] = action.payload
      } else {
        state.products.unshift(action.payload)
      }
    },
    removeProduct: (state, action: PayloadAction<string>) => {
      state.products = state.products.filter(p => p.id !== action.payload)
    },
    updateProduct: (state, action: PayloadAction<{ id: string; updates: Partial<Product> }>) => {
      const product = state.products.find(p => p.id === action.payload.id)
      if (product) {
        Object.assign(product, action.payload.updates)
      }
    },
    updateInventoryItemLocal: (state, action: PayloadAction<{ id: string; updates: Partial<InventoryItem> }>) => {
      const item = state.inventory.find(i => i.id === action.payload.id)
      if (item) {
        Object.assign(item, action.payload.updates)
      }
    },
    clearError: state => {
      state.error = null
    },
  },
  extraReducers: builder => {
    builder
      // Fetch products
      .addCase(fetchProducts.pending, state => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchProducts.fulfilled, (state, action) => {
        state.isLoading = false
        state.products = action.payload.products
        state.pagination = {
          page: action.payload.page,
          limit: action.payload.limit,
          total: action.payload.total,
          totalPages: action.payload.totalPages,
        }
      })
      .addCase(fetchProducts.rejected, (state, action) => {
        state.isLoading = false
        state.error = (action.payload as Error).message
      })
      // Fetch product by ID
      .addCase(fetchProductById.pending, state => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchProductById.fulfilled, (state, action) => {
        state.isLoading = false
        state.selectedProduct = action.payload
        // Also update in products array if it exists
        const existingIndex = state.products.findIndex(p => p.id === action.payload.id)
        if (existingIndex >= 0) {
          state.products[existingIndex] = action.payload
        }
      })
      .addCase(fetchProductById.rejected, (state, action) => {
        state.isLoading = false
        state.error = (action.payload as Error).message
      })
      // Fetch inventory
      .addCase(fetchInventory.pending, state => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchInventory.fulfilled, (state, action) => {
        state.isLoading = false
        state.inventory = action.payload
      })
      .addCase(fetchInventory.rejected, (state, action) => {
        state.isLoading = false
        state.error = (action.payload as Error).message
      })
      // Update inventory item
      .addCase(updateInventoryItem.fulfilled, (state, action) => {
        const index = state.inventory.findIndex(item => item.id === action.payload.id)
        if (index >= 0) {
          state.inventory[index] = action.payload
        }
      })
      .addCase(updateInventoryItem.rejected, (state, action) => {
        state.error = (action.payload as Error).message
      })
      // Search products
      .addCase(searchProducts.pending, state => {
        state.isLoading = true
        state.error = null
      })
      .addCase(searchProducts.fulfilled, (state, action) => {
        state.isLoading = false
        state.products = action.payload.products
      })
      .addCase(searchProducts.rejected, (state, action) => {
        state.isLoading = false
        state.error = (action.payload as Error).message
      })
  },
})

export const {
  setSelectedProduct,
  setFilters,
  updateFilter,
  clearFilters,
  setSearchQuery,
  setPagination,
  addProduct,
  removeProduct,
  updateProduct,
  updateInventoryItemLocal,
  clearError,
} = inventorySlice.actions

export const { actions } = inventorySlice
export default inventorySlice.reducer