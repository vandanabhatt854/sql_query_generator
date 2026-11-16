import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || `http://${window.location.hostname}:8000`,
  withCredentials: true,
  timeout: 45000,
});

export default api;
