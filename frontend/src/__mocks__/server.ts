import { setupServer } from 'msw/node';
import { customerHandlers } from './handlers/customers';
import { billingHandlers } from './handlers/billing';

// Combine all handlers from different modules
const handlers = [
  ...customerHandlers,
  ...billingHandlers,
  // Add other module handlers here
  // ...ticketHandlers,
  // ...networkHandlers,
];

// Setup MSW server for Node.js (Jest tests)
// Only active when NEXT_PUBLIC_API_MOCKING is enabled
export const server = setupServer(...handlers);
