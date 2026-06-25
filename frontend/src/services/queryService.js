import api from './api';

export function generateQuery(payload) {
  return api.post('/generate', payload);
}

export function executeQuery(query) {
  return api.post('/execute', { sql: query });
}
