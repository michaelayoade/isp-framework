import '@testing-library/jest-dom';

// Only enable MSW if API mocking is explicitly enabled
if (process.env.NEXT_PUBLIC_API_MOCKING === 'enabled') {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { server } = require('./__mocks__/server');
  
  // Establish API mocking before all tests
  beforeAll(() => server.listen());
  
  // Reset any request handlers that we may add during the tests,
  // so they don't affect other tests
  afterEach(() => server.resetHandlers());
  
  // Clean up after the tests are finished
  afterAll(() => server.close());
}
