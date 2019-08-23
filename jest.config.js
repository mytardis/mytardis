testRegex = "((\\.|/*.)(spec))\\.js?$";
setupFilesAfterEnv= ["<rootDir>/jest.setup.js"];
transformIgnorePatterns= ["/node_modules/"];
module.exports ={
  moduleNameMapper: {
    "\\.css$": "identity-obj-proxy",
  },
};