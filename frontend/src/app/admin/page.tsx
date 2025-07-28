'use client';

import React from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AppLayout, PageShell, PageContent, PageSection } from '@/components/ui/layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Users, CreditCard, Wifi, AlertTriangle, TrendingUp, DollarSign, Plus, ArrowRight } from 'lucide-react';
import Link from 'next/link';

const dashboardCards = [
  {
    title: 'Customer Management',
    description: 'Manage customers, accounts, and services',
    icon: Users,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    href: '/admin/customers',
    stats: '1,234 customers',
  },
  {
    title: 'Billing & Invoices',
    description: 'Process payments, generate invoices',
    icon: CreditCard,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    href: '/admin/billing',
    stats: '$45,678 this month',
  },
  {
    title: 'Network Management',
    description: 'Monitor devices, manage IP pools',
    icon: Wifi,
    color: 'text-orange-600',
    bgColor: 'bg-orange-50',
    href: '/admin/devices',
    stats: '567 devices online',
  },
  {
    title: 'Support Tickets',
    description: 'Handle customer support requests',
    icon: AlertTriangle,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    href: '/admin/tickets',
    stats: '23 open tickets',
  },
  {
    title: 'System Settings',
    description: 'Configure system preferences',
    icon: DollarSign,
    color: 'text-gray-600',
    bgColor: 'bg-gray-50',
    href: '/admin/settings',
    stats: 'Last updated 2h ago',
  },
];

export default function AdminDashboard() {
  const breadcrumbs = [
    { label: 'Admin', href: '/admin' },
    { label: 'Dashboard' },
  ];

  return (
    <ProtectedRoute requiredRole="admin">
      <AppLayout>
        <PageShell
          title="Dashboard"
          subtitle="Welcome to the ISP Framework administration panel"
          breadcrumbs={breadcrumbs}
          actions={
            <Button variant="outline">
              <DollarSign className="w-4 h-4 mr-2" />
              Settings
            </Button>
          }
        >
          <PageContent>
            {/* Quick Stats */}
            <PageSection title="Quick Stats" className="mb-8">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-green-100 rounded-lg">
                        <TrendingUp className="w-6 h-6 text-green-600" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Total Revenue</p>
                        <p className="text-2xl font-bold text-gray-900">$45,678</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-green-100 rounded-lg">
                        <Users className="w-6 h-6 text-green-600" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Active Customers</p>
                        <p className="text-2xl font-bold text-gray-900">1,234</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-green-100 rounded-lg">
                        <Wifi className="w-6 h-6 text-green-600" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Devices Online</p>
                        <p className="text-2xl font-bold text-gray-900">567</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-red-100 rounded-lg">
                        <AlertTriangle className="w-6 h-6 text-red-600" />
                      </div>
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Open Tickets</p>
                        <p className="text-2xl font-bold text-gray-900">23</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </PageSection>

            {/* Management Sections */}
            <PageSection title="Management" subtitle="Access key areas of the ISP Framework">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {dashboardCards.map((card, index) => {
                  const Icon = card.icon;
                  return (
                    <Card key={index} className="hover:shadow-lg transition-shadow cursor-pointer">
                      <CardHeader>
                        <div className="flex items-center space-x-4">
                          <div className={`p-3 rounded-lg ${card.bgColor}`}>
                            <Icon className={`w-6 h-6 ${card.color}`} />
                          </div>
                          <div>
                            <CardTitle className="text-lg">{card.title}</CardTitle>
                            <CardDescription>{card.stats}</CardDescription>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-gray-600 mb-4">{card.description}</p>
                        <Button variant="outline" className="w-full">
                          Manage
                        </Button>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </PageSection>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="h-5 w-5" />
                    Customer Management
                  </CardTitle>
                  <CardDescription>
                    Manage customer accounts, services, and billing
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-2">
                    <Link href="/customers">
                      <Button size="sm" className="bg-green-600 hover:bg-green-700">
                        <Users className="h-4 w-4 mr-2" />
                        View Customers
                      </Button>
                    </Link>
                    <Button size="sm" variant="outline">
                      <Plus className="h-4 w-4 mr-2" />
                      Add Customer
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CreditCard className="h-5 w-5" />
                    Billing & Invoicing
                  </CardTitle>
                  <CardDescription>
                    Generate invoices, track payments, and manage billing
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-2">
                    <Link href="/billing">
                      <Button size="sm" className="bg-green-600 hover:bg-green-700">
                        <CreditCard className="h-4 w-4 mr-2" />
                        View Billing
                      </Button>
                    </Link>
                    <Button size="sm" variant="outline">
                      <Plus className="h-4 w-4 mr-2" />
                      Create Invoice
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Wifi className="h-5 w-5" />
                    Network Operations
                  </CardTitle>
                  <CardDescription>
                    Monitor network status, OLTs, and infrastructure
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button size="sm" className="w-full bg-green-600 hover:bg-green-700">
                    <Wifi className="h-4 w-4 mr-2" />
                    Network Dashboard
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </Button>
                </CardContent>
              </Card>
            </div>
          </PageContent>
        </PageShell>
      </AppLayout>
    </ProtectedRoute>
  );
}
