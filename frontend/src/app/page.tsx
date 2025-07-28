'use client';

import React from 'react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Users, 
  CreditCard, 
  Router, 
  TicketIcon, 
  BarChart3, 
  Shield,
  Zap
} from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-16">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <div className="mb-6">
            <Badge variant="secondary" className="mb-4">
              Enterprise ISP Platform
            </Badge>
          </div>
          <h1 className="text-5xl font-bold mb-6 bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
            ISP Framework
          </h1>
          <p className="text-xl text-muted-foreground mb-4 max-w-2xl mx-auto">
            Enterprise-Grade Internet Service Provider Management Platform
          </p>
          <p className="text-lg text-muted-foreground mb-8 max-w-3xl mx-auto">
            Built with Next.js, Tailwind CSS, ShadCN UI, TanStack Table, and Recharts for comprehensive ISP operations management.
          </p>
          
          <div className="flex gap-4 justify-center flex-wrap">
            <Link href="/admin">
              <Button size="lg" className="text-base">
                <BarChart3 className="mr-2 h-5 w-5" />
                Admin Dashboard
              </Button>
            </Link>
            <Link href="/components-demo">
              <Button variant="outline" size="lg" className="text-base">
                <Zap className="mr-2 h-5 w-5" />
                Component Demo
              </Button>
            </Link>
          </div>
        </div>

        {/* Features Section */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-center mb-12">Platform Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                    <Users className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                  </div>
                  <CardTitle>Customer Management</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Comprehensive customer lifecycle management with service plans, billing, and support tracking.
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                    <CreditCard className="h-6 w-6 text-green-600 dark:text-green-400" />
                  </div>
                  <CardTitle>Billing & Invoicing</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Automated billing cycles, invoice generation, payment processing, and financial reporting.
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                    <Router className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                  </div>
                  <CardTitle>Network Infrastructure</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  OLT/ONU management, network topology visualization, and equipment monitoring.
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
                    <TicketIcon className="h-6 w-6 text-orange-600 dark:text-orange-400" />
                  </div>
                  <CardTitle>Support Ticketing</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Integrated help desk with ticket management, SLA tracking, and customer communication.
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-cyan-100 dark:bg-cyan-900 rounded-lg">
                    <BarChart3 className="h-6 w-6 text-cyan-600 dark:text-cyan-400" />
                  </div>
                  <CardTitle>Analytics & Reporting</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Real-time dashboards, performance metrics, and business intelligence reporting.
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-red-100 dark:bg-red-900 rounded-lg">
                    <Shield className="h-6 w-6 text-red-600 dark:text-red-400" />
                  </div>
                  <CardTitle>Security & Compliance</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription>
                  Multi-tenant architecture, role-based access control, and audit logging.
                </CardDescription>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Tech Stack Section */}
        <div className="text-center">
          <h2 className="text-3xl font-bold mb-8">Built with Modern Technologies</h2>
          <div className="flex flex-wrap justify-center gap-3">
            <Badge variant="outline" className="text-sm py-1 px-3">Next.js 15</Badge>
            <Badge variant="outline" className="text-sm py-1 px-3">React 19</Badge>
            <Badge variant="outline" className="text-sm py-1 px-3">TypeScript</Badge>
            <Badge variant="outline" className="text-sm py-1 px-3">Tailwind CSS</Badge>
            <Badge variant="outline" className="text-sm py-1 px-3">ShadCN UI</Badge>
            <Badge variant="outline" className="text-sm py-1 px-3">TanStack Table</Badge>
            <Badge variant="outline" className="text-sm py-1 px-3">Recharts</Badge>
            <Badge variant="outline" className="text-sm py-1 px-3">React Hook Form</Badge>
            <Badge variant="outline" className="text-sm py-1 px-3">Zod</Badge>
            <Badge variant="outline" className="text-sm py-1 px-3">Lucide Icons</Badge>
          </div>
        </div>
      </div>
    </div>
  );
}
