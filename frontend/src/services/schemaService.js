import api from './api';

export function fetchSchema() {
  return api.get('/schema');
}
