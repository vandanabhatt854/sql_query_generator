// JWT authentication middleware placeholder
// Implement token verification, user extraction, and auth error handling.

function authenticateJWT(req, res, next) {
  // TODO: verify JWT token
  next();
}

module.exports = {
  authenticateJWT,
};
