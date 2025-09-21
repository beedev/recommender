import React from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Home, ArrowLeft } from 'lucide-react'
import Button from '@components/common/Button'

const NotFoundPage: React.FC = () => {
  const { t } = useTranslation('common')

  return (
    <div className="min-h-screen bg-gradient-esab flex items-center justify-center p-4">
      <div className="text-center">
        <div className="mb-8">
          <h1 className="text-9xl font-bold text-white text-opacity-20 mb-4">404</h1>
          <h2 className="text-3xl font-bold text-white mb-2">
            {t('not_found')}
          </h2>
          <p className="text-white text-opacity-70 text-lg max-w-md mx-auto">
            The page you're looking for doesn't exist or has been moved.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link to="/">
            <Button
              variant="primary"
              leftIcon={<Home className="w-4 h-4" />}
            >
              {t('go_back')} {t('home')}
            </Button>
          </Link>
          
          <Button
            onClick={() => window.history.back()}
            variant="outline"
            leftIcon={<ArrowLeft className="w-4 h-4" />}
          >
            {t('back')}
          </Button>
        </div>

        <div className="mt-12 text-white text-opacity-50 text-sm">
          <p>Lost? Try asking Sparky AI for help!</p>
        </div>
      </div>
    </div>
  )
}

export default NotFoundPage