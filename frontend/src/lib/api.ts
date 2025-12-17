// frontend/src/lib/api.ts em 2025-12-14 11:48

import axios from 'axios';
import { store } from '@/store'; // Criaremos no próximo passo
import { logout, setCredentials } from '@/store/slices/authSlice';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

// Interceptor de Request: Injeta o Token
api.interceptors.request.use((config) => {
  const token = store.getState().auth.accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor de Response: Refresh Token Automático
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = store.getState().auth.refreshToken;

      if (refreshToken) {
        try {
          // Tenta renovar o token
          const { data } = await axios.post(`${api.defaults.baseURL}/auth/token/refresh/`, {
            refresh: refreshToken
          });
          
          // Salva no Redux
          store.dispatch(setCredentials({ accessToken: data.access, refreshToken: refreshToken }));
          
          // Refaz a requisição original com o novo token
          originalRequest.headers.Authorization = `Bearer ${data.access}`;
          return api(originalRequest);
        } catch (refreshError) {
          // Se falhar, logout forçado
          store.dispatch(logout());
          window.location.href = '/login';
        }
      } else {
        store.dispatch(logout());
      }
    }
    return Promise.reject(error);
  }
);

export default api;
