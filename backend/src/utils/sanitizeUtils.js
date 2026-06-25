// Data sanitization utilities placeholder

function sanitizeString(value) {
  if (typeof value !== 'string') {
    return value;
  }
  return value.replace(/[<>"'`;]/g, '');
}

module.exports = {
  sanitizeString,
};
