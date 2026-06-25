// CORS configuration middleware placeholder
// Configure allowed origins, methods, headers, and credentials.

function configureCors(options = {}) {
  return (req, res, next) => {
    // TODO: set CORS headers
    next();
  };
}

module.exports = {
  configureCors,
};
