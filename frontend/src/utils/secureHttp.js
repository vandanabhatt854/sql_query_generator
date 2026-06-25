import axios from 'axios';
import { getCsrfToken } from '../security/validation/csrfProtection';

const secureHttp = axios.create();
secureHttp.interceptors.request.use((config) => {
  const token = getCsrfToken();
  if (token) config.headers['X-CSRF-Token'] = token;
  return config;
});

export default secureHttp;
