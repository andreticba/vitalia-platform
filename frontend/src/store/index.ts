// frontend/src/store/index.ts em 2025-12-14 11:48

import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    // Adicionaremos gamificationSlice e uiSlice (theme) aqui depois
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
