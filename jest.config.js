automock = false;
transformIgnorePatterns = ["/node_modules/"];
module.exports = {
  moduleNameMapper: {
    "\\.css$": "identity-obj-proxy",
    // Ignore index.js file as it only contains
    // legacy JS files not relevant to the React components
    // nor the tests.
    "\/assets\/js\/index$": "identity-obj-proxy"
  },
};
