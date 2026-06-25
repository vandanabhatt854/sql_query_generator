// CSRF protection middleware placeholder
// Validate CSRF tokens for state-changing requests.

function verifyCsrfToken(req, res, next) {
  // TODO: verify CSRF token in headers or body
  next();
}

module.exports = {
  verifyCsrfToken,
};
