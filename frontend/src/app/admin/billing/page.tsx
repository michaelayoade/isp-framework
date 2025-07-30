'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText, CreditCard, ArrowRight } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function BillingPage() {
  const router = useRouter();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Billing Management</h1>
        <p className="text-muted-foreground">
          Manage invoices, payments, and billing operations
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push('/billing/invoices')}>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <FileText className="h-5 w-5 text-blue-600" />
              <CardTitle>Invoice Management</CardTitle>
            </div>
            <CardDescription>
              Create, view, and manage customer invoices
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                View all invoices, filter by status, and manage billing
              </div>
              <Button variant="ghost" size="sm">
                <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => router.push('/billing/payments')}>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <CreditCard className="h-5 w-5 text-green-600" />
              <CardTitle>Payment Management</CardTitle>
            </div>
            <CardDescription>
              Track and manage customer payments
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                View payment records, track transactions, and reconcile accounts
              </div>
              <Button variant="ghost" size="sm">
                <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-8">
        <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
        <div className="flex gap-4">
          <Button onClick={() => router.push('/billing/invoices')}>
            <FileText className="h-4 w-4 mr-2" />
            View Invoices
          </Button>
          <Button variant="outline" onClick={() => router.push('/billing/payments')}>
            <CreditCard className="h-4 w-4 mr-2" />
            View Payments
          </Button>
        </div>
      </div>
    </div>
  );
}
