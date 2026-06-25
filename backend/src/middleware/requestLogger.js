// Request logging middleware placeholder

function requestLogger(req, res, next) {
  console.log(`${req.method} ${req.url}`);
  next();
}

module.exports = {
  requestLogger,
};
