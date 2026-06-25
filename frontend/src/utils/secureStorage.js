// Secure storage utilities placeholder
// Prefer secure, encrypted storage strategies in production.

export function setSecureItem(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

export function getSecureItem(key) {
  const item = localStorage.getItem(key);
  return item ? JSON.parse(item) : null;
}

export function removeSecureItem(key) {
  localStorage.removeItem(key);
}
