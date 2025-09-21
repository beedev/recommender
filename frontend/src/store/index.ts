import { configureStore } from '@reduxjs/toolkit'
import authSlice from './slices/authSlice'
import uiSlice from './slices/uiSlice'
import inventorySlice from './slices/inventorySlice'
import enhancedConversationSlice from './slices/enhancedConversationSlice'

export const store = configureStore({
  reducer: {
    auth: authSlice,
    ui: uiSlice,
    inventory: inventorySlice,
    enhancedConversation: enhancedConversationSlice,
  },
  middleware: getDefaultMiddleware =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
  devTools: import.meta.env.DEV,
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch

// Export action creators for convenience
export { actions as authActions } from './slices/authSlice'
export { actions as uiActions } from './slices/uiSlice'
export { actions as inventoryActions } from './slices/inventorySlice'
export { actions as enhancedConversationActions } from './slices/enhancedConversationSlice'