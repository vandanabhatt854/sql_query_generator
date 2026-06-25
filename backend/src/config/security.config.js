// Security configuration placeholder
// Centralize security-related configuration values.

module.exports = {
  jwtSecret: process.env.JWT_SECRET || 'change-me',
  csrfSecret: process.env.CSRF_SECRET || 'change-me',
};
