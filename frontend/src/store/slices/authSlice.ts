// frontend/src/store/slices/authSlice.ts em 2025-12-14 11:48

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { AuthState, UserProfile } from '@/types/auth';

export const STORAGE_KEYS = {
  ACCESS: '@vitalia:access_token_v1',
  REFRESH: '@vitalia:refresh_token_v1',
};

// Adiciona isInitialized à interface
interface ExtendedAuthState extends AuthState {
  isInitialized: boolean;
}

const initialState: ExtendedAuthState = {
  user: null,
  accessToken:  null,
  refreshToken: null,
  isAuthenticated: false,
  isInitialized: false, // <--- O Guardião do F5
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials: (
      state,
      action: PayloadAction<{ user?: UserProfile; accessToken: string; refreshToken: string }>
    ) => {
      const { user, accessToken, refreshToken } = action.payload;
      state.accessToken = accessToken;
      state.refreshToken = refreshToken;
      if (user) state.user = user;
      state.isAuthenticated = true;
      state.isInitialized = true; // <--- Boot completo com sucesso
      
      if (typeof window !== 'undefined') {
        sessionStorage.setItem(STORAGE_KEYS.ACCESS, accessToken);
        sessionStorage.setItem(STORAGE_KEYS.REFRESH, refreshToken);
      }
    },
    logout: (state) => {
      state.user = null;
      state.accessToken = null;
      state.refreshToken = null;
      state.isAuthenticated = false;
      state.isInitialized = true; // <--- Boot completo (mesmo que deslogado)
      
      if (typeof window !== 'undefined') {
        sessionStorage.clear();
        localStorage.clear();
      }
    },
    // Nova ação para quando verificamos o storage e não achamos nada
    initializeAuth: (state) => {
        state.isInitialized = true;
    }
  },
});

export const { setCredentials, logout, initializeAuth } = authSlice.actions;
export default authSlice.reducer;