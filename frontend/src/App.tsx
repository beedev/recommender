import React, { Suspense, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
// Helmet will be added later - commenting out for initial setup
// import { Helmet } from 'react-helmet-async'
import { useAppDispatch, useAppSelector } from '@hooks/redux'
import { initializeApp } from '@store/slices/uiSlice'
import Layout from '@components/layout/Layout'
import LoadingSpinner from '@components/common/LoadingSpinner'
import ErrorBoundary from '@components/common/ErrorBoundary'
import Toast from '@components/common/Toast'
import Modal from '@components/common/Modal'

// Lazy load pages for better performance
const SparkyPage = React.lazy(() => import('@pages/SparkyPage'))
const SystemDashboardPage = React.lazy(() => import('@pages/SystemDashboardPage'))
const QuoteManagementPage = React.lazy(() => import('@pages/QuoteManagementPage'))
const NotFoundPage = React.lazy(() => import('@pages/NotFoundPage'))

// Loading fallback component
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-screen">
    <LoadingSpinner size="lg" />
  </div>
)

const App: React.FC = () => {
  const { t, ready } = useTranslation()
  const dispatch = useAppDispatch()
  const { isLoading, error } = useAppSelector(state => state.ui)

  useEffect(() => {
    dispatch(initializeApp())
  }, [dispatch])

  // Show loading screen during i18n initialization
  if (!ready) {
    return <PageLoader />
  }

  return (
    <ErrorBoundary>
      {/* Helmet will be added later
      <Helmet
        defaultTitle="ESAB Welding Management System"
        titleTemplate="%s | ESAB"
      >
        <html lang={ready ? t('common.locale') : 'en'} />
        <meta name="description" content={t('app.description')} />
      </Helmet>
      */}

      <div className="App min-h-screen bg-gradient-esab">
        <Layout>
          <Suspense fallback={<PageLoader />}>
            <Routes>
              {/* Default redirect to Sparky */}
              <Route path="/" element={<Navigate to="/sparky" replace />} />
              
              {/* Main application pages */}
              <Route path="/sparky" element={<SparkyPage />} />
              <Route path="/dashboard" element={<SystemDashboardPage />} />
              <Route path="/quotes" element={<QuoteManagementPage />} />
              
              {/* 404 page */}
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </Suspense>
        </Layout>

        {/* Global components */}
        <Toast />
        <Modal />
        
        {/* Loading overlay for global operations */}
        {isLoading && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 flex items-center gap-3">
              <LoadingSpinner />
              <span className="text-neutral-700">{t('loading')}</span>
            </div>
          </div>
        )}
        
        {/* Global error display */}
        {error && (
          <div className="fixed bottom-4 right-4 bg-error-500 text-white p-4 rounded-lg shadow-lg max-w-md">
            <p className="font-medium">{t('common.error')}</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
        )}
      </div>
    </ErrorBoundary>
  )
}

export default App