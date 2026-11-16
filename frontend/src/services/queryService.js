import api from './api';

export function getGenerationStatus() { return api.get('/generation-status'); }
export function generateQuery(payload) { return api.post('/generate', payload); }
export function executeQuery(query) { return api.post('/execute', { sql: query }); }
