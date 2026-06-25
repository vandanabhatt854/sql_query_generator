// Security headers middleware placeholder using helmet-style configuration
// Add headers to protect against common web vulnerabilities.

function applySecurityHeaders(req, res, next) {
  // TODO: set Content-Security-Policy, X-Content-Type-Options, etc.
  next();
}

module.exports = {
  applySecurityHeaders,
};
