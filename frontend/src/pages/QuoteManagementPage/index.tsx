import React, { useState, useEffect } from 'react'
// import { useTranslation } from 'react-i18next'
import { 
  Plus, 
  Search, 
  X
} from 'lucide-react'

interface QuoteComponent {
  name: string
  description: string
  price: number
}

interface Quote {
  id: string
  customer: string
  customerEmail: string
  status: 'pending' | 'approved' | 'rejected'
  total: number
  date: string
  package: string
  components: QuoteComponent[]
}

const QuoteManagementPage: React.FC = () => {
  // const { t } = useTranslation(['common']) // Commented out until used
  const [quotes, setQuotes] = useState<Quote[]>([])
  const [filteredQuotes, setFilteredQuotes] = useState<Quote[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [selectedQuote, setSelectedQuote] = useState<Quote | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  // Mock quote data - in real app this would come from API
  useEffect(() => {
    const mockQuotes: Quote[] = [
      {
        id: 'Q-2024-0156',
        customer: 'Jane Chapman',
        customerEmail: 'jane.chapman@email.com',
        status: 'pending',
        total: 11378.92,
        date: '2024-01-15',
        package: 'Sparky\'s Choice - MIG/MMA Setup',
        components: [
          { name: 'Wire Feeder', description: 'Standard Wire Feeder', price: 2850.00 },
          { name: 'Connection Cable', description: '3m Cable Set', price: 145.00 },
          { name: 'Cooling Unit', description: 'Standard Cooling Unit', price: 1890.00 },
          { name: 'Power Source', description: 'Multipurpose MIG/MMA Welder 400A', price: 4500.00 },
          { name: 'Torches', description: 'Standard MIG Torch', price: 475.00 },
          { name: 'Trolley', description: 'Standard Trolley', price: 320.00 },
          { name: 'Accessories', description: 'Basic Accessory Kit', price: 285.00 },
          { name: 'Wear Parts', description: 'Standard Wear Parts Kit', price: 284.92 },
          { name: 'Ground Cable', description: 'Heavy Duty Ground Cable 5m', price: 89.00 },
          { name: 'Gas Regulator', description: 'Precision Gas Flow Regulator', price: 195.00 },
          { name: 'Wire Spool', description: 'ER70S-6 Wire 1.2mm 15kg', price: 125.00 },
          { name: 'Safety Equipment', description: 'Professional Welding Helmet & Gloves', price: 220.00 }
        ]
      },
      {
        id: 'Q-2024-0155',
        customer: 'Mike Johnson',
        customerEmail: 'mike.johnson@company.com',
        status: 'approved',
        total: 8765.50,
        date: '2024-01-14',
        package: 'Professional MIG Package',
        components: [
          { name: 'MIG Welder', description: 'Professional 300A MIG Welder', price: 3500.00 },
          { name: 'Wire Feeder', description: '4-Roll Professional Feeder', price: 1200.00 },
          { name: 'Torch Kit', description: 'Professional MIG Torch Kit', price: 800.00 },
          { name: 'Consumables', description: 'Complete Consumables Package', price: 665.50 },
          { name: 'Cart', description: 'Heavy Duty Welding Cart', price: 450.00 },
          { name: 'Gas Kit', description: 'Complete Gas Setup Kit', price: 350.00 },
          { name: 'Safety Package', description: 'Professional Safety Equipment', price: 280.00 },
          { name: 'Training Manual', description: 'Comprehensive Training Guide', price: 520.00 }
        ]
      },
      {
        id: 'Q-2024-0154',
        customer: 'Sarah Wilson',
        customerEmail: 'sarah.wilson@fabrication.com',
        status: 'rejected',
        total: 15240.00,
        date: '2024-01-13',
        package: 'Industrial TIG Setup',
        components: [
          { name: 'TIG Welder', description: 'Industrial 500A TIG Welder', price: 8500.00 },
          { name: 'Cooling System', description: 'Industrial Water Cooler', price: 2800.00 },
          { name: 'TIG Torch', description: 'Air-Cooled TIG Torch 350A', price: 1200.00 },
          { name: 'Tungsten Set', description: 'Complete Tungsten Electrode Set', price: 340.00 },
          { name: 'Filler Rods', description: 'Assorted TIG Filler Rods', price: 800.00 },
          { name: 'Gas Lens Kit', description: 'High-Performance Gas Lens Kit', price: 600.00 },
          { name: 'Foot Control', description: 'Wireless Foot Control', price: 450.00 },
          { name: 'Accessories', description: 'Complete TIG Accessory Package', price: 550.00 }
        ]
      }
    ]
    setQuotes(mockQuotes)
    setFilteredQuotes(mockQuotes)
  }, [])

  const handleSearch = () => {
    let filtered = quotes.filter(quote => {
      const matchesSearch = !searchTerm || 
        quote.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        quote.customer.toLowerCase().includes(searchTerm.toLowerCase()) ||
        quote.package.toLowerCase().includes(searchTerm.toLowerCase())
      
      const matchesStatus = !statusFilter || quote.status === statusFilter
      const matchesDate = !dateFrom || quote.date >= dateFrom
      
      return matchesSearch && matchesStatus && matchesDate
    })
    setFilteredQuotes(filtered)
  }

  const getStatusBadgeClass = (status: Quote['status']) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      case 'approved':
        return 'bg-green-100 text-green-800'
      case 'rejected':
        return 'bg-red-100 text-red-800'
    }
  }

  const openQuoteDetail = (quote: Quote) => {
    setSelectedQuote(quote)
    setIsModalOpen(true)
  }

  const closeModal = () => {
    setSelectedQuote(null)
    setIsModalOpen(false)
  }

  return (
    <div className="p-8 min-h-screen bg-gradient-to-br from-amber-900 via-orange-700 to-yellow-600">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-white text-4xl font-bold">Quote Management</h1>
        <button className="bg-yellow-400 text-black px-6 py-3 rounded-lg font-bold hover:bg-yellow-500 transition-colors flex items-center gap-2">
          <Plus className="h-5 w-5" />
          New Quote
        </button>
      </div>
      
      {/* Search and Filters */}
      <div className="bg-white bg-opacity-95 rounded-xl p-6 border-2 border-yellow-400 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Search Quotes</label>
            <div className="relative">
              <input 
                type="text" 
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Quote ID, Customer, or Package..."
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
              />
              <Search className="absolute right-3 top-3 h-5 w-5 text-gray-400" />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
            <select 
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500"
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Date From</label>
            <input 
              type="date" 
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-yellow-500"
            />
          </div>
          
          <div className="flex items-end">
            <button 
              onClick={handleSearch}
              className="w-full bg-yellow-400 text-black px-4 py-3 rounded-lg font-bold hover:bg-yellow-500 transition-colors"
            >
              Search
            </button>
          </div>
        </div>
        
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <span>Total Quotes: <strong>{filteredQuotes.length}</strong></span>
          <span>•</span>
          <span>Pending: <strong>{filteredQuotes.filter(q => q.status === 'pending').length}</strong></span>
          <span>•</span>
          <span>This Month: <strong>{filteredQuotes.filter(q => q.date.startsWith(new Date().toISOString().slice(0, 7))).length}</strong></span>
        </div>
      </div>
      
      {/* Quotes List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {filteredQuotes.map((quote) => (
          <div 
            key={quote.id}
            onClick={() => openQuoteDetail(quote)}
            className="bg-white bg-opacity-95 rounded-xl p-6 border border-yellow-400 hover:shadow-lg hover:-translate-y-1 transition-all cursor-pointer"
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="font-bold text-lg text-gray-900">{quote.id}</h3>
                <p className="text-sm text-gray-600">{quote.customer}</p>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-semibold uppercase ${getStatusBadgeClass(quote.status)}`}>
                {quote.status}
              </span>
            </div>
            
            <div className="mb-4">
              <p className="font-medium text-gray-800">{quote.package}</p>
              <p className="text-sm text-gray-600">{quote.date}</p>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold text-gray-900">${quote.total.toLocaleString()}</span>
              <span className="text-yellow-600 hover:text-yellow-700 font-medium">
                View Details →
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Quote Detail Modal */}
      {isModalOpen && selectedQuote && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-8 max-w-4xl max-h-[90vh] overflow-y-auto w-full">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold">Quote {selectedQuote.id}</h2>
              <button onClick={closeModal} className="text-gray-500 hover:text-gray-700">
                <X className="h-6 w-6" />
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div>
                <h3 className="font-bold text-lg mb-3">Customer Information</h3>
                <div className="space-y-2">
                  <p><strong>Name:</strong> {selectedQuote.customer}</p>
                  <p><strong>Email:</strong> {selectedQuote.customerEmail}</p>
                  <p><strong>Date:</strong> {selectedQuote.date}</p>
                  <p><strong>Status:</strong> 
                    <span className={`ml-2 px-3 py-1 rounded-full text-xs font-semibold uppercase ${getStatusBadgeClass(selectedQuote.status)}`}>
                      {selectedQuote.status}
                    </span>
                  </p>
                </div>
              </div>
              
              <div>
                <h3 className="font-bold text-lg mb-3">Package Summary</h3>
                <div className="space-y-2">
                  <p><strong>Package:</strong> {selectedQuote.package}</p>
                  <p><strong>Components:</strong> {selectedQuote.components.length} items</p>
                  <p><strong>Total Value:</strong> 
                    <span className="text-2xl font-bold text-green-600 ml-2">
                      ${selectedQuote.total.toLocaleString()}
                    </span>
                  </p>
                </div>
              </div>
            </div>
            
            <div className="mb-6">
              <h3 className="font-bold text-lg mb-3">Package Components</h3>
              <div className="overflow-x-auto">
                <table className="w-full border-collapse border border-gray-300 rounded-lg">
                  <thead>
                    <tr className="bg-gray-50">
                      <th className="border border-gray-300 px-4 py-3 text-left font-semibold">Component</th>
                      <th className="border border-gray-300 px-4 py-3 text-left font-semibold">Description</th>
                      <th className="border border-gray-300 px-4 py-3 text-right font-semibold">Price</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedQuote.components.map((component, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="border border-gray-300 px-4 py-3 font-medium">{component.name}</td>
                        <td className="border border-gray-300 px-4 py-3">{component.description}</td>
                        <td className="border border-gray-300 px-4 py-3 text-right font-medium">
                          ${component.price.toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="bg-gray-100 font-bold">
                      <td className="border border-gray-300 px-4 py-3" colSpan={2}>Total</td>
                      <td className="border border-gray-300 px-4 py-3 text-right text-lg">
                        ${selectedQuote.total.toLocaleString()}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
            
            <div className="flex gap-4 justify-end">
              <button 
                onClick={closeModal}
                className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Close
              </button>
              <button className="px-6 py-3 bg-yellow-400 text-black rounded-lg font-medium hover:bg-yellow-500 transition-colors">
                Edit Quote
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default QuoteManagementPage