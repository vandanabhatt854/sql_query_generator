// Security helper utilities placeholder

function isSecureConnection(req) {
  return req.secure || req.headers['x-forwarded-proto'] === 'https';
}

module.exports = {
  isSecureConnection,
};
