'use client';

import { AuthGuard } from '@/components/auth/AuthGuard';

export default function ResellerDashboardPage() {
  return (
    <AuthGuard requiredRole="reseller">
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-6">Reseller Dashboard</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-2">Partner Overview</h2>
            <p className="text-gray-600">View your partner account details, commissions, and performance metrics.</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-2">Customer Management</h2>
            <p className="text-gray-600">Manage your customers and their services.</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-2">Reports</h2>
            <p className="text-gray-600">Access financial reports and performance analytics.</p>
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
