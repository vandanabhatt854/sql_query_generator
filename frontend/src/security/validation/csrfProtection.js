// CSRF token handling placeholder
// Store and validate CSRF tokens for secure form submissions.

export function getCsrfToken() {
  return localStorage.getItem('csrf_token');
}

export function setCsrfToken(token) {
  localStorage.setItem('csrf_token', token);
}

export function clearCsrfToken() {
  localStorage.removeItem('csrf_token');
}
