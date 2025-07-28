// import { defineConfig } from 'orval';

/*
 * Orval configuration for generating typed API clients and React Query hooks.
 * Each entry corresponds to a feature-specific OpenAPI spec. Add additional
 * specs as needed (billing, tickets, etc.).
 */
export default {
  customers: {
    input: './customers.yml',
    output: {
      target: '../frontend/src/api/customers/',
      schemas: '../frontend/src/api/_schemas',
      client: 'react-query',
      mock: false,
      override: {
        mutator: {
          path: '../frontend/src/api/_utils/axios-instance.ts',
          name: 'axiosInstance',
        },
      },
    },
  },
  billing: {
    input: './billing.yml',
    output: {
      target: '../frontend/src/api/billing/',
      schemas: '../frontend/src/api/_schemas',
      client: 'react-query',
      mock: false,
      override: {
        mutator: {
          path: '../frontend/src/api/_utils/axios-instance.ts',
          name: 'axiosInstance',
        },
      },
    },
  },
  // Add more specs (tickets, network, etc.) below
};
