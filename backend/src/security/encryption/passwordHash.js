// Password hashing placeholder
// Use bcrypt or a comparable algorithm for secure password storage.

function hashPassword(password) {
  // TODO: hash the password securely
  return password;
}

function comparePassword(password, hashed) {
  // TODO: compare plain password to hash
  return password === hashed;
}

module.exports = {
  hashPassword,
  comparePassword,
};
