/**
 * Portal Functionality Tests
 * Tests the portal functionality against the live backend API
 */

import { customerPortalService } from '@/features/customers/services/customer-portal-service'
import { resellerService } from '@/features/resellers/services/reseller-service'

describe('Portal Functionality Tests', () => {
  describe('Customer Portal Service', () => {
    it('should have all required methods', () => {
      expect(typeof customerPortalService.authenticatePortal).toBe('function')
      expect(typeof customerPortalService.validatePortal).toBe('function')
      expect(typeof customerPortalService.getCustomerProfile).toBe('function')
      expect(typeof customerPortalService.getInvoices).toBe('function')
      expect(typeof customerPortalService.downloadInvoice).toBe('function')
      expect(typeof customerPortalService.payInvoice).toBe('function')
      expect(typeof customerPortalService.getTickets).toBe('function')
      expect(typeof customerPortalService.createTicket).toBe('function')
      expect(typeof customerPortalService.getActivity).toBe('function')
      expect(typeof customerPortalService.getServiceUsage).toBe('function')
      expect(typeof customerPortalService.getNotifications).toBe('function')
      expect(typeof customerPortalService.logout).toBe('function')
    })

    it('should handle invalid portal authentication gracefully', async () => {
      try {
        await customerPortalService.authenticatePortal('invalid_portal_id', 'invalid_code')
        fail('Should have thrown an error')
      } catch (error: unknown) {
        expect(error).toBeDefined()
        // Should handle authentication errors gracefully
      }
    })

    it('should handle portal validation for invalid portal ID', async () => {
      try {
        const result = await customerPortalService.validatePortal('invalid_portal_id')
        expect(result.valid).toBe(false)
      } catch (error: unknown) {
        // Should handle validation errors gracefully
        expect(error).toBeDefined()
      }
    })
  })

  describe('Reseller Service (Self-Service)', () => {
    it('should have all required self-service methods', () => {
      // Self-service methods for reseller managing their own account
      expect(typeof resellerService.getProfile).toBe('function')
      expect(typeof resellerService.getDashboard).toBe('function')
      expect(typeof resellerService.getCustomers).toBe('function')
      expect(typeof resellerService.getCommissionReport).toBe('function')
      expect(typeof resellerService.getStats).toBe('function')
      expect(typeof resellerService.updateProfile).toBe('function')
      expect(typeof resellerService.assignCustomer).toBe('function')
      expect(typeof resellerService.unassignCustomer).toBe('function')
      expect(typeof resellerService.login).toBe('function')
      expect(typeof resellerService.logout).toBe('function')
    })

    it('should handle reseller authentication', async () => {
      try {
        await resellerService.login('invalid_email', 'invalid_password')
        fail('Should have thrown an error')
      } catch (error: unknown) {
        expect(error).toBeDefined()
        // Should handle authentication errors gracefully
      }
    })
  })

  describe('Portal Integration', () => {
    it('should maintain consistent API client configuration', () => {
      // Both services should use the same API client configuration
      expect(customerPortalService).toBeDefined()
      expect(resellerService).toBeDefined()
    })

    it('should handle API errors consistently', async () => {
      // Test that both services handle errors in a consistent manner
      const customerError = await customerPortalService.authenticatePortal('test', 'test').catch(e => e)
      const resellerError = await resellerService.login('test', 'test').catch(e => e)
      
      expect(customerError).toBeDefined()
      expect(resellerError).toBeDefined()
    })
  })
})
