import type { Meta, StoryObj } from '@storybook/react'
import { action } from '@storybook/addon-actions'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'

// Extract the modal component for Storybook
const CustomerDetailsModal = ({ 
  isOpen, 
  onClose, 
  customer 
}: {
  isOpen: boolean
  onClose: () => void
  customer: {
    id: number
    name: string
    email: string
    phone?: string
    status: string
    services?: Array<{ id: number; name: string }>
    monthly_revenue?: number
    created_at?: string
  } | null
}) => {
  const getStatusColor = (status: string) => {
    const variants = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-gray-100 text-gray-800',
      suspended: 'bg-red-100 text-red-800',
      pending: 'bg-yellow-100 text-yellow-800',
      paid: 'bg-green-100 text-green-800',
    };
    
    return variants[status as keyof typeof variants] || 'bg-gray-100 text-gray-800';
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Customer Details</DialogTitle>
          <DialogDescription>
            View detailed information about this customer.
          </DialogDescription>
        </DialogHeader>
        {customer ? (
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-3 items-center gap-4">
              <Label className="font-medium">Name:</Label>
              <span className="col-span-2">{customer.name}</span>
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
                <Badge className={getStatusColor(customer.status)}>
                  {customer.status.charAt(0).toUpperCase() + customer.status.slice(1)}
                </Badge>
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
                {customer.created_at ? new Date(customer.created_at).toLocaleDateString() : 'N/A'}
              </span>
            </div>
          </div>
        ) : (
          <div className="py-4 text-center text-gray-500">
            Customer details not found.
          </div>
        )}
        <DialogFooter>
          <Button type="button" onClick={onClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

const meta: Meta<typeof CustomerDetailsModal> = {
  title: 'Modals/CustomerDetailsModal',
  component: CustomerDetailsModal,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A modal component for displaying detailed customer information in the reseller portal.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    isOpen: {
      control: 'boolean',
      description: 'Controls whether the modal is open or closed',
    },
    onClose: {
      action: 'closed',
      description: 'Callback fired when the modal is closed',
    },
    customer: {
      description: 'Customer data to display in the modal',
    },
  },
}

export default meta
type Story = StoryObj<typeof meta>

const mockActiveCustomer = {
  id: 1,
  name: 'John Doe',
  email: 'john@example.com',
  phone: '+1234567890',
  status: 'active',
  services: [
    { id: 1, name: 'Internet Plan - 100 Mbps' },
    { id: 2, name: 'Voice Plan - Unlimited' }
  ],
  monthly_revenue: 129.98,
  created_at: '2024-01-01T00:00:00Z',
}

const mockSuspendedCustomer = {
  id: 2,
  name: 'Jane Smith',
  email: 'jane@example.com',
  phone: '+0987654321',
  status: 'suspended',
  services: [],
  monthly_revenue: 0,
  created_at: '2024-01-15T00:00:00Z',
}

const mockPendingCustomer = {
  id: 3,
  name: 'Bob Johnson',
  email: 'bob@example.com',
  status: 'pending',
  services: [
    { id: 3, name: 'Basic Internet Plan' }
  ],
  monthly_revenue: 49.99,
  created_at: '2024-01-20T00:00:00Z',
}

export const Default: Story = {
  args: {
    isOpen: true,
    onClose: action('closed'),
    customer: mockActiveCustomer,
  },
}

export const SuspendedCustomer: Story = {
  args: {
    isOpen: true,
    onClose: action('closed'),
    customer: mockSuspendedCustomer,
  },
}

export const PendingCustomer: Story = {
  args: {
    isOpen: true,
    onClose: action('closed'),
    customer: mockPendingCustomer,
  },
}

export const CustomerWithoutPhone: Story = {
  args: {
    isOpen: true,
    onClose: action('closed'),
    customer: {
      ...mockActiveCustomer,
      phone: undefined,
    },
  },
}

export const NoCustomerData: Story = {
  args: {
    isOpen: true,
    onClose: action('closed'),
    customer: null,
  },
}

export const Closed: Story = {
  args: {
    isOpen: false,
    onClose: action('opened'),
    customer: mockActiveCustomer,
  },
}

export const MinimalCustomerData: Story = {
  args: {
    isOpen: true,
    onClose: action('closed'),
    customer: {
      id: 4,
      name: 'Minimal Customer',
      email: 'minimal@example.com',
      status: 'active',
    },
  },
}
