import React from 'react'
import { useLocation } from 'react-router-dom'
import Sidebar from '../Sidebar'
import Header from '../Header'
import MobileNav from '../MobileNav'

interface LayoutProps {
  children: React.ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation()

  // Check if we're on a full-screen route (like login)
  const isAuthRoute = location.pathname.startsWith('/auth') || 
                     location.pathname === '/login' || 
                     location.pathname === '/register'

  if (isAuthRoute) {
    return (
      <div className="min-h-screen bg-gradient-esab">
        {children}
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-esab">
      {/* Mobile Navigation */}
      <MobileNav />
      
      {/* Top Header */}
      <Header />
      
      <div className="flex" style={{ height: 'calc(100vh - 80px)' }}>
        {/* Desktop Sidebar Navigation */}
        <div className="hidden lg:block">
          <Sidebar />
        </div>
        
        {/* Main Content Area */}
        <main className="main-content flex-1 overflow-y-auto">
          <div className="h-full">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}

export default Layout