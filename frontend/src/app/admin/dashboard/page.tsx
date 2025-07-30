'use client';

import { AuthGuard } from '@/components/auth/AuthGuard';

export default function DashboardPage() {
  return (
    <AuthGuard requiredRole="admin">
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-6">Admin Dashboard</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-2">System Overview</h2>
            <p className="text-gray-600">Welcome to the admin portal. This is your central hub for managing the entire ISP system.</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-2">Quick Actions</h2>
            <p className="text-gray-600">Access key administrative functions and system controls.</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-2">Recent Activity</h2>
            <p className="text-gray-600">Monitor system events and administrative actions.</p>
          </div>
        </div>
      </div>
    </AuthGuard>
  );
}
