// Stub for next/font in Jest environment
module.exports = new Proxy({}, {
  get: () => () => ({ className: "mock-font", style: { fontFamily: "mock" } }),
});
