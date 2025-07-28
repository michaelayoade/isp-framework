import { setupWorker } from 'msw';
import { customerHandlers } from './handlers/customers';
import { billingHandlers } from './handlers/billing';

// Combine all handlers from different modules
const handlers = [
  ...customerHandlers,
  ...billingHandlers,
  // Add other module handlers here
];

// Setup MSW worker for browser (development)
export const worker = setupWorker(...handlers);
