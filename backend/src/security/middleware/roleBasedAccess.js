// Role-based access control middleware placeholder
// Enforce permissions based on user roles and route requirements.

function requireRole(role) {
  return (req, res, next) => {
    // TODO: check req.user.role against required role
    next();
  };
}

module.exports = {
  requireRole,
};
