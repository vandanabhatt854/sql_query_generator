// Session management placeholder
// Track authenticated user session state and expiration.

export function createSession(user, token) {
  setToken(token);
  return { user, token, createdAt: Date.now() };
}

export function destroySession() {
  clearToken();
}

function setToken(token) {
  localStorage.setItem('auth_token', token);
}

function clearToken() {
  localStorage.removeItem('auth_token');
}
