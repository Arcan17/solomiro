/** @type {import('jest').Config} */
const config = {
  testEnvironment: "jest-environment-jsdom",
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/$1",
    // Stub next/font so Jest doesn't fail on it
    "^next/font/(.*)$": "<rootDir>/__mocks__/nextFontMock.js",
  },
  transform: {
    "^.+\\.(ts|tsx|js|jsx)$": ["babel-jest", { configFile: "./babel.jest.config.js" }],
  },
  testPathIgnorePatterns: ["<rootDir>/.next/", "<rootDir>/node_modules/"],
};

module.exports = config;
