// Response time monitoring middleware placeholder

function responseTime(req, res, next) {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(`Response time: ${duration}ms`);
  });
  next();
}

module.exports = {
  responseTime,
};
