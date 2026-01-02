// frontend/src/lib/api.ts em 2025-12-14 11:48

import axios from 'axios';
import { store } from '@/store';
import { logout, setCredentials, STORAGE_KEYS } from '@/store/slices/authSlice';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

// --- INTERCEPTOR DE REQUEST ---
api.interceptors.request.use((config) => {
  // 1. Tenta pegar do Redux
  let token = store.getState().auth.accessToken;
  let source = 'Redux';

  // 2. Fallback: SessionStorage
  if (!token && typeof window !== 'undefined') {
    token = sessionStorage.getItem(STORAGE_KEYS.ACCESS);
    source = 'SessionStorage (Fallback)';
  }

  console.log(`[AUTH DEBUG] API Request: ${config.url}`, {
    source,
    hasToken: !!token
  });

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  } else {
    console.warn('[AUTH DEBUG] ⚠️ AVISO CRÍTICO: Requisição saindo SEM token!');
  }
  
  return config;
});

// --- INTERCEPTOR DE RESPONSE ---
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      console.log('[AUTH DEBUG] API: 401 Recebido. Tentando Refresh...');
      originalRequest._retry = true;

      const refreshToken = 
        store.getState().auth.refreshToken || 
        (typeof window !== 'undefined' ? sessionStorage.getItem(STORAGE_KEYS.REFRESH) : null);

      if (refreshToken) {
        try {
          const response = await axios.post(
            `${api.defaults.baseURL}/auth/token/refresh/`, 
            { refresh: refreshToken }
          );
          
          const newAccess = response.data.access;
          console.log('[AUTH DEBUG] API: Token renovado com sucesso.');

          store.dispatch(setCredentials({ 
              accessToken: newAccess, 
              refreshToken: refreshToken,
              user: store.getState().auth.user || undefined 
          }));
          
          originalRequest.headers.Authorization = `Bearer ${newAccess}`;
          return api(originalRequest);

        } catch (refreshError) {
          console.error('[AUTH DEBUG] API: Falha no refresh.', refreshError);
          store.dispatch(logout());
          if (typeof window !== 'undefined') window.location.href = '/login';
        }
      } else {
        console.warn('[AUTH DEBUG] API: Sem refresh token. Logout.');
        store.dispatch(logout());
        if (typeof window !== 'undefined') window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;