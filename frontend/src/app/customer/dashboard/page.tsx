'use client';

import { AuthGuard } from '@/components/auth/AuthGuard';

export default function CustomerDashboardPage() {
  return (
    <AuthGuard requiredRole="customer">
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-6">Customer Dashboard</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-2">Account Overview</h2>
            <p className="text-gray-600">View your account details, billing information, and service status.</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-2">Services</h2>
            <p className="text-gray-600">Manage your internet, voice, and other services.</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-2">Support</h2>
            <p className="text-gray-600">Access help resources and submit support tickets.</p>
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
