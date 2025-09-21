# ESAB Welding Management System - Frontend

Modern React TypeScript frontend application with AI-powered features and comprehensive welding equipment management.

## 🚀 Quick Start

### Prerequisites
- Node.js >= 18.0.0
- npm >= 9.0.0
- Backend API running on http://localhost:3000

### Installation & Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Environment configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

4. **Access the application**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:3000

## 🏗️ Architecture

### Tech Stack
- **Framework**: React 18 + TypeScript
- **State Management**: Redux Toolkit
- **Routing**: React Router v6
- **Styling**: Tailwind CSS + SCSS
- **Animations**: Framer Motion
- **Build Tool**: Vite
- **Testing**: Vitest + Testing Library
- **Internationalization**: i18next

### Project Structure
```
src/
├── components/          # Reusable UI components
│   ├── common/         # Generic components (Button, Modal, etc.)
│   └── layout/         # Layout components (Header, Sidebar)
├── pages/              # Page components
│   ├── SparkyPage/     # Main Sparky AI chat interface
│   ├── DashboardPage/  # Analytics dashboard
│   ├── InventoryPage/  # Product inventory management
│   └── SettingsPage/   # User settings
├── services/           # API integration layer
│   ├── api/           # HTTP client and endpoints
│   ├── auth/          # Authentication service
│   ├── sparky/        # Sparky AI service
│   └── inventory/     # Inventory service
├── store/             # Redux store and slices
│   └── slices/        # Feature-based state slices
├── types/             # TypeScript type definitions
├── hooks/             # Custom React hooks
├── locales/           # Internationalization files
└── styles/            # Global styles and themes
```

## 🎨 Features

### Core Features
- **Sparky AI Chat**: Intelligent welding assistant with personality customization
- **Real-time Communication**: WebSocket support for live updates
- **Responsive Design**: Mobile-first, adaptive UI
- **Dark/Light Theme**: System-aware theme switching
- **Multi-language**: English and Spanish support
- **Accessibility**: WCAG 2.1 AA compliance

### Business Features
- **Inventory Management**: Product catalog with search and filtering
- **Dashboard Analytics**: Real-time metrics and insights
- **User Management**: Profile settings and preferences
- **Notification System**: Toast notifications and alerts

### Technical Features
- **Type Safety**: Full TypeScript coverage
- **Performance**: Code splitting and lazy loading
- **Error Handling**: Comprehensive error boundaries
- **Testing**: Unit and integration tests
- **PWA Ready**: Service worker and offline support

## 🛠️ Development

### Available Scripts
```bash
npm run dev          # Start development server
npm run build        # Production build
npm run preview      # Preview production build
npm run test         # Run tests
npm run test:ui      # Run tests with UI
npm run test:coverage # Generate coverage report
npm run lint         # Lint code
npm run lint:fix     # Fix linting issues
npm run type-check   # TypeScript type checking
npm run format       # Format code with Prettier
```

### Development Workflow
1. **Feature Development**:
   - Create feature branch from `main`
   - Implement component with TypeScript
   - Add tests for critical functionality
   - Update translations if needed

2. **Code Quality**:
   - All code must pass TypeScript checks
   - ESLint rules must be followed
   - Components should be accessible
   - Add proper error handling

3. **Testing Strategy**:
   - Unit tests for utilities and hooks
   - Component tests for UI behavior
   - Integration tests for user flows
   - E2E tests for critical paths

## 🎯 Customization

### Theme Customization
- Edit `tailwind.config.js` for design tokens
- Modify `src/styles/globals.scss` for custom CSS
- Update ESAB brand colors in CSS variables

### Adding New Features
1. Create feature slice in `src/store/slices/`
2. Add service functions in `src/services/`
3. Create page component in `src/pages/`
4. Add route in `src/App.tsx`
5. Update navigation in `src/components/layout/Sidebar/`

### Internationalization
- Add new languages in `src/locales/i18n.ts`
- Create translation files in `src/locales/{lang}/`
- Use `useTranslation` hook in components

## 🔧 Configuration

### Environment Variables
```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:3000

# Feature Flags
VITE_ENABLE_SPARKY_AI=true
VITE_ENABLE_VOICE_INPUT=false
VITE_ENABLE_PWA=true

# Analytics (optional)
VITE_GOOGLE_ANALYTICS_ID=
VITE_SENTRY_DSN=
```

### API Integration
- Backend endpoints configured in `src/services/api/endpoints.ts`
- HTTP client with interceptors in `src/services/api/client.ts`
- Automatic token refresh and error handling

## 📱 Mobile Support

### Responsive Design
- Mobile-first approach with Tailwind CSS
- Touch-friendly interface elements
- Optimized for tablets and phones
- Progressive Web App features

### Performance
- Bundle splitting for optimal loading
- Image optimization and lazy loading
- Service worker for caching
- Core Web Vitals optimization

## 🚀 Deployment

### Production Build
```bash
npm run build
```

### Deployment Checklist
- [ ] Environment variables configured
- [ ] API endpoints updated
- [ ] Analytics tracking enabled
- [ ] Error monitoring configured
- [ ] Performance budgets met
- [ ] Accessibility tested
- [ ] Browser compatibility verified

## 🤝 Contributing

1. Follow the established code style
2. Add tests for new features
3. Update documentation
4. Ensure accessibility compliance
5. Test on multiple browsers and devices

## 📄 License

This project is part of the ESAB Welding Management System. All rights reserved.