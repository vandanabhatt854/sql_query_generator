import api from './api';

export function fetchHistory() {
  return api.get('/history');
}
