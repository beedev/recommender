import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Search, Package, AlertTriangle, TrendingUp, TrendingDown } from 'lucide-react'
import Button from '@components/common/Button'

const InventoryPage: React.FC = () => {
  const { t } = useTranslation(['inventory', 'common'])
  const [searchQuery, setSearchQuery] = useState('')
  const [activeFilter, setActiveFilter] = useState('all')

  const mockInventory = [
    { id: '1', name: 'MIG Welder 200A', category: 'Welders', stock: 45, status: 'in_stock', price: 1299.99 },
    { id: '2', name: 'Welding Helmet Auto-Dark', category: 'Safety', stock: 12, status: 'low_stock', price: 199.99 },
    { id: '3', name: 'Electrode E7018', category: 'Consumables', stock: 0, status: 'out_of_stock', price: 89.99 },
    { id: '4', name: 'TIG Tungsten 2.4mm', category: 'Consumables', stock: 156, status: 'in_stock', price: 45.99 },
    { id: '5', name: 'Plasma Cutter 40A', category: 'Cutters', stock: 8, status: 'low_stock', price: 899.99 },
  ]

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'in_stock': return 'text-success-500'
      case 'low_stock': return 'text-warning-500'
      case 'out_of_stock': return 'text-error-500'
      default: return 'text-neutral-500'
    }
  }

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'in_stock': return 'bg-success-100 text-success-800'
      case 'low_stock': return 'bg-warning-100 text-warning-800'
      case 'out_of_stock': return 'bg-error-100 text-error-800'
      default: return 'bg-neutral-100 text-neutral-800'
    }
  }

  const filteredInventory = mockInventory.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesFilter = activeFilter === 'all' || item.status === activeFilter
    return matchesSearch && matchesFilter
  })

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">{t('inventory:title')}</h1>
          <p className="text-white text-opacity-70 mt-1">Manage your welding equipment inventory</p>
        </div>
        <Button variant="primary">
          Add Product
        </Button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white bg-opacity-10 backdrop-blur-sm rounded-lg p-4 border border-white border-opacity-20">
          <div className="flex items-center gap-3">
            <Package className="w-8 h-8 text-sparky-gold" />
            <div>
              <p className="text-white text-opacity-70 text-sm">Total Items</p>
              <p className="text-xl font-bold text-white">1,234</p>
            </div>
          </div>
        </div>

        <div className="bg-white bg-opacity-10 backdrop-blur-sm rounded-lg p-4 border border-white border-opacity-20">
          <div className="flex items-center gap-3">
            <TrendingUp className="w-8 h-8 text-success-500" />
            <div>
              <p className="text-white text-opacity-70 text-sm">In Stock</p>
              <p className="text-xl font-bold text-white">987</p>
            </div>
          </div>
        </div>

        <div className="bg-white bg-opacity-10 backdrop-blur-sm rounded-lg p-4 border border-white border-opacity-20">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-8 h-8 text-warning-500" />
            <div>
              <p className="text-white text-opacity-70 text-sm">Low Stock</p>
              <p className="text-xl font-bold text-white">23</p>
            </div>
          </div>
        </div>

        <div className="bg-white bg-opacity-10 backdrop-blur-sm rounded-lg p-4 border border-white border-opacity-20">
          <div className="flex items-center gap-3">
            <TrendingDown className="w-8 h-8 text-error-500" />
            <div>
              <p className="text-white text-opacity-70 text-sm">Out of Stock</p>
              <p className="text-xl font-bold text-white">12</p>
            </div>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white bg-opacity-10 backdrop-blur-sm rounded-lg p-6 border border-white border-opacity-20">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-white text-opacity-60" />
              <input
                type="text"
                placeholder={t('inventory:products.search_placeholder')}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-white bg-opacity-10 text-white placeholder-white placeholder-opacity-60 rounded-lg border border-white border-opacity-20 focus:outline-none focus:ring-2 focus:ring-sparky-gold focus:border-transparent"
              />
            </div>
          </div>

          <div className="flex gap-2">
            {[
              { key: 'all', label: 'All' },
              { key: 'in_stock', label: 'In Stock' },
              { key: 'low_stock', label: 'Low Stock' },
              { key: 'out_of_stock', label: 'Out of Stock' },
            ].map(filter => (
              <button
                key={filter.key}
                onClick={() => setActiveFilter(filter.key)}
                className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
                  activeFilter === filter.key
                    ? 'bg-sparky-gold text-black font-medium'
                    : 'bg-white bg-opacity-10 text-white hover:bg-white hover:bg-opacity-20'
                }`}
              >
                {filter.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Inventory Table */}
      <div className="bg-white bg-opacity-10 backdrop-blur-sm rounded-lg border border-white border-opacity-20 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-white bg-opacity-5">
              <tr>
                <th className="text-left px-6 py-4 text-white text-sm font-medium">Product</th>
                <th className="text-left px-6 py-4 text-white text-sm font-medium">Category</th>
                <th className="text-left px-6 py-4 text-white text-sm font-medium">Stock</th>
                <th className="text-left px-6 py-4 text-white text-sm font-medium">Status</th>
                <th className="text-left px-6 py-4 text-white text-sm font-medium">Price</th>
                <th className="text-left px-6 py-4 text-white text-sm font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white divide-opacity-10">
              {filteredInventory.map((item) => (
                <tr key={item.id} className="hover:bg-white hover:bg-opacity-5 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-sparky-gold bg-opacity-20 rounded-lg flex items-center justify-center">
                        <Package className="w-5 h-5 text-sparky-gold" />
                      </div>
                      <div>
                        <p className="text-white font-medium">{item.name}</p>
                        <p className="text-white text-opacity-60 text-sm">ID: {item.id}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-white text-opacity-80">{item.category}</td>
                  <td className="px-6 py-4">
                    <span className={`font-medium ${getStatusColor(item.status)}`}>
                      {item.stock}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBg(item.status)}`}>
                      {t(`inventory:products.${item.status}`)}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-white font-medium">
                    ${item.price.toFixed(2)}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <Button variant="ghost" size="sm">
                        Edit
                      </Button>
                      <Button variant="ghost" size="sm">
                        View
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredInventory.length === 0 && (
          <div className="p-12 text-center">
            <Package className="w-12 h-12 text-white text-opacity-30 mx-auto mb-4" />
            <p className="text-white text-opacity-60">{t('common:no_results')}</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default InventoryPage