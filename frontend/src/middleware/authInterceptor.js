import api from '../services/api';
import { getToken } from '../security/auth/tokenManager';

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default api;
