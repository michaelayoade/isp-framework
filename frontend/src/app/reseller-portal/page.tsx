'use client';

import { useState } from 'react';
import { AuthGuard } from '@/components/auth/AuthGuard';
import { ErrorBoundary } from '@/components/error/ErrorBoundary';
import { useResellerProfile, useResellerDashboard, useResellerCustomers, useCommissionReports } from '@/features/resellers/hooks/useResellers';
import type { CommissionReport, ResellerCustomer } from '@/features/resellers/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Users, 
  DollarSign, 
  TrendingUp, 
  Building,
  Plus,
  Eye,

  BarChart3,
  Calendar,
  Target
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';







function ResellerPortalPageContent() {
  const { toast } = useToast();
  
  // Modal states
  const [isAddCustomerOpen, setIsAddCustomerOpen] = useState(false);
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | null>(null);
  const [isCustomerDetailsOpen, setIsCustomerDetailsOpen] = useState(false);
  
  // Form state for customer registration
  const [customerForm, setCustomerForm] = useState({
    name: '',
    email: '',
    phone: '',
    company: '',
    address: '',
    city: '',
    state: '',
    zip: '',
    plan: ''
  });


  // Fetch reseller profile
  const { data: resellerProfile, isLoading: profileLoading, error: profileError } = useResellerProfile();

  // Fetch reseller dashboard
  const { data: dashboard, isLoading: dashboardLoading } = useResellerDashboard();

  // Fetch reseller customers
  const { data: customersData } = useResellerCustomers({ page: 1, per_page: 10 });

  // Fetch commission reports
  const { data: commissions } = useCommissionReports();

  // Handle loading and error states
  if (profileLoading || dashboardLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading reseller portal...</p>
        </div>
      </div>
    );
  }

  if (profileError) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">Error loading reseller data</p>
          <Button onClick={() => window.location.reload()}>Retry</Button>
        </div>
      </div>
    );
  }

  const reseller = resellerProfile;
  const dashboardData = dashboard;
  const customers = (customersData as { customers: ResellerCustomer[] })?.customers || [];
  const commissionReports: CommissionReport[] = (commissions as CommissionReport[] | undefined) || [];

  const getStatusBadge = (status: string) => {
    const variants = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-gray-100 text-gray-800',
      suspended: 'bg-red-100 text-red-800',
      pending: 'bg-yellow-100 text-yellow-800',
      paid: 'bg-green-100 text-green-800',
      gold: 'bg-yellow-100 text-yellow-800',
      silver: 'bg-gray-100 text-gray-800',
      bronze: 'bg-orange-100 text-orange-800',
    };
    
    return (
      <Badge className={variants[status as keyof typeof variants] || 'bg-gray-100 text-gray-800'}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const getTierIcon = (tier: string) => {
    switch (tier) {
      case 'gold':
        return <Target className="h-5 w-5 text-yellow-600" />;
      case 'silver':
        return <Target className="h-5 w-5 text-gray-600" />;
      case 'bronze':
        return <Target className="h-5 w-5 text-orange-600" />;
      default:
        return <Target className="h-5 w-5 text-gray-600" />;
    }
  };

  const handleAddCustomer = () => {
    setIsAddCustomerOpen(true);
  };

  const handleSubmitCustomer = async () => {
    try {
      // Validate required fields
      if (!customerForm.name || !customerForm.email || !customerForm.phone) {
        toast({
          title: 'Validation Error',
          description: 'Please fill in all required fields (name, email, phone).',
          variant: 'destructive'
        });
        return;
      }

      // TODO: Replace with actual API call to create customer
      // await createCustomer(customerForm);
      
      toast({
        title: 'Customer Created',
        description: `Successfully registered ${customerForm.name}`,
      });
      
      // Reset form and close modal
      setCustomerForm({
        name: '',
        email: '',
        phone: '',
        company: '',
        address: '',
        city: '',
        state: '',
        zip: '',
        plan: ''
      });
      setIsAddCustomerOpen(false);
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to create customer. Please try again.',
        variant: 'destructive'
      });
    }
  };

  const handleViewCustomer = (customerId: number) => {
    setSelectedCustomerId(customerId);
    setIsCustomerDetailsOpen(true);
  };

  const getCustomerDetails = (customerId: number) => {
    // Find customer in the current data
    return (customersData as { customers: ResellerCustomer[] })?.customers?.find(c => c.id === customerId);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Reseller Portal
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Welcome back, {reseller?.name || 'Reseller'}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm text-gray-500">Partner Tier</p>
                <div className="flex items-center space-x-2">
                  {getTierIcon(reseller?.tier || 'bronze')}
                  {getStatusBadge(reseller?.tier || 'bronze')}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <Users className="h-8 w-8 text-blue-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Customers</p>
                  <p className="text-2xl font-bold text-gray-900">{dashboardData?.total_customers || 0}</p>
                  <p className="text-xs text-green-600">+3 this month</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <DollarSign className="h-8 w-8 text-green-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Monthly Revenue</p>
                  <p className="text-2xl font-bold text-gray-900">${dashboardData?.monthly_revenue?.toLocaleString() || '0'}</p>
                  <p className="text-xs text-green-600">+8.2% from last month</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <TrendingUp className="h-8 w-8 text-purple-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Commission</p>
                  <p className="text-2xl font-bold text-gray-900">${dashboardData?.total_commission?.toLocaleString() || '0'}</p>
                  <p className="text-xs text-purple-600">{dashboardData?.commission_rate || 0}% rate</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <Calendar className="h-8 w-8 text-orange-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Pending Payout</p>
                  <p className="text-2xl font-bold text-gray-900">${dashboardData?.pending_commission?.toLocaleString() || '0'}</p>
                  <p className="text-xs text-gray-500">Due Feb 15</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Commission Alert */}
        {(dashboardData?.pending_commission || 0) > 0 && (
          <Alert className="mb-6 border-green-200 bg-green-50">
            <DollarSign className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              <strong>Commission Ready:</strong> ${dashboardData?.pending_commission?.toFixed(2) || '0.00'} will be paid on February 15, 2025
            </AlertDescription>
          </Alert>
        )}

        {/* Tabs Content */}
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="customers">Customers</TabsTrigger>
            <TabsTrigger value="commissions">Commissions</TabsTrigger>
            <TabsTrigger value="account">Account</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Performance Summary */}
              <Card>
                <CardHeader>
                  <CardTitle>Performance Summary</CardTitle>
                  <CardDescription>Your reseller performance this month</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Active Customers:</span>
                    <span className="font-medium">{dashboardData?.active_customers || 0} / {dashboardData?.total_customers || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Commission Rate:</span>
                    <span className="font-medium">{dashboardData?.commission_rate || 0}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Monthly Revenue:</span>
                    <span className="font-medium">${dashboardData?.monthly_revenue?.toLocaleString() || '0'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">This Month Commission:</span>
                    <span className="font-medium text-green-600">${dashboardData?.total_commission?.toLocaleString() || '0'}</span>
                  </div>
                </CardContent>
              </Card>

              {/* Quick Actions */}
              <Card>
                <CardHeader>
                  <CardTitle>Quick Actions</CardTitle>
                  <CardDescription>Common tasks and shortcuts</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <Button 
                      className="w-full justify-start bg-green-600 hover:bg-green-700"
                      onClick={handleAddCustomer}
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      Add New Customer
                    </Button>
                    <Button variant="outline" className="w-full justify-start">
                      <BarChart3 className="h-4 w-4 mr-2" />
                      View Analytics
                    </Button>
                    <Button variant="outline" className="w-full justify-start">
                      <Building className="h-4 w-4 mr-2" />
                      Marketing Materials
                    </Button>
                    <Button variant="outline" className="w-full justify-start">
                      <Target className="h-4 w-4 mr-2" />
                      Partner Resources
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>Latest updates and customer activity</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">New customer signup: ABC Corporation</p>
                      <p className="text-xs text-gray-500">January 22, 2025 - Business Fiber 500Mbps</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">Commission payment processed</p>
                      <p className="text-xs text-gray-500">January 15, 2025 - $1,797.00</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">Customer plan upgrade: Smith Family</p>
                      <p className="text-xs text-gray-500">January 18, 2025 - Premium to Business</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="customers" className="space-y-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Customer Management</CardTitle>
                  <CardDescription>Manage your customer base and track their status</CardDescription>
                </div>
                <Button 
                  className="bg-green-600 hover:bg-green-700"
                  onClick={handleAddCustomer}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Customer
                </Button>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {customers.map((customer: ResellerCustomer) => (
                    <div key={customer.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center space-x-4">
                        <Building className="h-5 w-5 text-gray-400" />
                        <div>
                          <p className="font-medium">{customer.first_name} {customer.last_name}</p>
                          <p className="text-sm text-gray-500">{customer.email}</p>
                          <p className="text-xs text-gray-400">Joined: {customer.registration_date}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="text-right">
                          <p className="font-medium">{customer.services[0]?.service_name || 'No Service'}</p>
                          <p className="text-sm text-gray-500">${customer.services[0]?.monthly_fee || 0}/month</p>
                          <p className="text-xs text-green-600">Commission: ${customer.services[0]?.commission_amount || 0}</p>
                        </div>
                        <div className="flex flex-col items-center space-y-2">
                          {getStatusBadge(customer.status)}
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleViewCustomer(customer.id)}
                          >
                            <Eye className="h-4 w-4 mr-1" />
                            View
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="commissions" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Commission History</CardTitle>
                <CardDescription>Track your monthly commissions and payouts</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {commissionReports.map((commission: CommissionReport, index: number) => (
                    <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center space-x-4">
                        <DollarSign className="h-5 w-5 text-green-600" />
                        <div>
                          <p className="font-medium">{commission.period}</p>
                          <p className="text-sm text-gray-500">
                            {commission.customer_commissions.length} customers | ${commission.total_commission.toLocaleString()} revenue
                          </p>
                          <p className="text-xs text-gray-400">
                            Payout: {commission.payment_date || 'N/A'}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="text-right">
                          <p className="text-lg font-semibold text-green-600">
                            ${commission.total_commission.toLocaleString()}
                          </p>
                          {getStatusBadge(commission.payment_status)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="account" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Reseller Account</CardTitle>
                <CardDescription>Manage your reseller account details and settings</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-lg font-medium mb-4">Company Information</h3>
                    <div className="space-y-3">
                      <div>
                        <label className="text-sm font-medium text-gray-600">Company Name</label>
                        <p className="text-gray-900">{reseller?.name || 'N/A'}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-600">Email</label>
                        <p className="text-gray-900">{reseller?.email || 'N/A'}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-600">Phone</label>
                        <p className="text-gray-900">{reseller?.phone || 'N/A'}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-600">Business Address</label>
                        <p className="text-gray-900">{reseller?.address || 'N/A'}</p>
                      </div>
                    </div>
                  </div>
                  <div>
                    <h3 className="text-lg font-medium mb-4">Partner Settings</h3>
                    <div className="space-y-3">
                      <div>
                        <label className="text-sm font-medium text-gray-600">Partner Tier</label>
                        <div className="flex items-center space-x-2 mt-1">
                          {getTierIcon(reseller?.tier || 'bronze')}
                          {getStatusBadge(reseller?.tier || 'bronze')}
                        </div>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-600">Commission Rate</label>
                        <p className="text-gray-900">{reseller?.commission_rate || 0}%</p>
                      </div>
                      <div className="space-y-2 mt-4">
                        <Button variant="outline" className="w-full justify-start">
                          Update Company Information
                        </Button>
                        <Button variant="outline" className="w-full justify-start">
                          Change Password
                        </Button>
                        <Button variant="outline" className="w-full justify-start">
                          Notification Preferences
                        </Button>
                        <Button variant="outline" className="w-full justify-start">
                          Payment Settings
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Customer Registration Modal */}
      <Dialog open={isAddCustomerOpen} onOpenChange={setIsAddCustomerOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Add New Customer</DialogTitle>
            <DialogDescription>
              Register a new customer under your reseller account.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="name" className="text-right">
                Name *
              </Label>
              <Input
                id="name"
                value={customerForm.name}
                onChange={(e) => setCustomerForm({...customerForm, name: e.target.value})}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="email" className="text-right">
                Email *
              </Label>
              <Input
                id="email"
                type="email"
                value={customerForm.email}
                onChange={(e) => setCustomerForm({...customerForm, email: e.target.value})}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="phone" className="text-right">
                Phone *
              </Label>
              <Input
                id="phone"
                value={customerForm.phone}
                onChange={(e) => setCustomerForm({...customerForm, phone: e.target.value})}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="company" className="text-right">
                Company
              </Label>
              <Input
                id="company"
                value={customerForm.company}
                onChange={(e) => setCustomerForm({...customerForm, company: e.target.value})}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="plan" className="text-right">
                Service Plan
              </Label>
              <Select value={customerForm.plan} onValueChange={(value) => setCustomerForm({...customerForm, plan: value})}>
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="Select a plan" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="basic">Basic Plan</SelectItem>
                  <SelectItem value="standard">Standard Plan</SelectItem>
                  <SelectItem value="premium">Premium Plan</SelectItem>
                  <SelectItem value="enterprise">Enterprise Plan</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setIsAddCustomerOpen(false)}>
              Cancel
            </Button>
            <Button type="button" onClick={handleSubmitCustomer}>
              Create Customer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Customer Details Modal */}
      <Dialog open={isCustomerDetailsOpen} onOpenChange={setIsCustomerDetailsOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Customer Details</DialogTitle>
            <DialogDescription>
              View detailed information about this customer.
            </DialogDescription>
          </DialogHeader>
          {selectedCustomerId && (() => {
            const customer = getCustomerDetails(selectedCustomerId);
            return customer ? (
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-3 items-center gap-4">
                  <Label className="font-medium">Name:</Label>
                  <span className="col-span-2">{customer.first_name} {customer.last_name}</span>
                </div>
                <div className="grid grid-cols-3 items-center gap-4">
                  <Label className="font-medium">Email:</Label>
                  <span className="col-span-2">{customer.email}</span>
                </div>
                <div className="grid grid-cols-3 items-center gap-4">
                  <Label className="font-medium">Phone:</Label>
                  <span className="col-span-2">{customer.phone || 'N/A'}</span>
                </div>
                <div className="grid grid-cols-3 items-center gap-4">
                  <Label className="font-medium">Status:</Label>
                  <span className="col-span-2">
                    {getStatusBadge(customer.status)}
                  </span>
                </div>
                <div className="grid grid-cols-3 items-center gap-4">
                  <Label className="font-medium">Services:</Label>
                  <span className="col-span-2">{customer.services?.length || 0} active</span>
                </div>
                <div className="grid grid-cols-3 items-center gap-4">
                  <Label className="font-medium">Monthly Revenue:</Label>
                  <span className="col-span-2">${customer.monthly_revenue?.toFixed(2) || '0.00'}</span>
                </div>
                <div className="grid grid-cols-3 items-center gap-4">
                  <Label className="font-medium">Join Date:</Label>
                  <span className="col-span-2">
                    {customer.registration_date ? new Date(customer.registration_date).toLocaleDateString() : 'N/A'}
                  </span>
                </div>
              </div>
            ) : (
              <div className="py-4 text-center text-gray-500">
                Customer details not found.
              </div>
            );
          })()}
          <DialogFooter>
            <Button type="button" onClick={() => setIsCustomerDetailsOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default function ResellerPortalPage() {
  return (
    <ErrorBoundary>
      <AuthGuard requiredRole="reseller">
        <ResellerPortalPageContent />
      </AuthGuard>
    </ErrorBoundary>
  );
}
