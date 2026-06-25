// Client-side encryption placeholder
// Use only for non-sensitive data obfuscation in the browser.

export function encryptData(value) {
  return btoa(JSON.stringify(value));
}

export function decryptData(value) {
  try {
    return JSON.parse(atob(value));
  } catch (error) {
    return null;
  }
}
