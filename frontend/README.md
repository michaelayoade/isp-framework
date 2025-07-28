# ISP Framework Frontend

This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

The frontend provides self-service portals for customers and resellers, plus a comprehensive admin interface for ISP management.

## Architecture

### Feature Modules
The application is organized into feature modules under `src/features/`:
- `customers/` - Customer management and portal services
- `resellers/` - Reseller management and portal services
- `billing/` - Billing and invoice management
- `services/` - Service plans and provisioning
- `networking/` - Network infrastructure management
- `tickets/` - Support ticket system
- `plugins/` - Plugin system management
- `radius/` - RADIUS session management

Each feature module contains:
- `components/` - React components specific to the feature
- `services/` - API service hooks using RTK Query
- `types/` - TypeScript interfaces and types
- `hooks/` - Custom React hooks
- `utils/` - Utility functions

### Common Types
Shared types and interfaces are centralized in `src/types/common.ts` to reduce duplication across feature modules.

## Self-Service Portals

### Customer Portal (`/customer-portal`)
Provides customers with self-service access to:
- **Account Overview**: Profile information, service status, usage statistics
- **Billing**: Invoice history, payment processing, download receipts
- **Support**: Ticket creation and tracking
- **Services**: Service usage monitoring and statistics
- **File Downloads**: Invoice PDFs and service documentation

**Key Features:**
- Secure authentication with JWT tokens
- File download with blob streaming
- Payment processing integration (configurable provider)
- Real-time usage statistics
- Responsive design for mobile/desktop

### Reseller Portal (`/reseller-portal`)
Provides resellers with self-service access to:
- **Dashboard**: Commission reports, customer statistics, performance metrics
- **Customer Management**: Register new customers, view customer details
- **Commission Tracking**: Earnings reports and payment history
- **Customer Support**: View and manage customer tickets

**Key Features:**
- Customer registration with service plan selection
- Commission reporting and analytics
- Customer details modal with comprehensive information
- Bulk customer operations
- Export functionality for reports

### Authentication & Security
Both portals implement:
- **Route Guards**: Role-based access control with automatic redirects
- **Token Expiry**: Automatic logout on JWT expiration
- **Error Boundaries**: Graceful error handling with user-friendly messages
- **Input Validation**: Client-side and server-side validation
- **CSRF Protection**: Secure API communication

### Component Architecture
- **AuthGuard**: Protects routes based on user roles
- **ErrorBoundary**: Catches and displays errors gracefully
- **Modal Components**: Reusable dialogs for forms and details
- **Toast Notifications**: User feedback for actions
- **Loading States**: Progress indicators for async operations

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
