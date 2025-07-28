import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import CustomerPortalPage from '../page'
import { customerPortalService } from '@/features/customers/services/customer-portal-service'
import { useToast } from '@/hooks/use-toast'

// Mock the customer portal service
jest.mock('@/features/customers/services/customer-portal-service', () => ({
  customerPortalService: {
    getCustomerProfile: jest.fn(),
    getServices: jest.fn(),
    getInvoices: jest.fn(),
    getTickets: jest.fn(),
    getActivity: jest.fn(),
    downloadInvoice: jest.fn(),
    makePayment: jest.fn(),
  },
}))

// Mock the toast hook
jest.mock('@/hooks/use-toast', () => ({
  useToast: jest.fn(),
}))

const mockCustomer = {
  id: 1,
  name: 'John Doe',
  email: 'john@example.com',
  phone: '+1234567890',
  address: '123 Main St, City, State 12345',
  account_number: 'ACC001',
  status: 'active',
}

const mockServices = [
  {
    id: 1,
    name: 'Internet Plan - 100 Mbps',
    type: 'internet',
    status: 'active',
    monthly_cost: 99.99,
    next_billing_date: '2024-02-01',
  },
  {
    id: 2,
    name: 'Voice Plan - Unlimited',
    type: 'voice',
    status: 'active',
    monthly_cost: 29.99,
    next_billing_date: '2024-02-01',
  },
]

const mockInvoices = [
  {
    id: 'INV-001',
    date: '2024-01-01',
    amount: 129.98,
    status: 'paid',
    due_date: '2024-01-15',
  },
  {
    id: 'INV-002',
    date: '2024-01-15',
    amount: 129.98,
    status: 'pending',
    due_date: '2024-01-30',
  },
]

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  
  const TestWrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
  TestWrapper.displayName = 'TestWrapper'
  return TestWrapper
}

// Mock URL.createObjectURL for download tests
global.URL.createObjectURL = jest.fn(() => 'mock-url')
global.URL.revokeObjectURL = jest.fn()

// Mock document.createElement and appendChild for download tests
const mockLink = {
  href: '',
  download: '',
  click: jest.fn(),
}
document.createElement = jest.fn().mockImplementation((tagName) => {
  if (tagName === 'a') {
    return mockLink
  }
  return {}
})
document.body.appendChild = jest.fn()
document.body.removeChild = jest.fn()

describe('CustomerPortalPage', () => {
  const mockCustomerPortalService = customerPortalService as jest.Mocked<typeof customerPortalService>

  beforeEach(() => {
    mockCustomerPortalService.getCustomerProfile.mockResolvedValue(mockCustomer)
    mockCustomerPortalService.getServices.mockResolvedValue(mockServices)
    mockCustomerPortalService.getInvoices.mockResolvedValue(mockInvoices)
    mockCustomerPortalService.getActivity.mockResolvedValue([])
    mockCustomerPortalService.getTickets.mockResolvedValue([])
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  it('renders the customer portal page', async () => {
    render(<CustomerPortalPage />, { wrapper: createWrapper() })
    
    await waitFor(() => {
      expect(screen.getByText('Customer Portal')).toBeInTheDocument()
      expect(screen.getByText('Welcome back, John Doe')).toBeInTheDocument()
    })
  })

  it('displays customer account information', async () => {
    render(<CustomerPortalPage />, { wrapper: createWrapper() })
    
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.getByText('john@example.com')).toBeInTheDocument()
      expect(screen.getByText('ACC001')).toBeInTheDocument()
    })
  })

  it('displays active services', async () => {
    render(<CustomerPortalPage />, { wrapper: createWrapper() })
    
    await waitFor(() => {
      expect(screen.getByText('Internet Plan - 100 Mbps')).toBeInTheDocument()
      expect(screen.getByText('Voice Plan - Unlimited')).toBeInTheDocument()
      expect(screen.getByText('$99.99')).toBeInTheDocument()
      expect(screen.getByText('$29.99')).toBeInTheDocument()
    })
  })

  it('displays invoice history', async () => {
    render(<CustomerPortalPage />, { wrapper: createWrapper() })
    
    await waitFor(() => {
      expect(screen.getByText('INV-001')).toBeInTheDocument()
      expect(screen.getByText('INV-002')).toBeInTheDocument()
      expect(screen.getByText('$129.98')).toBeInTheDocument()
    })
  })

  it('handles invoice download functionality', async () => {
    const user = userEvent.setup()
    const mockToast = jest.fn()
    
    ;(useToast as jest.Mock).mockReturnValue({
      toast: mockToast,
    })
    
    render(<CustomerPortalPage />, { wrapper: createWrapper() })
    
    await waitFor(() => {
      expect(screen.getByText('INV-001')).toBeInTheDocument()
    })
    
    // Find and click download button
    const downloadButtons = screen.getAllByText('Download')
    await user.click(downloadButtons[0])
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Download Started',
        description: 'Preparing invoice INV-001 for download...',
      })
    })
    
    // Verify download process
    await waitFor(() => {
      expect(global.URL.createObjectURL).toHaveBeenCalled()
      expect(mockLink.click).toHaveBeenCalled()
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Download Complete',
        description: 'Invoice INV-001 has been downloaded successfully.',
      })
    })
  })

  it('handles payment functionality', async () => {
    const user = userEvent.setup()
    const mockToast = jest.fn()
    
    // Mock window.confirm
    window.confirm = jest.fn().mockReturnValue(true)
    
    ;(useToast as jest.Mock).mockReturnValue({
      toast: mockToast,
    })
    
    render(<CustomerPortalPage />, { wrapper: createWrapper() })
    
    await waitFor(() => {
      expect(screen.getByText('INV-002')).toBeInTheDocument()
    })
    
    // Find and click pay button for pending invoice
    const payButtons = screen.getAllByText('Pay Now')
    await user.click(payButtons[0])
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Payment Portal',
        description: 'Initializing secure payment process...',
      })
    })
    
    // Verify confirmation dialog was shown
    expect(window.confirm).toHaveBeenCalledWith(
      expect.stringContaining('Proceed with payment for invoice INV-002?')
    )
    
    // Verify payment initiated toast
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Payment Initiated',
        description: 'Payment process started for invoice INV-002. You will receive a confirmation email shortly.',
      })
    }, { timeout: 2000 })
  })

  it('handles payment cancellation', async () => {
    const user = userEvent.setup()
    const mockToast = jest.fn()
    
    // Mock window.confirm to return false (cancelled)
    window.confirm = jest.fn().mockReturnValue(false)
    
    ;(useToast as jest.Mock).mockReturnValue({
      toast: mockToast,
    })
    
    render(<CustomerPortalPage />, { wrapper: createWrapper() })
    
    await waitFor(() => {
      expect(screen.getByText('INV-002')).toBeInTheDocument()
    })
    
    // Find and click pay button
    const payButtons = screen.getAllByText('Pay Now')
    await user.click(payButtons[0])
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Payment Cancelled',
        description: 'Payment process was cancelled by user.',
      })
    })
  })

  it('handles download errors gracefully', async () => {
    const user = userEvent.setup()
    const mockToast = jest.fn()
    
    // Mock URL.createObjectURL to throw an error
    global.URL.createObjectURL = jest.fn().mockImplementation(() => {
      throw new Error('Download failed')
    })
    
    ;(useToast as jest.Mock).mockReturnValue({
      toast: mockToast,
    })
    
    render(<CustomerPortalPage />, { wrapper: createWrapper() })
    
    await waitFor(() => {
      expect(screen.getByText('INV-001')).toBeInTheDocument()
    })
    
    // Find and click download button
    const downloadButtons = screen.getAllByText('Download')
    await user.click(downloadButtons[0])
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Download Failed',
        description: 'Unable to download the invoice. Please try again.',
        variant: 'destructive',
      })
    })
  })

  it('handles payment errors gracefully', async () => {
    const user = userEvent.setup()
    const mockToast = jest.fn()
    
    // Mock window.confirm to throw an error
    window.confirm = jest.fn().mockImplementation(() => {
      throw new Error('Payment error')
    })
    
    ;(useToast as jest.Mock).mockReturnValue({
      toast: mockToast,
    })
    
    render(<CustomerPortalPage />, { wrapper: createWrapper() })
    
    await waitFor(() => {
      expect(screen.getByText('INV-002')).toBeInTheDocument()
    })
    
    // Find and click pay button
    const payButtons = screen.getAllByText('Pay Now')
    await user.click(payButtons[0])
    
    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith({
        title: 'Payment Error',
        description: 'Unable to process payment. Please try again or contact support.',
        variant: 'destructive',
      })
    })
  })

  it('displays loading states', () => {
    mockCustomerPortalService.getCustomerProfile.mockImplementation(() => new Promise(() => {}))
    
    render(<CustomerPortalPage />, { wrapper: createWrapper() })
    
    // Should render without crashing during loading
    expect(screen.getByText('Customer Portal')).toBeInTheDocument()
  })

  it('handles service loading errors', async () => {
    mockCustomerPortalService.getCustomerProfile.mockRejectedValue(new Error('Failed to load'))
    
    render(<CustomerPortalPage />, { wrapper: createWrapper() })
    
    // Should handle error gracefully
    expect(screen.getByText('Customer Portal')).toBeInTheDocument()
  })
})
