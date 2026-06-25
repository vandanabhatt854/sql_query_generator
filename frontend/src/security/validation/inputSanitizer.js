// Input sanitization placeholder
// Clean potentially unsafe values before using them in the app.

export function sanitizeInput(value) {
  if (typeof value !== 'string') return value;
  return value.replace(/[<>"'`;&]/g, '');
}
