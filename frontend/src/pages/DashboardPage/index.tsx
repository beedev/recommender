import React from 'react'
import { useTranslation } from 'react-i18next'
import { BarChart3, TrendingUp, Package, Users, AlertTriangle } from 'lucide-react'

const DashboardPage: React.FC = () => {
  const { t } = useTranslation(['navigation', 'common'])

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">{t('dashboard')}</h1>
          <p className="text-white text-opacity-70 mt-1">Welcome to your ESAB dashboard</p>
        </div>
        <div className="text-white text-opacity-60 text-sm">
          {new Date().toLocaleDateString()}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white bg-opacity-10 backdrop-blur-sm rounded-lg p-6 border border-white border-opacity-20">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white text-opacity-70 text-sm">Total Products</p>
              <p className="text-2xl font-bold text-white">1,234</p>
              <p className="text-success-400 text-sm flex items-center gap-1">
                <TrendingUp className="w-4 h-4" />
                +12% from last month
              </p>
            </div>
            <div className="p-3 bg-sparky-gold bg-opacity-20 rounded-full">
              <Package className="w-6 h-6 text-sparky-gold" />
            </div>
          </div>
        </div>

        <div className="bg-white bg-opacity-10 backdrop-blur-sm rounded-lg p-6 border border-white border-opacity-20">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white text-opacity-70 text-sm">Active Users</p>
              <p className="text-2xl font-bold text-white">567</p>
              <p className="text-success-400 text-sm flex items-center gap-1">
                <TrendingUp className="w-4 h-4" />
                +8% from last month
              </p>
            </div>
            <div className="p-3 bg-sparky-gold bg-opacity-20 rounded-full">
              <Users className="w-6 h-6 text-sparky-gold" />
            </div>
          </div>
        </div>

        <div className="bg-white bg-opacity-10 backdrop-blur-sm rounded-lg p-6 border border-white border-opacity-20">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white text-opacity-70 text-sm">Sparky Interactions</p>
              <p className="text-2xl font-bold text-white">2,890</p>
              <p className="text-success-400 text-sm flex items-center gap-1">
                <TrendingUp className="w-4 h-4" />
                +25% from last month
              </p>
            </div>
            <div className="p-3 bg-sparky-gold bg-opacity-20 rounded-full">
              <BarChart3 className="w-6 h-6 text-sparky-gold" />
            </div>
          </div>
        </div>

        <div className="bg-white bg-opacity-10 backdrop-blur-sm rounded-lg p-6 border border-white border-opacity-20">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white text-opacity-70 text-sm">Low Stock Alerts</p>
              <p className="text-2xl font-bold text-white">23</p>
              <p className="text-warning-400 text-sm flex items-center gap-1">
                <AlertTriangle className="w-4 h-4" />
                Requires attention
              </p>
            </div>
            <div className="p-3 bg-warning-500 bg-opacity-20 rounded-full">
              <AlertTriangle className="w-6 h-6 text-warning-500" />
            </div>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white bg-opacity-10 backdrop-blur-sm rounded-lg p-6 border border-white border-opacity-20">
          <h2 className="text-xl font-semibold text-white mb-4">Sales Overview</h2>
          <div className="h-64 flex items-center justify-center text-white text-opacity-60">
            Chart placeholder - Connect to backend analytics
          </div>
        </div>

        <div className="bg-white bg-opacity-10 backdrop-blur-sm rounded-lg p-6 border border-white border-opacity-20">
          <h2 className="text-xl font-semibold text-white mb-4">Inventory Status</h2>
          <div className="h-64 flex items-center justify-center text-white text-opacity-60">
            Chart placeholder - Connect to inventory data
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white bg-opacity-10 backdrop-blur-sm rounded-lg p-6 border border-white border-opacity-20">
        <h2 className="text-xl font-semibold text-white mb-4">Recent Activity</h2>
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((item) => (
            <div key={item} className="flex items-center gap-3 p-3 bg-white bg-opacity-5 rounded-lg">
              <div className="w-2 h-2 bg-sparky-gold rounded-full"></div>
              <div className="flex-1">
                <p className="text-white text-sm">Sample activity {item}</p>
                <p className="text-white text-opacity-60 text-xs">{item} minutes ago</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default DashboardPage