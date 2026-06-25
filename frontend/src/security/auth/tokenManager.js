// Token management placeholder
// Handle access tokens and refresh tokens securely in the frontend.

export function getToken() {
  return localStorage.getItem('auth_token');
}

export function setToken(token) {
  localStorage.setItem('auth_token', token);
}

export function clearToken() {
  localStorage.removeItem('auth_token');
}
