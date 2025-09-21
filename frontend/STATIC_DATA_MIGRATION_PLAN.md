# Static Data Migration Plan

## Overview
This document outlines the migration from static hardcoded data to dynamic API integration in the ESAB Welding Management System frontend.

## Identified Static Data Dependencies

### 1. SparkyPage (frontend/src/pages/SparkyPage/index.tsx)
- **Issue**: References undefined `packageComponents` array
- **Hardcoded Values**:
  - PowerSource fallback: $4,500
  - Feeder fallback: $1,800
  - Cooler fallback: $2,200
  - Torch fallback: $450
  - Ground Cable: $89
  - Wire Spool: $125
  - Accessories fallback: $285
- **Static Product Names**:
  - "MIG Torch"
  - "Ground Cable"
  - "Wire Spool"
  - "ER4043 Aluminum Wire 1.2mm 7kg"

### 2. QuoteManagementPage (frontend/src/pages/QuoteManagementPage/index.tsx)
- **Static Package Data**: Complete hardcoded package configurations with prices
- **Hardcoded Components**: Wire Feeder, Connection Cable, Cooling Unit, etc.

### 3. InventoryPage (frontend/src/pages/InventoryPage/index.tsx)
- **Static Inventory Items**: Hardcoded product list with prices and stock levels

### 4. DashboardPage (frontend/src/pages/DashboardPage/index.tsx)
- **Static Metrics**: Hardcoded interaction counts and statistics

## Migration Strategy

### Phase 1: Remove Static Dependencies (Current Task)
1. Fix SparkyPage compilation errors by removing undefined references
2. Replace hardcoded fallback values with dynamic API data
3. Remove static product names and descriptions
4. Implement proper error handling for missing data

### Phase 2: Dynamic API Integration (Next Tasks)
1. Implement Enhanced Orchestrator API service layer
2. Add proper state management for dynamic data
3. Implement caching and error recovery

### Phase 3: Update Other Pages (Future Tasks)
1. Migrate QuoteManagementPage to use dynamic data
2. Migrate InventoryPage to use real inventory API
3. Migrate DashboardPage to use real metrics API

## Implementation Plan

### Step 1: Fix SparkyPage Compilation Issues
- Remove references to undefined `packageComponents`
- Replace static fallback values with API data or loading states
- Add proper error boundaries for missing data

### Step 2: Clean Up Hardcoded Values
- Remove all hardcoded prices and product names
- Use data from EnhancedWeldingPackage interface
- Add loading states for missing components

### Step 3: Improve Error Handling
- Add graceful degradation when API data is unavailable
- Implement proper loading states
- Add user-friendly error messages

## Success Criteria
- [ ] No compilation errors related to undefined static data
- [ ] All product information comes from API responses
- [ ] Proper loading states when data is unavailable
- [ ] Graceful error handling for missing components
- [ ] No hardcoded prices or product names in the UI