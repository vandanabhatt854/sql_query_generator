// Whitelist validation placeholder
// Allow only approved values and patterns.

function validateWhitelist(value, whitelist) {
  const allowed = Array.isArray(whitelist) ? whitelist.includes(value) : false;
  return { valid: allowed };
}

module.exports = {
  validateWhitelist,
};
